# Documentation technique — Module Vision (logos)

**Responsable :** Florient Kalumuna  
**Projet :** Détection de phishing avancée par IA multimodale (Groupe 8)

---

## Périmètre du module

Analyse des images extraites des emails suspects : extraction, prétraitement, comparaison avec une base de logos officiels, score de risque visuel (`0`–`1`), export JSON pour fusion multimodale (étudiant 4).

**Hors périmètre :** NLP email, analyse URL, VirusTotal (modules collègues).

---

## Avancement par rapport au CDC Groupe 8

| Exigence module Images | Statut |
|------------------------|--------|
| Extraction logos | OK |
| Prétraitement OpenCV | OK |
| Scoring (IA baseline hash + SSIM) | OK |
| OCR (optionnel) | Non fait |
| Scripts de test unitaires | OK (`tests/`, 25 tests) |
| Reporting | OK (JSON + HTML ; Streamlit optionnel) |
| Fusion multimodale | OK (`fusion_multimodale.py`) |

**Projet global :** modules email (Masudi) et URL (Béni) partiellement branchés ; NLP encore incomplet (4 emails dans `resultats_texte.json` vs 68+ côté URL/vision). Étapes 6 (métriques précision/rappel) et 8 (Docker) restent à faire pour tout le groupe.

---

## Architecture

```
phishing-2025.mbox
    → convertir_mbox.py          → emails_extraits/ (481 .eml)
    → filtrer_emails_avec_images.py → emails_avec_images/ (~68)
    → extraire_images.py         → images_extraites/ (~76–80 PNG)
    → comparer_logos.py          → resultats.json, stats_comparaison.json
    → generer_rapport.py         → rapport_analyse.html (optionnel)
    → fusion_multimodale.py      → resultats_fusion.json
    → verifier_projet.py           → contrôle automatique
    → streamlit run app.py       → dashboard (optionnel, démo uniquement)
```

### Fichiers Python (module vision)

| Fichier | Rôle |
|---------|------|
| `convertir_mbox.py` | MBOX → fichiers `.eml` |
| `filtrer_emails_avec_images.py` | Filtre emails contenant au moins une image |
| `extraire_images.py` | Extraction PJ + base64 HTML, grayscale 128×128 |
| `comparer_logos.py` | Hash perceptuel + SSIM, scoring, `resultats.json` |
| `generer_rapport.py` | Rapport HTML statique |
| `fusion_multimodale.py` | Fusion vision + NLP + URL |
| `verifier_projet.py` | Vérification dépendances, tests, fusion |
| `app.py` | UI Streamlit (optionnel — démo, pas requis au pipeline) |

---

## Algorithmes

### 1. Hash perceptuel (pHash simplifié)

- Redimensionnement 16×16, niveaux de gris
- Comparaison Hamming normalisée sur 128 bits → score `0`–`1`

### 2. SSIM (Structural Similarity)

- Redimensionnement 64×64
- `skimage.metrics.structural_similarity`

### 3. Score combiné

```python
score_visuel = 0.6 * hash_score + 0.4 * ssim_score
```

### 4. Ajustement domaine expéditeur

- Domaine officiel pour la marque détectée → `score_final = score_visuel * 0.5`
- Domaine non officiel → `score_final = min(score_visuel * 1.2, 1.0)`
- Seuil alerte : `SEUIL = 0.60` dans `comparer_logos.py`

### Logos de référence (9 marques)

Apple, Amazon, PayPal, Google, Facebook, Microsoft, Netflix, Instagram, Crédit Agricole — fichiers PNG/JPEG à la **racine du projet** (pas dans un sous-dossier). Domaines officiels : `DOMAINES_OFFICIELS` dans `comparer_logos.py`.

---

## Sorties

### `resultats.json` (livrable fusion)

```json
{
  "image": "email_0041_part3.png",
  "ressemble_a": "apple.png",
  "visual_score": 0.707,
  "score_final": 0.848,
  "expediteur": "...",
  "domaine_expediteur": "example.com",
  "domaine_officiel": false,
  "statut": "ALERTE",
  "scores_detail": { "hash": 0.859, "ssim": 0.477, "combined": 0.707 }
}
```

