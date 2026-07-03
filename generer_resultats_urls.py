#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère resultats_urls.json complet pour tous les emails
Analyse: typosquatting + threat intelligence via VirusTotal
"""

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
import time
from datetime import datetime
from email import message_from_file

# Try to load from .env
try:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8-sig')
except ImportError:
    pass

VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')

# Domaines officiels pour detection typosquatting
DOMAINES_OFFICIELS = {
    'google.com': 'Google',
    'facebook.com': 'Facebook',
    'amazon.com': 'Amazon',
    'microsoft.com': 'Microsoft',
    'apple.com': 'Apple',
    'netflix.com': 'Netflix',
    'paypal.com': 'PayPal',
    'twitter.com': 'Twitter',
    'instagram.com': 'Instagram',
}

# Cache local pour éviter re-queries VirusTotal
VIRUSTOTAL_CACHE = {}
RATE_LIMIT_COUNTER = {'count': 0, 'reset_time': time.time()}

def extraire_urls_email(chemin_eml):
    """
    Extrait toutes les URLs d'un email
    """
    urls = set()
    try:
        with open(chemin_eml, 'r', encoding='utf-8', errors='ignore') as f:
            contenu = f.read()
        # Corriger les césures Quoted-Printable et URLs brisées par des retours à la ligne
        contenu = re.sub(r'=\r?\n', '', contenu)
        
        # Regex pour URLs
        url_pattern = r'https?://[^\s\'"<>)]*'
        trouvees = re.findall(url_pattern, contenu)
        
        for url in trouvees:
            # Nettoyer
            url = url.rstrip(',;:.)')
            if len(url) > 10:  # Filtrer bruit
                urls.add(url)
    except Exception as e:
        pass
    
    return list(urls)

def check_virustotal(domain, cached_only=False):
    """
    Vérifie reputation domaine via VirusTotal API
    Avec rate-limiting et caching
    """
    
    if domain in VIRUSTOTAL_CACHE:
        return VIRUSTOTAL_CACHE[domain]
    
    if cached_only or not VIRUSTOTAL_API_KEY:
        return {
            'malicious': 0,
            'suspicious': 0,
            'undetected': 0,
            'verdict': 'UNKNOWN',
            'from_cache': False
        }
    
    # Rate-limiting: max 4 requests/minute
    global RATE_LIMIT_COUNTER
    elapsed = time.time() - RATE_LIMIT_COUNTER['reset_time']
    if RATE_LIMIT_COUNTER['count'] >= 4 and elapsed < 60:
        time.sleep(60 - elapsed + 0.5)
        RATE_LIMIT_COUNTER['count'] = 0
        RATE_LIMIT_COUNTER['reset_time'] = time.time()
    
    try:
        import requests
        headers = {'x-apikey': VIRUSTOTAL_API_KEY}
        url = f"https://www.virustotal.com/api/v3/domains/{domain}"
        response = requests.get(url, headers=headers, timeout=5)
        RATE_LIMIT_COUNTER['count'] += 1
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
            
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            
            verdict = 'COMPROMISED' if malicious > 0 else ('SUSPICIOUS' if suspicious > 0 else 'CLEAN')
            
            result = {
                'malicious': malicious,
                'suspicious': suspicious,
                'undetected': stats.get('undetected', 0),
                'verdict': verdict,
                'from_cache': False
            }
        else:
            result = {
                'malicious': 0,
                'suspicious': 0,
                'undetected': 0,
                'verdict': 'UNKNOWN',
                'from_cache': False
            }
        
        # Cache
        VIRUSTOTAL_CACHE[domain] = result
        return result
        
    except Exception as e:
        return {
            'malicious': 0,
            'suspicious': 0,
            'undetected': 0,
            'verdict': 'ERROR',
            'from_cache': False
        }

def detect_typosquatting(url_string):
    """
    Détecte typosquatting (homoglyphs, substitutions)
    Retourne: score [0, 1], domain officiel detected
    """
    try:
        parsed = urlparse(url_string)
        domain = parsed.netloc.lower()
        
        # Exact match check
        if domain in DOMAINES_OFFICIELS:
            return {
                'typosquatting_score': 0.0,
                'suspected_brand': DOMAINES_OFFICIELS[domain],
                'suspicious': False,
                'reason': 'LEGITIMATE'
            }
        
        # Check substitutions: o→0, l→1, i→1
        domain_normalized = domain.replace('0', 'o').replace('1', 'l').replace('1', 'i')
        
        suspicions = []
        for legit_domain, brand in DOMAINES_OFFICIELS.items():
            # Fuzzy match
            legit_base = legit_domain.replace('.com', '')
            norm_base = domain_normalized.replace('.com', '')
            if legit_base in norm_base or norm_base in legit_base:
                suspicions.append({
                    'brand': brand,
                    'legitimate': legit_domain,
                    'suspicious_domain': domain
                })
        
        if suspicions:
            return {
                'typosquatting_score': 0.75,
                'suspected_brand': suspicions[0]['brand'],
                'suspicious': True,
                'reason': 'POSSIBLE_HOMOGLYPH'
            }
        
        # Check suspicious TLDs
        if domain.endswith(('.tk', '.ml', '.ga', '.cf', '.xyz', '.ru', '.ua', '.info', '.biz')):
            return {
                'typosquatting_score': 0.5,
                'suspected_brand': None,
                'suspicious': True,
                'reason': 'SUSPICIOUS_TLD'
            }
        
        return {
            'typosquatting_score': 0.0,
            'suspected_brand': None,
            'suspicious': False,
            'reason': 'UNKNOWN'
        }
        
    except Exception as e:
        return {
            'typosquatting_score': 0.0,
            'suspected_brand': None,
            'suspicious': False,
            'reason': 'ERROR'
        }

def analyser_url(email_id, url_string):
    """
    Analyse complète d'une URL
    """
    try:
        parsed = urlparse(url_string)
        domain = parsed.netloc.lower()
        
        # Typosquatting
        typosq = detect_typosquatting(url_string)
        
        # VirusTotal (caching intelligent)
        vt = check_virustotal(domain, cached_only=False)
        
        # Score combine
        typosq_score = typosq['typosquatting_score']
        vt_score = 1.0 if vt['verdict'] == 'COMPROMISED' else (0.7 if vt['verdict'] == 'SUSPICIOUS' else 0.0)
        
        final_score = (typosq_score + vt_score) / 2.0
        
        return {
            'email_id': email_id,
            'url': url_string,
            'domain': domain,
            'typosquatting_score': round(typosq_score, 2),
            'typosquatting_reason': typosq['reason'],
            'virustotal_verdict': vt['verdict'],
            'virustotal_malicious': vt['malicious'],
            'virustotal_suspicious': vt['suspicious'],
            'score_url': round(min(final_score, 1.0), 3),
            'statut_url': 'MALVEILLANT' if final_score >= 0.6 else ('SUSPECT' if final_score >= 0.4 else 'SAIN')
        }
        
    except Exception as e:
        return {
            'email_id': email_id,
            'url': url_string,
            'domain': 'ERROR',
            'typosquatting_score': 0.0,
            'typosquatting_reason': 'ERROR',
            'virustotal_verdict': 'ERROR',
            'virustotal_malicious': 0,
            'virustotal_suspicious': 0,
            'score_url': 0.0,
            'statut_url': 'ERROR'
        }

def generer_resultats_urls():
    """
    Génère resultats_urls.json complet
    """
    
    emails_dir = Path('emails_extraits')
    output_file = Path('resultats_urls.json')
    
    if not emails_dir.exists():
        print(f"❌ Dossier {emails_dir} non trouvé")
        return False
    
    eml_files = sorted(emails_dir.glob('email_*.eml'))
    print(f"📧 Trouvé {len(eml_files)} emails pour extraction URLs...")
    
    if len(eml_files) == 0:
        print("❌ Aucun fichier email_*.eml trouvé")
        return False
    
    # Agrégrer par email au lieu de lister toutes les URLs
    par_email = {}
    stats = {
        'total_emails': len(eml_files),
        'total_urls': 0,
        'urls_malveillants': 0,
        'urls_suspects': 0,
        'urls_sains': 0,
    }
    
    for idx, chemin_eml in enumerate(eml_files, 1):
        email_id = chemin_eml.stem
        
        # Extraire URLs
        urls = extraire_urls_email(str(chemin_eml))
        
        if urls:
            max_score = 0.0
            nb_urls = len(urls)
            alertes = []
            
            for url in urls:
                resultat = analyser_url(email_id, url)
                score = resultat['score_url']
                statut = resultat['statut_url']
                
                stats['total_urls'] += 1
                if statut == 'MALVEILLANT':
                    stats['urls_malveillants'] += 1
                    alertes.append(url)
                elif statut == 'SUSPECT':
                    stats['urls_suspects'] += 1
                    alertes.append(url)
                else:
                    stats['urls_sains'] += 1
                
                max_score = max(max_score, score)
            
            # Agréger par email
            par_email[email_id] = {
                'email': email_id,
                'url_score': round(max_score, 3),
                'urls_analysees': nb_urls,
                'alertes': alertes,
                'statut_url': 'MALVEILLANT' if max_score >= 0.6 else ('SUSPECT' if max_score >= 0.4 else 'SAIN')
            }
        else:
            # Pas d'URLs dans cet email
            par_email[email_id] = {
                'email': email_id,
                'url_score': 0.0,
                'urls_analysees': 0,
                'alertes': [],
                'statut_url': 'SAIN'
            }
        
        # Progress
        if idx % 50 == 0 or idx == len(eml_files):
            print(f"  ✓ {idx}/{len(eml_files)} emails traités... ({stats['total_urls']} URLs trouvées)")
    
    # Convertir en liste pour output
    resultats = list(par_email.values())
    
    # Ajouter metadata
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'module': 'URL_ANALYZER',
            'version': '2.0',
            'stats': stats
        },
        'resultats': resultats
    }
    
    # Sauver
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ resultats_urls.json généré: {stats['total_urls']} URLs analysées")
    print(f"   📊 MALVEILLANTS: {stats['urls_malveillants']}, SUSPECTS: {stats['urls_suspects']}, SAINS: {stats['urls_sains']}")
    
    return True

if __name__ == '__main__':
    import sys
    
    if not VIRUSTOTAL_API_KEY:
        print("⚠️  VIRUSTOTAL_API_KEY non trouvé dans .env")
        print("   VirusTotal checks seront skippés")
    
    try:
        success = generer_resultats_urls()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
