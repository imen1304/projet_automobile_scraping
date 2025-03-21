from fastapi import FastAPI, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI()

DB_CONFIG = {
    "dbname": "scrapping",
    "user": "postgres",
    "password": "1",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/annonces")
def get_annonces(
    carburant: str = Query(None, description="Filtrer par type de carburant"),
    boite: str = Query(None, description="Filtrer par type de boîte de vitesse"),
    min_prix: int = Query(None, description="Filtrer par prix minimum"),
    max_prix: int = Query(None, description="Filtrer par prix maximum")
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = "SELECT * FROM annonces_automobile WHERE 1=1"
    params = []

    if carburant:
        query += " AND carburant = %s"
        params.append(carburant)
    if boite:
        query += " AND boite = %s"
        params.append(boite)
    if min_prix:
        query += " AND prix >= %s"
        params.append(min_prix)
    if max_prix:
        query += " AND prix <= %s"
        params.append(max_prix)

    cur.execute(query, params)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

@app.get("/annonce/{id}")
def get_annonce(id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM annonces_automobile WHERE id = %s", (id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    return result
