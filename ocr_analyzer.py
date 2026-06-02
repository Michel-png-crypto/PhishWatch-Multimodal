# -*- coding: utf-8 -*-
"""
Module OCR + Typo Detection pour images.
Extraction de texte depuis images (OCR) et detection d'erreurs orthographiques.
Utilise par comparer_logos.py pour ajouter score textuel aux images.

Auteur: Florent Kalumuna (Etudiant 2)
Date: Juin 2025
"""

import pytesseract
import cv2
import numpy as np
from PIL import Image
from spellchecker import SpellChecker
import json
import re
from pathlib import Path

# CONFIGURATION
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LANGUES_OCR = "fra+eng"

try:
    pytesseract.pytesseract.pytesseract_cmd = TESSERACT_PATH
except:
    pass

# Spell checker
try:
    SPELL_CHECK_FR = SpellChecker(language='fr')
    SPELL_CHECK_EN = SpellChecker(language='en')
except:
    SPELL_CHECK_FR = None
    SPELL_CHECK_EN = None

# Mots suspects indiquant du phishing
MOTS_SUSPECTS = [
    'urgence', 'urgent', 'immediat', 'maintenant',
    'confirmer', 'verifier', 'cliquer', 'valider',
    'password', 'mot de passe', 'identifiant',
    'compte', 'acces', 'securite', 'bloque',
    'alerte', 'danger', 'action requise'
]