### Fichiers auxiliaires

- `extraction_log.json` — détail par email
- `stats_comparaison.json` — KPI globaux (durée, taux d’alertes)

---

## Installation

```powershell
cd C:\logos_reference
pip install opencv-python pillow streamlit plotly numpy scikit-image
```

Vérification : `python -c "import cv2, streamlit; print('OK')"`

---

## Exécution

**Pipeline complet (première fois) :**

```powershell
python convertir_mbox.py
python filtrer_emails_avec_images.py
python extraire_images.py
python comparer_logos.py
python generer_rapport.py   # optionnel
streamlit run app.py
```

**Relance rapide** (dossiers déjà présents) : `python comparer_logos.py` puis `streamlit run app.py`.

---

## Configuration

| Paramètre | Fichier | Défaut |
|-----------|---------|--------|
| Seuil alerte | `comparer_logos.py` | `0.60` |
| Taille image | `extraire_images.py` | `128×128` |
| Poids hash/SSIM | `comparer_logos.py` | `60% / 40%` |
| Racine projet | Tous les scripts | `Path(__file__).parent` (relatif) |

Pour ajouter une marque : image PNG/JPEG à la racine + entrée dans `DOMAINES_OFFICIELS`, puis `python comparer_logos.py`.

---

## Performance (référence)

- ~80 images × 9 logos en ~3–4 s
- Objectif cahier des charges : &lt; 2–3 s/email (module seul largement en dessous sur batch)

---

## Intégration équipe

> Le document groupe mélange parfois les rôles : **Florient** assure le module **images / logos** (OpenCV, extraction, scoring, reporting vision). **Foze** travaille sur l’architecture globale et la **fusion** des scores.

| Module | Fichier sortie typique | Responsable |
|--------|------------------------|-------------|
| Texte / NLP | `resultats_texte.json` | Masudi |
| URL | `resultats_urls.json` | Béni |
| **Vision (logos)** | **`resultats.json`** | **Florient** |
| Fusion multimodale | score unifié | Foze (+ équipe) |

Chaque entrée `resultats.json` peut être jointe à un email via le préfixe `email_XXXX` dans le nom d’image (`email_0041_part3.png` → `email_0041`).

### Fusion multimodale

```powershell
python fusion_multimodale.py
```

Lit les trois JSON, agrège la vision par email (score max des images), calcule :

```
score_fusion = (0.35 × vision + 0.35 × nlp + 0.30 × url) / somme_poids_disponibles
```

Sortie : `resultats_fusion.json` avec `email_id`, `scores`, `statut_fusion` (`SAIN` / `SUSPECT` / `PHISHING`).

Vérification complète :

```powershell
python verifier_projet.py
```

---

## Limites connues

- Pas de deep learning (baseline classique volontaire)
- OCR non implémenté (optionnel au CDC ; peu utile pour détection de logo pur)
- Faux positifs possibles sur icônes génériques proches d’une marque
- Docker / déploiement multi-OS (étape 8 CDC) non fait
- Métriques précision/rappel (étape 6) non formalisées sur jeu étiqueté

---

## Tests unitaires

```powershell
pytest tests/ -v
```

Fichiers : `tests/test_comparer_logos.py`, `tests/test_extraire_images.py`, `tests/test_fusion.py`

Contrôle global : `python verifier_projet.py`

### Dashboard Streamlit : obligatoire ?

**Non.** Le cœur du module est le pipeline CLI → `resultats.json`. Le dashboard sert à :

- montrer des graphiques et images en soutenance ;
- tester un `.eml` ou une image à la volée.

Pour l’intégration avec l’équipe et les tests automatiques, utiliser `verifier_projet.py` et `pytest`, pas Streamlit.

---

## Références document projet

- Cahier des charges : *Groupe-8-Détection de phishing avancée par IA multimodale*
- Guide accessible : `GUIDE_POUR_DEBUTANTS.md`
- Vue d’ensemble : `README.md`
