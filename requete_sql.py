import os
import pyodbc
import logging
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(level=logging.ERROR, filename='sql_errors.log')

def requete(sql_requete) -> pd.DataFrame:
    logging.basicConfig(level=logging.ERROR, filename='sql_errors.log')
    HOST = os.getenv('HOST')
    ID = os.getenv('ID')
    DATABASE = os.getenv('DATABASE')
    PSWD = os.getenv('PSWD')
    
    try:

        connection_string = f"mssql+pyodbc://{ID}:{PSWD}@{HOST}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server"

        engine = create_engine(connection_string)
    
        df = pd.read_sql_query(sql_requete, engine)
        
        engine.dispose()
    except Exception as ex:
        logging.error(f"Erreur lors de l'insertion des données : {ex}")
        if engine:
            engine.dispose()
    
    return df

def save_donnees_sql(df: pd.DataFrame):
    """
    Fonction qui sauvegardes les données dans une base SQL
    :param data: dictionnaire contenant les info recolter
    :param df_base: dataframe contenant les info à recolter
    :param profil: profil des pneu rechercher
    """
    logging.basicConfig(level=logging.ERROR, filename='sql_errors.log')
    HOST = os.getenv('HOST')
    ID = os.getenv('ID')
    DATABASE = os.getenv('DATABASE')
    PSWD = os.getenv('PSWD')

    str_connection_string = (
        "DRIVER={SQL Server};"
        f"SERVER={HOST};"
        f"DATABASE={DATABASE};"
        f"UID={ID};"
        f"PWD={PSWD};"
    )

    try:
        conn = pyodbc.connect(str_connection_string)
        conn.timeout = 0
        cursor = conn.cursor()
        cursor.execute("set transaction isolation level read uncommitted")

        for index, row in df.iterrows():
            cursor.execute("""
                    INSERT INTO scraping_price (Marque, Model, Charge, Vitesse, Largeur, Diametre, Hauteur, Prix_HT, Saison, Date, Site, EAN)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, row['Marque'], row['Model'], row['Charge'], row['Vitesse'], row['Largeur'], row['Diametre'],
                            row['Hauteur'], row['Prix_HT'], row['Saison'], row['Date'], row['Site'], row['EAN'])
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as ex:
        logging.error(f"Erreur lors de l'insertion des données : {ex}")
        if conn:
            conn.close()
        pass
