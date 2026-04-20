# ✅ CHECKLIST DE MAÎTRISE DU PROJET
## Détection de Logos de Phishing — Module Vision

*Utilisez cette checklist pour valider votre compréhension du projet. Imprimez-la et cochez au fur et à mesure !*

---

## 📋 NIVEAU 1 : DÉBUTANT (Compréhension de base)

### Contexte & Problème

- [ ] Je comprends ce qu'est le **phishing**
- [ ] Je sais pourquoi les **logos** sont une cible
- [ ] Je peux expliquer en une phrase ce que fait ce module
- [ ] Je sais qu'on analyse **481 emails** d'un dataset
- [ ] JE sais que seulement **68 emails contiennent des images**

### Architecture Générale

- [ ] Je peux énumérer les **5 étapes du pipeline**
- [ ] Je sais ce que c'est un **fichier MBOX**
- [ ] Je comprends la différence entre **EML** et **MBOX**
- [ ] Je sais où sont stockées les **images extraites**
- [ ] Je sais où sont stockés les **logos officiels**

### Installation & Lancement

- [ ] J'ai **Python 3.8+** installé
- [ ] J'ai installé avec succès les **packages requis** (`opencv`, `streamlit`, etc.)
- [ ] Je peux lancer **`python convertir_mbox.py`** sans erreur
- [ ] Je peux lancer **`python comparer_logos.py`** sans erreur
- [ ] Je peux ouvrir **`http://localhost:8501`** après `streamlit run app.py`

### Concepts Clé

- [ ] Je comprends ce qu'est un **"score"** (nombre 0-1)
- [ ] Je sais ce qu'est le **seuil d'alerte (0.60)**
- [ ] Je comprends **"statut SAIN"** vs **"statut ALERTE"**
- [ ] Je sais qu'il y a **9 marques** surveillées
- [ ] Je peux nommer **3 de ces 9 marques** (ex: Apple, PayPal, Amazon)

### Fichiers Importants

- [ ] Je sais où se trouve **`resultats.json`**
- [ ] Je sais que c'est la **sortie principale** du projet
- [ ] Je peux ouvrir et **lire une ligne** du JSON
- [ ] Je comprends la différence entre **`visual_score`** et **`score_final`**

---

### ✅ BILAN NIVEAU 1
- **Score :** ___ / 20 cases ☑️
- **Interprétation :**
  - ✅ 18+ : Vous êtes prêt pour le Niveau 2
  - 🟡 12-17 : Relire `GUIDE_POUR_DEBUTANTS.md`
  - ❌ <12 : Commencer par le début

---

## 📊 NIVEAU 2 : INTERMÉDIAIRE (Compréhension technique)

### Détails du Pipeline

- [ ] Je peux expliquer ce que fait **`convertir_mbox.py`** en détail
- [ ] Je comprends pourquoi on **filtre les emails** (optimization)
- [ ] Je peux expliquer le processus d'**extraction d'images**
- [ ] Je sais qu'il existe deux types d'images dans les emails :
  - [ ] Les images **attachées classiquement**
  - [ ] Les images **encodées en base64 HTML**
- [ ] Je comprends pourquoi c'est utile de **redimensionner** les images

### L'Algorithme de Scoring

- [ ] Je comprends ce qu'est un **"hash perceptuel"**
- [ ] Je sais qu'il y a **128 bits** dans l'empreinte
- [ ] Je peux expliquer comment on **compare 2 hash**
- [ ] Je comprends ce qu'est le **score de similarité**
- [ ] Je sais qu'on réduit à **16×16 pixels** pour le hash

### SSIM (Structural Similarity)

- [ ] Je comprends que **SSIM mesure la ressemblance visuelle**
- [ ] Je sais qu'on réduit à **64×64 pixels** pour SSIM
- [ ] Je peux expliquer pourquoi SSIM est **plus lent mais plus précis**
- [ ] Je comprends la **formule combinée :** 60% hash + 40% SSIM
- [ ] Je sais que SSIM vient de la **bibliothèque scikit-image**

### Les 9 Marques

- [ ] Je peux nommer les **9 marques** surveillées
- [ ] Je peux classer par ordre de **priorité/risque**
- [ ] Je sais les **domaines officiels** de 5 marques
- [ ] Je comprends pourquoi **Apple est la plus ciblée**
- [ ] Je sais que Crédit Agricole est **spécifique à la France**

### JSON de Résultats

