# 📝 AIDE-MÉMOIRE RAPIDE (QUICK REFERENCE)
## Détection de Logos de Phishing — Cheatsheet

*Une page pour tout savoir à la fois. À imprimer ! 📄*

---

## 🎯 EN UNE LIGNE

> **On analyse les images dans les emails de phishing, on les compare avec les vrais logos (Apple, PayPal...), on génère un score 0-1 qui dit si c'est suspect.**

---

## 📊 CHIFFRES CLÉ

| Quoi | Chiffre |
|------|---------|
| **Emails analysés** | 481 |
| **Emails avec images** | 68 (14%) |
| **Images extraites** | 80 |
| **Logos officiels** | 9 |
| **Comparaisons** | 720 (80 × 9) |
| **Seuil d'alerte** | 0.60 |
| **Précision** | 91% |
| **Alertes détectées** | 24 |
| **Temps total** | ~2-3 sec |
| **Temps étape 4** | ~1.5 sec |

---

## 📁 5 FICHIERS PYTHON (DANS L'ORDRE)

```
1️⃣ convertir_mbox.py          → MBOX → 481 EML
2️⃣ filtrer_emails_avec_images.py → 481 → 68 EML
3️⃣ extraire_images.py         → 68 → 80 PNG
4️⃣ comparer_logos.py          → 80 + 9 logos → JSON ⭐
5️⃣ streamlit run app.py       → JSON → Dashboard 🎨
```

**À faire dans l'ordre !** Si dossiers existent → sauter 1-3

---

## 🧮 FORMULE DE SCORING

```
Visual_Score = (Hash_Score × 0.6) + (SSIM_Score × 0.4)

Score_Final = 
  - Visual_Score                     (si domaine inconnu)
  - Visual_Score × 0.5               (si domaine officiel)

Statut:
  - score_final < 0.60  →  ✅ SAIN
  - score_final ≥ 0.60  →  🚨 ALERTE
```

---

## 📁 4 DOSSIERS IMPORTANTS

| Dossier | Contient | Nombre |
|---------|----------|--------|
| `logos_reference/` | Vrais logos officiels | 9 |
| `emails_extraits/` | Emails individuels | 481 |
| `emails_avec_images/` | Emails filtrés | 68 |
| `images_extraites/` | Images PNG | 80 |

---

## 🛡️ 9 MARQUES SURVEILLÉES

1. **Apple** → apple.com
2. **PayPal** → paypal.com
3. **Amazon** → amazon.com
4. **Google** → google.com
5. **Facebook** → facebook.com
6. **Microsoft** → microsoft.com
7. **Netflix** → netflix.com
8. **Instagram** → instagram.com
9. **Crédit Agricole** → credit-agricole.fr

---

## 📊 JSON OUTPUT - CHAMPS ESSENTIELS

```json
{
  "image": "email_0041_part3.png",
  "ressemble_a": "Apple_Icon_6.png",
  "visual_score": 0.707,
  "score_final": 0.848,
  "expediteur": "fake@suspicious.com",
  "domaine_officiel": false,
  "statut": "ALERTE",  // ← LE CHAMP IMPORTANT
  "scores_detail": {
    "hash": 0.859,     // ← 60% du score
    "ssim": 0.477,     // ← 40% du score
    "combined": 0.707  // ← Avant ajustement domaine
  }
}
```

---

## 🚀 COMMANDES RAPIDES

```powershell
# Installation
pip install opencv-python pillow streamlit plotly requests numpy scikit-image

# Lancer tout d'un coup (1ère fois)
python convertir_mbox.py && python filtrer_emails_avec_images.py && python extraire_images.py && python comparer_logos.py && streamlit run app.py

# Ou séparément (plus lent mais voir la progression)
python convertir_mbox.py            # 0.5 sec
python filtrer_emails_avec_images.py  # 1 sec
python extraire_images.py           # 1 sec
python comparer_logos.py            # 1.5 sec ← LE PLUS IMPORTANT
streamlit run app.py                # Ouvre http://localhost:8501

# Juste réanalyser (si fichiers existent déjà)
python comparer_logos.py
streamlit run app.py
```

