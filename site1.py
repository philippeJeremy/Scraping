import os
import re
import time
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from dotenv import load_dotenv
from requete_sql import save_donnees_sql
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

logging.basicConfig(level=logging.ERROR, filename='site1_errors.log')

# Configuration des sélecteurs NAMES
NAMES = {
    'login': 'login',
    'password': 'password'
}

# Configuration des sélecteurs XPATH/ID
XPATHS = {
    'prix': '/html/body/div[2]/div[8]/div[7]/div[2]/div[1]/div[4]/table/tbody/tr/td[16]/span/b',
    'saison': '/html/body/div[2]/div[8]/div[7]/div[2]/div[1]/div[4]/table/tbody/tr/td[29]/b/img',
    'marque': '/html/body/div[2]/div[8]/div[7]/div[2]/div[1]/div[4]/table/tbody/tr/td[9]/img',
    'chaine': '/html/body/div[2]/div[8]/div[7]/div[2]/div[1]/div[4]/table/tbody/tr/td[11]/a',
}

ID = {
    'input_article': 'code_article_input'
}


def login(driver: webdriver, username: str, password: str):
    """
    Effectue la connexion à un site donné.

    Args:
        driver (webdriver): Instance du navigateur Selenium.
        username (str): Nom d'utilisateur.
        password (str): Mot de passe.
    """
    try:
        input_login = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, NAMES['login'])))
        input_login.send_keys(username)

        input_password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, NAMES['password'])))
        input_password.send_keys(password)
        time.sleep(2)
        input_password.send_keys(Keys.ENTER)
    except Exception as ex:
        logging.error(f"Erreur lors de la connexion : {ex}")
        driver.quit()
        raise


def extract_tire_data(driver: webdriver, ean: str) -> dict:
    """
    Extrait les informations d'un pneu à partir d'un EAN donné.

    Args:
        driver (webdriver): Instance du navigateur Selenium.
        ean (str): Code EAN du pneu.

    Returns:
        dict: Informations sur le pneu.
    """
    try:

        input_article = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, ID['input_article'])))
        driver.execute_script("arguments[0].value = '';", input_article)
        input_article.send_keys(ean)
        input_article.send_keys(Keys.ENTER)
        time.sleep(3)
        prix = driver.find_element(By.XPATH, XPATHS['prix']).text
        saison = driver.find_element(
            By.XPATH, XPATHS['saison']).get_attribute('title')
        if saison == 'été / hiver':
            saison = '4 Saisons'
        if saison == 'été':
            saison = 'Ete'
        marque = driver.find_element(
            By.XPATH, XPATHS['marque']).get_attribute('title')
        chaine = driver.find_element(By.XPATH, XPATHS['chaine']).text

        largeur = re.search(r'(\d{3})/', chaine)
        largeur = largeur.group(1)
        # Hauteur : deux chiffres après le '/'
        hauteur = re.search(r'/(\d{2})', chaine)
        hauteur = hauteur.group(1)
        # Diamètre : deux chiffres après le R (avec ou sans espace autour)
        diametre = re.search(r'R\s?(\d{2})', chaine)
        diametre = diametre.group(1)
        # Charge : deux chiffres suivis d'une lettre majuscule
        charge_vit = re.search(r'R\s?\d{2}\s?(\d{2})([A-Z])', chaine)
        charge = charge_vit.group(1)
        vitesse = charge_vit.group(2)

        return {
            'Marque': marque.upper(),
            'Model': chaine,
            'Charge': charge,
            'Vitesse': vitesse,
            'Largeur': largeur,
            'Diametre': diametre,
            'Hauteur': hauteur,
            'Prix_HT': prix,
            'Saison': saison,
            'Date': datetime.now().strftime("%d-%m-%Y"),
            'Site': 'SITE1',
            'EAN': ean
        }
    except Exception as ex:
        logging.error(
            f"Erreur lors de l'extraction des données pour l'EAN {ean} : {ex}")
        return None


def site1():
    """Extrait les données des pneus depuis SITE1."""
    logging.basicConfig(level=logging.ERROR, filename='SITE1_errors.log')
    # Charger les données initiales
    df = pd.read_excel('pneus.xlsx', sheet_name='SITE1')
    df = df[df['EAN'] != '']

    options = Options()
    options.headless = False

    driver = webdriver.Firefox(options=options)
    driver.get(os.getenv('SITE1'))
    data = []
    try:
        login(driver, os.getenv('SITE1_LOG'), os.getenv('SITE1_PASS'))

        for _, row in df.iterrows():
            ean = str(row['EAN']).split('.')[0]
            if ean != 'nan':
                time.sleep(2)
                tire_data = extract_tire_data(driver, ean)
                if tire_data:
                    data.append(tire_data)
    # Sauvegarder les données
        df = pd.DataFrame(data)
        # df.to_csv('SITE1.csv', index=False)
        save_donnees_sql(df)

    except Exception as ex:
        logging.error(
            f"Erreur lors de l'extraction des données pour l'EAN {ean} : {ex}")

    finally:
        driver.quit()


if __name__ == '__main__':
    site1()
