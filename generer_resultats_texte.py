#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère resultats_texte.json complet pour 480 emails
Analyse: mots phishing, urgency markers, financial threats
"""

import json
import os
from pathlib import Path
from email import message_from_file
from datetime import datetime

# MOTS SUSPECTS FRANÇAIS
MOTS_SUSPECTS = {
    'urgence': ['urgent', 'immédiat', 'asap', "aujourd'hui", 'maintenant', 'rapide'],
    'action': ['cliquez', 'confirmer', 'mettre à jour', 'vérifier', 'valider', 'activer', 'cliquer'],
    'menace': ['compte suspendu', 'compte fermé', 'unauthorized', 'compromis', 'pirate', 'virus', 'suppression'],
    'finances': ['paiement', 'facture', 'remboursement', 'credit card', 'numéro de carte', 'transaction', 'carte bancaire'],
    'personnelles': ['mot de passe', 'identifiant', 'ssn', 'date naissance', 'sécurité sociale', 'n° client'],
}

def analyser_email_texte(email_id, text_content):
    """
    Analyse contenu texte email pour phishing markers
    """
    if not text_content or len(text_content) < 5:
        return {
            'email_id': email_id,
            'score_nlp': 0.0,
            'statut_nlp': 'SAIN',
            'mots_detectes': [],
            'categorie_menace': 'AUCUNE',
            'confiance': 0.0
        }
    
    text_lower = text_content.lower()
    mots_trouves = {}
    score_menaces = 0
    nombre_menaces = 0
    
    # Scanner les catégories de mots suspects
    for categorie, mots in MOTS_SUSPECTS.items():
        for mot in mots:
            if mot in text_lower:
                if categorie not in mots_trouves:
                    mots_trouves[categorie] = []
                mots_trouves[categorie].append(mot)
                score_menaces += 0.15  # Increment score par mot
                nombre_menaces += 1
    
    # Normaliser le score [0, 1]
    score_nlp = min(score_menaces / 10.0, 1.0) if nombre_menaces > 0 else 0.0
    
    # Déterminer statut
    if score_nlp >= 0.60:
        statut_nlp = 'ALERTE'
        categorie = 'PHISHING_PROBABLE'
    elif score_nlp >= 0.40:
        statut_nlp = 'SUSPECT'
        categorie = 'SUSPECT'
    else:
        statut_nlp = 'SAIN'
        categorie = 'AUCUNE'
    
    # Confiance: plus de mots = plus confiance
    confiance = min(nombre_menaces * 0.15, 0.95)
    
    return {
        'email': email_id,
        'score_nlp': round(score_nlp, 3),
        'statut_nlp': statut_nlp,
        'mots_detectes': list(mots_trouves.keys()),
        'menaces_detectees': list(mots_trouves.keys()),
        'nombre_mots_suspects': nombre_menaces,
        'categorie_menace': categorie,
        'confiance': round(confiance, 2)
    }

def extraire_texte_email(chemin_eml):
    """
    Extrait texte brut d'un fichier EML
    """
    try:
        with open(chemin_eml, 'r', encoding='utf-8', errors='ignore') as f:
            msg = message_from_file(f)
        
        texte = ""
        
        # Subject
        subject = msg.get('Subject', '')
        if subject:
            texte += subject + " "
        
        # Body text/plain et text/html
        for part in msg.walk():
            if part.get_content_type() in ['text/plain', 'text/html']:
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        payload = payload.decode('utf-8', errors='ignore')
                    texte += payload + " "
                except:
                    pass
        
        return texte.strip()
    except Exception as e:
        print(f"⚠️  Erreur lecture {chemin_eml}: {e}")
        return ""

def generer_resultats_texte():
    """
    Génère resultats_texte.json complet pour tous les emails
    """
    
    # Chemins
    emails_dir = Path('emails_extraits')
    output_file = Path('resultats_texte.json')
    
    if not emails_dir.exists():
        print(f"❌ Dossier {emails_dir} non trouvé")
        return False
    
    # Scanner tous les EML
    eml_files = sorted(emails_dir.glob('email_*.eml'))
    print(f"📧 Trouvé {len(eml_files)} emails à analyser...")
    
    if len(eml_files) == 0:
        print("❌ Aucun fichier email_*.eml trouvé")
        return False
    
    resultats = []
    stats = {
        'total': 0,
        'sain': 0,
        'suspect': 0,
        'alerte': 0,
        'erreur': 0
    }
    
    for idx, chemin_eml in enumerate(eml_files, 1):
        email_id = chemin_eml.stem  # email_0001 → 0001
        
        # Extraire texte
        texte = extraire_texte_email(str(chemin_eml))
        
        # Analyser
        resultat = analyser_email_texte(email_id, texte)
        resultats.append(resultat)
        
        # Stats
        stats['total'] += 1
        statut = resultat['statut_nlp'].lower()
        if statut in stats:
            stats[statut] = stats[statut] + 1
        
        # Progress
        if idx % 50 == 0 or idx == len(eml_files):
            print(f"  ✓ {idx}/{len(eml_files)} emails traités...")
    
    # Ajouter stats
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'module': 'NLP_ANALYZER',
            'version': '2.0',
            'coverage': len(resultats),
            'stats': stats
        },
        'resultats': resultats
    }
    
    # Sauver
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ resultats_texte.json généré: {len(resultats)} emails")
    print(f"   📊 SAIN: {stats['sain']}, SUSPECT: {stats.get('suspect', 0)}, ALERTE: {stats['alerte']}")
    
    return True

if __name__ == '__main__':
    import sys
    try:
        success = generer_resultats_texte()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
