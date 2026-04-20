# 🛡️ Module Vision par Ordinateur — Etudiant 2
## Détection d'usurpation de logos dans les emails de phishing

---

## 📋 C'est quoi ce module ?

Ce module analyse les **images contenues dans les emails suspects** pour détecter si elles ressemblent à des logos officiels (Apple, PayPal, Amazon...). Si un email de phishing copie le logo de PayPal pour tromper la victime, ce module le détecte et génère un **score de risque visuel entre 0 et 1**.

Ce score est ensuite transmis à l'**Etudiant 4** qui le fusionne avec les scores des autres modules.

---

## 📁 Structure des fichiers

```
C:\logos_reference\
│
├── 📂 logos_reference\        ← Base de logos officiels (9 logos)
│   ├── amazon.png
│   ├── apple.png (Apple_Icon_6.png)
│   ├── paypal.jpeg
│   ├── google.png
│   ├── facebook.png
│   ├── netflix.png
│   ├── microsoft.png
│   ├── instagram.png
│   └── credit_agricole.png
│
├── 📂 emails_extraits\        ← 481 fichiers .eml individuels
├── 📂 emails_avec_images\     ← 68 emails qui contiennent des images
├── 📂 images_extraites\       ← 80 images PNG extraites
│
├── 📄 convertir_mbox.py       ← Etape 1 : convertit phishing-2025.mbox → .eml
├── 📄 filtrer_emails.py       ← Etape 2 : garde seulement les emails avec images
├── 📄 extraire_images.py      ← Etape 3 : extrait les images des .eml
├── 📄 comparer_logos.py       ← Etape 4 : compare les images aux logos + génère resultats.json
├── 📄 app.py                  ← Dashboard Streamlit interactif
│
├── 📄 phishing-2025.mbox      ← Dataset brut (Nazario Corpus 2025)
└── 📄 resultats.json          ← ⭐ SORTIE FINALE pour l'Etudiant 4
```

---

## ⚙️ Installation

### 1. Installer Python 3.x
Télécharge sur https://python.org

### 2. Installer les dépendances
```powershell
pip install opencv-python pillow streamlit plotly requests numpy
```

### 3. Vérifier l'installation
```powershell
python -c "import cv2, streamlit, plotly; print('OK')"
```

---

## 🚀 Comment lancer le module (ordre important !)

> ⚠️ Si les dossiers `emails_extraits/`, `emails_avec_images/` et `images_extraites/` existent déjà, tu peux sauter directement à l'étape 4.

### Etape 1 — Convertir le .mbox en fichiers .eml
```powershell
cd C:\logos_reference
python convertir_mbox.py
```
➡️ Génère 481 fichiers `.eml` dans `emails_extraits/`

### Etape 2 — Filtrer les emails avec images
```powershell
python filtrer_emails.py
```
➡️ Génère 68 fichiers dans `emails_avec_images/`

### Etape 3 — Extraire les images
```powershell
python extraire_images.py
```
➡️ Génère 80 images PNG dans `images_extraites/`

### Etape 4 — Lancer la comparaison
```powershell
python comparer_logos.py
```
➡️ Génère `resultats.json` avec tous les scores

### Etape 5 — Lancer le dashboard
```powershell
streamlit run app.py
```
➡️ Ouvre automatiquement dans le navigateur sur http://localhost:8501

---

## 📤 Ce que ce module livre à l'Etudiant 4

Le fichier `resultats.json` contient la liste de toutes les images analysées avec leur score. Pour chaque email analysé en live via le dashboard, le JSON de sortie est :

```json
{
  "visual_score": 0.902,
  "ressemble_a": "PayPal_Icon_15.jpeg",
  "statut": "ALERTE",
  "details": [
    {
      "image": "email_0214_html0.png",
      "ressemble_a": "PayPal_Icon_15.jpeg",
      "score": 0.902
    }
  ]
}
```

| Champ | Description |
|-------|-------------|
| `visual_score` | Score entre 0 et 1 (1 = usurpation certaine) |
| `ressemble_a` | Nom du logo le plus proche |
| `statut` | `"ALERTE"` si score >= 0.75, sinon `"SAIN"` |
| `details` | Liste de toutes les images analysées |

---

## 🔢 Interprétation des scores

| Score | Signification | Couleur dashboard |
|-------|--------------|-------------------|
| >= 90% | Critique — usurpation quasi-certaine | 🔴 Rouge foncé |
| 75% - 90% | Elevé — forte suspicion | 🟠 Orange |
| 60% - 75% | Moyen — à surveiller | 🟡 Jaune |
| < 60% | Faible — probablement légitime | 🟢 Vert |

---

## 📊 Résultats sur le dataset Nazario 2025

| Métrique | Valeur |
|----------|--------|
| Emails analysés | 481 |
| Emails avec images | 68 (14%) |
| Images extraites | 80 |
| Alertes détectées | **36 (45%)** |
| Score maximum | **90,2%** (PayPal, Apple) |
| Marque la plus usurpée | **Apple** (24 alertes) |

---

## 🔧 Comment ajouter un nouveau logo

1. Télécharge l'image du logo en PNG (fond blanc, bonne qualité)
2. Copie-le dans `C:\logos_reference\`
3. Nomme-le sans accents ni espaces (ex: `laposte.png`, `bnp.png`)
4. Relance `python comparer_logos.py`

Le logo est automatiquement pris en compte. ✅

---

## 🤝 Dépendances avec les autres modules

| Module | Dépendance | Détail |
|--------|-----------|--------|
| Etudiant 1 (NLP) | ✅ Aucune | On travaille en parallèle |
| Etudiant 3 (URL) | ✅ Aucune | On travaille en parallèle |
| Etudiant 4 (Lead Dev) | ⚠️ JSON uniquement | Il lit `resultats.json` ou appelle la fonction `analyser_email()` |

**On peut travailler totalement en parallèle et assembler à la semaine 7.**

---

## ❓ Problèmes fréquents

**`can't open/read file`** → Vérifier que le nom du fichier logo ne contient pas d'accents. Renommer avec :
```powershell
Rename-Item "Crédit_Agricole.png" "credit_agricole.png"
```

**`No module named 'cv2'`** → Lancer `pip install opencv-python`

**`No module named 'streamlit'`** → Lancer `pip install streamlit plotly`

**Le dashboard ne s'ouvre pas** → Ouvrir manuellement http://localhost:8501 dans le navigateur

---

*Module développé par Etudiant 2 — Projet IA Multimodale 2025-2026*
