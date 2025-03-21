import requests
from bs4 import BeautifulSoup
import re
import psycopg2
from datetime import datetime
import time
import os
import json

DB_CONFIG = {
    "dbname": "scrapping",
    "user": "postgres",
    "password": "1",
    "host": "localhost",
    "port": "5432"
}

def setup_session():
    session = requests.Session()
    return session

def scrape_details(url, session):
    try:
        response = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        details = {"année": "N/A", "kilométrage": "N/A", "carburant": "N/A", "boîte": "N/A"}
        
        specs = soup.select(".caracteristiques li")
        for spec in specs:
            text = spec.get_text(strip=True)
            if "Année" in text:
                details["année"] = text.split(":")[-1].strip()
            elif "Kilométrage" in text:
                details["kilométrage"] = text.split(":")[-1].strip()
            elif "Carburant" in text:
                details["carburant"] = text.split(":")[-1].strip()
            elif "Boîte" in text:
                details["boîte"] = text.split(":")[-1].strip()
        
        return details
    except requests.RequestException as e:
        print(f"Erreur scraping détails {url}: {e}")
        return {"année": "N/A", "kilométrage": "N/A", "carburant": "N/A", "boîte": "N/A"}

def scrape_automobile_tn(page_num=1, session=None):
    if session is None:
        session = setup_session()
    
    url = f"https://www.automobile.tn/fr/voiture-neuve.html?page={page_num}"
    try:
        response = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        annonces = []
        for card in soup.select(".annonce-item"):
            titre = card.select_one(".annonce-title").text.strip()
            prix = card.select_one(".annonce-price").text.strip()
            lien = "https://www.automobile.tn" + card.select_one("a")["href"]
            
            details = scrape_details(lien, session)
            
            annonces.append({
                "titre": titre,
                "prix": prix,
                "année": details["année"],
                "kilométrage": details["kilométrage"],
                "carburant": details["carburant"],
                "boîte": details["boîte"],
                "lien": lien
            })
            
            time.sleep(1)
        
        return annonces
    except requests.RequestException as e:
        print(f"Erreur scraping page {page_num}: {e}")
        return []

def save_to_postgres(annonces):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for annonce in annonces:
            cur.execute("""
                INSERT INTO annonces_automobile (titre, prix, annee, kilometrage, carburant, boite, lien)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (lien) DO NOTHING
            """, (
                annonce["titre"], annonce["prix"], annonce["année"], annonce["kilométrage"],
                annonce["carburant"], annonce["boîte"], annonce["lien"]
            ))
        
        conn.commit()
        print(f"{len(annonces)} annonces insérées dans PostgreSQL.")
    except psycopg2.Error as e:
        print(f"Erreur PostgreSQL : {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def save_to_json(annonces, filename="data/annonces.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)  
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(annonces, f, ensure_ascii=False, indent=4)
        print(f"{len(annonces)} annonces sauvegardées dans {filename}.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde JSON : {e}")

if __name__ == "__main__":
    session = setup_session()
    all_annonces = []
    for page in range(1, 3):
        print(f"Scraping page {page}...")
        page_annonces = scrape_automobile_tn(page, session)
        all_annonces.extend(page_annonces)
    
    print(f"Total annonces trouvées : {len(all_annonces)}")
    save_to_postgres(all_annonces)
    save_to_json(all_annonces)
