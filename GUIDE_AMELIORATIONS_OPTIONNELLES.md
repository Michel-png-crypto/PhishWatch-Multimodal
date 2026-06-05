# 🚀 GUIDE AMÉLIORATIONS OPTIONNELLES

**Date:** 6 Juin 2026  
**Statut:** Post-Soutenance (optionnel)  
**Effort:** 30 min à 2 heures

---

## 🎯 3 Améliorations Prioritaires

### 1️⃣ Configurer VirusTotal API (30 min)
### 2️⃣ Augmenter Couverture Vision - HTML Images (1-2 heures)
### 3️⃣ Tester sur Dataset Réel - PhishTank (1-2 heures)

---

## 1️⃣ CONFIGURER VIRUSTOTAL API

### ⏱️ Temps: 30 minutes
### 📈 Impact: +10-15% détection URLs malveillantes

### Étape 1: Obtenir une API Key

**Option A: Gratuit (Limité)**
```
1. Aller sur https://www.virustotal.com/gui/home/upload
2. S'inscrire (gratuit)
3. Aller sur https://www.virustotal.com/gui/user/apikey
4. Copier la clé
```

**Option B: Premium (Illimité)**
```
1. Compte gratuit: ~4 requêtes/minute
2. Compte premium: ~600 requêtes/minute (payant)
```

### Étape 2: Configurer .env

```bash
# Ouvrir .env
code .env

# Ajouter la ligne
VIRUSTOTAL_API_KEY=your_api_key_here

# Exemple:
VIRUSTOTAL_API_KEY=9aa0aa8bd1d9c5a2f8d5782177d63adbb8fd2177fa92819344a6f3f079b13f46
```

### Étape 3: Tester la Configuration

```bash
# Exécuter le test
python -c "
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('VIRUSTOTAL_API_KEY')

if api_key and len(api_key) > 30:
    print('✅ API Key configurée correctement')
    print(f'   Clé: {api_key[:20]}...')
else:
    print('❌ API Key non trouvée ou invalide')
"
```

### Étape 4: Réexécuter le Module URL

```bash
# Générer nouveaux résultats avec API
python generer_resultats_urls.py

# La sortie affichera maintenant:
# ✅ VirusTotal API configurée
# 📊 X URLs malveillantes détectées
# 📊 Y URLs suspectes
```

### Résultat Attendu

**Avant:**
```
MALVEILLANTS: 0
SUSPECTS: 0
SAINS: 1787
```

**Après (avec API):**
```
MALVEILLANTS: 15-25 (détection réelle)
SUSPECTS: 10-20
SAINS: 1752-1762
```

### Code impacté: [generer_resultats_urls.py](generer_resultats_urls.py)

```python
def check_virustotal(url, cache=None):
    """Vérifie l'URL contre VirusTotal"""
    api_key = os.getenv('VIRUSTOTAL_API_KEY')
    
    if not api_key:
        return {'status': 'no_api', 'score': 0.0}
    
    # Appel API VirusTotal
    headers = {'x-apikey': api_key}
    response = requests.post(
        'https://www.virustotal.com/api/v3/urls',
        headers=headers,
        data={'url': url}
    )
    
    # Récupérer le score
    # ...retourne 0.0-1.0
```

---

## 2️⃣ AUGMENTER COUVERTURE VISION - HTML IMAGES

### ⏱️ Temps: 1-2 heures
### 📈 Impact: +20-30% couverture images (10.8% → 30-40%)

### Problème Actuel

```
Couverture: 52/481 emails (10.8%)

Raison: Images HTML inline base64 non extraites
  ├─ <img src="data:image/png;base64,...">
  ├─ <img src="cid:image@...">
  └─ Background images CSS
```

### Amélioration Proposée

Modifier [extraire_images.py](extraire_images.py) pour extraire toutes les images HTML :

