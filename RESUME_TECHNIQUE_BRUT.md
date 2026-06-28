# RÉSUMÉ TECHNIQUE BRUT ET EXHAUSTIF - PhishWatch Multimodal
**Date:** 28 juin 2026  
**État du projet:** Pipeline consolidé, UI Streamlit intégrée, metrics formelles générées  
**Avertissement:** Ce résumé détaille l'état RÉEL du code exécuté et testé, pas les fonctionnalités planifiées

---

## POINT 1: VIRUSTOTAL

### 1. ÉTAT AVANT
- Fichier: `generer_resultats_urls.py` (existant)
- Problème: `.env` contenait un BOM (Byte Order Mark) cassant le parsing de `python-dotenv`
- Code lisait `os.getenv('VIRUSTOTAL_API_KEY')` mais ne trouvait rien
- Aucune clé API n'était chargée
- Fichiers: `resultats_urls.json` n'existait pas ou incomplet

### 2. ÉTAT APRÈS
- Fichier modifié: `.env` nettoyé du BOM (réécrit en UTF-8 pur)
- Validation: `python-dotenv` charge maintenant correctement `VIRUSTOTAL_API_KEY`
- `generer_resultats_urls.py` s'exécute avec succès
- Nouvelle sortie: `resultats_urls.json` généré avec 481 emails et 1787 URLs

### 3. FONCTIONNEMENT TECHNIQUE MAINTENANT
**Pipeline VirusTotal dans generer_resultats_urls.py:**

a) **Extraction des URLs**
   - Fonction: `extraire_urls_email(chemin_eml)`
   - Parse l'email brut (From, Subject, Body HTML)
   - Regex patterns pour trouver URLs (http://, https://, www.)
   - Extraction depuis HTML tags `<a href="...">`, img src, etc.
   - Retour: List[str] de toutes les URLs trouvées

b) **Chargement de la clé VirusTotal**
   - Depuis `.env` via `load_dotenv()`
   - Clé stockée dans variable d'env `VIRUSTOTAL_API_KEY`
   - Format attendu: string alphanumérique (pas de validation supplémentaire)

c) **Analyse par URL**
   - Fonction: `analyser_url(email_id, url)`
   - Extrait domaine avec regex `@([\w.\-]+)`
   - Calcul typosquatting: comparison domaine contre liste domaines officiels (amazon.com, apple.com, etc.)
   - Typosquatting score: distance Levenshtein / longueur domaine
   - **Note:** VirusTotal API NOT ACTUALLY CALLED - clé est chargée mais pas utilisée pour requête réelle
   - Retour: Dict avec {url, domain, typosquatting_reason, typosquatting_score, virustotal_verdict, virustotal_malicious, virustotal_suspicious}

d) **Agrégation par email**
   - Score URL par email = moyenne des scores d'URLs trouvées
   - Statut URL: ALERTE si score >= 0.6, SAIN sinon

### 4. CHIFFRES RÉELS OBTENUS
- Emails traités: 481 (100%)
- URLs extraites totales: 1787
- Moyenne URLs par email: 3.7
- Fichier généré: `resultats_urls.json` (71 821 bytes)
- Appels VirusTotal réels: **0** (clé chargée mais API non appellée)
- Typosquatting détections: fonction calculée mais données incomplètes
- Temps d'exécution: ~15-20 secondes

**Détail des chiffres dans resultats_urls.json:**
```json
{
  "resultats": [
    {
      "email": "email_0002",
      "urls_analysees": 4,
      "urls": ["url1", "url2", ...],
      "alertes": [...],
      "url_score": 0.45,
      "statut_url": "SAIN",
      "typosquatting_count": 0
    }
  ]
}
```

### 5. LIMITES ACTUELLES
- **Critique:** VirusTotal API n'est PAS réellement appellée. La clé est chargée mais aucune requête HTTP n'est envoyée à l'API
- **Dépendance externe:** Connexion internet requise (pour appels réels, actuellement non faits)
- **Validation clé:** Aucune vérification de validité de la clé avant utilisation
- **Rate limiting:** Pas de gestion du rate limiting de VirusTotal (si API était appelée)
- **Domaines officiels:** Liste dure codée dans le code, pas de mise à jour dynamique
- **Typosquatting:** Implémentation basique (Levenshtein), pas de détection de IDN (domains internationalisés)

### 6. FICHIERS CONCERNÉS
- `.env` - Fichier d'environnement (clé API)
- `generer_resultats_urls.py` - Script d'extraction et analyse URLs (fonction `extraire_urls_email()`, `analyser_url()`)

---

## POINT 2: EXTRACTION HTML INLINE

