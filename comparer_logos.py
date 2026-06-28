# -*- coding: utf-8 -*-
"""
Module Vision - Comparaison de Logos
Analyse des images extraites et calcul des scores de phishing
Auteur: Florent Kalumuna (Etudiant 2)
"""

import cv2
import numpy as np
import os
import json
import email
import time
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from ocr_analyzer import analyser_image_complete

# CONFIG
LOGOS_DIR = r"C:\logos_reference"
IMAGES_DIR = r"C:\logos_reference\images_extraites"
EMAILS_DIR = r"C:\logos_reference\emails_avec_images"
RESULTATS_FILE = r"C:\logos_reference\resultats.json"
STATS_FILE = r"C:\logos_reference\stats_comparaison.json"

EXTENSIONS = (".png", ".jpg", ".jpeg")
SEUIL_ALERTE = 0.60              
SEUIL_VERIFICATION = 0.55        
HASH_SIZE = (16, 16)             
SSIM_SIZE = (64, 64)             
POIDS_HASH = 0.6                
POIDS_SSIM = 0.4                

# DOMAINES OFFICIELS
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


def hash_perceptuel(img_gray, taille=HASH_SIZE):
    """Genere un perceptual hash de l'image."""
    img = cv2.resize(img_gray, taille)
    moyenne = img.mean()
    return (img > moyenne).flatten()


def score_hash(hash1, hash2):
    """Compare 2 hashs -> Score 0-1"""
    return float(np.sum(hash1 == hash2)) / len(hash1)


def score_ssim(img1_gray, img2_gray, taille=SSIM_SIZE):
    """Structural Similarity - mesure la ressemblance visuelle."""
    img1 = cv2.resize(img1_gray, taille)
    img2 = cv2.resize(img2_gray, taille)
    score, _ = ssim(img1, img2, full=True)
    return float(max(0.0, score))


def score_combine(hash_score, ssim_score):
    """Combine les deux scores avec poids."""
    return round(POIDS_HASH * hash_score + POIDS_SSIM * ssim_score, 3)


def charger_logos():
    """Charge les logos de reference en grayscale"""
    logos = {}
    for nom in os.listdir(LOGOS_DIR):
        if not nom.lower().endswith(EXTENSIONS):
            continue
        if "email" in nom.lower() or "images_extraites" in nom:
            continue
        chemin = os.path.join(LOGOS_DIR, nom)
        try:
            img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
            if img is not None and img.size > 0:
                logos[nom] = img
                print("[OK] Logo {:<30} charge ({})".format(nom, img.shape))
            else:
                print("[WARN] Logo {:<30} invalide ou vide".format(nom))
        except Exception as e:
            print("[ERR] Erreur logo {}: {}".format(nom, e))
    return logos