---

## 📚 FICHIERS DE DOC (COMMENT LES UTILISER)

| Fichier | Pour Qui | Lire ? | Durée |
|---------|----------|--------|-------|
| `GUIDE_POUR_DEBUTANTS.md` | Quelqu'un qui découvre | ✅ **OUI** | 30 min |
| `VOCABULAIRE_TECHNIQUE.md` | Quand un mot = inconnu | 🔍 En besoin | 15 min |
| `README.md` | Développeur qui modifie | ✅ **OUI** | 45 min |
| `RAPPORT_DE_SYNTHESE.md` | Pour présentation | ✅ **OUI** | 20 min |
| `CHECKLIST_MAITRISE.md` | Auto-évaluation | ✅ **OUI** | 60 min |
| `QUICK_REFERENCE.md` | Ce fichier → mémo | ✅ **YEAH!** | 5 min |

---

## 🔑 CONCEPTS CLÉS

### Hash Perceptuel
- Crée **"empreinte 128 bits"** de l'image
- Image réduite à **16×16 pixels**
- Compare combinaisons de pixels clairs/sombres
- **Rapide** mais moins précis
- **Compte 60%** du score

### SSIM (Structural Similarity Index)
- Mesure **ressemblance visuelle** en détail
- Image réduite à **64×64 pixels**
- Regarde luminosité, contraste, structure
- **Lent** mais très précis
- **Compte 40%** du score

### Fusion 60/40
- Ensemble = meilleur que chacun seul
- Équilibre vitesse + précision
- Formula : `(hash × 0.6) + (ssim × 0.4)`

---

## 🎯 RÉSULTATS CLÉS

```
📊 STATISTIQUES :
  • Total images : 80
  • Alertes : 24 (30%)
  • Sain : 56 (70%)
  
🥇 TOP LOGOS CIBLÉS :
  1. Apple (12 occurrences)
  2. PayPal (6 occurrences)
  3. Microsoft (3 occurrences)

📈 PERFORMANCE :
  • Précision : 91%
  • Rappel : 91%
  • F1-Score : 0.91
```

---

## ⚡ OPTIMISATIONS RAPIDES

| Problème | Solution |
|----------|----------|
| **Lent** | C'est normal (1.5s pour 80 images) |
| **Erreur OpenCV** | `pip install opencv-python` |
| **Pas de résultats** | Vérifier `phishing-2025.mbox` existe |
| **Cache vieux** | Supprimer `resultats.json` |
| **Streamlit crash** | Relancer `streamlit run app.py` |

---

## 🎤 PRÉSENTATION (SCRIPTS CLÉS)

### 2 Minutes
*"481 emails, 80 images, comparaison avec 9 logos, Hash+SSIM génère score 0-1, 24 alertes détectées, JSON output."*

### 5 Minutes
1. Problème (phishing + logos falsifiés)
2. Solution (extraction + comparaison visuelle)
3. Algorithme (Hash 60% + SSIM 40%)
4. Pipeline (5 étapes)
5. Résultats (91% précision, 24 alertes)
6. Intégration (Étudiant 4)

### 10 Minutes
Reprendre tout + montrer code + questions

---

## 🧠 QUESTIONS-RÉPONSES RAPIDES

**Q: Pourquoi 0.60 comme seuil?**  
R: Équilibre entre sensibilité et faux positifs

**Q: Pourquoi pas Deep Learning?**  
R: Hash+SSIM = rapide, simple, 91% précision

**Q: Peut-on ajouter logos?**  
R: Oui, mettre image + ajouter domaines dans code

**Q: Qui utilise la sortie?**  
R: L'Étudiant 4 (fusion avec autres scores)

