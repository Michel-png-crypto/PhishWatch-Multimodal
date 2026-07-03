# PhishWatch — Guide complet du scoring

> Document de référence pour la présentation. Décrit comment chaque module calcule son score, comment ils sont fusionnés, pourquoi la précision affichait 0 %, et quelles améliorations sont réalistes.

---

## 1. Architecture globale

PhishWatch est un **détecteur multimodal** : trois modules indépendants analysent un email, puis une couche de **fusion** produit un verdict unique.

```
Email (.eml)
    ├── Vision  → score 0–1  (logos, images, OCR)
    ├── NLP     → score 0–1  (texte, mots-clés, urgence)
    └── URL     → score 0–1  (typosquatting, VirusTotal)
              ↓
         Fusion pondérée + règles
              ↓
    statut_fusion : SAIN | SUSPECT | PHISHING
```

**Fichiers clés :**

| Fichier | Rôle |
|---------|------|
| `comparer_logos.py` | Module Vision |
| `generer_resultats_texte_v2.py` | Module NLP |
| `generer_resultats_urls.py` | Module URL |
| `fusion_multimodale.py` | Fusion + statut final |
| `generer_metrics.py` | Précision / rappel / F1 |
| `app.py` | Interface Streamlit (analyse live) |

---

## 2. Module Vision (images & logos)

**Auteur :** Florent — **Fichier :** `comparer_logos.py`

### 2.1 Pipeline

1. Extraction des images depuis l'email (`extraire_images_v2.py`)
2. Pour chaque image `email_XXXX_*` :
   - Comparaison avec les logos de référence (Apple, PayPal, Microsoft…)
   - Vérification du domaine expéditeur vs domaines officiels de la marque
   - Analyse OCR optionnelle (`ocr_analyzer.py`)

### 2.2 Score visuel (hash + SSIM)

Deux métriques complémentaires sont combinées :

| Métrique | Poids | Description |
|----------|-------|-------------|
| **Hash perceptuel** | 60 % | Compare des bits binaires d'une version 16×16 de l'image |
| **SSIM** | 40 % | Structural Similarity Index — ressemblance structurelle 64×64 |

```
score_visuel = 0.6 × hash_score + 0.4 × ssim_score
```

- `hash_score = 1.0` → images quasi identiques
- `ssim_score` proche de 1.0 → même structure visuelle

### 2.3 Ajustement domaine + OCR

Si `score_visuel ≥ 0.55` (seuil de vérification) :

| Situation | Effet sur le score |
|-----------|-------------------|
| Domaine expéditeur **officiel** (ex. `@apple.com`) | Score × **0.5** (réduction — probablement légitime) |
| Domaine **non officiel** + logo ressemblant | Score × **1.2** (max 1.0) — signal fort de spoofing |
| OCR détecte menaces textuelles | Blend 60 % visuel + 40 % OCR, puis × 1.1 si score > 0.5 |

**Seuils Vision :**

- `SEUIL_VERIFICATION = 0.55` — déclenche la vérification domaine
- `SEUIL_ALERTE = 0.60` — statut `ALERTE` (sinon `SAIN`)

### 2.4 Agrégation par email

Un email peut contenir plusieurs images. La fusion Vision retient le **score maximum** parmi toutes les images.

---

## 3. Module NLP (texte)

**Auteur :** Masudi — **Fichier :** `generer_resultats_texte_v2.py`

### 3.1 Techniques combinées

| Technique | Ce qu'elle détecte |
|-----------|-------------------|
| Mots-clés par catégorie | Urgence, finances, identité, menaces |
| Erreurs d'orthographe / typos | Emails mal rédigés (souvent phishing) |
| Ponctuation excessive | `!!!`, `???`, majuscules abusives |
| Urgence artificielle | « agir maintenant », « compte suspendu » |
| Spoofing de domaines | `verify-amazon.malicious.ru` dans le texte |

Chaque sous-score est borné à 1.0, puis agrégé en `score_nlp`.

### 3.2 Statuts NLP

| Score NLP | Statut |
|-----------|--------|
| ≥ 0.60 | `SUSPECT` |
| < 0.60 | `SAIN` |

Le NLP produit aussi une liste `menaces_detectees` (catégories trouvées).

---

## 4. Module URL

**Auteur :** Béni — **Fichier :** `generer_resultats_urls.py`

### 4.1 Analyse par URL