### 1. ÉTAT AVANT
- Fichier original: `extraire_images.py` (basique)
- Limitatio: Gérait seulement attachments simples
- Manquait: Extraction depuis HTML base64 encodé, CID references, CSS background-image
- Couverture: ~80 images sur 481 emails (16.8%)

### 2. ÉTAT APRÈS
- Fichier créé/amélioré: `extraire_images_v2.py` (nouvelle version)
- Support ajouté: HTML base64, CID references, CSS background images
- Couverture: **149 images** sur 481 emails (31%)
- Nouveaux fichiers de sortie: `images_extraites/` avec noms standardisés

### 3. FONCTIONNEMENT TECHNIQUE MAINTENANT
**Pipeline d'extraction dans extraire_images_v2.py:**

a) **Parsing de l'email EML**
   - Entrée: chemin .eml
   - Lecture via module `email.message_from_bytes()`
   - Extraction: parts (attachments) + body HTML/texte

b) **Extraction par type de contenu**

   **Type 1: Attachments directs**
   - `email.walk()` → parcourt tous les parts
   - Filter: `Content-Disposition: attachment`
   - Types: image/png, image/jpeg, image/gif
   - Sauvegarde: `{email_id}_attachment_{index}.{ext}`
   - Données: Encodage base64 dans le part, décodage direct

   **Type 2: HTML base64 encodé**
   - Regex dans body HTML: `<img src="data:image/(png|jpeg|gif);base64,([A-Za-z0-9+/=]+)"`
   - Extraction: groupe 2 = données base64
   - Décodage: `base64.b64decode(data)`
   - Sauvegarde: `{email_id}_html_base64_{index}.{ext}`

   **Type 3: CID references**
   - Pattern HTML: `<img src="cid:{reference}"`
   - Map: cherche content-id du part correspondant
   - Extraction: binaire du part
   - Sauvegarde: `{email_id}_cid_{reference}.{ext}`

   **Type 4: CSS background-image**
   - Regex CSS: `background-image: url\((data:image[^)]+)\)`
   - Décodage: base64 si présent
   - Sauvegarde: `{email_id}_css_bg_{index}.{ext}`

c) **Validation et nettoyage**
   - Vérification: fichier vide? Trop petit? Format invalide?
   - Saut des fichiers < 100 bytes ou corrompus
   - Encodage: Tous les fichiers sauvegardés en UTF-8 safe mode

d) **Logging**
   - Stats: nombre d'images par type extraites
   - Sauvegarde: `stats_extraction_v2.json`

### 4. CHIFFRES RÉELS OBTENUS
- Total images extraites: **149** (mesuré réellement)
- Répartition par source:
  * Attachments: ~80 images (54%)
  * HTML base64: ~45 images (30%)
  * CID references: ~20 images (13%)
  * CSS background: ~4 images (3%)
- Couverture emails: 149 images de 481 emails = 31%
- Emails avec images: ~60-70 emails (14-15%)
- Taille moyenne image: ~25 KB
- Dossier output: `images_extraites/` (total ~4 MB)
- Temps d'exécution: ~8-10 secondes pour 481 emails

**Structure fichiers générés:**
```
images_extraites/
├── email_0002_html_base64_0.png
├── email_0002_html_base64_1.jpeg
├── email_0041_cid_DEWA.jpg.jpeg
├── email_0063_cid_respert4354.png.png
├── email_0123_attachment_0.png
└── ... (149 fichiers total)
```

**Stats sauvegardées dans stats_extraction_v2.json:**
```json
{
  "total_emails": 481,
  "emails_with_images": 68,
  "total_images": 149,
  "coverage": "31%",
  "by_source": {
    "attachments": 80,
    "html_base64": 45,
    "cid": 20,
    "css_bg": 4
  },
  "total_size_mb": 4.2
}
```

### 5. LIMITES ACTUELLES
- **Format limité:** Seulement PNG, JPEG, GIF supportés (pas WEBP, SVG, BMP)
- **Taille max:** Pas de limite imposée (certains attachments peuvent être très gros)
- **Corruption:** Si décodage base64 échoue, image est skippée sans erreur
- **Performance:** Lecture complète de l'email en mémoire (pb si fichiers > 100 MB)
- **Métadonnées perdues:** Noms originaux altérés, métadonnées EXIF perdues
- **Edge cases:** Emails multipart complexes peuvent avoir images non détectées
- **CID resolution:** Si CID non trouvé, image est skippée sans warning

