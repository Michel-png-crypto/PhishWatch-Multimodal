# Détection de phishing — Module Vision (logos)

**Florient Kalumuna** · Groupe 8 · IA multimodale (email + URL + images)

Extraction et analyse des images dans les emails suspects : comparaison aux logos officiels (Apple, PayPal, Amazon, etc.) et production d’un **score de risque visuel** (`resultats.json`) pour la fusion multimodale.

---

## Avancement vs cahier des charges (Groupe 8)

| Phase CDC | Contenu | État global | Ta partie (vision) |
|-----------|---------|-------------|-------------------|
| 1 – Besoins | Cas d’usage, métriques | OK (doc groupe) | OK |
| 2 – Architecture | Modules, flux | Partiel | Pipeline documenté |
| 3–4 – Développement | Email, URL, images | Partiel | **OK** |
| 5 – Intégration IA | Fusion des scores | En cours | JSON prêt + `fusion_multimodale.py` |
| 6 – Tests | Précision / rappel, rapport | Partiel | **25 tests pytest** ; métriques formelles à faire |
| 7 – Reporting | Dashboard, exports | Partiel | HTML + Streamlit **optionnel** |
| 8 – Déploiement | Docker, multi-OS | Non fait | Chemins relatifs OK |

**KPI CDC :** précision &gt; 90 %, faux positifs &lt; 10 %, scan &lt; 2–3 s/email — **non mesurés officiellement** sur tout le corpus ; le module vision seul est rapide (~2 s pour 80 images).

---

## Statut module vision (Florient)

| Élément | État |
|---------|------|
| Extraction images (PJ + base64) | OK |
| Prétraitement (grayscale, redimensionnement) | OK |
| Scoring (hash + SSIM + domaine) | OK |
| `resultats.json` | OK (80 images) |
| Interconnexion + `resultats_fusion.json` | OK |
| Tests unitaires | OK (`pytest tests/`) |
| Rapport HTML (`generer_rapport.py`) | OK (optionnel) |
| Dashboard Streamlit (`app.py`) | OK (**optionnel**, démo) |
| OCR Tesseract | Non fait (optionnel au CDC) |

---

## Vérifier et tester (recommandé)

```powershell
cd C:\logos_reference
pip install -r requirements.txt

python verifier_projet.py          # contrôle complet + fusion
python verifier_projet.py --pipeline   # + ré-extraction et comparaison logos

pytest tests/ -v                   # 25 tests unitaires
```

---

## Pipeline vision

```powershell
python convertir_mbox.py              # si phishing-2025.mbox présent
python filtrer_emails_avec_images.py
python extraire_images.py
python comparer_logos.py                # produit resultats.json
python fusion_multimodale.py            # fusion avec collègues
python generer_rapport.py               # optionnel → rapport_analyse.html
```

**Dashboard :** pas obligatoire pour le pipeline ni la soutenance technique. Utile pour **démo visuelle** (`streamlit run app.py`). En production / intégration, seuls les **JSON** comptent.

---

## Interconnexion équipe

| Fichier | Module | Responsable |
|---------|--------|-------------|
| `resultats.json` | Vision / logos | **Florient** |
| `resultats_texte.json` | NLP | Masudi |
| `resultats_urls.json` | URL | Béni |
| `resultats_fusion.json` | Score unifié | `fusion_multimodale.py` (équipe ; Foze = architecture / fusion avancée) |

| Membre | Rôle |
|--------|------|
| **Florient Kalumuna** | Images, logos, OpenCV, scoring, reporting vision |
| Masudi Rene-Michel | Email, parsing, NLP |
| Béni GANGOUE | URL, threat intelligence |
| Foze Kamgang Junior | Architecture globale, intégration IA avancée |

---

## Documentation

| Fichier | Public |
|---------|--------|
| [GUIDE_POUR_DEBUTANTS.md](GUIDE_POUR_DEBUTANTS.md) | Comprendre sans jargon |
| [DOCUMENTATION_TECHNIQUE.md](DOCUMENTATION_TECHNIQUE.md) | Algorithmes, config, fusion, tests |

---

## Structure

```
logos_reference/          # dépôt projet (nom du repo)
├── *.png / *.jpeg        # logos officiels (racine du projet)
├── emails_extraits/
├── emails_avec_images/
├── images_extraites/
├── extraire_images.py
├── comparer_logos.py
├── fusion_multimodale.py
├── verifier_projet.py
├── resultats.json
├── resultats_fusion.json
└── tests/
```

---

## Livrable principal

**`resultats.json`** : une entrée par image (`score_final`, `statut` SAIN/ALERTE, domaine expéditeur). Agrégé par email dans la fusion.
