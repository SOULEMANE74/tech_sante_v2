
# from pathlib import Path
# import sqlite3
# import os
# from langchain.tools import tool
# import requests
# from bs4 import BeautifulSoup
# import re
# from urllib.parse import unquote

# BASE_DIR = Path.cwd().resolve().parent

# SQL_DB_PATH = BASE_DIR/'databases/BaseHop.db'

# ##############################################################################################
# #---------------------------------------------Tools------------------------------------------#
# ##############################################################################################

# def calculate_distance(lat1, lon1, lat2, lon2):
#     """Retourne la distance en km entre deux points"""
#     import math
#     if not lat1 or not lon1 or not lat2 or not lon2:
#         return 9999 
        
#     R = 6371  # Rayon de la terre en km
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
#          math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
#          math.sin(dlon / 2) * math.sin(dlon / 2))
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
#     return R * c

# @tool
# def check_beds_availability(user_lat: float = None, user_lon: float = None):
#     """ Fonction pour voir la disponibilite des lits """
#     print("[DEBUG] L'agent consulte la base de données...")
#     try:
#         if not os.path.exists(SQL_DB_PATH):
#             return 'Erreur : Base de données introuvable.'
        
#         conn = sqlite3.connect(f"file:{SQL_DB_PATH}?mode=ro", uri=True)
#         c = conn.cursor()
        
#         # On récupère aussi lat, lon et le lien
#         query = """
#                     SELECT h.nom, h.ville, s.nom_service, s.lits_disponibles, h.latitude, h.longitude, h.lien_reservation
#                     FROM service s
#                     JOIN hospital h ON s.hospital_id = h.id
#                     WHERE s.lits_disponibles > 0
#         """
        
#         c.execute(query)
#         results = c.fetchall()
#         conn.close()

#         if not results: 
#             return "ALERTE: AUCUN LIT DISPONIBLE."

#         # Traitement des données
#         hospital_data = []
#         for row in results:
#             nom, ville, service, lits, h_lat, h_lon, lien = row
            
#             dist = 0
#             dist_str = ""
            
#             # Calcul de distance 
#             if user_lat and user_lon and h_lat and h_lon:
#                 dist = calculate_distance(user_lat, user_lon, h_lat, h_lon)
#                 dist_str = f"a {dist:.1f} km"
            
#             hospital_data.append({
#                 "info": f"- {nom} ({dist_str}) : {service} [{lits} places] -> Lien: {lien}",
#                 "distance": dist
#             })

#         # Tri par distance 
#         hospital_data.sort(key=lambda x: x["distance"])

#         txt = "DISPONIBILITES (Triees par proximite) :\n"
#         for item in hospital_data:
#             txt += item["info"] + "\n"
            
#         return txt
        
#     except Exception as e:
#         print('[BUG] Erreur SQL')
#         return f"Erreur SQL : {e}"
    

# ################################### PHARMACY SCRAPPING ######################################

# def pharma_scraping():

#     URL = "https://sites.google.com/view/pharmaciedegarde-lome/tour-de-garde/"

#     html = requests.get(URL, timeout=15).text
#     soup = BeautifulSoup(html, "html.parser")

#     pharmacies_raw = []

#     for a in soup.find_all("a"):
#         href = a.get("href", "")
#         text = a.get_text(strip=True).lower()
        

#         if "maps" in href or "itin" in text:
#             pharmacies_raw.append({
#                 "lien_itineraire": href,
#                 "context": a.find_parent().get_text(separator="\n")
#             })
#     return pharmacies_raw


# def extract_pharmacies(pharmacies_raw: list) -> dict:
    
#     pharmacies = []

#     for item in pharmacies_raw:
#         url = item.get("lien_itineraire", "")

#         # --- Extraction du nom ---
#         name_match = re.search(r"/dir//([^/]+),", url)
#         name = (
#             unquote(name_match.group(1)).replace("+", " ")
#             if name_match else "Nom inconnu"
#         )

#         # --- Extraction coordonnées GPS ---
#         lat, lon = None, None