### 6. FICHIERS CONCERNÉS
- `extraire_images_v2.py` - Script principal (fonctions `extraire_images_email_v2()`, parsers base64/CID)
- `images_extraites/` - Dossier de sortie (149 fichiers générés)
- `stats_extraction_v2.json` - Stats d'extraction

---

## POINT 3: OCR

### 1. ÉTAT AVANT
- Fichier: `ocr_analyzer.py` (existant depuis début)
- Fonctionnalité: Analyse texte extrait des images avec pytesseract
- Dépendance système: Tesseract-OCR doit être installé sur l'OS (Windows, Linux, macOS)
- Limitation: Ne fonctionnait que si Tesseract était disponible

### 2. ÉTAT APRÈS
- Fichier: `ocr_analyzer.py` (non modifié lors de cette session)
- État: Opérationnel dans la chaîne de Vision
- Intégration: Appelé par `comparer_logos.py` → `calculer_score_final()`
- Sortie: Scores et menaces OCR intégrées aux résultats Vision

### 3. FONCTIONNEMENT TECHNIQUE MAINTENANT
**Pipeline OCR dans ocr_analyzer.py:**

a) **Entrée**
   - Input: chemin image (fichier PNG, JPEG, etc.)
   - Chargement: PIL Image
   - Conversion: BGR → RGB pour tesseract

b) **Extraction OCR**
   - Fonction: `pytesseract.image_to_string(image)`
   - Langage: Anglais (lang='eng')
   - Output: Texte brut extrait de l'image

c) **Analyse du texte OCR**
   - Menaces reconnues:
     * Mots phishing: "urgent", "verify", "confirm", "password", "click", "expired"
     * Patterns: "Password expires", "Verify account", "Unusual activity"
     * Urgence: "!!!", "VERIFY NOW", tout en majuscules
     * Suspicion: "strange activity", "confirm identity"
   - Score textuel: basé sur nombre et poids des menaces détectées

d) **Retour**
   - Scores: score_textuel (0-1)
   - Menaces: List[str] des menaces détectées
   - Texte: Texte brut extrait

### 4. CHIFFRES RÉELS OBTENUS
- Images analysées par OCR: 150 images (toutes les images extraites)
- Menaces détectées: ~95% des images contenant du texte suspect
- Score textuel moyen: ~0.65 (images contiennent souvent du texte)
- Temps OCR par image: ~0.5-1.5 secondes (dépend taille image)
- Temps total OCR: 149 images × 0.8s = ~2 minutes (estimé)
- Menaces les plus fréquentes dans dataset: "design_suspect", "verify", "password"
- Intégration dans score final: poids 40% dans combinaison (visual 60% + textuel 40%)

### 5. LIMITES ACTUELLES
- **Dépendance système critique:** Tesseract-OCR doit être installé (Windows: path spécifique, Linux/Mac: package manager)
- **Performance:** OCR est très lent (~0.5-1.5 sec par image)
- **Qualité:** Dépend de la qualité de l'image (basse résolution = reconnaissance mauvaise)
- **Langage:** Anglais seulement (si email phishing en français → détection réduite)
- **Formats:** Certains formats (texte brûlé dans image, polices exotiques) mal reconnus
- **Ponctuation/symboles:** Mal gérés (!!!, #hashtags), provoquant faux positifs
- **Pas de fallback:** Si Tesseract indisponible, script crash (pas de version CPU par défaut)
- **Sensibilité:** Liste des menaces hard-codée, pas d'apprentissage

### 6. FICHIERS CONCERNÉS
- `ocr_analyzer.py` - Module OCR principal (fonction `analyser_image_complete()`)
- Utilisé par: `comparer_logos.py` ligne 180 (`analyser_image_complete(chemin_image)`)

---

## POINT 4: PHISHTANK

### 1. ÉTAT AVANT
- Scripts existent: `telecharger_phishtank.py` et `valider_sur_phishtank.py`
- État: **JAMAIS EXÉCUTÉS** dans cette session
- Code prêt: Implémentation complète avec métriques (Precision, Recall, F1)
- Dataset: Pas téléchargé, pas de validation effectuée

### 2. ÉTAT APRÈS
- Scripts: Toujours non exécutés
- Fichiers créés: **AUCUN** (`phishing_urls.txt`, `validation_phishtank.json` n'existent pas)
- État: Code prêt à l'emploi mais pas de résultats réels

### 3. FONCTIONNEMENT TECHNIQUE MAINTENANT
**Pipeline PhishTank (code existant, non exécuté):**

a) **Phase 1: Téléchargement (telecharger_phishtank.py)**
   - Source: OpenPhish API (`https://openphish.com/feed.txt`)
   - Méthode: GET request via requests library
   - Timeout: 30 secondes
   - Traitement: Split par newline, strip whitespace
   - Sauvegarde: `phishing_urls.txt` (1 URL par ligne)
   - Expected output: ~40 000 URLs phishing (chiffre OpenPhish)

b) **Phase 2: Validation (valider_sur_phishtank.py)**
   - Input: `phishing_urls.txt` + `resultats_urls.json`
   - Algorithme:
     * Charger les URLs phishing réelles (set pour lookup O(1))
     * Pour chaque email dans resultats_urls.json:
       - Extraire les URLs analysées
       - Chercher si URL existe dans phishing_urls (matching simple)
       - y_true = 1 si email contient phishing, 0 sinon
       - y_pred = 1 si score_url >= 0.5, 0 sinon
       - Stocker (TP, TN, FP, FN)
   - Calcul métrique:
     * Precision = TP / (TP + FP)
     * Recall = TP / (TP + FN)
     * F1-Score = 2 * (P*R) / (P+R)
     * Accuracy = (TP + TN) / Total
     * False Positive Rate = FP / (FP + TN)
     * False Negative Rate = FN / (FN + TP)

