import re
import email
import os
import json
from urllib.parse import urlparse
from fuzzywuzzy import fuzz # <-- Le nouveau cerveau du script

# Domaines officiels de référence
DOMAINES_OFFICIELS = {
    "apple":      ["apple.com", "icloud.com", "itunes.com"],
    "paypal":     ["paypal.com", "paypal.me"],
    "amazon":     ["amazon.com", "amazon.fr", "amazonaws.com"],
    "google":     ["google.com", "googleapis.com", "gstatic.com"],
    "facebook":   ["facebook.com", "fbcdn.net", "fb.com"],
    "microsoft":  ["microsoft.com", "microsoftonline.com", "outlook.com"],
    "netflix":    ["netflix.com", "nflximg.com"],
    "instagram":  ["instagram.com", "cdninstagram.com"],
    "credit_agricole": ["credit-agricole.fr", "ca-paris.fr"],
    "bnp":        ["bnpparibas.com", "mabanque.bnpparibas"],
    "laposte":    ["laposte.fr", "laposte.net"],
}

def detecter_typosquatting(domaine, marque):
    """Détecte si un domaine imite une marque avec analyse de similarité."""
    domaine = domaine.lower()
    marque = marque.lower()
    signaux = []

    # 1. ANALYSE DE SIMILARITÉ (Le fameux Fuzzy Matching)
    # On compare le nom de domaine principal avec la marque
    nom_principal = domaine.split('.')[0]
    ratio = fuzz.ratio(nom_principal, marque)
    
    # Si ça ressemble à 80% mais que ce n'est pas identique
    if 80 <= ratio < 100:
        signaux.append(f"Similarité textuelle suspecte : {ratio}% avec '{marque}'")

    # 2. SUBSTITUTION DE CARACTÈRES
    substitutions = {"o": "0", "l": "1", "i": "1", "e": "3", "a": "4", "s": "5"}
    marque_modifiee = marque
    for lettre, chiffre in substitutions.items():
        marque_modifiee = marque_modifiee.replace(lettre, chiffre)
    if marque_modifiee in domaine and marque not in domaine:
        signaux.append(f"Substitution détectée ('{marque}' imité par '{marque_modifiee}')")

    # 3. MOTS SUSPECTS & TLD
    mots_suspects = ["secure", "login", "verify", "account", "update", "bank", "alert"]
    if marque in domaine:
        for mot in mots_suspects:
            if mot in domaine:
                signaux.append(f"Mot suspect '{mot}' associé à '{marque}'")
                break

    tlds_suspects = [".xyz", ".ru", ".tk", ".ml", ".pw", ".top", ".link"]
    if any(domaine.endswith(tld) for tld in tlds_suspects):
        signaux.append("Utilisation d'une extension de domaine (TLD) suspecte")

    return signaux

def extraire_urls_images(contenu_html):
    """Extrait les URLs d'images depuis le HTML."""
    urls = []
    pattern_src = r'src=["\']([^"\']+)["\']'
    matches = re.findall(pattern_src, contenu_html, re.IGNORECASE)
    for url in matches:
        if url.startswith("http") and not url.startswith("data:"):
            urls.append(url)
    return list(set(urls))

def analyser_url_image(url):
    """Analyse une URL et retourne un score de risque."""
    try:
        parsed = urlparse(url)
        domaine = parsed.netloc.lower().replace("www.", "")
    except: return None

    score_max = 0.0
    alertes = []

    for marque, officiels in DOMAINES_OFFICIELS.items():
        # Vérifier si c'est officiel
        if any(domaine == d or domaine.endswith("." + d) for d in officiels):
            return {"url": url, "domaine": domaine, "score_url": 0.0, "alertes": [], "officiel": True}

        # Sinon, chercher le typosquatting
        signaux = detecter_typosquatting(domaine, marque)
        if signaux:
            # Calcul du score : chaque signal ajoute du danger
            score = min(len(signaux) * 0.35, 1.0)
            score_max = max(score_max, score)
            alertes.extend(signaux)

    return {
        "url": url,
        "domaine": domaine,
        "score_url": round(score_max, 2),
        "alertes": list(set(alertes)) # Éviter les doublons
    }

def analyser_email_urls(chemin_eml):
    """Analyse toutes les URLs d'un fichier .eml."""
    with open(chemin_eml, "rb") as f:
        msg = email.message_from_bytes(f.read())

    toutes_urls = []
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                contenu = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                toutes_urls.extend(extraire_urls_images(contenu))
            except: pass

    if not toutes_urls:
        return {"url_score": 0.0, "urls_analysees": 0, "alertes": []}

    resultats = []
    score_global = 0.0
    toutes_alertes = []

    for url in toutes_urls:
        res = analyser_url_image(url)
        if res:
            resultats.append(res)
            score_global = max(score_global, res["score_url"])
            toutes_alertes.extend(res["alertes"])

    return {
        "url_score": round(score_global, 2),
        "urls_analysees": len(resultats),
        "alertes": list(set(toutes_alertes)),
        "details": resultats
    }

if __name__ == "__main__":
    EMAILS_DIR = r"C:\logos_reference\emails_avec_images"
    JSON_OUT = r"C:\logos_reference\resultats_urls.json"
    
    resultats_globaux = []
    print("🚀 Démarrage de l'analyse intelligente des URLs...\n")

    for nom in sorted(os.listdir(EMAILS_DIR)):
        if nom.endswith(".eml"):
            r = analyser_email_urls(os.path.join(EMAILS_DIR, nom))
            if r["url_score"] > 0:
                print(f"🚨 {nom} | Danger : {int(r['url_score']*100)}% | {r['alertes'][0] if r['alertes'] else ''}")
            resultats_globaux.append({"email": nom, **r})

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(resultats_globaux, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analyse terminée. {len(resultats_globaux)} emails traités.")