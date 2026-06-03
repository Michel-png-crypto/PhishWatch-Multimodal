"""Module Vision — Analyse et comparaison des logos (PhishWatch-Multimodal)."""

import os
import cv2
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SEUIL_ALERTE = 0.50

def hash_perceptuel(image_grayscale):
    """Calcule le hash perceptuel (pHash) d'une image en niveaux de gris."""
    # Redimensionner à 32x32 pour la DCT
    resized = cv2.resize(image_grayscale, (32, 32))
    # Convertir en float32 pour la transformée en cosinus discrète
    dct = cv2.dct(np.float32(resized))
    # Prendre le sous-bloc 8x8 en haut à gauche (basses fréquences)
    dct_low = dct[0:8, 0:8]
    # Calculer la médiane en excluant la composante DC (0,0)
    medienne = np.median(dct_low)
    # Générer le hash binaire
    return dct_low > medienne

def score_hash(hash1, hash2):
    """Calcule la similarité entre deux hashs perceptuels (Distance de Hamming inversée)."""
    distance = np.count_nonzero(hash1 != hash2)
    return 1.0 - (distance / 64.0)

def score_ssim(img1, img2):
    """Calcule un score de similarité structurelle simplifié basé sur OpenCV."""
    # S'assurer que les deux images font la même taille pour la comparaison
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    # Calcul de la corrélation croisée normalisée (alternative robuste à SSIM via OpenCV)
    res = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    return max(0.0, float(max_val))

def score_combine(s_hash, s_ssim):
    """Combine le score pHash (60%) et le score SSIM (40%)."""
    return (s_hash * 0.6) + (s_ssim * 0.4)

def verifier_domaine(domaine, logo_name):
    """Vérifie si le domaine de l'email correspond au logo officiel."""
    domaine = domaine.lower()
    logo_name = logo_name.lower()
    
    if "apple" in logo_name and "apple.com" in domaine:
        return True
    if "paypal" in logo_name and "paypal.com" in domaine:
        return True
    if "netflix" in logo_name and "netflix.com" in domaine:
        return True
    return False

def calculer_score_final(score_visuel, est_officiel):
    """Ajuste le score selon la légitimité du domaine."""
    if score_visuel >= 0.70 and not est_officiel:
        return min(1.0, score_visuel * 1.2) # Augmente le risque si usurpation de marque
    if score_visuel >= 0.80 and est_officiel:
        return 0.4 # Réduit le risque si c'est le vrai site officiel
    return score_visuel

def charger_logos():
    """Charge les logos de référence disponibles."""
    logos = {}
    # On cherche les fichiers logos à la racine ou dans un sous-dossier de référence
    extensions = ["*.png", "*.jpg", "*.jpeg"]
    for ext in extensions:
        for chemin in BASE_DIR.glob(ext):
            img = cv2.imread(str(chemin), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                logos[chemin.name] = img
    return logos

def analyser_image(chemin_image, logos):
    """Compare une image extraite avec le dictionnaire des logos de référence."""
    if not os.path.exists(chemin_image):
        return None, None, None
        
    img_suspecte = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
    if img_suspecte is None:
        return None, None, None

    meilleur_logo = None
    meilleur_score = -1.0

    for nom_logo, img_logo in logos.items():
        h1 = hash_perceptuel(img_suspecte)
        h2 = hash_perceptuel(img_logo)
        
        s_hash = score_hash(h1, h2)
        s_ssim = score_ssim(img_suspecte, img_logo)
        score_tot = score_combine(s_hash, s_ssim)
        
        if score_tot > meilleur_score:
            meilleur_score = score_tot
            meilleur_logo = nom_logo

    details = {"pHash": s_hash, "SSIM": s_ssim}
    return meilleur_logo, meilleur_score, details