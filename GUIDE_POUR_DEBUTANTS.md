# 📚 Guide Complet pour Débutants — Détection de Phishing par Logos

*Bienvenue ! Ce guide explique le projet pas à pas, sans jargon compliqué.*

---

## 🎯 C'est quoi ce projet ? (En 30 secondes)

Imagine que tu reçois un email qui dit **"Connectez-vous à votre compte PayPal"** où un logo PayPal est affiché. 
Mais attention : le logo est FAUX ! Les criminels l'ont copié ou légèrement modifié.

**Ce projet détecte ça automatiquement.** 

Il prend chaque image dans les emails suspects, la compare avec les vrais logos PayPal, Apple, Amazon... et dit : "⚠️ ATTENTION, ce logo est suspect !" ou "✅ C'est bon, ça semble normal."

---

## 📁 Les dossiers — Où tout se passe

```
📂 C:\logos_reference\
│
├── 📂 logos_reference/         ← Les VRAIS logos des grandes marques
│   │                             (Apple, PayPal, Google, Amazon...)
│   ├── paypal.jpeg
│   ├── apple.png
│   ├── amazon.png
│   └── ... (9 logos officiels)
│
├── 📂 emails_extraits/         ← Les 481 emails convertis individuellement
│   │                             (format .eml, prêts à être analysés)
│   ├── email_0000.eml
│   ├── email_0001.eml
│   └── email_0480.eml
│
├── 📂 emails_avec_images/      ← Les emails QUI CONTIENNENT des images
│   │                             (seulement 68 sur 481)
│   ├── email_0041.eml
│   └── email_0042.eml
│
├── 📂 images_extraites/        ← Les images EXTRAITES des emails
│   │                             (80 images au total)
│   ├── email_0041_part3.png
│   ├── email_0042_part3.png
│   └── ...
│
├── 📄 resultats.json           ← ⭐ LE RÉSULTAT FINAL
│   │                             (scores, alertes, tout est dedans)
│   ...
```

### 🔍 Qu'est-ce que chaque dossier contient ?

| Dossier | Contient | Exemple |
|---------|----------|---------|
| **logos_reference** | Les logos VRAIS, officiels | paypal.jpeg = le vrai logo PayPal |
| **emails_extraits** | Tous les emails convertis | email_0041.eml = 1 email suspect |
| **emails_avec_images** | Emails contenant au moins 1 image | Seulement 68 emails = 68/481 = 14% |
| **images_extraites** | Toutes les images trouvées | email_0041_part3.png = une image |

---

## 🧩 Les fichiers Python — Expliqués simplement

### 1️⃣ `convertir_mbox.py` — Découper l'énorme fichier email

**Qu'est-ce que c'est ?**
Un fichier `.mbox` c'est comme une **grosse boîte** contenant 481 emails entassés les uns sur les autres.

**Ce que fait ce script :**
- Ouvre `phishing-2025.mbox` (le gros fichier)
- Découpe chaque email individuellement 
- Les sauvegarde comme des fichiers `.eml` numérotés (email_0000.eml, email_0001.eml...)

**Résultat :** 481 fichiers séparés, plus faciles à traiter

```powershell
python convertir_mbox.py
```

---

### 2️⃣ `filtrer_emails_avec_images.py` — Garder seulement les importants

**Qu'est-ce que c'est ?**
Sur 481 emails, beaucoup NE CONTIENNENT PAS d'images. Alors pourquoi les analyser ?

**Ce que fait ce script :**
- Ouvre chaque email
- Demande : "Y a-t-il une image dedans ?"
- Si OUI → sauvegarde dans `emails_avec_images/`
- Si NON → ignore complètement

**Résultat :** Seulement 68 emails avec images (beaucoup plus rapide à analyser)

```powershell
python filtrer_emails_avec_images.py
```

---

### 3️⃣ `extraire_images.py` — Sortir les images des emails

**Qu'est-ce que c'est ?**
Les images ne sont pas faciles à sortir des emails. Elles peuvent être :
- Attachées normalement
- Ou **cachées en code** (base64) dans du HTML

**Ce que fait ce script :**
- Ouvre chaque email (des 68 qui contiennent des images)
- Cherche les images attachées → les extrait
- Cherche les images cachées en HTML → les extrait aussi
- Les sauvegarde comme des fichiers `.png` dans `images_extraites/`

**Résultat :** 80 images PNG, prêtes à être comparées

```powershell
python extraire_images.py
```

---

