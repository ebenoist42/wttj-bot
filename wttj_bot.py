import requests
import json
import time
import os
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1483091697284939817/u4P7ykolPQeUuKII846P0THtMwZFwVYraaRjjbRpAtq--Pdw794o2LdQyqR7DPiSoNg6"
SEEN_JOBS_FILE = "seen_jobs.json"
CHECK_INTERVAL = 900  # 15 minutes

# ============================================================
# FONCTIONS
# ============================================================

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def fetch_jobs():
    """Récupère les offres via l'API Algolia utilisée par WTTJ"""
    url = "https://csekhvms53-dsn.algolia.net/1/indexes/*/queries"
    
    params = {
        "x-algolia-agent": "Algolia for JavaScript (4.14.2); Browser (lite)",
        "x-algolia-api-key": "7d4aa99c1c1e66bba3e5d1b876b6a7c1",
        "x-algolia-application-id": "CSEKHVMS53"
    }
    
    payload = {
        "requests": [
            {
                "indexName": "wttj_jobs_production_fr",
                "params": "query=cyber&filters=contract_type%3Aapprenticeship%20OR%20contract_type%3Ainternship&facetFilters=%5B%5B%22offices.country_code%3AFR%22%5D%5D&hitsPerPage=30&page=0"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://www.welcometothejungle.com/",
        "Origin": "https://www.welcometothejungle.com"
    }
    
    try:
        response = requests.post(url, params=params, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        hits = data.get("results", [{}])[0].get("hits", [])
        print(f"[{datetime.now()}] {len(hits)} offres trouvées")
        return hits
    except Exception as e:
        print(f"[{datetime.now()}] Erreur : {e}")
        return []

def send_discord_notification(job):
    title = job.get("name", "Titre inconnu")
    company = job.get("organization", {}).get("name", "Entreprise inconnue")
    contract = job.get("contract_type", "")
    offices = job.get("offices", [])
    city = offices[0].get("city", "") if offices else ""
    slug = job.get("slug", "")
    org_slug = job.get("organization", {}).get("slug", "")
    url = f"https://www.welcometothejungle.com/fr/companies/{org_slug}/jobs/{slug}"
    contract_fr = "Alternance" if contract == "apprenticeship" else "Stage" if contract == "internship" else contract

    message = {
        "content": f"🆕 **Nouvelle offre !**\n\n**{title}**\n🏢 {company}\n📄 {contract_fr} | 📍 {city}\n🔗 {url}"
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        response.raise_for_status()
        print(f"[{datetime.now()}] ✅ Envoyé : {title} - {company}")
    except Exception as e:
        print(f"[{datetime.now()}] Erreur Discord : {e}")

def check_new_jobs():
    print(f"[{datetime.now()}] Vérification des nouvelles offres...")
    jobs = fetch_jobs()
    if not jobs:
        return

    seen_jobs = load_seen_jobs()
    new_jobs_found = 0

    for job in jobs:
        job_id = str(job.get("objectID", ""))
        if job_id and job_id not in seen_jobs:
            send_discord_notification(job)
            seen_jobs.add(job_id)
            new_jobs_found += 1
            time.sleep(1)

    save_seen_jobs(seen_jobs)

    if new_jobs_found == 0:
        print(f"[{datetime.now()}] Aucune nouvelle offre")
    else:
        print(f"[{datetime.now()}] {new_jobs_found} nouvelle(s) offre(s) envoyée(s) !")

# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    print("🤖 Bot WTTJ démarré !")
    print(f"Intervalle : {CHECK_INTERVAL // 60} minutes")
    print("=" * 50)
    check_new_jobs()
    while True:
        time.sleep(CHECK_INTERVAL)
        check_new_jobs()
