import os
import email
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
EMAILS_DIR = BASE_DIR / "emails_extraits"
SORTIE_DIR = BASE_DIR / "emails_avec_images"

SORTIE_DIR.mkdir(parents=True, exist_ok=True)

compteur = 0

for nom_fichier in os.listdir(str(EMAILS_DIR)):
    chemin = EMAILS_DIR / nom_fichier
    
    with open(str(chemin), "rb") as f:
        msg = email.message_from_bytes(f.read())
    
    # Vérifier si l'email contient une image
    contient_image = False
    for part in msg.walk():
        if part.get_content_type().startswith("image/"):
            contient_image = True
            break
        # Certaines images sont embarquées en base64 dans le HTML
        if part.get_content_type() == "text/html":
            contenu = str(part.get_payload())
            if "data:image" in contenu or "base64" in contenu:
                contient_image = True
                break
    
    if contient_image:
        shutil.copy(str(chemin), str(SORTIE_DIR / nom_fichier))
        compteur += 1

print(f"✅ {compteur} emails avec images trouvés sur 481")