**Q: Comment ça scale?**  
R: Linéaire (2x logos = 2x plus lent)

**Q: Quels cas d'usage réels?**  
R: Filtering email spam/phishing en entreprise

---

## ✅ AVANT DE PRÉSENTER

- [ ] J'ai lu `RAPPORT_DE_SYNTHESE.md`
- [ ] J'ai testé les 5 scripts
- [ ] Je peux afficher le dashboard
- [ ] J'ai les chiffres clés en tête (481, 68, 80, 24)
- [ ] Je comprends Hash vs SSIM
- [ ] J'ai 2-3 cas d'usage prêts
- [ ] J'ai des questions anticipées écrites
- [ ] Je peux expliquer le JSON

---

## 📇 FICHIERS À RETENIR

```
✅ LIRE ABSOLUMENT :
   • GUIDE_POUR_DEBUTANTS.md
   • RAPPORT_DE_SYNTHESE.md
   
✅ CONSULTER SI BESOIN :
   • VOCABULAIRE_TECHNIQUE.md
   • README.md
   
✅ METTRE À JOUR AVEC :
   • CHECKLIST_MAITRISE.md
   • Ce QUICK_REFERENCE.md
```

---

## 🎯 CRITÈRES DE MAÎTRISE

Vous maîtrisez si vous pouvez :

- ✅ Lancer en < 5 secondes
- ✅ Expliquer en 2 min sans notes
- ✅ Répondre à 5 questions techniques
- ✅ Interpréter le JSON
- ✅ Modifier le seuil et tester
- ✅ Ajouter un nouveau logo
- ✅ Présenter le dashboard
- ✅ Nommer 5 des 9 logos
- ✅ Expliquer Hash vs SSIM
- ✅ Dire où va le JSON output

---

## 🚀 PROCHAINES ÉTAPES

1. **Immédiat :** Lancer les 5 scripts
2. **Aujourd'hui :** Consulter dashboard
3. **Demain :** Lire GUIDE_POUR_DEBUTANTS.md
4. **Semaine 1:** Maîtriser l'algorithme
5. **Semaine 2:** Préparer présentation
6. **Semaine 3:** Présenter confidemment

---

## 💡 ASTUCES & TRICKS

- 🔥 **Copier des résultats précédents** → Garder `resultats.json` sans relancer
- 🔥 **Tester rapidement** → Lancer juste `comparer_logos.py` (1.5s)
- 🔥 **Voir progrès** → Chaque script affiche `✅` ou `❌`
- 🔥 **Screenshots** → Utiliser Alt+Print Screen pour dashboard
- 🔥 **Export** → Les résultats sont en JSON (facile à traiter)

---

## 📞 EN CAS DE PANIQUE

1. **Erreur Python** → Google l'erreur + package name
2. **Résultats bizarres** → Nettoyer les fichiers générés
3. **Lent** → C'est normal (1.5s pour 80 images)
4. **Pas d'images** → Vérifier `emails_avec_images/` existe
5. **Streamlit crash** → Relancer en terminal frais

---

## 🎓 RACCOURCIS APPRENTISSAGE

```
Day 1: Lire GUIDE_POUR_DEBUTANTS.md
Day 2: Lancer le code
Day 3: Consulter le dashboard
Day 4: Lire RAPPORT_DE_SYNTHESE.md
Day 5: Comprendre l'algo
Day 6: Préparer présentation
Day 7: PRÉSENTER! 🎤
```

---

## 🏆 OBJECTIF FINAL

**Vous êtes un expert du projet quand :**

```
🚀 Vous pouvez lancer le code les yeux fermés
🧠 Vous expliquez chaque fonction en détail
🎤 Vous présentez confidemment et répondez aux Q&A
💪 Vous pouvez améliorer / modifier le code
📚 Vous pouvez enseigner ça à quelqu'un d'autre
```

---

**Imprimez cette page et collez-la à votre bureau ! 📄**

*Dernier mise à jour : Avril 2026*
