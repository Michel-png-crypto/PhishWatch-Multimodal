#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE NLP AMÉLIORÉ - v2.0
Analyse phishing avancée avec :
  - Détection d'orthographe et typos
  - Analyse de ponctuation suspecte
  - Patterns d'urgence
  - Spoofing de domaines
  - Sentiment d'alarme

Auteur: PhishWatch Team
"""

import json
import re
from pathlib import Path
from email import message_from_file
from datetime import datetime

# MOTS SUSPECTS FRANÇAIS ET ANGLAIS (ENRICHIS)
MOTS_SUSPECTS = {
    'urgence': [
        'urgent', 'immédiat', 'asap', "aujourd'hui", 'maintenant', 'rapide',
        'action immédiate', 'veuillez confirmer', 'veuillez valider',
        'action requise', 'renouveler', 'renouvellement'
    ],
    'action': [
        'cliquez', 'confirmer', 'mettre à jour', 'vérifier', 'valider', 'activer', 'cliquer',
        'vérifiez', 'confirmez', 'mettez à jour', 'signer', 'accepter'
    ],
    'menace': [
        'compte suspendu', 'compte fermé', 'unauthorized', 'compromis', 'pirate', 'virus', 'suppression',
        'bloqué', 'gelé', 'désactivé', 'violation', 'intrusion', 'malveillant',
        'accès refusé', 'erreur', 'problème'
    ],
    'finances': [
        'paiement', 'facture', 'remboursement', 'credit card', 'numéro de carte', 'transaction', 'carte bancaire',
        'virement', 'solde', 'prélèvement', 'cotisation', 'impôt', 'taxe', 'dû', 'montant'
    ],
    'personnelles': [
        'mot de passe', 'identifiant', 'ssn', 'date naissance', 'sécurité sociale', 'n° client',
        'numéro', 'code', 'secret', 'privé', 'personnel', 'confidentiel', 'sécurisé'
    ],
}

# PATTERNS D'URGENCE (REGEX)
PATTERNS_URGENCE = [
    r'(confirm|verify|update|activate|vérif|confirm)\s+(your|your|the|votre|l[ea])\s+(account|password|identity|email|compte|mot de passe)',
    r'act\s+(now|immediately|today|immediately|maintenant|aujourd)',
    r'within\s+\d+\s+(hours?|days?|minutes?|heures|jours|minutes)',
    r'failure\s+(will|to|entraîner)',
    r'(limited|exclusive|urgent|restreint)\s+offer',
    r'(click|verify|confirm|cliquez|vérif)\s+here\s+(immédiat|now|asap)',
]

# DOMAINES OFFICIELS (pour détecter spoofing)
DOMAINES_OFFICIELS = [
    'amazon.com', 'apple.com', 'paypal.com', 'google.com', 'facebook.com', 'microsoft.com',
    'netflix.com', 'instagram.com', 'credit-agricole.fr', 'societe-generale.fr', 'bnpparibas.fr',
    'impots.gouv.fr', 'ameli.fr', 'laposte.fr', 'orange.fr', 'sfr.fr', 'bouygues.fr'
]

def analyser_orthographe(texte):
    """
    Détecte les erreurs d'orthographe et typos (indicateur de phishing)
    Plus d'erreurs = plus suspect
    """
    if not texte or len(texte) < 20:
        return 0.0
    
    mots = texte.split()
    nb_mots = len(mots)
    
    # Mots trop courts (< 2 caractères) sont souvent des typos
    typos_courts = sum(1 for m in mots if len(m) < 2)
    
    # Mots avec chiffres au milieu (p4ssw0rd, t0ken, etc.)
    typos_leetspeak = len(re.findall(r'\w*[0-9]+\w*', texte))
    
    # Mots répétés (signe de mauvais français)
    mots_lower = [m.lower() for m in mots]
    repetitions = sum(1 for i in range(1, len(mots_lower)) if mots_lower[i] == mots_lower[i-1])
    
    # Majuscules mal placées (CrEdIt CaRd)
    maj_bizarres = len(re.findall(r'[a-z][A-Z]', texte))
    
    # Score orthographe
    score = (typos_courts + typos_leetspeak + repetitions + maj_bizarres*0.5) / nb_mots
    
    return min(score / 0.3, 1.0)  # Normaliser à [0, 1]


def analyser_ponctuation(texte):
    """
    Détecte patterns de ponctuation suspects
    Phishing utilise souvent: !!!, ???, MAJUSCULES EXCESSIVES
    """
    if not texte or len(texte) < 10:
        return 0.0
    
    score = 0.0
    
    # Trop d'exclamations
    nb_exclamations = texte.count('!')
    if nb_exclamations > 3:
        score += min(nb_exclamations / 10.0, 0.3)
    
    # Points d'interrogation répétés
    nb_points_interro = texte.count('?')
    if nb_points_interro > 2:
        score += min(nb_points_interro / 10.0, 0.2)
    
    # Majuscules excessives (>30% = suspect)
    caracteres = [c for c in texte if c.isalpha()]
    if caracteres:
        ratio_maj = sum(1 for c in caracteres if c.isupper()) / len(caracteres)
        if ratio_maj > 0.3:
            score += min((ratio_maj - 0.3) * 2, 0.3)
    
    # Points suspensifs (... ou …) = mystère artificiel
    nb_suspension = texte.count('...') + texte.count('…')
    if nb_suspension > 0:
        score += 0.15
    
    # Tirets ou traits d'union répétés (---- = séparation importante)
    nb_traits = len(re.findall(r'-{3,}', texte))
    if nb_traits > 0:
        score += 0.1
    
    return min(score, 1.0)


def analyser_urgence(texte):
    """
    Détecte patterns d'urgence artificielle
    """
    if not texte:
        return 0.0
    
    score = 0.0
    texte_lower = texte.lower()
    
    # Checker patterns regex
    for pattern in PATTERNS_URGENCE:
        if re.search(pattern, texte_lower, re.IGNORECASE):
            score += 0.2
    
    # Mots d'urgence simples
    mots_urgence_simples = [
        'urgent', 'immédiat', 'rapide', 'asap', 'aujourd',
        'now', 'immediately', 'quickly', 'immediately'
    ]
    count = sum(texte_lower.count(mot) for mot in mots_urgence_simples)
    score += min(count * 0.15, 0.3)
    
    return min(score, 1.0)


def detecter_spoofing_domaines(texte):
    """
    Détecte tentatives de spoofing de domaines
    Ex: 'verify-amazon.malicious.ru', 'secure-paypal.fake.com'
    """
    if not texte:
        return 0.0
    
    score = 0.0
    texte_lower = texte.lower()
    
    # Chercher patterns: [officiel-word] suivi d'un domaine
    for domaine_officiel in DOMAINES_OFFICIELS:
        domaine_base = domaine_officiel.split('.')[0]  # amazon, paypal, etc
        
        # Patterns: verify-amazon, secure-apple, update-paypal
        patterns = [
            rf'(verify|secure|update|confirm|account|verify){domaine_base}',
            rf'{domaine_base}[-.]?\w+\.(ru|tk|ml|com|xyz)',  # amazon-something.ru
            rf'{domaine_base}[-\.]?\w*\.\w{2,}(?!\.)',  # paypal-verify.ru
        ]
        
        for pattern in patterns:
            if re.search(pattern, texte_lower):
                score += 0.25
    
    return min(score, 1.0)


def analyser_email_texte_v2(email_id, text_content):
    """
    ANALYSE COMPLÈTE NLP v2.0
    Combine 5 techniques de détection
    """
    if not text_content or len(text_content) < 5:
        return {
            'email': email_id,
            'score_nlp': 0.0,
            'statut_nlp': 'SAIN',
            'mots_detectes': [],
            'menaces_detectees': [],
            'nombre_mots_suspects': 0,
            'categorie_menace': 'AUCUNE',
            'confiance': 0.0,
            'details': {
                'orthographe': 0.0,
                'ponctuation': 0.0,
                'urgence': 0.0,
                'spoofing': 0.0,
                'keywords': 0.0
            }
        }
    
    text_lower = text_content.lower()
    
    # ===== 1. ANALYSE KEYWORDS =====
    mots_trouves = {}
    score_keywords = 0
    nombre_mots = 0
    
    for categorie, mots in MOTS_SUSPECTS.items():
        for mot in mots:
            if mot in text_lower:
                if categorie not in mots_trouves:
                    mots_trouves[categorie] = []
                mots_trouves[categorie].append(mot)
                score_keywords += 0.15
                nombre_mots += 1
    
    score_keywords = min(score_keywords / 10.0, 1.0) if nombre_mots > 0 else 0.0
    
    # ===== 2. ANALYSE ORTHOGRAPHE =====
    score_orthographe = analyser_orthographe(text_content)
    
    # ===== 3. ANALYSE PONCTUATION =====
    score_ponctuation = analyser_ponctuation(text_content)
    
    # ===== 4. ANALYSE URGENCE =====
    score_urgence = analyser_urgence(text_content)
    
    # ===== 5. DÉTECTION SPOOFING =====
    score_spoofing = detecter_spoofing_domaines(text_content)
    
    # ===== SCORE FINAL NLP (moyenne pondérée) =====
    score_nlp = (
        score_keywords * 0.25 +      # Mots clés
        score_orthographe * 0.20 +   # Erreurs d'orthographe
        score_ponctuation * 0.20 +   # Ponctuation suspecte
        score_urgence * 0.20 +       # Patterns d'urgence
        score_spoofing * 0.15        # Spoofing domaines
    )
    
    # ===== DÉTERMINER STATUT =====
    if score_nlp >= 0.60:
        statut_nlp = 'ALERTE'
        categorie = 'PHISHING_PROBABLE'
    elif score_nlp >= 0.40:
        statut_nlp = 'SUSPECT'
        categorie = 'SUSPECT'
    else:
        statut_nlp = 'SAIN'
        categorie = 'AUCUNE'
    
    # Confiance = combinaison du nombre de signaux et du score
    nb_signaux = (
        (1 if score_keywords > 0.3 else 0) +
        (1 if score_orthographe > 0.2 else 0) +
        (1 if score_ponctuation > 0.2 else 0) +
        (1 if score_urgence > 0.2 else 0) +
        (1 if score_spoofing > 0.2 else 0)
    )
    confiance = min(score_nlp * (1 + nb_signaux * 0.15), 1.0)
    
    return {
        'email': email_id,
        'score_nlp': round(score_nlp, 3),
        'statut_nlp': statut_nlp,
        'mots_detectes': list(mots_trouves.keys()),
        'menaces_detectees': list(mots_trouves.keys()),
        'nombre_mots_suspects': nombre_mots,
        'categorie_menace': categorie,
        'confiance': round(confiance, 2),
        'details': {
            'orthographe': round(score_orthographe, 3),
            'ponctuation': round(score_ponctuation, 3),
            'urgence': round(score_urgence, 3),
            'spoofing': round(score_spoofing, 3),
            'keywords': round(score_keywords, 3),
        }
    }


def extraire_texte_email(chemin_eml):
    """Extrait texte brut d'un fichier EML"""
    try:
        with open(chemin_eml, 'r', encoding='utf-8', errors='ignore') as f:
            msg = message_from_file(f)
        
        texte = ""
        
        # Essayer body principal
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    texte = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                elif part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    # Simple HTML strip
                    html_clean = re.sub('<[^>]+>', ' ', html)
                    texte = html_clean
        else:
            texte = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Ajouter sujet (souvent phishing indicators)
        sujet = msg.get('Subject', '')
        if sujet:
            texte = f"{sujet} {texte}"
        
        return texte
    
    except Exception as e:
        print(f"[WARN] Erreur extraction {chemin_eml}: {e}")
        return ""