### 4️⃣ `comparer_logos.py` — LE TRAVAIL PRINCIPAL ⭐

**Qu'est-ce que c'est ?**
C'est le cœur du projet. Ici, on compare chaque image extraite avec les vrais logos.

**Comment ça marche ?**

1. **Charge les vrais logos** (les 9 logos officiels)
2. **Pour chaque image extraite:**
   - Crée une "empreinte digitale" de l'image (hash perceptuel)
   - Crée la même "empreinte" de chaque vrai logo
   - Compare les deux → donne un **score de similarité** entre 0 et 1
   - Utilise aussi une 2e méthode (SSIM) pour plus de précision
   - **Combine les deux scores** = score final

3. **Génère le JSON de résultats** avec tous les scores et alertes

**Résultat :** `resultats.json` avec tout ce qu'il faut savoir

```powershell
python comparer_logos.py
```

---

### 5️⃣ `app.py` — Le Dashboard Interactif 🎨

**Qu'est-ce que c'est ?**
Une interface Web jolie et facile d'utilisation pour voir les résultats.

**Ce que tu y trouves :**
- 📊 Graphiques montrant les résultats
- 👁️ Les images avec les scores
- 📈 Statistiques globales
- 🎨 Alertes visuelles (vert = bon, rouge = danger)

```powershell
streamlit run app.py
```

Puis ouvre ton navigateur à : `http://localhost:8501`

---

## 🔢 Les Scores — Comment ça marche ?

### Score entre 0 et 1

```
0.0 ─────────────────────────── 1.0
|                                 |
✅ SAIN                      🚨 PHISHING
(image = pas ressemblance)   (image = très susvisé)

0.0 → 0.59 = ✅ OK
0.60 → 1.00 = 🚨 ALERTE !
```

### D'où vient le score ?

Le score est calculé avec **2 méthodes** :

#### Méthode 1 : Hash Perceptuel (60%)
- Crée une "empreinte" de l'image (petite image 16×16)
- La compare avec l'empreinte du vrai logo
- Rapide et efficace
- **Compte pour 60% du score final**

#### Méthode 2 : SSIM (40%)
- Regarde les pixels et la ressemblance visuelle
- Plus détaillée et précise
- **Compte pour 40% du score final**

#### Formule :
```
Score Final = (Hash × 0.6) + (SSIM × 0.4)
```

Exemple :
- Hash score = 0.8, SSIM score = 0.6
- Score final = (0.8 × 0.6) + (0.6 × 0.4) = 0.48 + 0.24 = **0.72** = 🚨 ALERTE

---

## 📤 Le fichier `resultats.json` — Ce que tu reçois

**C'est le fichier le plus important !** C'est ce qu'on donne à l'Étudiant 4.

### Structure d'une ligne :

```json
{
  "image": "email_0041_part3.png",           // Nom de l'image
  "ressemble_a": "Apple_Icon_6.png",         // Quel logo ça ressemble
  "visual_score": 0.707,                     // Score de similarité (0-1)
  "score_final": 0.848,                      // Score ajusté final
  "expediteur": "DEWA<lara@enroutel.com>",   // Qui a envoyé l'email
  "domaine_expediteur": "enroutel.com",      // Domaine de l'expéditeur
  "domaine_officiel": false,                 // Est-ce un vrai domaine ?
  "statut": "ALERTE",                        // ✅ SAIN ou 🚨 ALERTE
  "scores_detail": {
    "hash": 0.859,                           // Détail hash perceptuel
    "ssim": 0.477,                           // Détail SSIM
    "combined": 0.707                        // Score combiné
  }
}
```

### Qu'est-ce que ça veut dire ?

- **visual_score** = Ressemblance entre l'image et le logo
- **score_final** = Score ajusté (si domaine = pas officiel → risque plus haut)
- **statut** = Une seule couleur :
  - ✅ SAIN : score < 0.60
  - 🚨 ALERTE : score ≥ 0.60

---

## 🚀 Comment lancer le projet entièrement

### Si c'est la première fois

L'ordre est **TRÈS IMPORTANT** :

```powershell
cd C:\logos_reference

# Étape 1 : Découper le gros fichier
python convertir_mbox.py
# ✅ Résultat : 481 fichiers email_XXXX.eml

# Étape 2 : Garder seulement ceux avec images
python filtrer_emails_avec_images.py
# ✅ Résultat : 68 emails dans emails_avec_images/

# Étape 3 : Extraire les images
python extraire_images.py
# ✅ Résultat : 80 images PNG

# Étape 4 : Comparer avec les logos
python comparer_logos.py
# ✅ Résultat : resultats.json avec les scores

# Étape 5 : Lancer le dashboard
streamlit run app.py
# ✅ Ouvre http://localhost:8501 automatiquement
```

