import requests
from PIL import Image
import io, os

LOGOS_DIR = r"C:\logos_reference"
headers = {'User-Agent': 'Mozilla/5.0'}

logos = {
    # Ces URLs fonctionnent
    "google.png": "https://logodownload.org/wp-content/uploads/2014/09/google-logo-1.png",
    "facebook.png": "https://logodownload.org/wp-content/uploads/2014/09/facebook-logo-0.png",
    "microsoft.png": "https://logodownload.org/wp-content/uploads/2020/04/microsoft-logo-0.png",
    "netflix.png": "https://logodownload.org/wp-content/uploads/2014/10/netflix-logo-1.png",
    "instagram.png": "https://logodownload.org/wp-content/uploads/2017/04/instagram-logo-0.png",
    "dhl.png": "https://logodownload.org/wp-content/uploads/2014/12/dhl-logo-0.png",
    "bnp.png": "https://logodownload.org/wp-content/uploads/2017/02/bnp-paribas-logo-0.png",
}

for nom, url in logos.items():
    chemin = os.path.join(LOGOS_DIR, nom)
    try:
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img.save(chemin)
            taille = os.path.getsize(chemin)
            print(f"✅ {nom} → {taille:,} octets")
        else:
            print(f"❌ {nom} → Status {r.status_code}")
    except Exception as e:
        print(f"❌ {nom} → Erreur: {e}")

print("\n🎯 Terminé !")