```python
def extraire_images_html_base64(contenu_html, email_id, output_dir):
    """
    Extrait les images inline base64 des emails HTML
    Exemple: <img src="data:image/png;base64,iVBORw0KG...">
    """
    import re
    import base64
    from pathlib import Path
    
    # Pattern pour images base64
    pattern = r'data:image/([^;]+);base64,([A-Za-z0-9+/=]+)'
    matches = re.findall(pattern, contenu_html)
    
    images_extraites = []
    
    for idx, (format_img, data_base64) in enumerate(matches):
        try:
            # Décoder base64
            image_data = base64.b64decode(data_base64)
            
            # Sauver
            filename = f"{email_id}_html_{idx}.{format_img.lower()}"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            images_extraites.append(str(filepath))
            print(f"  ✓ Image HTML #{idx+1}: {filename} ({len(image_data)} bytes)")
        
        except Exception as e:
            print(f"  ❌ Erreur extraction image #{idx+1}: {e}")
    
    return images_extraites


def extraire_images_html_cid(msg, email_id, output_dir):
    """
    Extrait les images référencées par CID (Content-ID)
    Exemple: <img src="cid:image@01D6E4F5.2A1C0AC0">
    """
    images_extraites = []
    
    if msg.is_multipart():
        for part in msg.walk():
            # Chercher Content-ID
            content_id = part.get('Content-ID')
            
            if content_id and part.get_content_maintype() == 'image':
                try:
                    # Récupérer l'image
                    image_data = part.get_payload(decode=True)
                    
                    # Déterminer format
                    content_type = part.get_content_type()
                    format_img = content_type.split('/')[-1]
                    
                    # Sauver
                    filename = f"{email_id}_cid_{content_id.strip('<>')}.{format_img}"
                    filepath = Path(output_dir) / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    images_extraites.append(str(filepath))
                    print(f"  ✓ Image CID: {filename} ({len(image_data)} bytes)")
                
                except Exception as e:
                    print(f"  ❌ Erreur CID: {e}")
    
    return images_extraites


def extraire_images_css_url(contenu_html, email_id, output_dir):
    """
    Extrait les images CSS background
    Exemple: background-image: url('data:image/png;base64,...')
    """
    import re
    import base64
    
    # Pattern pour CSS background
    pattern = r"url\(['\"]?data:image/([^;]+);base64,([A-Za-z0-9+/=]+)['\"]?\)"
    matches = re.findall(pattern, contenu_html, re.IGNORECASE)
    
    images_extraites = []
    
    for idx, (format_img, data_base64) in enumerate(matches):
        try:
            image_data = base64.b64decode(data_base64)
            filename = f"{email_id}_css_{idx}.{format_img.lower()}"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            images_extraites.append(str(filepath))
            print(f"  ✓ Image CSS #{idx+1}: {filename}")
        
        except Exception as e:
            print(f"  ❌ Erreur CSS: {e}")
    
    return images_extraites
```

### Étapes d'Implémentation

**Étape 1: Sauvegarder script original**
```bash
cp extraire_images.py extraire_images_backup.py
```

**Étape 2: Ajouter les 3 nouvelles fonctions**

Dans [extraire_images.py](extraire_images.py), ajouter le code ci-dessus

**Étape 3: Modifier la fonction principale**

```python
def extraire_images_email_v2(chemin_eml, email_id, output_dir):
    """
    Version améliorée avec support HTML
    """
    images = []
    
    with open(chemin_eml, 'r', encoding='utf-8', errors='ignore') as f:
        msg = message_from_file(f)
    
    # 1. Images attachées (original)
    images.extend(extraire_images_attachees(msg, email_id, output_dir))
    
    # 2. Images HTML base64 (NOUVEAU)
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            images.extend(extraire_images_html_base64(html, email_id, output_dir))
            images.extend(extraire_images_css_url(html, email_id, output_dir))
    
    # 3. Images CID (NOUVEAU)
    images.extend(extraire_images_html_cid(msg, email_id, output_dir))
    
    return images
```

**Étape 4: Tester**

```bash
# Réexécuter extraction
python generer_resultats_texte.py  # Pour base64 detection

# Vérifier nouvelles images
ls images_extraites/ | wc -l

# Avant: 80 images
# Après: 120-150 images (+50-87%)
```

### Résultat Attendu

```
Avant:
  Images trouvées: 80
  Coverage: 52/481 (10.8%)

Après:
  Images trouvées: 120-150
  Coverage: 140-180/481 (29-37%)
  
  Amélioration: +100-150 images (+25% couverture)
```

---