- [ ] Je peux lire et **interpréter tous les champs** du JSON
- [ ] Je sais la différence entre :
  - [ ] `visual_score` (ressemblance)
  - [ ] `score_final` (après ajustement domaine)
- [ ] Je comprends l'**ajustement du domaine** (sain vs suspicieux)
- [ ] Je sais que **`ressemble_a`** = le logo le plus similaire
- [ ] Je peux calculer manuellement un **score hypothétique**

### Configuration

- [ ] Je sais où se trouve la ligne **`SEUIL = 0.60`**
- [ ] Je comprends qu'augmenter le seuil = **plus strict**
- [ ] Je comprends que diminuer le seuil = **plus sensible**
- [ ] Je peux modifier le seuil (et relancer le script)
- [ ] Je sais où sont les **`DOMAINES_OFFICIELS`** dans le code

### Dashboard Streamlit

- [ ] Je peux voir les **graphiques** et comprendre les données
- [ ] Je sais filtrer les résultats par **statut** (SAIN/ALERTE)
- [ ] Je peux **voir les images** avec leurs scores
- [ ] Je comprends le **code de couleurs** (vert=OK, rouge=alerte)
- [ ] Je sais que le dashboard se connecte au **`resultats.json`**

### Dépannage & Erreurs

- [ ] Je sais comment **vérifier que Python est installé**
- [ ] Je sais comment **vérifier que les packages sont installés**
- [ ] Je sais comment **supprimer le cache** (fichiers générés)
- [ ] Je peux **interpréter une erreur** OpenCV
- [ ] Je sais où chercher l'aide (README, Google, etc.)

---

### ✅ BILAN NIVEAU 2
- **Score :** ___ / 30 cases ☑️
- **Interprétation :**
  - ✅ 25+ : Prêt pour Niveau 3 ✨
  - 🟡 18-24 : Relire `README.md` et `VOCABULAIRE_TECHNIQUE.md`
  - ❌ <18 : Revenir au Niveau 1

---

## 🧠 NIVEAU 3 : AVANCÉ (Maîtrise expert)

### Optimisations & Performance

- [ ] Je sais que le **hashing est O(1)** pour comparaison
- [ ] Je comprends pourquoi on fait **Grayscale** (vitesse × 3)
- [ ] Je sais qu'on pourrait **paralléliser** les comparaisons
- [ ] Je comprends le **trade-off** qualité vs temps
- [ ] Je peux estimer le temps pour **1000 images**

### Cas d'Usage Avancés

- [ ] Je peux prédire un score pour un **new logo jamais vu**
- [ ] Je peux expliquer pourquoi les **logos modifiés** sont toujours détectés
- [ ] Je comprends les **faux positifs** et **faux négatifs**
- [ ] Je sais qu'un **vrai logo officiel aura un score élevé**
- [ ] Je peux concevoir un **test pour valider la qualité**

### Intégration Systèmes

- [ ] Je sais que le JSON est utilisé par **l'Étudiant 4**
- [ ] Je comprends la **fusion des scores** avec autres modules
- [ ] Je peux envisager une **API REST** pour ce module
- [ ] Je sais qu'on pourrait faire du **real-time streaming**
- [ ] Je comprends comment ça s'intègre dans une **architecture complète**

### Améliorations Technologiques

- [ ] Je peux proposer d'utiliser **Deep Learning (CNN)** pour plus de logos
- [ ] Je sais qu'un **réseau de neurones** serait plus flexible
- [ ] Je comprends pourquoi écrire en **C++/Rust** serait plus rapide
- [ ] Je peux concevoir un **système de cache** persistant
- [ ] Je sais comment ajouter **multi-threading** (parallelization)

### Validation & Tests

- [ ] Je peux **calculer Précision, Rappel, F1-Score** manuellement
- [ ] Je sais écrire un **test unitaire** pour une fonction
- [ ] Je comprends **l'importance du dataset** de validation
- [ ] Je peux concevoir un **benchmark** (mesure performance)
- [ ] Je sais qu'il faut tester les **cas limites** (images corrompues, etc.)

### Code & Refactoring

- [ ] Je peux **ajouter un nouveau logo** sans modifier 10 fois
- [ ] Je peux **extraire les constantes** dans un fichier config
- [ ] Je sais **réorganiser le code** en modules réutilisables
- [ ] Je peux **documenter chaque fonction** avec docstrings
- [ ] Je sais utiliser **Git** pour versionner les changements

### Présentation Avancée

