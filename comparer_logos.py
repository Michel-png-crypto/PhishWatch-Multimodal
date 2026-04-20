import cv2
import numpy as np
import os
import json
import email
from PIL import Image
from skimage.metrics import structural_similarity as ssim

LOGOS_DIR = r"C:\logos_reference"
IMAGES_DIR = r"C:\logos_reference\images_extraites"
EMAILS_DIR = r"C:\logos_reference\emails_avec_images"
EXTENSIONS = (".png", ".jpg", ".jpeg")
SEUIL = 0.60

# ── DOMAINES OFFICIELS ────────────────────────────────────────────────────────
DOMAINES_OFFICIELS = {
    "amazon":          ["amazon.com", "amazon.fr", "amazonaws.com"],
    "apple":           ["apple.com", "icloud.com", "itunes.com"],
    "paypal":          ["paypal.com", "paypal.me"],
    "google":          ["google.com", "googleapis.com", "gstatic.com"],
    "facebook":        ["facebook.com", "fbcdn.net", "fb.com"],
    "microsoft":       ["microsoft.com", "microsoftonline.com", "outlook.com", "live.com"],
    "netflix":         ["netflix.com", "nflximg.com"],
    "instagram":       ["instagram.com", "cdninstagram.com"],
    "credit_agricole": ["credit-agricole.fr", "ca-paris.fr"],
}

# ── FONCTIONS DE COMPARAISON ──────────────────────────────────────────────────
def hash_perceptuel(img_gray, taille=(16, 16)):
    img = cv2.resize(img_gray, taille)
    moyenne = img.mean()
    return (img > moyenne).flatten()

def score_hash(hash1, hash2):
    return float(np.sum(hash1 == hash2)) / len(hash1)

def score_ssim(img1_gray, img2_gray, taille=(64, 64)):
    img1 = cv2.resize(img1_gray, taille)
    img2 = cv2.resize(img2_gray, taille)
    score, _ = ssim(img1, img2, full=True)
    return float(max(0.0, score))

def score_combine(hash_score, ssim_score):
    """60% hash + 40% SSIM — le hash reste dominant car plus stable"""
    return round(0.6 * hash_score + 0.4 * ssim_score, 3)

# ── CHARGEMENT DES LOGOS ──────────────────────────────────────────────────────
def charger_logos():
    logos = {}
    for nom in os.listdir(LOGOS_DIR):
        if not nom.lower().endswith(EXTENSIONS):
            continue
        if "email" in nom.lower():
            continue
        chemin = os.path.join(LOGOS_DIR, nom)
        try:
            img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                logos[nom] = img
                print(f"✅ Logo chargé : {nom}")
        except Exception as e:
            print(f"❌ Erreur logo {nom}: {e}")
    return logos

# ── ANALYSE D'UNE IMAGE ───────────────────────────────────────────────────────
def analyser_image(chemin_image, logos):
    img = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    hash_img = hash_perceptuel(img)
    meilleur_logo = None
    meilleur_score = 0.0
    tous_scores = {}

    for nom_logo, logo_gray in logos.items():
        h_score = score_hash(hash_img, hash_perceptuel(logo_gray))
        s_score = score_ssim(img, logo_gray)
        score_final = score_combine(h_score, s_score)
        tous_scores[nom_logo] = {
            "hash": round(h_score, 3),
            "ssim": round(s_score, 3),
            "combined": score_final
        }
        if score_final > meilleur_score:
            meilleur_score = score_final
            meilleur_logo = nom_logo

    return meilleur_logo, meilleur_score, tous_scores

# ── EXTRACTION EXPÉDITEUR ─────────────────────────────────────────────────────
def extraire_expediteur(chemin_eml):
    try:
        import re
        with open(chemin_eml, "rb") as f:
            msg = email.message_from_bytes(f.read())
        expediteur = msg.get("From", "")
        match = re.search(r'@([\w.\-]+)', expediteur)
        if match:
            return expediteur, match.group(1).lower()
        return expediteur, ""
    except:
        return "", ""