## 3️⃣ TESTER SUR DATASET RÉEL - PHISHTANK

### ⏱️ Temps: 1-2 heures
### 📈 Impact: Validation metrics réels (Precision, Recall, F1)

### Qu'est-ce que PhishTank?

```
- Database gratuite de phishing vérifié
- 80,000+ URLs phishing confirmées
- API gratuite + CSV téléchargeable
- Updated daily
```

### Étape 1: Télécharger les Données

**Option A: Via API (Simple)**

```bash
# Créer script
cat > telecharger_phishtank.py << 'EOF'
import requests
import json
from datetime import datetime

# Télécharger dataset PhishTank
print("Téléchargement PhishTank...")
response = requests.get('http://phishtank.com/phish_detail.php?url=', timeout=30)

# Plus simple: utiliser le CSV
response = requests.get(
    'https://openphish.com/feed.txt',
    timeout=30
)

urls_phishing = response.text.strip().split('\n')
print(f"Trouvé {len(urls_phishing)} URLs phishing")

# Sauver
with open('phishing_urls.txt', 'w') as f:
    for url in urls_phishing[:100]:  # Limiter à 100 pour tests
        f.write(url + '\n')

print("✅ Données sauvegardées dans phishing_urls.txt")
EOF

python telecharger_phishtank.py
```

**Option B: Télécharger manuellement**

```
1. Aller sur https://openphish.com/
2. Télécharger feed.txt
3. Sauver dans c:\logos_reference\phishing_urls.txt
```

### Étape 2: Créer Script de Validation

```bash
cat > valider_sur_phishtank.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valide les résultats PhishWatch sur PhishTank dataset
"""

import json
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# Charger les URLs phishing réelles
phishing_urls = set()
with open('phishing_urls.txt') as f:
    phishing_urls = set(line.strip() for line in f)

print(f"📊 Chargé {len(phishing_urls)} URLs phishing de référence")

# Charger les résultats URLs
with open('resultats_urls.json') as f:
    data = json.load(f)

# Créer les labels
y_true = []  # Labels réels (0=sain, 1=phishing)
y_pred = []  # Prédictions (0=sain, 1=phishing)

for result in data['resultats']:
    urls_analysees = result.get('urls_analysees', 0)
    
    # Check si email contient phishing
    email_has_phishing = False
    for url in result.get('alertes', []):
        if url in phishing_urls:
            email_has_phishing = True
            break
    
    # Score de prédiction
    score = result['url_score']
    pred = 1 if score >= 0.5 else 0
    
    y_true.append(1 if email_has_phishing else 0)
    y_pred.append(pred)

# Calculer metrics
print("\n" + "="*70)
print("VALIDATION SUR PHISHTANK")
print("="*70)

tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

print(f"\nConfusion Matrix:")
print(f"  TP (Vrais Positifs):  {tp}")
print(f"  TN (Vrais Négatifs):  {tn}")
print(f"  FP (Faux Positifs):   {fp}")
print(f"  FN (Faux Négatifs):   {fn}")

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

print(f"\nMetrics:")
print(f"  Precision: {precision:.1%} (Combien de détections sont correctes)")
print(f"  Recall:    {recall:.1%} (Combien de phishing on détecte)")
print(f"  F1-Score:  {f1:.3f} (Harmonic mean)")

# Sauver résultats
results = {
    'metadata': {
        'timestamp': str(datetime.now()),
        'dataset': 'PhishTank',
        'urls_tested': len(y_true),
        'phishing_count': sum(y_true)
    },
    'confusion_matrix': {
        'tp': int(tp),
        'tn': int(tn),
        'fp': int(fp),
        'fn': int(fn)
    },
    'metrics': {
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1)
    }
}

with open('validation_phishtank.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ Résultats sauvegardés: validation_phishtank.json")
print("="*70)
EOF

python valider_sur_phishtank.py
```

### Étape 3: Interpréter les Résultats

**Exemple de résultat:**

```
VALIDATION SUR PHISHTANK

Confusion Matrix:
  TP (Vrais Positifs):  45
  TN (Vrais Négatifs):  420
  FP (Faux Positifs):   8
  FN (Faux Négatifs):   8

Metrics:
  Precision: 84.9% (Combien de détections sont correctes)
  Recall:    84.9% (Combien de phishing on détecte)
  F1-Score:  0.849 (Harmonic mean)
```

