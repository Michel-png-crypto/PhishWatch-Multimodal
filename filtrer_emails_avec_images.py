import os
import email
import shutil

EMAILS_DIR = r"C:\logos_reference\emails_extraits"
SORTIE_DIR = r"C:\logos_reference\emails_avec_images"

os.makedirs(SORTIE_DIR, exist_ok=True)

compteur = 0

for nom_fichier in os.listdir(EMAILS_DIR):
    chemin = os.path.join(EMAILS_DIR, nom_fichier)
    
    with open(chemin, "rb") as f:
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
        shutil.copy(chemin, os.path.join(SORTIE_DIR, nom_fichier))
        compteur += 1

print(f"✅ {compteur} emails avec images trouvés sur 481")