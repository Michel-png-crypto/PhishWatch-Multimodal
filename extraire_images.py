import os
import email
import base64
import re
from PIL import Image
import io

EMAILS_DIR = r"C:\logos_reference\emails_avec_images"
SORTIE_DIR = r"C:\logos_reference\images_extraites"

os.makedirs(SORTIE_DIR, exist_ok=True)

compteur_images = 0
compteur_emails = 0

for nom_fichier in os.listdir(EMAILS_DIR):
    chemin = os.path.join(EMAILS_DIR, nom_fichier)

    with open(chemin, "rb") as f:
        msg = email.message_from_bytes(f.read())

    email_id = nom_fichier.replace(".eml", "")
    images_trouvees = 0

    for i, part in enumerate(msg.walk()):

        # Cas 1 : image en pièce jointe classique
        if part.get_content_type().startswith("image/"):
            try:
                data = part.get_payload(decode=True)
                if data:
                    img = Image.open(io.BytesIO(data)).convert("RGB")
                    nom = f"{email_id}_part{i}.png"
                    img.save(os.path.join(SORTIE_DIR, nom))
                    images_trouvees += 1
                    compteur_images += 1
            except Exception as e:
                print(f"  ⚠️ Erreur image pièce jointe ({nom_fichier}): {e}")

        # Cas 2 : image embarquée en base64 dans le HTML
        if part.get_content_type() == "text/html":
            try:
                contenu = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                pattern = r'data:image/(png|jpeg|jpg|gif);base64,([A-Za-z0-9+/=\s]+)'
                matches = re.findall(pattern, contenu)
                for j, (ext, b64data) in enumerate(matches):
                    try:
                        b64data_clean = b64data.replace("\n", "").replace("\r", "").replace(" ", "")
                        data = base64.b64decode(b64data_clean)
                        img = Image.open(io.BytesIO(data)).convert("RGB")
                        nom = f"{email_id}_html{j}.png"
                        img.save(os.path.join(SORTIE_DIR, nom))
                        images_trouvees += 1
                        compteur_images += 1
                    except Exception as e:
                        print(f"  ⚠️ Erreur image base64 ({nom_fichier}): {e}")
            except Exception as e:
                print(f"  ⚠️ Erreur HTML ({nom_fichier}): {e}")

    if images_trouvees > 0:
        compteur_emails += 1
        print(f"✅ {nom_fichier} → {images_trouvees} image(s) extraite(s)")

print(f"\n🎯 Total : {compteur_images} images extraites depuis {compteur_emails} emails")
print(f"📁 Dossier : {SORTIE_DIR}")