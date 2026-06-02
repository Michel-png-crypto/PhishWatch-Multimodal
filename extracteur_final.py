import os
import email
import json
import re

EMAILS_DIR = r"C:\logos_reference\emails_extraits"

def extraire_donnees():
    base_donnees = []
    
    for nom_fichier in os.listdir(EMAILS_DIR):
        if not nom_fichier.endswith(".eml"): continue
        
        chemin = os.path.join(EMAILS_DIR, nom_fichier)
        with open(chemin, "rb") as f:
            msg = email.message_from_bytes(f.read())
            
            # 1. Extraire le corps du texte (Pour Junior - Étudiant 1)
            corps = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        corps = part.get_payload(decode=True).decode(errors='ignore')
            else:
                corps = msg.get_payload(decode=True).decode(errors='ignore')

            # 2. Extraire toutes les URLs (Pour ton module URL)
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', str(msg))

            base_donnees.append({
                "fichier": nom_fichier,
                "expediteur": msg['From'],
                "sujet": msg['Subject'],
                "texte": corps[:500], # On prend les 500 premiers caractères
                "urls": urls
            })

    # Sauvegarde pour le groupe
    with open("database_complete.json", "w", encoding="utf-8") as f:
        json.dump(base_donnees, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Analyse terminée : {len(base_donnees)} emails traités.")

if __name__ == "__main__":
    extraire_donnees()