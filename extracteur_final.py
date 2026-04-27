import os
import email
import json
import re
from urllib.parse import urlparse

# Dossiers source et destination
EMAILS_DIR = r"C:\logos_reference\emails_avec_images"
OUT_JSON = r"C:\logos_reference\metadata_emails.json"

def extraire_domaine(expediteur):
    """Extrait le domaine de l'adresse email (ex: service@paypal.com -> paypal.com)"""
    match = re.search(r'@([\w.-]+)', expediteur)
    return match.group(1).lower() if match else None

def extraire_metadata_email(chemin_eml):
    """Extrait les infos clés et les URLs d'images d'un fichier .eml"""
    with open(chemin_eml, "rb") as f:
        msg = email.message_from_bytes(f.read())

    expediteur = msg.get("From", "Inconnu")
    domaine = extraire_domaine(expediteur)
    urls_images = []

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                contenu = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                # Cherche les liens <img> ou les sources d'images
                urls_images.extend(re.findall(r'src=["\'](http[^"\']+)["\']', contenu))
            except:
                pass

    return {
        "fichier": os.path.basename(chemin_eml),
        "expediteur": expediteur,
        "domaine_mail": domaine,
        "urls_trouvees": list(set(urls_images)) # Supprime les doublons
    }

if _name_ == "_main_":
    if not os.path.exists(EMAILS_DIR):
        print(f"❌ Erreur : Le dossier {EMAILS_DIR} n'existe pas.")
    else:
        print("📁 Extraction des métadonnées en cours...")
        base_donnees = []
        
        for nom in os.listdir(EMAILS_DIR):
            if nom.endswith(".eml"):
                metadata = extraire_metadata_email(os.path.join(EMAILS_DIR, nom))
                base_donnees.append(metadata)

        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(base_donnees, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Terminé ! {len(base_donnees)} emails traités.")
        print(f"📄 Données sauvegardées dans : {OUT_JSON}")