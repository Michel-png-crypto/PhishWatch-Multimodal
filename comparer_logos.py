import cv2
import numpy as np
import os
import json
import email
import time
from pathlib import Path
from PIL import Image
from skimage.metrics import structural_similarity as ssim

# ─────────────────────────────────────────────────────────────────────────────
# 📋 CONFIGURATION — Module Vision (Florient Kalumuna)
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
LOGOS_DIR = BASE_DIR
IMAGES_DIR = BASE_DIR / "images_extraites"
EMAILS_DIR = BASE_DIR / "emails_avec_images"
RESULTATS_FILE = BASE_DIR / "resultats.json"
STATS_FILE = BASE_DIR / "stats_comparaison.json"

EXTENSIONS = (".png", ".jpg", ".jpeg")
SEUIL_ALERTE = 0.60              # ⚠️ Score minimum pour déclencher alerte
SEUIL_VERIFICATION = 0.55        # Score minimum pour vérifier domaine
HASH_SIZE = (16, 16)             # Taille du perceptual hash
SSIM_SIZE = (64, 64)             # Taille pour SSIM
POIDS_HASH = 0.6                 # 60% hash
POIDS_SSIM = 0.4                 # 40% SSIM

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

# ─────────────────────────────────────────────────────────────────────────────
# 🔧 FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def hash_perceptuel(img_gray, taille=HASH_SIZE):
    """
    Génère un perceptual hash de l'image.
    Plus résistant aux modifications mineures qu'un hash classique.
    
    Retourne : array boolean (256 bits)
    """
    img = cv2.resize(img_gray, taille)
    moyenne = img.mean()
    return (img > moyenne).flatten()

def score_hash(hash1, hash2):
    """Compare 2 hashs → Score 0-1 (O(1) complexity)"""
    return float(np.sum(hash1 == hash2)) / len(hash1)

def score_ssim(img1_gray, img2_gray, taille=SSIM_SIZE):
    """
    Structural Similarity — mesure la ressemblance visuelle structurelle.
    Plus lent mais plus précis que hash.
    
    Retourne : score 0-1
    """
    img1 = cv2.resize(img1_gray, taille)
    img2 = cv2.resize(img2_gray, taille)
    score, _ = ssim(img1, img2, full=True)
    return float(max(0.0, score))

def score_combine(hash_score, ssim_score):
    """
    Combine les deux scores avec poids.
    60% perceptual hash + 40% SSIM = équilibre vitesse/précision
    """
    return round(POIDS_HASH * hash_score + POIDS_SSIM * ssim_score, 3)

# ── CHARGEMENT DES LOGOS ──────────────────────────────────────────────────────
def charger_logos():
    """Charge les 9 logos de référence en grayscale"""
    logos = {}
    for nom in os.listdir(str(LOGOS_DIR)):
        if not nom.lower().endswith(EXTENSIONS):
            continue
        if "email" in nom.lower() or "images_extraites" in nom:
            continue
        chemin = str(LOGOS_DIR / nom)
        try:
            # Charger en grayscale directement
            img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
            if img is not None and img.size > 0:
                logos[nom] = img
                print(f"[OK] Logo {nom : <30} charge ({img.shape})")
            else:
                print(f"[WARN] Logo {nom : <30} invalide ou vide")
        except Exception as e:
            print(f"[ERR] Erreur logo {nom}: {e}")
    return logos

# ── ANALYSE D'UNE IMAGE ───────────────────────────────────────────────────────
def analyser_image(chemin_image, logos):
    """
    Compare une image testée contre TOUS les logos de référence.
    
    Retourne : (meilleur_logo, score_final, tous_scores) ou (None, None, None)
    """
    try:
        # Charger l'image en grayscale (compatible avec extraire_images.py)
        img = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
        if img is None or img.size == 0:
            return None, None, None

        hash_img = hash_perceptuel(img)
        meilleur_logo = None
        meilleur_score = 0.0
        tous_scores = {}

        # Comparer contre tous les logos
        for nom_logo, logo_gray in logos.items():
            try:
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
            except Exception as e:
                print(f"    [WARN] Erreur comparaison {nom_logo}: {e}")
        
        return meilleur_logo, meilleur_score, tous_scores
    
    except Exception as e:
        print(f"[ERR] Erreur analyse image : {e}")
        return None, None, None

# ── EXTRACTION EXPÉDITEUR ─────────────────────────────────────────────────────
def extraire_expediteur(chemin_eml):
    """Extrait adresse + domaine de l'email"""
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
    """
    Vérifie si le domaine de l'expéditeur correspond au logo détecté.
    
    Cas 1 : Apple logo + domaine apple.com → ✅ OFFICIEL
    Cas 2 : Apple logo + domaine malveillant.com → ⚠️ SUSPECT
    """
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