Pour chaque URL extraite de l'email :

1. **Typosquatting** — distance de Levenshtein vs domaines officiels (Google, PayPal…)
2. **VirusTotal** (si clé API présente) — réputation du domaine
3. **Heuristiques** — TLD suspects (`.ru`, `.tk`), sous-domaines trompeurs

### 4.2 Score URL

Le score final par email = **maximum** des scores de toutes ses URLs.

| Score URL | Statut |
|-----------|--------|
| ≥ 0.60 | `MALVEILLANT` |
| ≥ 0.40 | `SUSPECT` |
| < 0.40 | `SAIN` |

---

## 5. Fusion multimodale

**Fichier :** `fusion_multimodale.py`

### 5.1 Moyenne pondérée

```
score_fusion = (0.35 × vision + 0.35 × nlp + 0.30 × url) / somme_poids_disponibles
```

Si un module est absent (pas d'image, pas d'URL), son poids est retiré du dénominateur.

**Poids par défaut :** Vision 35 % · NLP 35 % · URL 30 %

### 5.2 Règles de statut (`statut_fusion`)

| Condition | Verdict |
|-----------|---------|
| `score_fusion ≥ 0.65` | **PHISHING** |
| `score ≥ 0.45` ET URL `MALVEILLANT`/`COMPROMISED` | **PHISHING** |
| `score ≥ 0.45` ET ≥ 2 modules en alerte (vision ALERTE, NLP SUSPECT, URL suspect…) | **PHISHING** |
| Au moins un module suspect OU `score ≥ 0.45` | **SUSPECT** |
| Sinon | **SAIN** |

> **Important :** le verdict peut être `PHISHING` même si `score_fusion < 0.65` (ex. email_0002 avec score 0.514 mais URL malveillante).

### 5.3 Exemple concret — `email_0002` (vrai phishing)

| Module | Score | Statut |
|--------|-------|--------|
| Vision | 0.727 | ALERTE (logo Facebook) |
| NLP | 0.098 | SAIN |
| URL | 0.750 | MALVEILLANT (`boxauth.ru`) |
| **Fusion** | **0.514** | **PHISHING** |

L'URL malveillante confirme le phishing malgré un score global modéré.

---

## 6. Métriques (Précision, Rappel, F1)

**Fichier :** `generer_metrics.py` → `metrics_formels.json`

### 6.1 Définitions

| Métrique | Formule | Signification |
|----------|---------|---------------|
| **Précision** | TP / (TP + FP) | Parmi les emails flaggés phishing, combien le sont vraiment ? |
| **Rappel** | TP / (TP + FN) | Parmi les vrais phishing, combien sont détectés ? |
| **F1** | Moyenne harmonique précision/rappel | Équilibre global |
| **Accuracy** | (TP + TN) / Total | Taux de bonnes réponses (trompeur si dataset déséquilibré) |
| **FPR** | FP / (FP + TN) | Taux de fausses alertes sur emails légitimes |

### 6.2 Ground truth (référence)

Labels utilisés, par ordre de priorité :

1. `ground_truth.json` (labels manuels)
2. Enrichissement automatique via `phishing_urls.txt` (PhishTank/OpenPhish)

**État actuel du corpus :** 481 emails, **1 seul** confirmé phishing via PhishTank (`email_0002`).

### 6.3 Pourquoi la précision affichait 0 % ?

Trois bugs cumulés :

| Bug | Effet |
|-----|-------|
| **Images orphelines** | 39 fichiers dans `images_extraites/` sans préfixe `email_XXXX` créaient de faux emails avec score vision élevé → 36 faux positifs |
| **Seuil métriques ≠ verdict** | `generer_metrics.py` utilisait `score ≥ 0.60` au lieu de `statut_fusion == PHISHING` → le seul vrai phishing (score 0.514) n'était pas compté en TP |
| **Ground truth quasi vide** | 1 seul label confirmé ; tous les autres emails = légitimes par défaut |

**Après correction (juin 2026) :**

```
TP=1  TN=468  FP=12  FN=0
Précision ≈ 7.7 %  |  Rappel = 100 %  |  Accuracy ≈ 97.5 %
```

La précision reste modeste car **12 emails légitimes** sont encore flaggés PHISHING (surtout URL typosquatting agressif sur des liens bénins), alors qu'**un seul** phishing est confirmé dans la référence.

