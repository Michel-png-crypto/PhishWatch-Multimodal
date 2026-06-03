"""Module de liaison — Relie l'extraction d'images et le calcul des scores."""

import json
from pathlib import Path
import comparer_logos as cl

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images_extraites"
FICHIER_RESULTATS_VISION = BASE_DIR / "resultats.json"

def executer_analyse_vision():
    print("=" * 80)
    print("ANALYSES ET NOTATION DES LOGOS VIA PHASH & SSIM")
    print("=" * 80)
    
    # 1. Charger les logos de référence officiels (ex: Apple, PayPal, Netflix...)
    logos_reference = cl.charger_logos()
    print(f"🔹 {len(logos_reference)} logo(s) de référence chargé(s).")
    
    if not IMAGES_DIR.is_dir():
        print(f"❌ Dossier d'images extraites introuvable : {IMAGES_DIR}")
        return
        
    lignes_resultats = []
    
    # 2. Parcourir toutes les images extraites des emails
    fichiers_images = list(IMAGES_DIR.glob("*.png"))
    print(f"🔹 Analyse de {len(fichiers_images)} image(s) extraite(s)...")
    
    for chemin_img in fichiers_images:
        nom_image = chemin_img.name # ex: email_0042_part1.png
        
        # Trouver à quel email appartient l'image
        # Exemple basique de détection de domaine : on simule ou on récupère
        # Ici on utilise une valeur par défaut, verifier_domaine l'ajustera si besoin
        domaine_expediteur = "inconnu.com" 
        
        # Analyser l'image avec le pHash et le SSIM
        meilleur_logo, score_visuel, details = cl.analyser_image(str(chemin_img), logos_reference)
        
        if meilleur_logo and score_visuel is not None:
            # Vérifier si le domaine est légitime pour cette marque
            est_officiel = cl.verifier_domaine(domaine_expediteur, meilleur_logo)
            # Calculer le score final ajusté selon le domaine
            score_final = cl.calculer_score_final(score_visuel, est_officiel)
            
            statut = "ALERTE" if score_final >= cl.SEUIL_ALERTE else "SAIN"
            
            lignes_resultats.append({
                "image": nom_image,
                "visual_score": round(score_visuel, 3),
                "ressemble_a": meilleur_logo,
                "score_final": round(score_final, 3),
                "statut": statut
            })
            if statut == "ALERTE":
                print(f"🚨 ALERT PHISHING : {nom_image} ressemble à {meilleur_logo} (Score: {score_final})")

    # 3. Sauvegarder au format attendu par fusion_multimodale.py
    with open(FICHIER_RESULTATS_VISION, "w", encoding="utf-8") as f:
        json.dump(lignes_resultats, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Fichier d'analyse vision enregistré : {FICHIER_RESULTATS_VISION} ({len(lignes_resultats)} lignes)")