**Interprétation:**

| Metric | Score | Signification |
|--------|-------|---------------|
| **Precision 85%** | Bon ✅ | 85% des URLs flaggées comme phishing sont vraiment phishing |
| **Recall 85%** | Bon ✅ | On détecte 85% des phishing réels |
| **F1 0.849** | Bon ✅ | Équilibre bon entre Precision et Recall |

---

## 📋 RÉSUMÉ DES AMÉLIORATIONS

| # | Amélioration | Effort | Impact | Priorité |
|---|--------------|--------|--------|----------|
| 1 | VirusTotal API | 30 min | +10-15% URLs détectées | 🟠 Court |
| 2 | Vision HTML Images | 1-2h | +25% couverture images | 🟠 Court |
| 3 | PhishTank Validation | 1-2h | Metrics réels | 🟡 Moyen |

---

## 🚀 ORDRE D'EXÉCUTION RECOMMANDÉ

### **Phase 1: API VirusTotal (30 min)**
```bash
1. Obtenir clé API gratuit (5 min)
2. Configurer .env (5 min)
3. Tester config (5 min)
4. Réexécuter generer_resultats_urls.py (15 min)
5. Vérifier nouveaux résultats
```

### **Phase 2: Vision HTML Images (1-2h)**
```bash
1. Sauvegarder script original (1 min)
2. Implémenter 3 nouvelles fonctions (30 min)
3. Tester sur quelques emails (15 min)
4. Réexécuter extraction complète (30 min)
5. Regénérer résultats fusion (10 min)
```

### **Phase 3: PhishTank Validation (1-2h)**
```bash
1. Télécharger données PhishTank (10 min)
2. Créer script de validation (20 min)
3. Exécuter validation (5 min)
4. Analyser résultats (15 min)
5. Documenter findings (10 min)
```

---

## 📊 RÉSULTATS ATTENDUS APRÈS AMÉLIORATIONS

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Couverture Vision** | 10.8% | 30-40% | +20-30% |
| **URLs Malveillantes** | 0 | 15-25 | +15-25 |
| **Phishing Détectés** | 9 | 45-60 | +500% |
| **Precision** | N/A | 84-90% | Validé |
| **Recall** | N/A | 80-85% | Validé |

---

## 📝 NOTES IMPORTANTES

### Limitations

**API VirusTotal Gratuit:**
- ~4 requêtes/minute
- 1000 requêtes/jour
- → Pour 1787 URLs: ~7-10 heures

**Solution:**
- Utiliser cache (implémenter dans code)
- Ou acheter plan premium (~500-1000€/an)

### Code Optimisations

```python
# Ajouter cache pour VirusTotal
CACHE_VT = {}

def check_virustotal_cached(url):
    if url in CACHE_VT:
        return CACHE_VT[url]
    
    result = check_virustotal(url)
    CACHE_VT[url] = result
    return result
```

---

## ✅ CHECKLIST

- [ ] **Phase 1: VirusTotal**
  - [ ] Clé API obtenue
  - [ ] .env configuré
  - [ ] Test passé
  - [ ] generer_resultats_urls.py réexécuté

- [ ] **Phase 2: Vision HTML**
  - [ ] Script original sauvegardé
  - [ ] 3 fonctions implémentées
  - [ ] Tests locaux passés
  - [ ] Extraction complète réexécutée

- [ ] **Phase 3: PhishTank**
  - [ ] Données téléchargées
  - [ ] Script validation créé
  - [ ] Validation exécutée
  - [ ] Résultats documentés

---

## 📞 SUPPORT

Si des erreurs:

1. **VirusTotal API**
   - Vérifier API key valide
   - Vérifier connexion internet
   - Vérifier limite requêtes

2. **Vision HTML**
   - Tester sur 1 email d'abord
   - Vérifier format base64
   - Vérifier permissions fichiers

3. **PhishTank**
   - Vérifier données téléchargées
   - Vérifier format URLs
   - Vérifier libraires sklearn

---

**Bonne chance avec les améliorations ! 🚀**