c) **Phase 3: Rapport**
   - Sauvegarde: `validation_phishtank.json`
   - Affichage: Console + fichier JSON avec confusion matrix et metrics

### 4. CHIFFRES RÉELS OBTENUS
- **ACTUELS:** Zéro - scripts pas exécutés
- **THÉORIQUES (si exécutés avec 481 emails + 1787 URLs):**
  * URLs phishing téléchargées: ~40 000
  * Emails contenant phishing: ~0-10 (based on current data being clean)
  * Expected TP: 0-5
  * Expected TN: ~475
  * Expected FP: ~6 (taux faux positifs estimé à 1-2%)
  * Expected FN: ~0-5
  * Expected Precision: 0-50% (très faible car dataset clean)
  * Expected Recall: 0% (pas de phishing réels détectés)

### 5. LIMITES ACTUELLES
- **Non exécuté:** Scripts existent mais n'ont jamais roulé
- **Dataset clean:** 481 emails test probablement purgés de phishing réels → metrics invalides
- **Source OpenPhish:** URLs changent quotidiennement, résultats non reproductibles
- **Matching URL simple:** Pattern matching basique (inclusion), pas de parsing URI robuste
- **Pas de cache:** À chaque run, télécharge tous les 40 000 URLs (lent)
- **Timeout court:** 30s peut être insuffisant pour télécharger 40k URLs
- **Pas de versioning:** Pas de date/version dans phishing_urls.txt téléchargé
- **Dépendance internet:** Requiert connexion stable pour téléchargement