#         marker_match = re.search(r"!2d([0-9\.\-]+)!2d([0-9\.\-]+)", url)
#         if marker_match:
#             lon = float(marker_match.group(1))
#             lat = float(marker_match.group(2))
#         else:
#             center_match = re.search(r"@([0-9\.\-]+),([0-9\.\-]+)", url)
#             if center_match:
#                 lat = float(center_match.group(1))
#                 lon = float(center_match.group(2))
#         pharmacies.append({
#             "name": name,
#             "latitude": lat,
#             "longitude": lon,
#             "lien_itineraire": url,
#         })

#     return {
#         "total": len(pharmacies),
#         "pharmacies": pharmacies
#     }

# @tool(description="Trouve les pharmacies les plus proches d'un utilisateur")
# def find_nearest_pharmacies(user_lat, user_lon):
    
#     pharmacies_data = extract_pharmacies(pharma_scraping())
#     results = []

#     for pharma in pharmacies_data["pharmacies"]:
#         if not pharma.get("latitude") or not pharma.get("longitude"):
#             continue

#         distance = calculate_distance(
#             user_lat,
#             user_lon,
#             pharma["latitude"],
#             pharma["longitude"]
#         )

#         results.append({
#             "name": pharma["name"],
#             "latitude": pharma["latitude"],
#             "longitude": pharma["longitude"],
#             "distance_km": round(distance, 2),
#             "lien_itinineraire": pharma.get("lien_itinineraire")
#         })

#     # Trier par distance croissante
#     results.sort(key=lambda x: x["distance_km"])

#     return results[:3]


from pathlib import Path
import sqlite3
import os
import json
import time
import math
import requests
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
from langchain.tools import tool
from typing import Optional
import pyshorteners


# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / 'databases'
SQL_DB_PATH = DB_DIR / 'BaseHop.db'
CACHE_FILE_PATH = DB_DIR / 'pharmacies_cache.json'

# Durée de validité du cache en secondes (24 heures = 86400)
CACHE_TTL = 86400 

##############################################################################################
#----------------------------------------- UTILITAIRES --------------------------------------#
##############################################################################################

def calculate_distance(lat1, lon1, lat2, lon2):
    """Retourne la distance en km entre deux points (Haversine)"""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 9999 
        
    R = 6371  # Rayon de la terre en km
    try:
        # Conversion sécurisée en float au cas où
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except ValueError:
        return 9999

##############################################################################################
#------------------------------------- OUTILS HOPITAUX --------------------------------------#
##############################################################################################

@tool
def check_beds_availability(user_lat: Optional[float] = None, user_lon: Optional[float] = None):
    """ 
    Consulte la base de données SQL pour trouver les lits d'hôpitaux disponibles.
    Trie les résultats par proximité si les coordonnées utilisateur sont fournies.
    """
    # print(f"[DEBUG] Check beds avec Lat: {user_lat}, Lon: {user_lon}") 
    try:
        if not os.path.exists(SQL_DB_PATH):
            return 'Erreur Critique : Base de données BaseHop.db introuvable.'
        
        conn = sqlite3.connect(f"file:{SQL_DB_PATH}?mode=ro", uri=True)
        c = conn.cursor()
        
        query = """
                    SELECT h.nom, h.ville, s.nom_service, s.lits_disponibles, h.latitude, h.longitude, h.lien_reservation
                    FROM service s
                    JOIN hospital h ON s.hospital_id = h.id
                    WHERE s.lits_disponibles > 0
        """
        
        c.execute(query)
        results = c.fetchall()
        conn.close()

        if not results: 
            return "ALERTE: AUCUN LIT DISPONIBLE DANS TOUT LE RÉSEAU."

        hospital_data = []
        for row in results:
            nom, ville, service, lits, h_lat, h_lon, lien = row
            
            dist = 9999
            dist_str = "Distance inconnue"
            
            # Vérification stricte que toutes les coordonnées sont présentes et non None
            if (user_lat is not None) and (user_lon is not None) and (h_lat is not None) and (h_lon is not None):
                dist = calculate_distance(user_lat, user_lon, h_lat, h_lon)
                dist_str = f"à {dist:.1f} km"
            
            hospital_data.append({
                "info": f"- {nom} ({dist_str}) : {service} [{lits} places] -> Lien: {lien}",
                "distance": dist
            })

        # Tri par distance (les plus proches d'abord)
        hospital_data.sort(key=lambda x: x["distance"])

        txt = f"DISPONIBILITÉS ({len(hospital_data)} trouvées) :\n"
        for item in hospital_data:
            txt += item["info"] + "\n"
            
        return txt
        
    except Exception as e:
        return f"Erreur Technique SQL : {e}"

