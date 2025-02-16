import os
import re
import time
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requete_sql import save_donnees_sql
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.ERROR, filename='site2_errors.log')

# Configuration des sélecteurs XPATH/ID
XPATHS = {
    'cookies_button': '/html/body/div[1]/div/div/div/div[1]/button[2]',
    'login_button': '/html/body/nav/div[1]/div[1]/div/div[1]/a[2]',
    'username_field': 'benutzername',
    'password_field': 'passwort',
    'submit_button': 'shop-login',
    'article_field': 'matchcodeid',
    'article_field_first': 'matchcodeid_kombi_1',
    'marque': '//*[@id="divergtablescroll"]/div[1]/div[3]',
    'model': '//*[@id="divergtablescroll"]/div[1]/div[4]',
    'saison': '//*[@id="iddiv_filter_container"]/div[1]/div[1]/img',
    'chaine': '//*[@id="divergtablescroll"]/div[1]/div[2]',
    'prix': '//*[@id="divergtablescroll"]/div[1]/div[12]/div/span[1]',
}

# Fonction de connexion au site


def login(driver: webdriver, username: str, password: str):
    """
    Effectue la connexion à un site donné.

    Args:
        driver (webdriver): Instance du navigateur Selenium.
        username (str): Nom d'utilisateur.
        password (str): Mot de passe.
    """
    try:
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, XPATHS['cookies_button']))
        ).click()
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, XPATHS['login_button']))
        ).click()
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, XPATHS['username_field']))
        ).send_keys(username)
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, XPATHS['password_field']))
        ).send_keys(password)
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, XPATHS['submit_button']))
        ).click()
    except Exception as ex:
        logging.error(f"Erreur lors de la connexion : {ex}")
        driver.quit()
        raise

# Fonction pour extraire les données d'un pneu


def extract_tire_data(driver: webdriver, ean: str, first_attempt: bool):
    """
    Extrait les informations d'un pneu à partir d'un EAN donné.

    Args:
        driver (webdriver): Instance du navigateur Selenium.
        ean (str): Code EAN du pneu.
        first_attempt (bool): Indique si c'est la première recherche.

    Returns:
        dict: Informations sur le pneu.
    """
    try:
        field_id = XPATHS['article_field_first'] if first_attempt else XPATHS['article_field']
        input_article = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, field_id))
        )

        if not first_attempt:
            driver.execute_script(
                f"document.getElementById('{XPATHS['article_field']}').value = '{ean}';")
        else:
            input_article.send_keys(ean)

        input_article.send_keys(Keys.ENTER)
        WebDriverWait(driver, 10).until(lambda d: len(
            d.find_elements(By.XPATH, XPATHS['marque'])) > 0)

        # Extraire les informations
        marque = driver.find_element(By.XPATH, XPATHS['marque']).text
        model = driver.find_element(By.XPATH, XPATHS['model']).text
        saison = driver.find_element(
            By.XPATH, XPATHS['saison']).get_attribute('title')
        if saison == 'Eté':
            saison = 'Ete'
        chaine = driver.find_element(By.XPATH, XPATHS['chaine']).text

        largeur = re.search(r'(\d{3})/', chaine).group(1)
        hauteur = re.search(r'/(\d{2})', chaine).group(1)
        diametre = re.search(r'R\s?(\d{2})', chaine).group(1)
        charge_vit = re.search(r'R\s?\d{2}\s?(\d{2})([A-Z])', chaine)
        charge = charge_vit.group(1)
        vitesse = charge_vit.group(2)
        prix = driver.find_element(By.XPATH, XPATHS['prix']).text

        return {
            'Marque': marque.upper(),
            'Model': chaine + ' ' + model,
            'Charge': charge,
            'Vitesse': vitesse,
            'Largeur': largeur,
            'Diametre': diametre,
            'Hauteur': hauteur,
            'Prix_HT': prix.split(' ')[0].replace('EUR', '').replace(',', '.'),
            'Saison': saison,
            'Date': datetime.now().strftime("%d-%m-%Y"),
            'Site': 'SITE2',
            'EAN': ean
        }
    except Exception as ex:
        logging.error(
            f"Erreur lors de l'extraction des données pour l'EAN {ean} : {ex}")
        return None

# Fonction principale


def site2():
    """Extrait les données des pneus depuis SITE2."""
    logging.basicConfig(level=logging.ERROR, filename='site2_errors.log')
    # Charger les données initiales
    df = pd.read_excel('pneus.xlsx', sheet_name='SITE2')
    df = df[df['EAN'] != '']

    options = Options()
    options.headless = False

    driver = webdriver.Firefox(options=options)
    driver.get(os.getenv('SITE2'))

    try:
        # Connexion
        login(driver, os.getenv('SITE2_LOG'), os.getenv('SITE2_PASS'))

        # Passer au deuxième onglet
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        # Extraire les données
        data = []
        for i, (_, row) in enumerate(df.iterrows()):
            ean = str(row['EAN']).split('.')[0]
            if ean != 'nan':
                time.sleep(2)
                tire_data = extract_tire_data(
                    driver, ean, first_attempt=(i == 0))
                time.sleep(2)
                if tire_data:
                    data.append(tire_data)

        # Sauvegarder les données
        df = pd.DataFrame(data)
        # df.to_csv('SITE2.csv', index=False)
        save_donnees_sql(df)

    except Exception as ex:
        logging.error(
            f"Erreur lors de l'extraction des données pour l'EAN {ean} : {ex}")

    finally:
        driver.quit()


if __name__ == '__main__':
    site2()
