import os
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

logging.basicConfig(level=logging.ERROR, filename='site3_errors.log')

# Configuration des sélecteurs NAMES
ID = {
    'login': 'login_form_customer_code',
    'password': 'login_form_password',
    'input_article': 'inputReference'
}

XPATHS = {
    'prix': '/html/body/main/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div[4]/div/div[2]/div/div[2]/span[2]',
    'charge': '/html/body/main/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div[2]/div/div/ul/li[1]',
    'vitesse': '/html/body/main/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div[2]/div/div/ul/li[2]',
    'saison': '/html/body/main/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div[2]/div/div/ul/li[3]',
    'model_marque': '/html/body/main/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div[1]/div/div[2]/div/div[1]/p',
    'largeur_hauteur_diam': '/html/body/main/div/div/div[2]/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div[1]/div/div[2]/div/div[1]/span',
    'detail': '//*[@id="product-list-container"]/div/div[2]/div/div/div/div[1]/div/div[2]/div/div[3]/a',
    'input_ref': '//*[@id="advancedSearch"]/div[3]/div[1]/a',
    'model': '//*[@id="product-list-container"]/div/div[2]/div/div/div/div[1]/div/div[2]/div/div[1]/span'
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
            EC.presence_of_element_located((By.ID, ID['login'])))
        input_login.send_keys(username)

        input_password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, ID['password'])))
        input_password.send_keys(password)
        time.sleep(2)
        input_password.send_keys(Keys.ENTER)
        time.sleep(2)
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
        input_article = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, ID['input_article'])))
        driver.execute_script("arguments[0].value = '';", input_article)
        input_article.send_keys(ean)

        input_article.send_keys(Keys.ENTER)

        details = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.XPATH, XPATHS['detail'])))
        details.click()

        prix = driver.find_element(
            By.XPATH, XPATHS['prix']).text.replace('€', '')
        charge = driver.find_element(
            By.XPATH, XPATHS['charge']).text.split(':')[-1]
        vitesse = driver.find_element(
            By.XPATH, XPATHS['vitesse']).text.split(':')[-1]
        saison = driver.find_element(
            By.XPATH, XPATHS['saison']).text.split(':')[-1]
        marque = driver.find_element(
            By.XPATH, XPATHS['model_marque']).text.split(' ')[0]
        chaine = driver.find_element(By.XPATH, XPATHS['model']).text
        largeur_hauteur_diam = driver.find_element(
            By.XPATH, XPATHS['largeur_hauteur_diam'])
        largeur = largeur_hauteur_diam.text.split('/')[0]
        tab = largeur_hauteur_diam.text.split('-')[0]
        hauteur = tab.split('/')[-1]
        diametre = largeur_hauteur_diam.text.split('-')[-1]

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
            'Site': 'SITE3',
            'EAN': ean
        }
    except Exception as ex:
        logging.error(
            f"Erreur lors de l'extraction des données pour l'EAN {ean} : {ex}")
        return None


def SITE3():
    """Extrait les données des pneus depuis SITE3."""

    logging.basicConfig(level=logging.ERROR, filename='SITE3_errors.log')
    # Charger les données initiales
    df = pd.read_excel('pneus.xlsx', sheet_name='SITE3')
    df = df[df['EAN'] != '']

    options = Options()
    options.headless = False

    driver = webdriver.Firefox(options=options)
    driver.get(os.getenv('SITE3'))

    try:
        # Connexion
        login(driver, os.getenv('SITE3_LOG'), os.getenv('SITE3_PASS'))

        data = []

        details = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.XPATH, XPATHS['input_ref'])))
        details.click()

        for _, row in df.iterrows():

            ean = str(row['EAN']).split('.')[0]
            if ean != 'nan':
                time.sleep(2)
                tire_data = extract_tire_data(driver, ean)
                time.sleep(2)
                if tire_data:
                    data.append(tire_data)
    # Sauvegarder les données
        df = pd.DataFrame(data)
        df['Vitesse'] = df['Vitesse'].str.lstrip()
        df['Saison'] = df['Saison'].str.lstrip()
        df['Saison'] = df['Saison'].apply(lambda x: 'Ete' if x == 'Eté' else x)
        # df.to_csv('SITE3.csv', index=False)
        save_donnees_sql(df)
    except Exception as ex:
        logging.error(
            f"Erreur lors de l'extraction des données pour l'EAN {ean} : {ex}")

    finally:
        driver.quit()


if __name__ == '__main__':

    SITE3()
