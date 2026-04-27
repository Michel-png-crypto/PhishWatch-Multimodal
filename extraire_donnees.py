import requests
import json
import time

# OBTENTION CLÉ : Crée un compte gratuit sur virustotal.com -> Profile -> API Key
API_KEY = "TA_CLE_API_ICI" 

def verifier_avec_virustotal(url_a_tester):
    """Vérifie une URL suspecte via l'API VirusTotal v3."""
    if API_KEY == "TA_CLE_API_ICI":
        return "⚠️ Erreur : Configure ta clé API dans le script !"

    url_api = "https://www.virustotal.com/api/v3/urls"
    headers = {"x-apikey": API_KEY}
    
    try:
        # 1. Envoyer l'URL pour analyse
        response = requests.post(url_api, headers=headers, data={"url": url_a_tester})
        if response.status_code == 200:
            analysis_id = response.json()["data"]["id"]
            
            # 2. Attendre courtement le traitement
            time.sleep(2)
            
            # 3. Récupérer le rapport final
            report_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            report = requests.get(report_url, headers=headers).json()
            
            stats = report["data"]["attributes"]["stats"]
            return {
                "url": url_a_tester,
                "malicieux": stats["malicious"],
                "suspect": stats["suspicious"],
                "total_moteurs": sum(stats.values()),
                "decision": "DANGEREUX" if stats["malicious"] > 0 else "SAIN"
            }
        else:
            return f"Erreur API : {response.status_code}"
    except Exception as e:
        return f"Erreur connexion : {e}"

if _name_ == "_main_":
    # Test sur une URL de phishing connue (exemple)
    test = "http://secure-paypal-login-update.xyz"
    print(f"🔍 Vérification externe de : {test}")
    resultat = verifier_avec_virustotal(test)
    print(json.dumps(resultat, indent=4))