### Si les dossiers existent déjà

Tu peux sauter aux étapes 4 et 5 (les plus rapides) :

```powershell
python comparer_logos.py
streamlit run app.py
```

---

## 🎓 Comprendre le domaine

### Les 9 marques surveillées

| Logo | Domaines officiels | Pourquoi ? |
|------|-------------------|-----------|
| **Apple** | apple.com, icloud.com | 💰 Très ciblé par phishing |
| **PayPal** | paypal.com, paypal.me | 💳 Infos bancaires |
| **Amazon** | amazon.com, amazon.fr | 🎁 Achats en ligne |
| **Google** | google.com, googleapis.com | 🔓 Compte très important |
| **Facebook** | facebook.com, fbcdn.net | 👥 Infos personnelles |
| **Microsoft** | microsoft.com, outlook.com, live.com | 💼 Professionnel |
| **Netflix** | netflix.com, nflximg.com | 📺 Accès payant |
| **Instagram** | instagram.com, cdninstagram.com | 📸 Réseau social |
| **Crédit Agricole** | credit-agricole.fr, ca-paris.fr | 🏦 Bancaire français |

**La règle :** Si tu vois le logo Apple MAIS que l'expéditeur vient de `fake-apple-support.ru` → ⚠️ **BIDOUILLE !**

---

## 🤔 Questions / Réponses

### Q. Pourquoi certains emails n'ont pas d'images ?
R. Les emails de phishing n'aiment pas les images (ça pèse lourd, c'est plus facile à filtrer). 68 sur 481 = seulement 14%.

### Q. D'où vient le fichier `phishing-2025.mbox` ?
R. C'est un dataset de 2025 venant du **Corpus Nazario** (une base de données de vrais emails de phishing).

### Q. Pourquoi 2 scores (hash + SSIM) ?
R. Le hash est rapide mais parfois imprécis. SSIM est lent mais précis. Ensemble = équilibre parfait.

### Q. Qui utilise le fichier `resultats.json` ?
R. L'**Étudiant 4** qui combine ça avec les scores d'autres modules (texte, domaine, etc.)

### Q. Comment je présente ça à quelqu'un ?
R. Voir la section "**Comment présenter ce projet**" en bas 👇

---

## 🎬 Comment présenter ce projet (Aide pour ta présentation)

### Version courte (2 minutes)
*"Ce projet détecte les images de phishing. Il reçoit des emails suspects, extrait les images, les compare avec les vrais logos (Apple, PayPal, Amazon...) et génère un score de risque entre 0 et 1. Plus c'est haut, plus c'est suspect."*

### Version moyenne (5 minutes)

1. **Le contexte :** 481 emails de phishing
2. **Le problème :** Comment détecter les faux logos ?
3. **La solution :**
   - Extraire les images ✅
   - Créer une "empreinte" de chaque image ✅
   - Comparer avec les vrais logos ✅
   - Générer un score ✅
4. **Les résultats :** Un JSON avec tous les scores pour les autres modules
5. **Le dashboard :** Interface pour visualiser tout ça

### Version longue (10 minutes)

*Reprendre tous les points du guide, avec les détails techniques et les files d'attente.*

---

## 📖 Vocabulaire Clé

Voir le fichier **`VOCABULAIRE_TECHNIQUE.md`** pour une explication complète de tous les termes.

---

## ✅ Checklist pour comprendre ce projet

- [ ] Je sais c'est quoi `phishing-2025.mbox`
- [ ] Je comprends la différence entre les 4 dossiers (emails_extraits, emails_avec_images, images_extraites, logos_reference)
- [ ] Je sais ce que font les 5 scripts Python
- [ ] Je comprends comment le score est calculé
- [ ] Je peux lancer `python comparer_logos.py` sans erreur
- [ ] Je peux ouvrir `http://localhost:8501` et voir le dashboard
- [ ] Je peux lire et comprendre une ligne du `resultats.json`
- [ ] Je peux présenter ce projet en 2 minutes

Si tout ✅ → **Tu maîtrises le projet !** 🎉

---

**Dernière question ? Vérifier le fichier `VOCABULAIRE_TECHNIQUE.md` ci-dessous !**