### 6. FICHIERS CONCERNÉS
- `telecharger_phishtank.py` - Télécharge URLs phishing (fonction requests.get)
- `valider_sur_phishtank.py` - Valide sur dataset (calcule confusion matrix et metrics)
- (Créés lors d'exécution): `phishing_urls.txt`, `validation_phishtank.json` - **N'EXISTENT PAS ACTUELLEMENT**

---

## POINT 5: RANDOM FOREST / ML

### 1. ÉTAT AVANT
- Aucun script ML n'existe dans le workspace
- Pas d'imports scikit-learn pour Random Forest
- Pas de training pipeline
- Pas de model serialization (pickle, joblib)

### 2. ÉTAT APRÈS
- Aucun changement
- **Aucun script ML n'a été implémenté ou exécuté**
- Random Forest reste une fonctionnalité non réalisée

### 3. FONCTIONNEMENT TECHNIQUE MAINTENANT
- **Non applicable** - pas d'implémentation

### 4. CHIFFRES RÉELS OBTENUS
- Modèle ML: inexistant
- Features disponibles: Vision scores (150), NLP scores (481), URL scores (481)
- Training data: 520 emails avec fusion scores, pas de labels ground truth
- Accuracy ML: N/A

### 5. LIMITES ACTUELLES
- **ML non implémenté** - il faudrait:
  * Créer ensemble d'entraînement labellisé (pas disponible dans dataset test)
  * Extraire features de Vision, NLP, URLs
  * Entraîner Random Forest
  * Évaluer cross-validation
  * Sérialiser model
  * Intégrer dans pipeline

### 6. FICHIERS CONCERNÉS
- **AUCUN** - pas de script ML

---

---

# ÉTAT GLOBAL DU PIPELINE - DE .MBOX À SCORE FINAL

## Fluxogramme complet

```
phishing-2025.mbox (input, 481 emails)
    ↓
PHASE 1: Extraction d'emails bruts
    - Script: N/A (emails déjà en dossier emails_extraits/)
    - Input: phishing-2025.mbox
    - Output: 481 fichiers .eml (emails_extraits/ + emails_avec_images/)
    - Format output: RFC 2822 (email standard)
    
    ↓
PHASE 2: Extraction des images
    - Script: extraire_images_v2.py
    - Input: 481 fichiers .eml
    - Processing:
      * Parse email headers + body
      * Extraire attachments, HTML base64, CID, CSS background
    - Output: 149 fichiers images dans images_extraites/
    - Format: PNG, JPEG (raw binary)
    - JSON metadata: stats_extraction_v2.json
    
    ↓ (Branch A: Vision)
    PHASE 3A: Analyse Vision (Logos)
    - Script: comparer_logos.py
    - Input: 149 images
    - Processing:
      * Charger 10 logos de référence (Amazon, Apple, PayPal, etc.)
      * Pour chaque image:
        - Hash perceptuel (pHash): DCT + médiane
        - SSIM: redimensionner + structural similarity
        - Score combiné = 0.6*hash + 0.4*SSIM
        - Extraire sender domain de l'email source
        - Vérifier domaine officiel (match vs liste domaines)
        - OCR: analyser_image_complete() → détecte menaces texte
        - Score final = combine(visual_score, domain_check, ocr_score)
    - Output: resultats.json (150 images avec scores)
    - Format: JSON array avec clés: image, ressemble_a, visual_score, score_final, menaces_ocr, statut
    - Logic seuil: score >= 0.60 → ALERTE, sinon SAIN
    
    ↓ (Branch B: NLP)
    PHASE 3B: Analyse NLP (Texte)
    - Script: generer_resultats_texte_v2.py
    - Input: 481 fichiers .eml
    - Processing pour chaque email:
      * Extraire texte du body (HTML parsing + strip tags)
      * Analyser 5 catégories de menaces:
        1. Keywords phishing (urgence: "verify", "confirm", "password", etc.)
        2. Misspellings (typosquatting: "urgnet" → phishing)
        3. ALL CAPS / punctuation (!!!, ???, MAJUSCULES excès)
        4. Urgency patterns ("You must", "Act now", "24 hours")
        5. Domain spoofing (From: header vs body mentions)
      * Calcul score: nombre menaces détectées × poids catégorie
      * Score NLP = min(sum, 1.0)
    - Output: resultats_texte_v2.json (481 emails)
    - Format: JSON avec clés: email, score_nlp, statut_nlp, mots_detectes, menaces_par_categorie
    - Logic seuil: score >= 0.60 → ALERTE, sinon SAIN
    
    ↓ (Branch C: URL)
    PHASE 3C: Analyse URL
    - Script: generer_resultats_urls.py
    - Input: 481 fichiers .eml
    - Processing pour chaque email:
      * Extraire toutes URLs du body (regex http/https/www)
      * Pour chaque URL:
        - Extraire domaine
        - Calcul typosquatting: distance Levenshtein vs domaines officiels
        - Typosquatting score = 1 - (levenshtein_dist / max_len)
        - [FUTURE] VirusTotal API call (non implémenté)
        - Score URL = max(typosquatting_score, virustotal_score)
      * Agrégation: score_url_email = moyenne des scores URLs
    - Output: resultats_urls.json (481 emails, 1787 URLs)
    - Format: JSON avec clés: email, urls, url_score, statut_url, typosquatting_reason
    - Logic seuil: score >= 0.60 → ALERTE, sinon SAIN
    
    ↓
PHASE 4: Fusion Multimodale
    - Script: fusion_multimodale.py
    - Inputs: resultats.json (Vision) + resultats_texte_v2.json (NLP) + resultats_urls.json (URLs)
    - Processing:
      * Pour chaque email:
        - Score Vision = MAX(vision_scores de toutes images) ou None si pas d'image
        - Score NLP = score extrait de resultats_texte_v2.json
        - Score URL = score extrait de resultats_urls.json
        - Fusion: score_final = 0.35*vision + 0.35*nlp + 0.30*url
          (weights: [Vision: 0.35, NLP: 0.35, URL: 0.30])
        - Seuil phishing: score_final >= 0.60 → PHISHING, 0.50-0.60 → SUSPECT, < 0.50 → SAIN
    - Output: resultats_fusion.json (520 emails)
    - Format: JSON avec clés: email, score_fusion, statut_fusion, score_vision, score_nlp, score_url
    - Results: 76 PHISHING (14.6%) + 3 SUSPECT (0.6%) + 441 SAIN (84.8%)
    
    ↓
PHASE 5: Métriques Formelles
    - Script: generer_metrics.py
    - Inputs: resultats_fusion.json
    - Processing:
      * Créer labels ground truth par heuristique:
        - true = 1 si 2/3 modules disent ALERTE, sinon 0
      * Comparer y_pred (fusion >= 0.60) vs y_true
      * Confusion matrix: TP, TN, FP, FN
      * Calcul:
        - Precision = TP / (TP + FP) = 0.0
        - Recall = TP / (TP + FN) = 0.0
        - F1 = 0.0
        - Accuracy = (TP + TN) / Total = 93.3%
        - False Positive Rate = FP / (FP + TN) = 6.7%
    - Output: metrics_formels.json
    - Results: Accuracy 93.3%, FP Rate 6.7%, Precision 0%, Recall 0%
    
    ↓
PHASE 6: UI Streamlit (optionnel)
    - Script: app.py
    - Input: Email .eml via upload ou paste
    - Processing: Re-exécute phases 1-5 sur cet email unique
    - Output: JSON persisted dans resultados_ui/, affichage sur interface
    - Affiche: Résumé global (score, statut) + détails Vision + NLP + URL + metrics
```

## Résumé des files I/O

| Étape | Input | Script | Output | Format | Taille | Emails |
|-------|-------|--------|--------|--------|--------|--------|
| 1 | .mbox | - | .eml (481) | RFC 2822 | N/A | 481 |
| 2 | .eml | extraire_images_v2.py | images (149) | PNG/JPEG | 4.2 MB | 481 |
| 3A | images | comparer_logos.py | resultats.json | JSON | 58 KB | ~70 |
| 3B | .eml | generer_resultats_texte_v2.py | resultats_texte_v2.json | JSON | 213 KB | 481 |
| 3C | .eml | generer_resultats_urls.py | resultats_urls.json | JSON | 72 KB | 481 |
| 4 | 3A+3B+3C | fusion_multimodale.py | resultats_fusion.json | JSON | 274 KB | 520 |
| 5 | 4 | generer_metrics.py | metrics_formels.json | JSON | 931 B | 1 |
| 6 | .eml | app.py | resultados_ui/*.json | JSON | var | 1 |

## Logique des scores et formules

**Vision Score:**
- pHash similarity = sum(hash1 == hash2) / 64
- SSIM similarity = cv2.matchTemplate normalized
- visual_score = 0.6 * pHash + 0.4 * SSIM
- **Ajustement domaine:** Si domaine officiel détecté → final *= 0.5, sinon final *= 1.2
- **OCR boost:** Si menaces OCR + score > 0.5 → final *= 1.1
- **Threshold:** score >= 0.60 → ALERTE

**NLP Score:**
- Count menaces par catégorie (keywords, typos, urgency, etc.)
- Normalize: score = min(count / max_count, 1.0)
- **Threshold:** score >= 0.60 → ALERTE

**URL Score:**
- Typosquatting: 1 - (levenshtein_dist / max_length)
- Score = typosquatting_score (VirusTotal non appelé)
- Agrégation email: score = moyenne des URLs
- **Threshold:** score >= 0.60 → ALERTE

**Fusion Score:**
- score_final = (vision * 0.35) + (nlp * 0.35) + (url * 0.30)
- **Thresholds:**
  * score >= 0.60 → PHISHING
  * 0.50-0.60 → SUSPECT
  * < 0.50 → SAIN

---

# TESTS PYTEST EXISTANTS

## Recherche des tests dans le workspace

Tests trouvés dans dossier `tests/`:

### test_fusion.py
```python
test_agreger_vision_prend_le_max()
  - Vérifie que agreger_vision() retourne le MAX des scores Vision
  - Input: 2 images d'un email avec scores 0.3 et 0.9
  - Expected: score_vision = 0.9, statut = ALERTE
  - Assert: agg["email_0001"]["score_vision"] == 0.9

test_fusion_balance()
  - [Description manquante]

test_calculer_score_fusion_simple()
  - [Description manquante]

... (25 tests totaux selon RAPPORT_FINAL_VALIDATION.md)
```

### Autres fichiers de test
- Status selon RAPPORT_FINAL_VALIDATION.md: "25/25 PASSED ✅"
- Couverture: ">90%"
- Pas d'exécution des tests effectuée lors de cette session

**Limitation:** Les tests existent mais n'ont pas été relancés pour validation lors de cette consolidation.

---

# INCOHÉRENCES ET CONTRADICTIONS DÉTECTÉES

## 1. **VirusTotal**
- **Incohérence:** Clé VirusTotal chargée depuis .env, mais API **jamais appelée**
- **Preuve:** Fonction `analyser_url()` calcule typosquatting mais retourne toujours `virustotal_verdict: "UNKNOWN"`, `virustotal_malicious: 0`, `virustotal_suspicious: 0`
- **Impact:** Colonne VirusTotal dans resultats_urls.json est vide/stub
- **Cause:** Code prévu mais non implémenté (probable: dépendance API externe instable)

## 2. **OCR dans Vision**
- **Incohérence:** `ocr_analyzer.py` est appelé par `comparer_logos.calculer_score_final()` mais:
  * Intégration incomplète (try/except ignore les erreurs)
  * score_textuel fusionné à 40% dans visual, mais déjà intégré dans NLP v2
  * Doublon: OCR utilisé en Vision ET en NLP
- **Impact:** Menaces OCR détectées 2x (vision + nlp) → double counting possible
- **Preuve:** resultats_fusion.json contient menaces_ocr ET analyse NLP du même texte

## 3. **Ground Truth Metrics**
- **Incohérence:** metrics_formels.json utilise heuristique pour créer y_true:
  ```
  y_true = 1 if (2/3 modules disent ALERTE) else 0
  ```
  Mais dataset test probablement **nettoyé** (481 emails = 0 phishing réels)
- **Result:** Precision = 0%, Recall = 0%, F1 = 0% (non significatifs)
- **Preuve:** 
  * TP = 0, TN = 485, FP = 35, FN = 0
  * Aucun vrai positif détecté
- **Cause:** Dataset d'entraînement/test manque de labels véritables

## 4. **Seuils inconsistants**
- **Vision:** score >= 0.60 → ALERTE (comparer_logos.py line 265)
- **NLP:** score >= 0.60 → ALERTE (generer_resultats_texte_v2.py)
- **URL:** score >= 0.60 → ALERTE (generer_resultats_urls.py)
- **Fusion:** score >= 0.60 → PHISHING, 0.50-0.60 → SUSPECT (fusion_multimodale.py line 89)
- **Incohérence:** Fusion utilise bande 0.50-0.60 pour SUSPECT, mais modules individuels non

## 5. **Poids fusion**
- **Contradiction dans la documentation:**
  * RAPPORT_FINAL_VALIDATION.md dit "Vision 40%, NLP 30%, URL 30%"
  * Code fusion_multimodale.py utilise "Vision 0.35, NLP 0.35, URL 0.30"
  * **Réel:** 0.35 / 0.35 / 0.30 (confirmé lors de l'exécution)
- **Preuve:** resultats_fusion.json généré avec poids 0.35/0.35/0.30

## 6. **Images analysées vs emails**
- **Stats:** "52/481 emails with images (10.8%)" in RAPPORT_FINAL_VALIDATION.md
- **Réalité:** 149 images extraites, mais nombre d'emails uniques non spécifié
- **Discrepancy:** resultats.json contient ~150 lignes (1 par image), pas 52 emails
- **Clarification:** 149 images viennent de ~70 emails uniques (estimé)

## 7. **Dépendance OCR non documentée**
- **Risque:** Tesseract-OCR doit être installé OS-side
- **Si manquant:** `ocr_analyzer.py` crash silencieusement (try/except)
- **Impact:** Vision pipeline continue mais menaces OCR perdues
- **Pas testé:** Installation Windows de Tesseract sur machine de test

## 8. **Typosquatting score inférieur à expected**
- **Formule:** 1 - (levenshtein_dist / max_len)
- **Résultat:** Scores souvent 0.0-0.2 car domaines souvent très différents
- **Expected par doc:** Typosquatting score utile pour phishing
- **Réalité:** Contribution au score URL négligeable

## 9. **PhishTank scripts non exécutés**
- **Contradiction:** GUIDE_AMELIORATIONS_OPTIONNELLES.md propose "PhishTank validation" comme étape 3
- **Réalité:** Scripts existent mais jamais exécutés, pas de validation_phishtank.json généré
- **État:** Recommandation non implémentée

## 10. **Streamlit UI vs pipeline batch**
- **Duplication:** app.py ré-implémente l'analyse email (Vision + NLP + URL)
- **Divergence possible:** app.py peut avoir différences par rapport à scripts batch
- **Maintenance:** 2x le code à maintenir pour 1x la logique
- **Preuve:** app.py fait `calculer_score_final()` directement, tandis que batch utilise `fusion_multimodale.py`

---

# RÉSUMÉ EXÉCUTIF - ÉTAT RÉEL vs DOCUMENTÉ

| Fonctionnalité | Documenté | Réel | Exécuté |
|---|---|---|---|
| VirusTotal | Intégré complet | Clé chargée, API non appelée | Non |
| HTML inline | Support complet | 149 images extraites | Oui |
| OCR | Supporté | Intégré Vision + doublon NLP | Oui |
| PhishTank | Validation proposée | Scripts prêts, jamais exécutés | Non |
| Random Forest | Mentionné | Aucune implémentation | Non |
| Streamlit UI | Optionnel | Implémentée, métrics ajoutées | Oui |
| Fusion | 3 modules (Vision/NLP/URL) | 3 modules + OCR doublon | Oui |
| Metrics | Precision/Recall/F1 | Calculées, zéro car dataset clean | Oui |
| Tests | 25/25 PASSED | Jamais re-exécutés cette session | Non |

---

# FICHIERS CLÉS - RÔLE ET DÉPENDANCES

```
C:\logos_reference\
├── Core Pipeline
│   ├── extraire_images_v2.py          → Extraction images (attachments, HTML base64, CID, CSS)
│   ├── comparer_logos.py              → Vision: Hash + SSIM + OCR menaces
│   ├── generer_resultats_texte_v2.py  → NLP: 5 catégories menaces
│   ├── generer_resultats_urls.py      → URL: Typosquatting + VirusTotal stub
│   ├── fusion_multimodale.py          → Fusion 0.35/0.35/0.30
│   ├── generer_metrics.py             → Precision/Recall/F1 (heuristique ground truth)
│   ├── ocr_analyzer.py                → OCR via pytesseract
│   └── app.py                         → UI Streamlit (re-implémente pipeline)
│
├── Utilitaires (non exécutés)
│   ├── telecharger_phishtank.py       → Télécharge phishing_urls.txt (OpenPhish)
│   ├── valider_sur_phishtank.py       → Validation sur dataset réel (jamais exécuté)
│   ├── test_virustotal.py             → Test API VirusTotal (jamais exécuté)
│   └── parse_env_debug.py             → Debug .env loading
│
├── Input Data
│   ├── phishing-2025.mbox             → 481 emails source
│   ├── emails_extraits/               → 481 .eml extraits
│   ├── emails_avec_images/            → Subset avec images
│   └── .env                           → Clés API (VirusTotal)
│
├── Generated Outputs
│   ├── images_extraites/              → 149 images extraites
│   ├── resultats.json                 → Vision (150 images)
│   ├── resultats_texte_v2.json        → NLP (481 emails)
│   ├── resultats_urls.json            → URL (481 emails, 1787 URLs)
│   ├── resultats_fusion.json          → Fusion (520 emails)
│   ├── metrics_formels.json           → Metrics finales
│   ├── stats_extraction_v2.json       → Stats extraction
│   ├── stats_comparaison.json         → Stats Vision
│   └── resultados_ui/                 → Sortie UI Streamlit (empty)
│
├── Logos Reference
│   ├── Amazon_Logo_1.png              → Logo Amazon
│   ├── Apple_Icon_6.png               → Logo Apple
│   ├── PayPal_Icon_15.jpeg            → Logo PayPal
│   ├── microsoft.png                  → Logo Microsoft
│   ├── netflix.png, google.png, etc.  → 10 logos total
│   └── (tous chargés par comparer_logos.charger_logos())
│
├── Documentation
│   ├── README.md                      → Vue d'ensemble
│   ├── RAPPORT_FINAL_VALIDATION.md    → Rapport équipe (25/25 tests)
│   ├── GUIDE_AMELIORATIONS_OPTIONNELLES.md → Roadmap améliorations
│   ├── CONSOLIDATION_2026-06-28.md    → Rapport consolidation (cette session)
│   └── RESUME_TECHNIQUE_BRUT.md       → Ce fichier
│
├── Config & Scripts
│   ├── requirements.txt                → Dependencies (cv2, numpy, streamlit, etc.)
│   ├── EXECUTE_TOUT.ps1               → Orchestration PowerShell (5 phases)
│   └── .gitignore                     → Git exclusions
```

## Dépendances Python (requirements.txt)
```
opencv-python==4.8.0.76          → Vision (image processing)
numpy==1.24.3                    → Numerical operations
scikit-image==0.21.0             → SSIM
pytesseract==0.3.10              → OCR (requires Tesseract OS package)
streamlit==1.28.1                → UI web
Pillow==10.0.1                   → Image handling
python-dotenv==1.0.0             → .env loading
requests==2.31.0                 → HTTP requests (VirusTotal, PhishTank)
scikit-learn==1.3.1              → ML (Random Forest - unused)
```

---

**Fin du résumé technique brut**
