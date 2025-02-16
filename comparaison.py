import pandas as pd
from requete_sql import requete, save_donnees_sql
from dotenv import load_dotenv

load_dotenv()

def recup_article_chrono():
    df = pd.read_excel('pneus.xlsx', sheet_name='Entreprise')
    ean_code = df['EAN'].to_list()
    codes_in_clause = ', '.join(f"'{code}'" for code in ean_code)
    
    request_sql = f"""
            SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT 
                RTRIM(m.nom_marque) AS Marque, RTRIM(a.lib_art) AS Model, RTRIM(a.ind_charge) AS Charge, RTRIM(a.ind_vit) AS Vitesse, 
                RTRIM(a.largeur) AS Largeur, RTRIM(a.diam) AS Diametre, RTRIM(a.serie) AS Hauteur, t.prix_ht AS Prix_HT, 
                CASE WHEN c_sfam_art IN ('4H', 'CH', 'TH') THEN 'Hiver'
                WHEN c_sfam_art IN ('TE', 'CE', '44') THEN 'Ete' 
                WHEN c_sfam_art IN ('4TS', 'CTS', 'TTS') THEN '4 Saisons' ELSE ' ' END AS Saison,  
                FORMAT(GETDATE(), 'dd-MM-yyyy') AS Date, 'Chrono' AS 'Site', a.gencode AS 'EAN'
            FROM 
                ******..article a 
                LEFT JOIN ******..marque m ON m.c_marque = a.c_marque
                LEFT JOIN ******..lig_tarif t ON t.c_art = a.c_art
            WHERE 
                a.gencode IN ({codes_in_clause}) AND t.c_tarif = 'PLOMB' 
        """
        
    df = requete(request_sql)  
    
    save_donnees_sql(df)
    
    
if __name__ == '__main__':
    recup_article_chrono()