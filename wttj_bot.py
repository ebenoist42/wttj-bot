import requests
import json
import time
import os
from datetime import datetime

# ============================================================
# CONFIGURATION - Modifie ces valeurs
# ============================================================

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1483091697284939817/u4P7ykolPQeUuKII846P0THtMwZFwVYraaRjjbRpAtq--Pdw794o2LdQyqR7DPiSoNg6"

# Mots-clés à chercher
SEARCH_QUERY = "cyber"

# Fichier pour mémoriser les offres déjà vues
SEEN_JOBS_FILE = "seen_jobs.json"

# Intervalle de vérification en secondes (900 = 15 minutes)
CHECK_INTERVAL = 900

# ============================================================
# FONCTIONS
# ============================================================

def load_seen_jobs():
    """Charge les offres déjà vues depuis le fichier JSON"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen_jobs):
    """Sauvegarde les offres déjà vues dans le fichier JSON"""
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def fetch_jobs():
    """Récupère les offres WTTJ via leur API interne"""
    url = "https://www.welcometothejungle.com/api/v1/jobs"
    params = {
        "query": SEARCH_QUERY,
        "page": 1,
        "per_page": 30,
        "contract_type[]": ["apprenticeship", "internship"],
        "office_country_code[]": "FR",
        "aroundQuery": "Ile-de-France, France",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.welcometothejungle.com/",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erreur lors de la récupération des offres : {e}")
        return None

def send_discord_notification(job):
    """Envoie une notification Discord pour une nouvelle offre"""
    title = job.get("name", "Titre inconnu")
    company = job.get("organization", {}).get("name", "Entreprise inconnue")
    contract = job.get("contract_type", {}).get("fr", "")
    city = job.get("office", {}).get("city", "")
    slug = job.get("slug", "")
    url = f"https://www.welcometothejungle.com/fr/companies/{job.get('organization', {}).get('slug', '')}/jobs/{slug}"
    
    message = {
        "content": f"🆕 **Nouvelle offre détectée !**\n\n**{title}**\n🏢 {company}\n📄 {contract} | 📍 {city}\n🔗 {url}"
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        response.raise_for_status()
        print(f"[{datetime.now()}] Notification envoyée : {title} - {company}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erreur Discord : {e}")

def check_new_jobs():
    """Vérifie les nouvelles offres et envoie des notifications"""
    print(f"[{datetime.now()}] Vérification des nouvelles offres...")
    
    data = fetch_jobs()
    if not data:
        return
    
    jobs = data.get("jobs", [])
    if not jobs:
        print(f"[{datetime.now()}] Aucune offre trouvée dans la réponse")
        return
    
    seen_jobs = load_seen_jobs()
    new_jobs_found = 0
    
    for job in jobs:
        job_id = str(job.get("id", ""))
        if job_id and job_id not in seen_jobs:
            send_discord_notification(job)
            seen_jobs.add(job_id)
            new_jobs_found += 1
    
    save_seen_jobs(seen_jobs)
    
    if new_jobs_found == 0:
        print(f"[{datetime.now()}] Aucune nouvelle offre")
    else:
        print(f"[{datetime.now()}] {new_jobs_found} nouvelle(s) offre(s) envoyée(s)")

# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    print("🤖 Bot WTTJ démarré !")
    print(f"Recherche : '{SEARCH_QUERY}' | Intervalle : {CHECK_INTERVAL // 60} minutes")
    print("=" * 50)
    
    # Première vérification immédiate
    check_new_jobs()
    
    # Boucle infinie
    while True:
        time.sleep(CHECK_INTERVAL)
        check_new_jobs()