def calculer_score_final(visual_score, domaine_officiel, seuil_verification=SEUIL_VERIFICATION):
    """
    Ajuste le score final en fonction de la vérification du domaine.
    
    Logique :
    - Si image faible (< 0.55) → pas phishing probant
    - Si image forte + domaine officiel → probablement légitime → score réduit
    - Si image forte + domaine malveillant → probablement phishing → score augmenté
    """
    if visual_score < seuil_verification:
        return visual_score  # Clairement sain, on ne modifie pas

    if domaine_officiel:
        return round(visual_score * 0.5, 3)   # Légitime → réduction 50%
    else:
        return round(min(visual_score * 1.2, 1.0), 3)  # Suspect → augmentation 20%

# ─────────────────────────────────────────────────────────────────────────────
# 🚀 PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    temps_debut = time.time()
    
    print("=" * 90)
    print("COMPARAISON DE LOGOS — Module Vision (Florient)")
    print("=" * 90)
    
    # Charger les logos
    logos = charger_logos()
    if not logos:
        print("[ERR] Aucun logo charge. Arret.")
        exit(1)
    
    print(f"\n{len(logos)} logos charges avec succes\n")

    # Mapping image → email source
    mapping_email = {}
    for nom_eml in os.listdir(str(EMAILS_DIR)):
        if not nom_eml.endswith(".eml"):
            continue
        email_id = nom_eml.replace(".eml", "")
        for nom_img in os.listdir(str(IMAGES_DIR)):
            if nom_img.startswith(email_id):
                mapping_email[nom_img] = nom_eml

    # Analyser toutes les images
    resultats = []
    alertes = 0
    erreurs = 0
    images_analysees = 0

    for nom_image in sorted(os.listdir(str(IMAGES_DIR))):
        if not nom_image.lower().endswith(EXTENSIONS):
            continue

        chemin_image = str(IMAGES_DIR / nom_image)
        resultat = analyser_image(chemin_image, logos)
        
        if resultat[0] is None:  # Erreur d'analyse
            erreurs += 1
            continue
        
        images_analysees += 1
        meilleur_logo, visual_score, tous_scores = resultat

        # Croiser avec l'expéditeur
        nom_eml = mapping_email.get(nom_image, "")
        expediteur = ""
        domaine_expediteur = ""
        domaine_officiel = False

        if nom_eml:
            chemin_eml = str(EMAILS_DIR / nom_eml)
            expediteur, domaine_expediteur = extraire_expediteur(chemin_eml)
            if visual_score >= SEUIL_VERIFICATION:
                domaine_officiel = verifier_domaine(domaine_expediteur, meilleur_logo)

        score_final = calculer_score_final(visual_score, domaine_officiel)
        statut = "ALERTE" if score_final >= SEUIL_ALERTE else "SAIN"

        if score_final >= SEUIL_ALERTE:
            alertes += 1
            flag = "[ALERTE]"
        else:
            flag = "[OK]"

        marque = meilleur_logo.replace(".png","").replace(".jpeg","").replace("_"," ").title()
        print(f"{flag} {nom_image : <35} -> {marque : <25} Score: {score_final:.1%} ({statut})")

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

    # ─ SAUVEGARDE RÉSULTATS ─────────────────────────────────────────────────────────
    with open(str(RESULTATS_FILE), "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

    # ─ STATISTIQUES ─────────────────────────────────────────────────────────────────
    temps_total = time.time() - temps_debut
    stats = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "durée_secondes": round(temps_total, 2),
        "images_analysees": images_analysees,
        "alertes": alertes,
        "erreurs": erreurs,
        "taux_alertes": round(alertes / images_analysees * 100 if images_analysees > 0 else 0, 1),
        "config": {
            "seuil_alerte": SEUIL_ALERTE,
            "poids_hash": POIDS_HASH,
            "poids_ssim": POIDS_SSIM,
        }
    }

    with open(str(STATS_FILE), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # ─ RÉSUMÉ FINAL ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("RESUME D'ANALYSE")
    print("=" * 90)
    print(f"Images analysees   : {images_analysees}")
    print(f"Alertes          : {alertes} ({stats['taux_alertes']:.1f}%)")
    print(f"Erreurs          : {erreurs}")
    print(f"Temps total      : {temps_total:.2f}s")
    if images_analysees > 0:
        print(f"Vitesse          : {images_analysees/temps_total:.1f} images/sec")
    print("=" * 90)
    print(f"Resultats : {RESULTATS_FILE}")
    print(f"Stats     : {STATS_FILE}")
    print("ANALYSE TERMINEE")