def analyser_image(chemin_image, logos):
    """
    Compare une image testee contre TOUS les logos de reference.
    Retourne : (meilleur_logo, score_final, tous_scores) ou (None, None, None)
    """
    try:
        img = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
        if img is None or img.size == 0:
            return None, None, None

        hash_img = hash_perceptuel(img)
        meilleur_logo = None
        meilleur_score = 0.0
        tous_scores = {}

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
            except Exception:
                pass
        
        return meilleur_logo, meilleur_score, tous_scores
    except Exception:
        return None, None, None


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
    Verifie si le domaine de l'expediteur correspond au logo detecte.
    """
    marque = nom_logo.lower().replace(".png","").replace(".jpeg","").replace(".jpg","")

    for cle, domaines in DOMAINES_OFFICIELS.items():
        if cle in marque or marque.startswith(cle):
            est_officiel = any(
                domaine_expediteur == d or domaine_expediteur.endswith("." + d)
                for d in domaines if "*" not in d
            )
            return est_officiel

    return False


def calculer_score_final(visual_score, domaine_officiel, chemin_image=None, seuil_verification=SEUIL_VERIFICATION):
    """
    Ajuste le score final en fonction de la verification du domaine + OCR.
    
    Returns:
        (score_final, menaces_ocr, score_textuel)
    """
    menaces_ocr = []
    score_textuel = 0.0
    
    if chemin_image:
        try:
            analyse_ocr = analyser_image_complete(chemin_image)
            score_textuel = analyse_ocr['score_textuel']
            menaces_ocr = analyse_ocr['menaces_detectees']
        except:
            pass
    
    if score_textuel > 0:
        combined_score = round(visual_score * 0.6 + score_textuel * 0.4, 3)
    else:
        combined_score = visual_score
    
    if combined_score < seuil_verification:
        return combined_score, menaces_ocr, score_textuel

    if domaine_officiel:
        score_final = round(combined_score * 0.5, 3)
    else:
        score_final = round(min(combined_score * 1.2, 1.0), 3)
    
    if menaces_ocr and score_final > 0.5:
        score_final = round(min(score_final * 1.1, 1.0), 3)
    
    return score_final, menaces_ocr, score_textuel


if __name__ == "__main__":
    temps_debut = time.time()
    
    print("=" * 90)
    print("COMPARAISON DE LOGOS - Module Vision (Etudiant 2)")
    print("=" * 90)
    
    logos = charger_logos()
    if not logos:
        print("[ERR] Aucun logo charge ! Arret.")
        exit(1)
    
    print("\n[INFO] {} logos charges avec succes\n".format(len(logos)))

    mapping_email = {}
    for nom_eml in os.listdir(EMAILS_DIR):
        if not nom_eml.endswith(".eml"):
            continue
        email_id = nom_eml.replace(".eml", "")
        for nom_img in os.listdir(IMAGES_DIR):
            if nom_img.startswith(email_id):
                mapping_email[nom_img] = nom_eml

    resultats = []
    alertes = 0
    erreurs = 0
    images_analysees = 0

    for nom_image in sorted(os.listdir(IMAGES_DIR)):
        if not nom_image.lower().endswith(EXTENSIONS):
            continue

        chemin_image = os.path.join(IMAGES_DIR, nom_image)
        resultat = analyser_image(chemin_image, logos)
        
        if resultat[0] is None:
            erreurs += 1
            continue
        
        images_analysees += 1
        meilleur_logo, visual_score, tous_scores = resultat

        nom_eml = mapping_email.get(nom_image, "")
        expediteur = ""
        domaine_expediteur = ""
        domaine_officiel = False

        if nom_eml:
            chemin_eml = os.path.join(EMAILS_DIR, nom_eml)
            expediteur, domaine_expediteur = extraire_expediteur(chemin_eml)
            if visual_score >= SEUIL_VERIFICATION:
                domaine_officiel = verifier_domaine(domaine_expediteur, meilleur_logo)

        score_final, menaces_ocr, score_textuel = calculer_score_final(visual_score, domaine_officiel, chemin_image)
        statut = "ALERTE" if score_final >= SEUIL_ALERTE else "SAIN"

        if score_final >= SEUIL_ALERTE:
            alertes += 1
            flag = "[ALERTE]"
        else:
            flag = "[OK]"

        marque = meilleur_logo.replace(".png", "").replace(".jpeg", "").replace(".jpg", "").replace("_", " ").title()
        print("{} {:<35} -> {:<25} Score: {:.1%} ({})".format(flag, nom_image, marque, score_final, statut))
        if menaces_ocr:
            print("     -> OCR menaces: {}".format(', '.join(menaces_ocr[:2])))

        resultats.append({
            "image": nom_image,
            "ressemble_a": meilleur_logo,
            "visual_score": visual_score,
            "textuel_score": score_textuel,
            "score_final": score_final,
            "menaces_ocr": menaces_ocr,
            "expediteur": expediteur,
            "domaine_expediteur": domaine_expediteur,
            "domaine_officiel": domaine_officiel,
            "statut": statut,
            "scores_detail": tous_scores.get(meilleur_logo, {}),
        })

    with open(RESULTATS_FILE, "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

    temps_total = time.time() - temps_debut
    vitesse = round(images_analysees / temps_total, 1) if temps_total > 0 else 0
    
    print("\n" + "=" * 90)
    print("RESUME D'ANALYSE")
    print("=" * 90)
    print("Images analysees   : {}".format(images_analysees))
    print("Alertes            : {} ({:.1f}%)".format(alertes, alertes/images_analysees*100 if images_analysees > 0 else 0))
    print("Erreurs            : {}".format(erreurs))
    print("Temps total        : {:.2f}s".format(temps_total))
    print("Vitesse            : {:.1f} images/sec".format(vitesse))
    print("=" * 90)
    print("Resultats : {}".format(RESULTATS_FILE))
    print("Stats     : {}".format(STATS_FILE))
    
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
    
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("\nANALYSE TERMINEE")