def verifier_domaine(domaine_expediteur, nom_logo):
    """Vérifie si le domaine expéditeur correspond au logo détecté."""
    marque = nom_logo.lower().replace(".png","").replace(".jpeg","").replace(".jpg","")

    for cle, domaines in DOMAINES_OFFICIELS.items():
        if cle in marque or marque.startswith(cle):
            est_officiel = any(
                domaine_expediteur == d or domaine_expediteur.endswith("." + d)
                for d in domaines if "*" not in d
            )
            return est_officiel

    # Marque inconnue → domaine considéré comme NON officiel
    return False

def calculer_score_final(visual_score, domaine_officiel, seuil=0.55):
    """
    Si logo détecté ET domaine non officiel → score augmenté (phishing probable)
    Si logo détecté ET domaine officiel    → score réduit  (email légitime)
    """
    if visual_score < seuil:
        return visual_score  # Clairement sain, on ne touche pas

    if domaine_officiel:
        return round(visual_score * 0.5, 3)   # Légitime → on réduit
    else:
        return round(min(visual_score * 1.2, 1.0), 3)  # Suspect → on augmente

# ── PROGRAMME PRINCIPAL ───────────────────────────────────────────────────────
if __name__ == "__main__":
    logos = charger_logos()
    print(f"\n📦 {len(logos)} logos chargés\n")

    resultats = []
    alertes = 0

    # Mapping image → email source
    mapping_email = {}
    for nom_eml in os.listdir(EMAILS_DIR):
        if not nom_eml.endswith(".eml"):
            continue
        email_id = nom_eml.replace(".eml", "")
        for nom_img in os.listdir(IMAGES_DIR):
            if nom_img.startswith(email_id):
                mapping_email[nom_img] = nom_eml

    for nom_image in sorted(os.listdir(IMAGES_DIR)):
        if not nom_image.lower().endswith(EXTENSIONS):
            continue

        chemin_image = os.path.join(IMAGES_DIR, nom_image)
        resultat = analyser_image(chemin_image, logos)
        if not resultat:
            continue

        meilleur_logo, visual_score, tous_scores = resultat

        # Croiser avec l'expéditeur
        nom_eml = mapping_email.get(nom_image, "")
        expediteur = ""
        domaine_expediteur = ""
        domaine_officiel = False

        if nom_eml:
            chemin_eml = os.path.join(EMAILS_DIR, nom_eml)
            expediteur, domaine_expediteur = extraire_expediteur(chemin_eml)
            if visual_score >= 0.55:
                domaine_officiel = verifier_domaine(domaine_expediteur, meilleur_logo)

        score_final = calculer_score_final(visual_score, domaine_officiel)
        statut = "ALERTE" if score_final >= SEUIL else "SAIN"

        if score_final >= SEUIL:
            alertes += 1
            flag = "🚨"
        else:
            flag = "✅"

        marque = meilleur_logo.replace(".png","").replace(".jpeg","").replace("_"," ").title()
        print(f"{flag} {nom_image}")
        print(f"   Logo       : {marque}")
        print(f"   Hash       : {tous_scores[meilleur_logo]['hash']*100:.1f}%  |  SSIM : {tous_scores[meilleur_logo]['ssim']*100:.1f}%  |  Combiné : {visual_score*100:.1f}%")
        print(f"   Expéditeur : {domaine_expediteur or 'inconnu'} ({'✅ officiel' if domaine_officiel else '⚠️ suspect'})")
        print(f"   Score final: {score_final*100:.1f}% → {statut}\n")

        resultats.append({
            "image": nom_image,
            "ressemble_a": meilleur_logo,
            "visual_score": visual_score,
            "score_final": score_final,
            "expediteur": expediteur,
            "domaine_expediteur": domaine_expediteur,
            "domaine_officiel": domaine_officiel,
            "statut": statut,
            "scores_detail": tous_scores[meilleur_logo]
        })

    with open(r"C:\logos_reference\resultats.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 {alertes} alertes sur {len(resultats)} images analysées")
    print(f"📁 Résultats sauvegardés dans resultats.json")