##############################################################################################
#----------------------------------- GESTION DU CACHE PHARMA --------------------------------#
##############################################################################################

def _scrape_pharmacies_online():
    """Scrape le site en direct (Fonction interne lente)"""
    print("[INFO] Mise à jour du cache : Scraping des pharmacies en cours...")
    URL = "https://sites.google.com/view/pharmaciedegarde-lome/tour-de-garde/"
    
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"[ERREUR] Échec du téléchargement de la page : {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    pharmacies = []

    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()

        if "maps" in href or "itin" in text:
            # Extraction du nom
            name_match = re.search(r"/dir//([^/]+),", href)
            name = (
                unquote(name_match.group(1)).replace("+", " ")
                if name_match else "Pharmacie (Nom non détecté)"
            )

            # Extraction coordonnées GPS
            lat, lon = None, None
            marker_match = re.search(r"!2d([0-9\.\-]+)!2d([0-9\.\-]+)", href)
            if marker_match:
                lon = float(marker_match.group(1))
                lat = float(marker_match.group(2))
            else:
                center_match = re.search(r"@([0-9\.\-]+),([0-9\.\-]+)", href)
                if center_match:
                    lat = float(center_match.group(1))
                    lon = float(center_match.group(2))
            
            if lat and lon: 
                pharmacies.append({
                    "name": name,
                    "latitude": lat,
                    "longitude": lon,
                    "lien_itineraire": href
                })
    
    return pharmacies

def _get_pharmacies_data():
    """Gestionnaire intelligent : Cache vs Live"""
    data = {"timestamp": 0, "pharmacies": []}
    
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("[WARN] Cache corrompu, réinitialisation.")

    current_time = time.time()
    age = current_time - data.get("timestamp", 0)

    if age < CACHE_TTL and data["pharmacies"]:
        return data["pharmacies"]

    new_pharmacies = _scrape_pharmacies_online()

    if new_pharmacies:
        new_data = {
            "timestamp": current_time,
            "pharmacies": new_pharmacies
        }
        os.makedirs(DB_DIR, exist_ok=True)
        with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        return new_pharmacies
    
    else:
        return data["pharmacies"]

##############################################################################################
#------------------------------------- OUTILS PHARMACIE -------------------------------------#
##############################################################################################

@tool(description="Trouve les 3 pharmacies de garde les plus proches d'un utilisateur")
def find_nearest_pharmacies(user_lat: Optional[float] = None, user_lon: Optional[float] = None):
    """
    Recherche les pharmacies les plus proches.
    Args:
        user_lat (Optional[float]): Latitude de l'utilisateur.
        user_lon (Optional[float]): Longitude de l'utilisateur.
    """
    # Si les coordonnées sont absentes, on prévient l'agent
    if user_lat is None or user_lon is None:
        return "ERREUR : Les coordonnées GPS de l'utilisateur sont nécessaires pour trouver la pharmacie la plus proche. Demandez sa localisation."

    pharmacies_list = _get_pharmacies_data()
    
    if not pharmacies_list:
        return "ERREUR: Impossible de récupérer la liste des pharmacies de garde pour le moment."

    results = []
    
    for pharma in pharmacies_list:
        dist = calculate_distance(
            user_lat, user_lon,
            pharma["latitude"], pharma["longitude"]
        )
        s = pyshorteners.Shortener()
        long_url = pharma["lien_itineraire"]
        pharma["lien_itineraire"] = s.isgd.short(long_url)

        results.append({
            "name": pharma["name"],
            "distance_km": round(dist, 2),
            "lien_itineraire": pharma["lien_itineraire"]
        })

    results.sort(key=lambda x: x["distance_km"])
    top_3 = results[:3]
    
    response_txt = "PHARMACIES DE GARDE LES PLUS PROCHES :\n"
    for p in top_3:
        response_txt += f"- {p['name']} (à {p['distance_km']} km) -> {p['lien_itineraire']}\n"
        
    return response_txt