def generer_resultats_texte_v2():
    """Génère resultats_texte.json avec NLP v2.0"""
    
    emails_dir = Path('emails_extraits')
    output_file = Path('resultats_texte_v2.json')
    
    if not emails_dir.exists():
        print(f"❌ Dossier {emails_dir} non trouvé")
        return False
    
    eml_files = sorted(emails_dir.glob('email_*.eml'))
    print(f"📧 Trouvé {len(eml_files)} emails à analyser (NLP v2.0)...")
    
    if len(eml_files) == 0:
        print("❌ Aucun fichier email_*.eml trouvé")
        return False
    
    resultats = []
    stats = {
        'total_emails': len(eml_files),
        'alerte': 0,
        'suspect': 0,
        'sain': 0,
    }
    
    for idx, chemin_eml in enumerate(eml_files, 1):
        email_id = chemin_eml.stem
        
        # Extraire texte
        texte = extraire_texte_email(str(chemin_eml))
        
        # Analyser
        resultat = analyser_email_texte_v2(email_id, texte)
        resultats.append(resultat)
        
        # Stats
        statut = resultat['statut_nlp']
        if statut == 'ALERTE':
            stats['alerte'] += 1
        elif statut == 'SUSPECT':
            stats['suspect'] += 1
        else:
            stats['sain'] += 1
        
        # Progress
        if idx % 50 == 0 or idx == len(eml_files):
            print(f"  ✓ {idx}/{len(eml_files)} emails traités...")
    
    # Sauver
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'module': 'NLP_ANALYZER_V2',
            'version': '2.0',
            'stats': stats
        },
        'resultats': resultats
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ resultats_texte_v2.json généré: {stats['total_emails']} emails")
    print(f"   📊 ALERTE: {stats['alerte']}, SUSPECT: {stats['suspect']}, SAIN: {stats['sain']}")
    
    return True


if __name__ == '__main__':
    generer_resultats_texte_v2()
