import streamlit as st
import cv2
import numpy as np
import os
import json
import email
import base64
import re
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from datetime import datetime
import io
import shutil

# ── CONFIG ────────────────────────────────────────────────────────────────────
LOGOS_DIR    = "C:/logos_reference"
IMAGES_DIR   = "C:/logos_reference/images_extraites"
RESULTATS_JSON = "C:/logos_reference/resultats.json"
HISTORIQUE_JSON = "C:/logos_reference/historique.json"
SEUIL = 0.60

st.set_page_config(
    page_title="Phishing Detector — Vision IA",
    page_icon="🛡️",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #1e293b; border-radius: 12px;
    padding: 16px; border-left: 4px solid #3b82f6;
    margin-bottom: 10px;
}
.alert-box {
    background: #450a0a; border-radius: 8px;
    padding: 12px; margin: 4px 0;
    border-left: 4px solid #ef4444;
}
.safe-box {
    background: #052e16; border-radius: 8px;
    padding: 12px; margin: 4px 0;
    border-left: 4px solid #22c55e;
}
</style>
""", unsafe_allow_html=True)

# ── FONCTIONS ALGO ────────────────────────────────────────────────────────────
def hash_perceptuel(img_gray, taille=(16,16)):
    img = cv2.resize(img_gray, taille)
    return (img > img.mean()).flatten()

def score_hash(h1, h2):
    return float(np.sum(h1 == h2)) / len(h1)

def score_ssim(img1, img2, taille=(64,64)):
    i1 = cv2.resize(img1, taille)
    i2 = cv2.resize(img2, taille)
    score, _ = ssim(i1, i2, full=True)
    return float(max(0.0, score))

def score_combine(h, s):
    return round(0.6 * h + 0.4 * s, 3)

DOMAINES_OFFICIELS = {
    "amazon":   ["amazon.com","amazon.fr","amazonaws.com"],
    "apple":    ["apple.com","icloud.com","itunes.com"],
    "paypal":   ["paypal.com","paypal.me"],
    "google":   ["google.com","googleapis.com","gstatic.com"],
    "facebook": ["facebook.com","fbcdn.net","fb.com"],
    "microsoft":["microsoft.com","microsoftonline.com","outlook.com","live.com"],
    "netflix":  ["netflix.com","nflximg.com"],
    "instagram":["instagram.com","cdninstagram.com"],
    "credit_agricole":["credit-agricole.fr","ca-paris.fr"],
}

def verifier_domaine(domaine, nom_logo):
    marque = nom_logo.lower().replace(".png","").replace(".jpeg","").replace(".jpg","")
    for cle, domaines in DOMAINES_OFFICIELS.items():
        if cle in marque or marque.startswith(cle):
            return any(domaine == d or domaine.endswith("."+d) for d in domaines if "*" not in d)
    return False

def calculer_score_final(visual_score, domaine_officiel):
    if visual_score < 0.55:
        return visual_score
    if domaine_officiel:
        return round(visual_score * 0.5, 3)
    return round(min(visual_score * 1.2, 1.0), 3)

def extraire_expediteur(msg_bytes):
    try:
        msg = email.message_from_bytes(msg_bytes)
        expediteur = msg.get("From", "")
        match = re.search(r'@([\w.\-]+)', expediteur)
        return expediteur, match.group(1).lower() if match else ""
    except:
        return "", ""

@st.cache_resource
def charger_logos():
    logos = {}
    for nom in os.listdir(LOGOS_DIR):
        if not nom.lower().endswith((".png",".jpg",".jpeg")):
            continue
        if "email" in nom.lower():
            continue
        img = cv2.imread(os.path.join(LOGOS_DIR, nom), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            logos[nom] = img
    return logos

def analyser_image_pil(img_pil, logos):
    img_gray = np.array(img_pil.convert("L"))
    hash_img = hash_perceptuel(img_gray)
    meilleur_logo, meilleur_score = None, 0.0
    tous_scores = {}
    for nom_logo, logo_gray in logos.items():
        h = score_hash(hash_img, hash_perceptuel(logo_gray))
        s = score_ssim(img_gray, logo_gray)
        score = score_combine(h, s)
        tous_scores[nom_logo] = {"hash": round(h,3), "ssim": round(s,3), "combined": score}
        if score > meilleur_score:
            meilleur_score, meilleur_logo = score, nom_logo
    return meilleur_logo, meilleur_score, tous_scores

def extraire_images_eml(fichier_bytes):
    images = []
    msg = email.message_from_bytes(fichier_bytes)
    for i, part in enumerate(msg.walk()):
        if part.get_content_type().startswith("image/"):
            try:
                data = part.get_payload(decode=True)
                if data:
                    img = Image.open(io.BytesIO(data)).convert("RGB")
                    images.append((f"piece_jointe_{i}", img))
            except: pass
        if part.get_content_type() == "text/html":
            try:
                contenu = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                for j, (ext, b64) in enumerate(re.findall(r'data:image/(png|jpeg|jpg|gif);base64,([A-Za-z0-9+/=\s]+)', contenu)):
                    try:
                        data = base64.b64decode(b64.replace("\n","").replace("\r","").replace(" ",""))
                        img = Image.open(io.BytesIO(data)).convert("RGB")
                        images.append((f"html_image_{j}", img))
                    except: pass
            except: pass
    return images

# ── HISTORIQUE ────────────────────────────────────────────────────────────────
def charger_historique():
    if os.path.exists(HISTORIQUE_JSON):
        with open(HISTORIQUE_JSON, encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_historique(entree):
    historique = charger_historique()
    historique.insert(0, entree)
    historique = historique[:100]  # garder les 100 dernières
    with open(HISTORIQUE_JSON, "w", encoding="utf-8") as f:
        json.dump(historique, f, indent=2, ensure_ascii=False)

# ── CHARGEMENT DONNÉES ────────────────────────────────────────────────────────
logos = charger_logos()

with open(RESULTATS_JSON, encoding="utf-8") as f:
    resultats = json.load(f)

# Compatibilité ancien/nouveau format
for r in resultats:
    if "score_final" not in r:
        r["score_final"] = r.get("visual_score", 0)
    if "statut" not in r:
        r["statut"] = "ALERTE" if r["score_final"] >= SEUIL else "SAIN"

alertes = [r for r in resultats if r["statut"] == "ALERTE"]
sains   = [r for r in resultats if r["statut"] == "SAIN"]
marques = Counter(
    r["ressemble_a"].replace(".png","").replace(".jpeg","").replace("_"," ").title()
    for r in alertes
)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=80)
st.sidebar.title("🛡️ Phishing Detector")
st.sidebar.markdown("**Module Vision par Ordinateur**")
st.sidebar.markdown("---")
st.sidebar.markdown(f"📦 **{len(logos)}** logos chargés")
st.sidebar.markdown(f"📧 **{len(resultats)}** images analysées")
st.sidebar.markdown(f"🚨 **{len(alertes)}** alertes")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "📧 Analyser un email",
    "🖼️ Analyser une image",
    "➕ Ajouter un logo",
    "📜 Historique"
])

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard — Résultats du dataset")
    st.caption("Nazario Phishing Corpus 2025 — Hash perceptuel + SSIM + Vérification expéditeur")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Images analysées", len(resultats))
    c2.metric("🚨 Alertes", len(alertes), delta=f"{round(len(alertes)/len(resultats)*100)}%")
    c3.metric("✅ Saines", len(sains))
    c4.metric("Score max", f"{max(r['score_final'] for r in resultats)*100:.1f}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Marques les plus usurpées")
        if marques:
            fig = px.bar(
                x=list(marques.values()), y=list(marques.keys()),
                orientation="h", color=list(marques.values()),
                color_continuous_scale="Reds",
                labels={"x": "Alertes", "y": "Marque"}
            )
            fig.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                              font_color="white", showlegend=False,
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Distribution des scores finaux")
        niveaux = {
            "🔴 Critique (≥85%)":  len([r for r in resultats if r["score_final"] >= 0.85]),
            "🟠 Élevé (70-85%)":   len([r for r in resultats if 0.70 <= r["score_final"] < 0.85]),
            "🟡 Moyen (60-70%)":   len([r for r in resultats if 0.60 <= r["score_final"] < 0.70]),
            "🟢 Sain (<60%)":      len([r for r in resultats if r["score_final"] < 0.60]),
        }
        fig2 = px.pie(
            values=list(niveaux.values()), names=list(niveaux.keys()),
            color_discrete_sequence=["#ef4444","#f97316","#f59e0b","#22c55e"]
        )
        fig2.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Détail des analyses")
    col_f1, col_f2 = st.columns(2)
    filtre = col_f1.selectbox("Filtrer", ["Tout", "🚨 Alertes", "✅ Sains"])
    marque_filtre = col_f2.selectbox("Par marque", ["Toutes"] + sorted(set(
        r["ressemble_a"].replace(".png","").replace(".jpeg","").replace("_"," ").title()
        for r in resultats
    )))

    data = resultats
    if filtre == "🚨 Alertes":
        data = alertes
    elif filtre == "✅ Sains":
        data = sains

    if marque_filtre != "Toutes":
        data = [r for r in data if marque_filtre.lower().replace(" ","_") in r["ressemble_a"].lower()]

    for r in sorted(data, key=lambda x: x["score_final"], reverse=True):
        score = r["score_final"]
        marque = r["ressemble_a"].replace(".png","").replace(".jpeg","").replace("_"," ").title()
        exp = r.get("domaine_expediteur", "")
        off = r.get("domaine_officiel", False)
        tag = "✅ officiel" if off else "⚠️ suspect"

        if score >= SEUIL:
            st.markdown(f"""<div class="alert-box">
                🚨 <b>{r['image']}</b> — ressemble à <b>{marque}</b>
                — Score : <b>{score*100:.1f}%</b>
                — Expéditeur : {exp} ({tag})
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="safe-box">
                ✅ <b>{r['image']}</b> — {marque}
                — Score : {score*100:.1f}%
                — Expéditeur : {exp} ({tag})
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — ANALYSER UN EMAIL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📧 Analyser un email":
    st.title("📧 Analyser un email en temps réel")
    st.info("Upload un fichier .eml pour détecter les images suspectes.")

    fichier = st.file_uploader("Choisir un fichier .eml", type=["eml"])

    if fichier:
        fichier_bytes = fichier.read()
        expediteur, domaine_exp = extraire_expediteur(fichier_bytes)
        images = extraire_images_eml(fichier_bytes)

        st.markdown("---")
        col_info1, col_info2 = st.columns(2)
        col_info1.info(f"**Expéditeur :** {expediteur or 'Inconnu'}")
        col_info2.info(f"**Domaine :** {domaine_exp or 'Inconnu'}")

        if not images:
            st.warning("⚠️ Aucune image trouvée dans cet email.")
        else:
            st.success(f"✅ {len(images)} image(s) extraite(s)")
            score_global = 0.0
            details = []

            for nom, img in images:
                st.markdown(f"### 🖼️ `{nom}`")
                col1, col2 = st.columns([1, 2])

                with col1:
                    # Comparaison côte à côte
                    meilleur_logo, visual_score, tous_scores = analyser_image_pil(img, logos)
                    domaine_off = verifier_domaine(domaine_exp, meilleur_logo)
                    score_final = calculer_score_final(visual_score, domaine_off)
                    score_global = max(score_global, score_final)

                    st.image(img, caption="Image suspecte", use_container_width=True)

                with col2:
                    # Logo de référence côte à côte
                    chemin_logo = os.path.join(LOGOS_DIR, meilleur_logo)
                    logo_pil = Image.open(chemin_logo).convert("RGB")

                    marque = meilleur_logo.replace(".png","").replace(".jpeg","").replace("_"," ").title()

                    col_a, col_b = st.columns(2)
                    col_a.image(img, caption="📧 Image suspecte", use_container_width=True)
                    col_b.image(logo_pil, caption=f"✅ Logo officiel : {marque}", use_container_width=True)

                    if score_final >= SEUIL:
                        st.error(f"🚨 **ALERTE** — Ressemble à **{marque}** ({score_final*100:.1f}%)")
                    else:
                        st.success(f"✅ Sain — Proche de {marque} ({score_final*100:.1f}%)")

                    domaine_tag = "✅ Domaine officiel" if domaine_off else "⚠️ Domaine suspect"
                    st.caption(f"Expéditeur : **{domaine_exp}** — {domaine_tag}")

                    # Graphique scores
                    scores_tri = sorted(tous_scores.items(), key=lambda x: x[1]["combined"], reverse=True)[:5]
                    labels = [s[0].replace(".png","").replace(".jpeg","").title() for s in scores_tri]
                    values = [s[1]["combined"]*100 for s in scores_tri]

                    fig = px.bar(x=values, y=labels, orientation="h",
                                 color=values, color_continuous_scale="Reds",
                                 labels={"x": "Similarité (%)", "y": ""})
                    fig.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                      font_color="white", showlegend=False,
                                      coloraxis_showscale=False, height=200,
                                      margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                details.append({
                    "image": nom,
                    "ressemble_a": meilleur_logo,
                    "visual_score": visual_score,
                    "score_final": score_final,
                    "statut": "ALERTE" if score_final >= SEUIL else "SAIN"
                })

            # Score global + JSON
            st.markdown("---")
            st.subheader("🎯 Score visuel global")
            couleur = "🔴" if score_global >= 0.85 else "🟠" if score_global >= 0.70 else "🟢"
            st.metric(f"{couleur} Score final", f"{score_global*100:.1f}%")

            json_result = {
                "email": fichier.name,
                "expediteur": expediteur,
                "domaine": domaine_exp,
                "visual_score": round(score_global, 3),
                "statut": "ALERTE" if score_global >= SEUIL else "SAIN",
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            st.code(json.dumps(json_result, indent=2, ensure_ascii=False), language="json")
            st.caption("📤 Ce JSON est prêt à être envoyé à l'Étudiant 4")

            # Sauvegarde historique
            sauvegarder_historique({
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "fichier": fichier.name,
                "expediteur": expediteur,
                "domaine": domaine_exp,
                "score_final": round(score_global, 3),
                "statut": "ALERTE" if score_global >= SEUIL else "SAIN",
                "nb_images": len(images)
            })
            st.success("✅ Analyse sauvegardée dans l'historique !")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — ANALYSER UNE IMAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🖼️ Analyser une image":
    st.title("🖼️ Analyser une image directement")
    st.info("Upload une image pour vérifier si elle ressemble à un logo officiel.")

    fichier = st.file_uploader("Choisir une image", type=["png","jpg","jpeg"])

    if fichier:
        img = Image.open(fichier).convert("RGB")
        meilleur_logo, visual_score, tous_scores = analyser_image_pil(img, logos)
        marque = meilleur_logo.replace(".png","").replace(".jpeg","").replace("_"," ").title()
        score_final = calculer_score_final(visual_score, False)

        st.markdown("---")
        st.subheader("🔍 Comparaison côte à côte")
        col1, col2 = st.columns(2)

        with col1:
            st.image(img, caption="📤 Image uploadée", use_container_width=True)

        with col2:
            chemin_logo = os.path.join(LOGOS_DIR, meilleur_logo)
            logo_pil = Image.open(chemin_logo).convert("RGB")
            st.image(logo_pil, caption=f"✅ Logo officiel le plus proche : {marque}", use_container_width=True)

        st.markdown("---")
        if score_final >= SEUIL:
            st.error(f"🚨 **ALERTE** — Ressemble à **{marque}** — Score : **{score_final*100:.1f}%**")
        else:
            st.success(f"✅ Aucune usurpation détectée — Score : {score_final*100:.1f}%")

        # Scores détaillés
        scores_tri = sorted(tous_scores.items(), key=lambda x: x[1]["combined"], reverse=True)
        labels = [s[0].replace(".png","").replace(".jpeg","").replace("_"," ").title() for s in scores_tri]
        hashes = [s[1]["hash"]*100 for s in scores_tri]
        ssims  = [s[1]["ssim"]*100 for s in scores_tri]
        combis = [s[1]["combined"]*100 for s in scores_tri]

        fig = go.Figure(data=[
            go.Bar(name="Hash", x=labels, y=hashes, marker_color="#3b82f6"),
            go.Bar(name="SSIM", x=labels, y=ssims,  marker_color="#f97316"),
            go.Bar(name="Combiné", x=labels, y=combis, marker_color="#ef4444"),
        ])
        fig.update_layout(
            barmode="group", plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="white", legend=dict(bgcolor="#1e293b"),
            title="Scores détaillés par logo"
        )
        st.plotly_chart(fig, use_container_width=True)

        json_result = {
            "visual_score": round(score_final, 3),
            "ressemble_a": meilleur_logo,
            "statut": "ALERTE" if score_final >= SEUIL else "SAIN"
        }
        st.code(json.dumps(json_result, indent=2), language="json")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — AJOUTER UN LOGO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "➕ Ajouter un logo":
    st.title("➕ Ajouter un nouveau logo de référence")
    st.info("Upload un logo pour l'ajouter à la base de référence. Le module l'utilisera automatiquement.")

    col1, col2 = st.columns(2)
    nom_marque = col1.text_input("Nom de la marque (ex: twitter, linkedin...)")
    domaines   = col2.text_input("Domaines officiels séparés par virgule (ex: twitter.com,t.co)")

    fichier = st.file_uploader("Logo PNG ou JPEG (fond blanc recommandé)", type=["png","jpg","jpeg"])

    if fichier and nom_marque:
        img = Image.open(fichier).convert("RGB")

        col_prev1, col_prev2 = st.columns(2)
        with col_prev1:
            st.image(img, caption=f"Aperçu : {nom_marque}", use_container_width=True)
        with col_prev2:
            st.markdown(f"**Marque :** {nom_marque}")
            st.markdown(f"**Domaines :** {domaines or 'Non spécifiés'}")
            st.markdown(f"**Taille :** {img.size[0]}x{img.size[1]} px")

        if st.button(f"✅ Ajouter {nom_marque} à la base", type="primary"):
            nom_fichier = f"{nom_marque.lower().replace(' ','_')}.png"
            chemin = os.path.join(LOGOS_DIR, nom_fichier)
            img.save(chemin)

            # Mettre à jour les domaines officiels dans le fichier
            st.success(f"✅ Logo **{nom_marque}** ajouté ! ({nom_fichier})")
            st.info("♻️ Relance `python comparer_logos.py` puis redémarre Streamlit pour prendre en compte le nouveau logo.")
            st.balloons()

    # Logos existants
    st.markdown("---")
    st.subheader("📦 Logos actuellement en base")
    logos_existants = [
        f for f in os.listdir(LOGOS_DIR)
        if f.lower().endswith((".png",".jpg",".jpeg")) and "email" not in f.lower()
    ]
    cols = st.columns(4)
    for i, nom in enumerate(sorted(logos_existants)):
        chemin = os.path.join(LOGOS_DIR, nom)
        try:
            img = Image.open(chemin).convert("RGB")
            cols[i % 4].image(img, caption=nom.replace(".png","").replace(".jpeg",""), use_container_width=True)
        except:
            cols[i % 4].text(nom)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — HISTORIQUE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📜 Historique":
    st.title("📜 Historique des analyses")

    historique = charger_historique()

    if not historique:
        st.info("Aucune analyse effectuée pour l'instant. Analyse un email depuis la page 'Analyser un email' !")
    else:
        st.success(f"**{len(historique)}** analyse(s) enregistrée(s)")

        # Stats rapides
        alertes_hist = [h for h in historique if h["statut"] == "ALERTE"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Total analyses", len(historique))
        col2.metric("🚨 Alertes", len(alertes_hist))
        col3.metric("✅ Sains", len(historique) - len(alertes_hist))

        # Graphique évolution dans le temps
        if len(historique) > 1:
            st.subheader("📈 Évolution des scores")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[h["timestamp"] for h in reversed(historique)],
                y=[h["score_final"]*100 for h in reversed(historique)],
                mode="lines+markers",
                line=dict(color="#ef4444", width=2),
                marker=dict(size=8),
                name="Score final"
            ))
            fig.add_hline(y=60, line_dash="dash", line_color="#f97316",
                         annotation_text="Seuil alerte (60%)")
            fig.update_layout(
                plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                font_color="white", xaxis_title="Date",
                yaxis_title="Score (%)", yaxis_range=[0, 105]
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Détail des analyses")

        for entree in historique:
            statut = entree["statut"]
            score = entree["score_final"]
            if statut == "ALERTE":
                st.markdown(f"""<div class="alert-box">
                    🚨 <b>{entree['fichier']}</b> — {entree['timestamp']}<br>
                    Expéditeur : {entree.get('domaine','?')} —
                    Score : <b>{score*100:.1f}%</b> —
                    {entree.get('nb_images','?')} image(s)
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="safe-box">
                    ✅ <b>{entree['fichier']}</b> — {entree['timestamp']}<br>
                    Expéditeur : {entree.get('domaine','?')} —
                    Score : {score*100:.1f}% —
                    {entree.get('nb_images','?')} image(s)
                </div>""", unsafe_allow_html=True)

        if st.button("🗑️ Effacer l'historique", type="secondary"):
            os.remove(HISTORIQUE_JSON)
            st.rerun()