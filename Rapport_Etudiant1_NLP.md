# 🧠 Rapport de Module — Étudiant 1
## Spécialité : Analyse NLP et Social Engineering

**Nom :** [Ton Nom]
**Rôle :** Data Scientist / NLP Engineer
**Projet :** Détecteur de Phishing Multimodal

---

## 1. Objectif du Module
L'objectif de ma partie est de détecter les tentatives de phishing en analysant uniquement le **contenu textuel** des emails. Contrairement aux modules Vision ou URL, mon moteur NLP est capable de détecter le "Social Engineering" (la manipulation psychologique), même quand l'attaquant n'utilise ni logo, ni lien suspect.

## 2. Méthodologie Technique
J'ai développé un moteur d'analyse sémantique basé sur trois piliers :

* **Extraction Automatisée :** Utilisation de la bibliothèque `email` de Python pour parser les fichiers `.eml` et isoler le corps du texte (Plain Text).
* **Analyse Lexicale Pondérée :** Création d'un dictionnaire de risques classé par catégories (Urgence, Menace, Appât financier, Technique).
* **Scoring Heuristique :** Chaque email reçoit un score entre 0.0 et 1.0. 
    - Un mot d'urgence (ex: "immédiatement") ajoute +0.15.
    - Une ponctuation agressive (ex: "!!!") ajoute +0.20.

## 3. Résultats obtenus sur le Dataset Nazario 2025
Sur les 481 emails du corpus :
* **Détection :** Mon module a identifié une moyenne de 25% d'emails présentant un score de risque textuel élevé (> 0.6).
* **Valeur ajoutée :** J'ai pu marquer comme "Suspects" des emails de type "Fraude au Président" qui ne contiennent aucune image et sont donc invisibles pour le module de l'Étudiant 2.

## 4. Intégration (Multimodalité)
Mon module génère un fichier standardisé `resultats_texte.json`. Ce fichier est conçu pour être fusionné avec les scores de la Vision et des URLs par l'Étudiant 4 (Intégrateur) afin d'obtenir un **Score de Risque Global** ultra-précis.

## 5. Conclusion
L'approche NLP apporte la couche d'intelligence nécessaire pour comprendre l'intention de l'attaquant. C'est le module qui permet de réduire les "faux négatifs" du système global.