def extraire_texte_ocr(chemin_image):
    """
    Extrait texte d'une image via OCR (Tesseract).
    
    Args:
        chemin_image: Chemin vers l'image
        
    Returns:
        Texte extrait (lowercase), ou "" si erreur
    """
    try:
        img = Image.open(chemin_image)
        
        # Pretraitement: ameliorer contraste pour OCR
        img_cv = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
        if img_cv is not None and img_cv.size > 0:
            # Adaptive threshold pour mieux reconnaitre le texte
            img_cv = cv2.adaptiveThreshold(
                img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            img = Image.fromarray(img_cv)
        
        # OCR
        texte = pytesseract.image_to_string(img, lang=LANGUES_OCR)
        return texte.lower().strip()
    
    except Exception as e:
        return ""


def analyser_orthographe(texte):
    """
    Detecte typos/orthographe dans le texte.
    
    Returns:
        {
            'nb_typos': int,
            'typos': [list of errors],
            'score_ortho': float 0-1 (1.0 = parfait, 0.0 = erreurs massives),
            'ratio_erreurs': float
        }
    """
    if not texte or len(texte) < 5:
        return {'nb_typos': 0, 'typos': [], 'score_ortho': 1.0, 'ratio_erreurs': 0.0}
    
    try:
        mots = texte.split()
        if len(mots) < 2:
            return {'nb_typos': 0, 'typos': [], 'score_ortho': 1.0, 'ratio_erreurs': 0.0}
        
        # Verifier avec FR et EN
        typos_fr = SPELL_CHECK_FR.unknown(mots) if SPELL_CHECK_FR else set()
        typos_en = SPELL_CHECK_EN.unknown(mots) if SPELL_CHECK_EN else set()
        
        # Intersection (erreur dans les deux langues)
        typos = list(typos_fr & typos_en) if (typos_fr and typos_en) else list(typos_fr or typos_en)
        
        nb_typos = len(typos)
        ratio_erreurs = nb_typos / len(mots) if mots else 0.0
        
        # Score: 1.0 (parfait) - (ratio * 2)
        score_ortho = max(0.0, 1.0 - ratio_erreurs * 2)
        
        return {
            'nb_typos': nb_typos,
            'typos': typos,
            'score_ortho': round(score_ortho, 2),
            'ratio_erreurs': round(ratio_erreurs, 3)
        }
    
    except Exception as e:
        return {'nb_typos': 0, 'typos': [], 'score_ortho': 1.0, 'ratio_erreurs': 0.0}


def analyser_design_image(chemin_image):
    """
    Analyse qualite design de l'image (aspect ratio, resolution, etc).
    
    Returns:
        {
            'qualite': 'normal'|'suspect',
            'ratio_aspect': float,
            'dimensions': (width, height),
            'anomalies': [list]
        }
    """
    try:
        img = Image.open(chemin_image)
        w, h = img.size
        
        ratio = w / h if h > 0 else 1.0
        pixels = w * h
        
        anomalies = []
        qualite = 'normal'
        
        # Verifier aspect ratio anormal (trop allonge)
        if ratio < 0.5 or ratio > 2.0:
            anomalies.append(f"aspect_ratio_anormal_{ratio:.2f}")
            qualite = 'suspect'
        
        # Verifier resolution suspect (trop petite ou trop grande)
        if pixels < 1000 or pixels > 100000:
            anomalies.append(f"resolution_suspect_{pixels}")
            qualite = 'suspect'
        
        return {
            'qualite': qualite,
            'ratio_aspect': round(ratio, 2),
            'dimensions': (w, h),
            'anomalies': anomalies
        }
    
    except Exception as e:
        return {
            'qualite': 'unknown',
            'ratio_aspect': 0.0,
            'dimensions': (0, 0),
            'anomalies': ['erreur_lecture_image']
        }


def detecter_mots_suspects(texte):
    """
    Scanne le texte pour mots suspects (phishing keywords).
    
    Returns:
        [list of detected suspicious words]
    """
    if not texte:
        return []
    
    texte_lower = texte.lower()
    trouves = []
    
    for mot in MOTS_SUSPECTS:
        if mot in texte_lower:
            trouves.append(mot)
    
    return trouves


def analyser_image_complete(chemin_image):
    """
    Main orchestrator: analyse complete d'une image.
    
    Returns:
        {
            'ocr_texte': str (truncated 200 chars),
            'orthographe': {...},
            'design': {...},
            'mots_suspects': [...],
            'score_textuel': float 0-1,
            'menaces_detectees': [...]
        }
    """
    try:
        # Extraire texte
        texte_complet = extraire_texte_ocr(chemin_image)
        
        # Analyser orthographe
        ortho = analyser_orthographe(texte_complet)
        
        # Analyser design
        design = analyser_design_image(chemin_image)
        
        # Detecter mots suspects
        mots_suspects = detecter_mots_suspects(texte_complet)
        
        # Score textuel: 60% orthographe + 40% design quality
        score_design = 1.0 if design['qualite'] == 'normal' else 0.5
        score_textuel = (ortho['score_ortho'] * 0.6) + (score_design * 0.4)
        
        # Menaces detectees
        menaces = []
        if ortho['nb_typos'] > 2:
            menaces.append(f"many_typos_{ortho['nb_typos']}")
        if design['qualite'] == 'suspect':
            menaces.append("design_suspect")
        if mots_suspects:
            menaces.extend([f"phishing_keyword_{m}" for m in mots_suspects[:3]])
        
        return {
            'ocr_texte': texte_complet[:200] if texte_complet else "",
            'orthographe': ortho,
            'design': design,
            'mots_suspects': mots_suspects,
            'score_textuel': round(score_textuel, 2),
            'menaces_detectees': menaces
        }
    
    except Exception as e:
        return {
            'ocr_texte': "",
            'orthographe': {'nb_typos': 0, 'typos': [], 'score_ortho': 0.5, 'ratio_erreurs': 0},
            'design': {'qualite': 'unknown', 'ratio_aspect': 0, 'dimensions': (0, 0), 'anomalies': []},
            'mots_suspects': [],
            'score_textuel': 0.5,
            'menaces_detectees': ['erreur_analyse']
        }


# Test: si execute directement
if __name__ == "__main__":
    import os
    images_dir = "images_extraites"
    if os.path.exists(images_dir):
        images = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png', '.jpeg'))][:3]
        for img in images:
            path = os.path.join(images_dir, img)
            result = analyser_image_complete(path)
            print(f"\n{img}:")
            print(f"  OCR: {result['ocr_texte'][:50]}...")
            print(f"  Score textuel: {result['score_textuel']}")
            print(f"  Menaces: {result['menaces_detectees']}")
