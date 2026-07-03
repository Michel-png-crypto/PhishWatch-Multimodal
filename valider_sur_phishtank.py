#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation PhishWatch sur dataset réel PhishTank
Calcule: Precision, Recall, F1, Confusion Matrix
"""

import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

print("\n" + "="*70)
print("📊 VALIDATION SUR DATASET PHISHTANK")
print("="*70 + "\n")


def normalize_url(url):
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        path = parsed.path.rstrip("/")
        return f"{host}{path}"
    except Exception:
        return url.lower().strip()


def normalize_domain(url):
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        host = urlparse(url).netloc.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return url.lower().strip()


def is_phishing_url(candidate, phishing_reference):
    norm_candidate = normalize_url(candidate)
    norm_ref = normalize_url(phishing_reference)
    if not norm_candidate or not norm_ref:
        return False
    if norm_candidate == norm_ref:
        return True
    if norm_candidate.startswith(norm_ref) or norm_ref.startswith(norm_candidate):
        return True
    if norm_candidate.endswith(norm_ref) or norm_ref.endswith(norm_candidate):
        return True
    domain_candidate = normalize_domain(candidate)
    domain_ref = normalize_domain(phishing_reference)
    if domain_candidate == domain_ref:
        return True
    if domain_candidate.endswith('.' + domain_ref) or domain_ref.endswith('.' + domain_candidate):
        return True
    return False

# Étape 1: Charger les URLs phishing réelles
if not Path('phishing_urls.txt').exists():
    print("❌ phishing_urls.txt non trouvé")
    print("   Exécute d'abord: python telecharger_phishtank.py")
    exit(1)

phishing_urls = set()
with open('phishing_urls.txt', 'r', encoding='utf-8') as f:
    phishing_urls = set(line.strip() for line in f if line.strip())

print(f"✅ Chargé {len(phishing_urls)} URLs phishing de référence")

# Étape 2: Charger les résultats URLs
if not Path('resultats_urls.json').exists():
    print("❌ resultats_urls.json non trouvé")
    exit(1)

with open('resultats_urls.json') as f:
    data = json.load(f)

print(f"✅ Chargé {len(data['resultats'])} résultats d'analyse")

# Étape 3: Créer les labels
y_true = []  # Labels réels (0=sain, 1=phishing)
y_pred = []  # Prédictions (0=sain, 1=phishing)
matches = []

for result in data['resultats']:
    # Check si email contient phishing
    email_has_phishing = False
    matched_urls = []
    
    for url_alert in result.get('alertes', []):
        try:
            for phishing_url in phishing_urls:
                if is_phishing_url(url_alert, phishing_url):
                    email_has_phishing = True
                    matched_urls.append(url_alert)
                    break
        except Exception:
            pass
    
    # Score de prédiction
    score = result.get('url_score', 0.0)
    pred = 1 if score >= 0.5 else 0
    
    y_true.append(1 if email_has_phishing else 0)
    y_pred.append(pred)
    
    if email_has_phishing:
        matches.append({
            'email': result['email'],
            'matched_urls': matched_urls,
            'score': score
        })

# Étape 4: Calculer metrics
tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

print(f"\n{'─'*70}")
print("CONFUSION MATRIX")
print(f"{'─'*70}")
print(f"  TP (Vrais Positifs):   {tp:3d}  ✅ Phishing détecté correctement")
print(f"  TN (Vrais Négatifs):   {tn:3d}  ✅ Sain reconnu correctement")
print(f"  FP (Faux Positifs):    {fp:3d}  ❌ Fausse alerte (sain → phishing)")
print(f"  FN (Faux Négatifs):    {fn:3d}  ❌ Ratés (phishing → sain)")
print(f"  Total:                 {len(y_true):3d}")

# Calculer scores
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
accuracy = (tp + tn) / len(y_true)

print(f"\n{'─'*70}")
print("SCORES DE PERFORMANCE")
print(f"{'─'*70}")
print(f"  Precision: {precision:6.1%}  (Combien de détections sont correctes)")
print(f"  Recall:    {recall:6.1%}  (Combien de phishing réels on détecte)")
print(f"  F1-Score:  {f1:6.3f}  (Harmonic mean Precision-Recall)")
print(f"  Accuracy:  {accuracy:6.1%}  (Exactitude globale)")

# False Positive Rate et False Negative Rate
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

print(f"\n{'─'*70}")
print("TAUX D'ERREUR")
print(f"{'─'*70}")
print(f"  FPR (False Positive Rate): {fpr:6.1%}  (% fausses alertes)")
print(f"  FNR (False Negative Rate): {fnr:6.1%}  (% phishing ratés)")

# Évaluation
print(f"\n{'─'*70}")
print("ÉVALUATION")
print(f"{'─'*70}")

if precision >= 0.85:
    print(f"  ✅ Precision {precision:.1%} - EXCELLENT (≥85%)")
elif precision >= 0.70:
    print(f"  🟡 Precision {precision:.1%} - BON (70-85%)")
else:
    print(f"  ❌ Precision {precision:.1%} - À AMÉLIORER (<70%)")

if recall >= 0.85:
    print(f"  ✅ Recall {recall:.1%} - EXCELLENT (≥85%)")
elif recall >= 0.70:
    print(f"  🟡 Recall {recall:.1%} - BON (70-85%)")
else:
    print(f"  ❌ Recall {recall:.1%} - À AMÉLIORER (<70%)")

if f1 >= 0.80:
    print(f"  ✅ F1-Score {f1:.3f} - EXCELLENT (≥0.80)")
elif f1 >= 0.70:
    print(f"  🟡 F1-Score {f1:.3f} - BON (0.70-0.80)")
else:
    print(f"  ❌ F1-Score {f1:.3f} - À AMÉLIORER (<0.70)")

# Phishing détectés
print(f"\n{'─'*70}")
print(f"PHISHING DÉTECTÉS: {len(matches)}")
print(f"{'─'*70}")

for match in matches[:5]:
    print(f"  • {match['email']}: {match['matched_urls'][:1]}")

if len(matches) > 5:
    print(f"  ... et {len(matches)-5} autres")

if len(matches) == 0:
    print("\n⚠️ Aucune correspondance trouvée avec les URLs PhishTank/OpenPhish. Cela peut être dû à un jeu de données différent ou à une URL de phishing non présente dans le référentiel.")

# Sauver résultats
results = {
    'metadata': {
        'timestamp': str(datetime.now()),
        'dataset': 'PhishTank (OpenPhish)',
        'reference_urls': len(phishing_urls),
        'emails_tested': len(y_true),
        'phishing_detected': len(matches)
    },
    'confusion_matrix': {
        'true_positives': int(tp),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn)
    },
    'metrics': {
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'accuracy': float(accuracy),
        'false_positive_rate': float(fpr),
        'false_negative_rate': float(fnr)
    },
    'phishing_matches': matches[:10]  # Sauver premiers 10
}

with open('validation_phishtank.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Résultats sauvegardés: validation_phishtank.json")
print("="*70 + "\n")
