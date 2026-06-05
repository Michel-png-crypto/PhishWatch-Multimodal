#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharger dataset PhishTank pour validation
"""

import requests
import json
from datetime import datetime
from pathlib import Path

print("\n" + "="*70)
print("📥 TÉLÉCHARGEMENT DATASET PHISHTANK")
print("="*70 + "\n")

# Option 1: OpenPhish (plus simple, gratuit)
print("Source: OpenPhish (gratuit, updated daily)")
print("Téléchargement en cours...")

try:
    response = requests.get(
        'https://openphish.com/feed.txt',
        timeout=30
    )
    
    urls_phishing = response.text.strip().split('\n')
    print(f"✅ Téléchargé {len(urls_phishing)} URLs phishing")
    
    # Sauver dans phishing_urls.txt
    with open('phishing_urls.txt', 'w', encoding='utf-8') as f:
        for url in urls_phishing:
            if url.strip():
                f.write(url.strip() + '\n')
    
    # Statistiques
    print(f"\n📊 Statistiques:")
    print(f"  Total URLs: {len(urls_phishing)}")
    print(f"  HTTPS URLs: {sum(1 for u in urls_phishing if 'https://' in u)}")
    print(f"  HTTP URLs: {sum(1 for u in urls_phishing if 'http://' in u)}")
    
    # Exemples
    print(f"\n📝 Exemples (premiers 5):")
    for url in urls_phishing[:5]:
        if url.strip():
            print(f"  • {url[:60]}...")
    
    print(f"\n✅ Données sauvegardées: phishing_urls.txt")
    print("="*70 + "\n")

except Exception as e:
    print(f"\n❌ Erreur téléchargement: {e}")
    print("\nAlternative manuelle:")
    print("1. Aller sur https://openphish.com/")
    print("2. Télécharger feed.txt")
    print("3. Sauver dans c:\\logos_reference\\phishing_urls.txt")
    print("="*70 + "\n")
