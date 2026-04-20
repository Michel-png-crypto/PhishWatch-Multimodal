import requests
from PIL import Image
import io, os

LOGOS_DIR = r"C:\logos_reference"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

logos = {
    "microsoft.png": "https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31",
    "instagram.png": "https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png",
    "dhl.png": "https://www.dhl.com/content/dam/dhl/global/core/images/logos/dhl-logo.svg",
    "bnp.png": "https://mabanque.bnpparibas/etc/designs/mabanque/images/logo-bnp.png",
    "laposte.png": "https://upload.wikimedia.org/wikipedia/fr/thumb/8/8e/Logo_-_La_Poste.svg/320px-Logo_-_La_Poste.svg.png",
    "orange.png": "https://upload.wikimedia.org/wikipedia/fr/thumb/5/5b/Orange_logo.svg/320px-Orange_logo.svg.png",
}

for nom, url in logos.items():
    try:
        r = requests.get(url, timeout=10, headers=headers)
        print(f"{nom} - Status: {r.status_code} - Taille: {len(r.content):,} octets")
        if r.status_code == 200 and len(r.content) > 1000:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img.save(os.path.join(LOGOS_DIR, nom))
            print(f"  ✅ Sauvegardé !")
        else:
            print(f"  ❌ Ignoré (trop petit ou erreur)")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

print("\n🎯 Terminé !")