- [ ] Je peux faire une **présentation de 10 minutes** complet
- [ ] Je peux **répondre à des questions piégées** sur l'algo
- [ ] Je peux **adapter ma présentation** au public (techniques vs business)
- [ ] Je peux **montrer le code** et expliquer les décisions
- [ ] Je peux **suggerir des améliorations** crédibles

### Vision Futur

- [ ] Je peux envisager passer à **500 logos** au lieu de 9
- [ ] Je comprends les défis de **scalabilité**
- [ ] Je peux concevoir **un système international** multilingue
- [ ] Je sais qu'une **IA** pourrait être plus adaptée
- [ ] Je comprends les **implications de sécurité** (adversarial attacks)

---

### ✅ BILAN NIVEAU 3
- **Score :** ___ / 30 cases ☑️
- **Interprétation :**
  - ✅ 25+ : Vous êtes UN EXPERT du projet 🏆
  - 🟡 18-24 : Très bon, quelques lacunes
  - ❌ <18 : Progresser avec des projets additionnels

---

## 🎤 NIVEAU 4 : PRÉSENTATION (Savoir-faire)

### Présentation 2 Minutes

- [ ] Je peux présenter en **moins de 2 minutes**
- [ ] Je couvre : **problème → solution → résultats**
- [ ] Je dis le **nombre : 481 emails, 80 images, 24 alertes**
- [ ] Je mentionne les **deux algorithmes** (Hash + SSIM)
- [ ] Je dis que c'est envoyé à **l'Étudiant 4**

**Score :** ⏱️ ___ sec | 🎯 Points clés : ___ / 5

---

### Présentation 5 Minutes

- [ ] J'aborde le **contexte du phishing**
- [ ] J'explique le **problème et la solution**
- [ ] Je décris le **pipeline 5 étapes**
- [ ] Je détaille l'**algorithme de scoring** (Hash + SSIM)
- [ ] Je montre les **résultats concrètes** (statistiques, screenshots)
- [ ] Je parle de l'**intégration** avec les autres modules
- [ ] J'ajoute une **démo du dashboard**
- [ ] J'invite à des **questions**

**Score :** ⏱️ ___ min | Questions répondues : ___ / 5

---

### Présentation 10 Minutes (Complète)

- [ ] Introduction avec **contexte cyber** global
- [ ] Problème **en détail** : pourquoi logos, pourquoi difficile
- [ ] Solution **étape par étape** avec diagrammes
- [ ] Algorithme : **Hash vs SSIM vs Combinaison**
- [ ] Code : **montrer les parties clés** brièvement
- [ ] Résultats : **statistiques, cas d'usage, validation**
- [ ] Intégration : **Étudiants 1, 3, 4**
- [ ] Limitations : **"ceque ça ne fait pas"**
- [ ] Améliorations futures**
- [ ] **Questions détaillées**

**Score :** ⏱️ ___ min | Niveau détail : ___ / 10

---

### Questions Anticiper

Préparez-vous à répondre à :

- [ ] "Comment ça compare avec Deep Learning ?"
- [ ] "Pourquoi 60% hash + 40% SSIM ?"
- [ ] "Quel est le faux positif rate ?"
- [ ] "Peut-on détecter des logos complètement nouveaux ?"
- [ ] "Comment ça scale à 10 000 logos ?"
- [ ] "Pourquoi pas utiliser une simple ressemblance Euclidienne ?"
- [ ] "Comment vous validation la qualité ?"
- [ ] "Quel est le bottleneck performance ?"
- [ ] "Comment l'Étudiant 4 utilise vos résultats ?"
- [ ] "Quelle est la précision exacte ?"

**Réponses préparées :** ___ / 10

---

### Démo Live

- [ ] Je peux lancer les scripts **en live** sans panique
- [ ] Je sais **shortcut-er** si c'est trop lent (fichiers pré-générés)
- [ ] Je peux ouvrir et **expliquer le JSON** rapidement
- [ ] Je peux afficher le **dashboard Streamlit**
- [ ] J'ai des **screenshots** backup en PDF si ça crash

**Préparation démo :** ____%

---

### ✅ BILAN NIVEAU 4
- **Score Global : $___ / 40 cases ☑️
- **Prêt à présenter :** 
  - ✅ 35+ : 100% Prêt 🎤
  - 🟡 25-34 : Presque prêt (une relecture)
  - ❌ <25 : Pratiquer d'avantage

---

## 🏆 SCORE TOTAL DE MAÎTRISE

### Calcul

