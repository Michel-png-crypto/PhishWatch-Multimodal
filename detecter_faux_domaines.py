import re
import email
import os
import json
from urllib.parse import urlparse

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
    "credit_agricole": ["credit-agricole.fr", "ca-*.fr"],
    "bnp":        ["bnpparibas.com", "mabanque.bnpparibas"],
    "laposte":    ["laposte.fr", "laposte.net"],
}

# Techniques de typosquatting courantes
def detecter_typosquatting(domaine, marque):
    """Détecte si un domaine imite une marque."""
    domaine = domaine.lower()
    marque = marque.lower()

    signaux = []

    # 1. Substitution de caractères (paypa1.com, g00gle.com)
    substitutions = {"o": "0", "l": "1", "i": "1", "e": "3", "a": "4", "s": "5"}
    marque_modifiee = marque
    for lettre, chiffre in substitutions.items():
        marque_modifiee = marque_modifiee.replace(lettre, chiffre)
    if marque_modifiee in domaine and marque not in domaine:
        signaux.append(f"Substitution de caracteres : '{marque}' → '{marque_modifiee}'")

    # 2. Ajout de mots suspects autour de la marque (apple-secure.com, paypal-login.xyz)
    mots_suspects = ["secure", "login", "verify", "account", "update",
                     "support", "service", "help", "auth", "confirm",
                     "alert", "urgent", "suspended", "billing"]
    if marque in domaine:
        for mot in mots_suspects:
            if mot in domaine:
                signaux.append(f"Mot suspect detecte : '{mot}' associe a '{marque}'")
                break

    # 3. TLD suspect (.xyz, .ru, .tk, .ml, .ga, .cf)
    tlds_suspects = [".xyz", ".ru", ".tk", ".ml", ".ga", ".cf",
                     ".pw", ".top", ".click", ".link", ".gq"]
    for tld in tlds_suspects:
        if domaine.endswith(tld):
            signaux.append(f"TLD suspect : '{tld}'")
            break

    # 4. Marque dans un sous-domaine (apple.login-secure.com)
    parties = domaine.split(".")
    if len(parties) > 2 and marque in parties[0] and marque not in ".".join(parties[-2:]):
        signaux.append(f"Marque dans le sous-domaine uniquement : '{domaine}'")

    # 5. Domaine très long (souvent signe de phishing)
    domaine_principal = ".".join(domaine.split(".")[-2:])
    if len(domaine_principal) > 30:
        signaux.append(f"Domaine anormalement long : {len(domaine_principal)} caracteres")

    return signaux

def extraire_urls_images(contenu_html):
    """Extrait toutes les URLs d'images depuis le HTML."""
    urls = []
    # src="..." dans les balises img
    pattern_src = r'src=["\']([^"\']+)["\']'
    # url(...) dans les CSS inline
    pattern_url = r'url\(["\']?([^"\')\s]+)["\']?\)'
    
    for pattern in [pattern_src, pattern_url]:
        matches = re.findall(pattern, contenu_html, re.IGNORECASE)
        for url in matches:
            if url.startswith("http") and not url.startswith("data:"):
                urls.append(url)
    return list(set(urls))

def analyser_url_image(url):
    """Analyse une URL d'image et retourne un score de risque."""
    try:
        parsed = urlparse(url)
        domaine = parsed.netloc.lower().replace("www.", "")
    except:
        return None

    resultats_marques = {}
    score_max = 0.0
    alertes = []

    for marque, domaines_officiels in DOMAINES_OFFICIELS.items():
        # Vérifier si c'est un domaine officiel
        est_officiel = any(
            domaine == d or domaine.endswith("." + d)
            for d in domaines_officiels
            if "*" not in d
        )

        if est_officiel:
            resultats_marques[marque] = {"officiel": True, "score": 0.0, "signaux": []}
            continue

        # Chercher des signaux de typosquatting
        signaux = detecter_typosquatting(domaine, marque)
        if signaux:
            # Score basé sur le nombre de signaux
            score = min(len(signaux) * 0.3, 1.0)
            score_max = max(score_max, score)
            alertes.extend(signaux)
            resultats_marques[marque] = {
                "officiel": False,
                "score": round(score, 2),
                "signaux": signaux
            }

    return {
        "url": url,
        "domaine": domaine,
        "score_url": round(score_max, 2),
        "alertes": alertes,
        "details": resultats_marques
    }

def analyser_email_urls(chemin_eml):
    """Analyse toutes les URLs d'images d'un email."""
    with open(chemin_eml, "rb") as f:
        msg = email.message_from_bytes(f.read())

    toutes_urls = []

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                contenu = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                urls = extraire_urls_images(contenu)
                toutes_urls.extend(urls)
            except:
                pass

    if not toutes_urls:
        return {"url_score": 0.0, "urls_analysees": 0, "alertes": []}

    resultats = []
    score_global = 0.0

    for url in toutes_urls:
        r = analyser_url_image(url)
        if r:
            resultats.append(r)
            score_global = max(score_global, r["score_url"])
            if r["alertes"]:
                print(f"  🚨 URL suspecte : {r['domaine']}")
                for alerte in r["alertes"]:
                    print(f"     → {alerte}")

    return {
        "url_score": round(score_global, 2),
        "urls_analysees": len(resultats),
        "alertes": [a for r in resultats for a in r["alertes"]],
        "details": resultats
    }

# ── TEST SUR LE DATASET ───────────────────────────────────────────────────────
if __name__ == "__main__":
    EMAILS_DIR = r"C:\logos_reference\emails_avec_images"
    resultats_globaux = []
    emails_suspects = 0

    print("🔍 Analyse des URLs d'images dans les emails...\n")

    for nom in sorted(os.listdir(EMAILS_DIR)):
        if not nom.endswith(".eml"):
            continue

        chemin = os.path.join(EMAILS_DIR, nom)
        r = analyser_email_urls(chemin)

        if r["alertes"]:
            emails_suspects += 1
            print(f"🚨 {nom} — Score URL : {r['url_score']} — {len(r['alertes'])} alerte(s)")

        resultats_globaux.append({"email": nom, **r})

    print(f"\n🎯 {emails_suspects} emails avec URLs d'images suspectes")

    with open(r"C:\logos_reference\resultats_urls.json", "w") as f:
        json.dump(resultats_globaux, f, indent=2)
    print("📁 Resultats sauvegardes dans resultats_urls.json")