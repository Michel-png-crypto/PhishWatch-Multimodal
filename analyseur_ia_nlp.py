import os
import email
import json
import re

class PhishingNLP:
    def __init__(self):
        # Lexique basé sur les techniques de manipulation connues
        self.poids_risques = {
            "URGENCE": ["immédiatement", "urgence", "sous 24h", "action requise", "vite"],
            "MENACE": ["suspendu", "bloqué", "clôture", "suppression", "irrégularité"],
            "APPAT": ["remboursement", "gagné", "cadeau", "prime", "bonus", "facture"],
            "TECHNIQUE": ["sécurité", "vérification", "connexion", "identifiants"]
        }

    def analyser_texte(self, chemin_eml):
        with open(chemin_eml, 'rb') as f:
            msg = email.message_from_bytes(f.read())
            # On récupère le sujet et le corps
            sujet = str(msg.get("Subject", ""))
            corps = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        corps += str(part.get_payload(decode=True))
            else:
                corps = str(msg.get_payload(decode=True))
            
            texte_complet = (sujet + " " + corps).lower()
            
            # Calcul du score
            score = 0.0
            alertes = []
            for categorie, mots in self.poids_risques.items():
                for mot in mots:
                    if mot in texte_complet:
                        score += 0.15
                        alertes.append(f"{categorie} ({mot})")
            
            # Bonus de score pour la ponctuation agressive (!!!)
            if "!!!" in texte_complet:
                score += 0.2
            
            return round(min(score, 1.0), 2), list(set(alertes))

# --- Lancement de l'analyse ---
if __name__ == "__main__":
    SOURCE = r"C:\logos_reference\emails_extraits"
    resultats_nlp = []

    print("🧠 Analyse NLP du dataset en cours...")
    ia = PhishingNLP()

    for fichier in os.listdir(SOURCE):
        if fichier.endswith(".eml"):
            score, raisons = ia.analyser_texte(os.path.join(SOURCE, fichier))
            resultats_nlp.append({
                "fichier": fichier,
                "score_nlp": score,
                "menaces_detectees": raisons,
                "statut_nlp": "SUSPECT" if score > 0.4 else "SAIN"
            })

    with open("resultats_texte.json", "w", encoding='utf-8') as f:
        json.dump(resultats_nlp, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Analyse terminée. {len(resultats_nlp)} emails traités.")