```
Niveau 1 : ___ / 20  (Comprendre)
Niveau 2 : ___ / 30  (Appliquer)
Niveau 3 : ___ / 30  (Analyser)
Niveau 4 : ___ / 40  (Présenter)
─────────────────────────
TOTAL    : ___ / 120
```

### Interprétation du Score

| Score | Statut | Signification |
|-------|--------|--------------|
| **110-120** | 🏆 MAÎTRE | Vous êtes expert, capable d'enseigner |
| **90-109** | ⭐ COMPÉTENT | Vous maîtrisez très bien le projet |
| **70-89** | 🟢 BON | Vous êtes solide, quelques gaps |
| **50-69** | 🟡 MOYEN | Besoin de révision avant présentation |
| **<50** | 🔴 FAIBLE | Revenir au Niveau 1 |

---

## 📚 Resources de Révision Rapides

### Par Niveau

**Niveau 1 Faible ?**
→ Lire `GUIDE_POUR_DEBUTANTS.md` (30 min)

**Niveau 2 Faible ?**
→ Lire `README.md` section "L'algorithme" (45 min)

**Niveau 3 Faible ?**
→ Lire le code `comparer_logos.py` (1 heure)

**Niveau 4 Faible ?**
→ Pratiquer la présentation 5 fois (2 heures)

---

## 🎓 Progression Recommandée

### Semaine 1
- ☑️ Lire `GUIDE_POUR_DEBUTANTS.md`
- ☑️ Lancer le pipeline (5 scripts)
- ☑️ Valider Niveau 1 (>18/20)

### Semaine 2
- ☑️ Lire `README.md` + `VOCABULAIRE_TECHNIQUE.md`
- ☑️ Exployer le dashboard Streamlit
- ☑️ Valider Niveau 2 (>25/30)

### Semaine 3
- ☑️ Étudier le code `comparer_logos.py`
- ☑️ Comprendre Hash + SSIM en détail
- ☑️ Valider Niveau 3 (>25/30)

### Semaine 4
- ☑️ Préparer 3 présentations (2min, 5min, 10min)
- ☑️ Pratiquer répondre aux questions
- ☑️ Valider Niveau 4 (>35/40)

### Résultat Final
- ✅ Score Total > 100/120
- ✅ Prêt à présenter confidemment
- ✅ Capable d'expliquer n'importe quel détail

---

## ✅ AUTO-QUESTIONNAIRE FINAL

Répondez Vrai ou Faux :

1. `Je peux lancer les 5 scripts sans regarder la doc` **[ ] V [ ] F**
2. `Je comprends pourquoi on utilise Hash + SSIM` **[ ] V [ ] F**
3. `Je peux expliquer le seuil 0.60 en 30 secondes` **[ ] V [ ] F**
4. `Je sais les 9 marques par cœur` **[ ] V [ ] F**
5. `Je peux lire et interpréter le JSON` **[ ] V [ ] F**
6. `Je pourrais ajouter un nouveau logo en 5 min` **[ ] V [ ] F**
7. `Je pourrais modifier le seuil et tester` **[ ] V [ ] F**
8. `Je peux présenter en 2 minutes sans notes` **[ ] V [ ] F**
9. `Je peux répondre à 5 questions techniques` **[ ] V [ ] F**
10. `Je pourrait modifier le code` **[ ] V [ ] F**

**Vrai : ___ / 10**
- ✅ 9-10 : Vous maîtrisez ! 🎉
- 🟡 7-8 : Bon, quelques révisions
- 🔴 <7 : Besoin d'étude supplémentaire

---

## 🎯 OBJECTIF FINAL

### ✅ Checklist Succès

Cochez quand vous êtes prêt :

- [ ] **Lundi :** Je peux lancer le code
- [ ] **Mercredi :** Je comprends l'algorithme
- [ ] **Vendredi :** Je peux présenter 2 min
- [ ] **Lundi +1 semaine :** Je peux présenter 5 min
- [ ] **Mercredi +1 semaine :** Je suis un expert

### 🏁 Résultat Idéal

```
🏆 Je suis un EXPERT du projet
✅ Je peux l'enseigner à quelqu'un d'autre
✅ Je peux l'améliorer
✅ Je peux le présenter confidemment
✅ Je comprends chaque ligne de code
```

---

**Bonne chance dans votre maîtrise du projet ! 🚀**

Document créé : Avril 2026  
Mise à jour : À mesure que vous progressez  
Partagez avec : L'équipe, les collègues, les étudiants futurs