> **Pour la présentation :** insister sur le **cas email_0002** (démo live) et le **rappel à 100 %**, plutôt que la précision globale sur un corpus quasi sans labels.

---

## 7. Validation PhishTank (module URL seul)

**Fichier :** `validation_phishtank.json`

Évalue uniquement le module URL contre ~301 URLs phishing connues.

Précision URL basse (~0.7 %) = beaucoup de typosquatting sur des domaines légitimes ressemblant à des marques. C'est **normal** sur un corpus d'emails marketing réels.

---

## 8. Un module ML serait-il pertinent ?

### Verdict : **oui, mais pas pour demain**

| Approche actuelle | Approche ML |
|-------------------|-------------|
| Règles explicables, seuils ajustables | Modèle entraîné sur features |
| Fonctionne sans dataset étiqueté massif | Nécessite des centaines/milliers de labels |
| Rapide (~2 s/email) | Inférence similaire si modèle léger |
| Facile à présenter (logique transparente) | Boîte noire sans explicabilité |

### Où le ML apporterait le plus de valeur

1. **NLP** — Classifier BERT/DistilBERT fine-tuné sur emails phishing (remplace les listes de mots-clés)
2. **Vision** — CNN ou CLIP pour détecter logos spoofés sans hash manuel
3. **Fusion** — Stacking (XGBoost) sur les 3 scores + features meta au lieu de moyenne pondérée fixe

### Pourquoi garder l'approche actuelle pour la soutenance

- **Explicabilité** : vous pouvez montrer *pourquoi* chaque module a alerté
- **Architecture multimodale** : c'est le cœur du projet CDC, pas un modèle monolithique
- **Démo fiable** : `email_0002` est détecté avec des signaux interprétables (logo + URL)

### Si vous voulez mentionner le ML demain

> « L'architecture actuelle est rule-based et multimodale. Une évolution naturelle serait un fine-tuning BERT sur le texte et un classifieur de fusion entraîné sur un corpus étiqueté (PhishTank, Nazario…), une fois le ground truth enrichi. »

---

## 9. Améliorations prioritaires (par effort / impact)

### Avant la présentation (rapide)

| Action | Impact | Effort |
|--------|--------|--------|
| Démo live sur `email_0002.eml` | Montre détection réelle | 5 min |
| Expliquer le bug 0 % (corrigé) | Crédibilité technique | Slide |
| Montrer les 3 modules séparément dans Streamlit | Comprendre la fusion | Déjà dans l'UI |
| Régénérer métriques : `python fusion_multimodale.py && python generer_metrics.py` | Chiffres à jour | 1 min |

### Court terme (1–2 semaines)

| Action | Impact |
|--------|--------|
| Enrichir `ground_truth.json` (20–50 emails étiquetés manuellement) | Métriques fiables |
| Assouplir typosquatting URL (whitelist domaines connus) | − faux positifs URL |
| Passer `domaine_officiel` du module Vision à la fusion | − faux positifs vision seule |
| Calibrer seuils sur un petit set validé | Meilleur F1 |

### Moyen terme

| Action | Impact |
|--------|--------|
| Fine-tuning DistilBERT (NLP) | Meilleure détection texte |
| Dataset Nazario / PhishTank emails complets | Entraînement + évaluation |
| API temps réel + file d'attente VirusTotal | Scalabilité |
| Explicabilité SHAP sur scores fusion | Confiance utilisateur |

---

## 10. Commandes utiles

```powershell
# Pipeline complet (batch)
python extraire_images_v2.py      # si nouvelles images
python comparer_logos.py
python generer_resultats_texte_v2.py
python generer_resultats_urls.py
python fusion_multimodale.py
python generer_metrics.py

# Interface
streamlit run app.py

# Tests
pytest tests/ -v
```

---

## 11. Résumé pour la slide « Scoring »

1. **3 modules** → scores 0–1 indépendants et explicables
2. **Fusion pondérée** 35/35/30 + règles métier (URL malveillante = alerte même si score modéré)
3. **Verdict** : SAIN / SUSPECT / PHISHING (pas seulement un pourcentage)
4. **Métriques** : comparaison vs PhishTank ; précision globale limitée par le peu de labels confirmés
5. **Évolution** : ML sur NLP et fusion une fois le corpus étiqueté

---

*Dernière mise à jour : 30 juin 2026 — corrections bugs métriques et images orphelines.*
