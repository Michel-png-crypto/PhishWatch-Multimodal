import os
import re
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
from PIL import Image

from extraire_images_v2 import extraire_images_email_v2
import comparer_logos
from comparer_logos import (
    charger_logos,
    analyser_image,
    verifier_domaine,
)
from generer_resultats_texte_v2 import extraire_texte_email, analyser_email_texte_v2
from generer_resultats_urls import extraire_urls_email, analyser_url
from fusion_multimodale import calculer_score_fusion, statut_fusion

ROOT_DIR = Path(__file__).resolve().parent
LOGOS_DIR = ROOT_DIR
OUTPUT_DIR = ROOT_DIR / "resultats_ui"


def init_app() -> None:
    st.set_page_config(
        page_title="PhishWatch - Détecteur de Phishing",
        page_icon="🛡️",
        layout="wide",
    )
    st.title("🛡️ PhishWatch - Protégez-vous du Phishing")
    st.markdown("""
    **Analysez vos emails pour déterminer s'ils sont sûrs ou suspects.**
    
    PhishWatch vérifie:
    - 📸 **Logos** - Les images correspondent-elles aux vrais logos des entreprises?
    - 📝 **Texte** - Le message contient-il des demandes suspectes?
    - 🔗 **Liens** - Les URLs pointent-elles vers des adresses douteuses?
    """)
    st.markdown("---")


def save_eml_file(uploaded_file, output_dir: Path) -> Path:
    target = output_dir / (uploaded_file.name or "email_input.eml")
    target.write_bytes(uploaded_file.getvalue())
    return target


def save_raw_email(raw_content: str, output_dir: Path) -> Path:
    target = output_dir / "email_paste.eml"
    target.write_text(raw_content, encoding="utf-8", errors="ignore")
    return target


def get_email_id(eml_path: Path) -> str:
    return eml_path.stem or "email_ui"


def load_logos() -> Dict[str, Any]:
    # Assure que le module cherche les logos dans le dossier racine
    os.environ["LOGOS_DIR"] = str(LOGOS_DIR)
    return charger_logos()


def analyze_text(eml_path: Path) -> Dict[str, Any]:
    texte = extraire_texte_email(str(eml_path))
    resultat = analyser_email_texte_v2(get_email_id(eml_path), texte)
    resultat["texte_extrait"] = texte
    return resultat


def analyze_urls(eml_path: Path) -> Dict[str, Any]:
    urls = extraire_urls_email(str(eml_path))
    analyses = [analyser_url(get_email_id(eml_path), url) for url in urls]
    return {
        "urls": urls,
        "analyses": analyses,
        "urls_extraites": urls,
        "urls_count": len(urls),
    }


def extract_sender_domain(eml_path: str) -> tuple[str, str]:
    try:
        import re
        from email import message_from_bytes

        with open(eml_path, "rb") as f:
            msg = message_from_bytes(f.read())
        expediteur = msg.get("From", "")
        match = re.search(r'@([\w.\-]+)', expediteur)
        if match:
            return expediteur, match.group(1).lower()
        return expediteur, ""
    except Exception:
        return "", ""


def analyze_images(eml_path: Path, output_dir: Path, logos: Dict[str, Any]) -> Dict[str, Any]:
    email_id = get_email_id(eml_path)
    images = extraire_images_email_v2(str(eml_path), email_id, str(output_dir))
    results = []
    expediteur, domaine_expediteur = extract_sender_domain(str(eml_path))

    for chemin_image in images:
        meilleur_logo, visual_score, details_scores = analyser_image(chemin_image, logos)
        domaine_officiel = False
        if visual_score is not None and visual_score >= 0.55:
            domaine_officiel = verifier_domaine(domaine_expediteur, meilleur_logo or "")
        try:
            final_score, menaces_ocr, score_textuel = comparer_logos.calculer_score_final(
                visual_score or 0.0,
                domaine_officiel,
                chemin_image,
            )
        except TypeError:
            final_score = comparer_logos.calculer_score_final(
                visual_score or 0.0,
                domaine_officiel,
            )
            menaces_ocr = []
            score_textuel = 0.0
        results.append(
            {
                "image": chemin_image,
                "meilleur_logo": meilleur_logo,
                "visual_score": round(visual_score or 0.0, 3),
                "score_final": round(final_score or 0.0, 3),
                "details_scores": details_scores,
                "domaine_expediteur": domaine_expediteur,
                "domaine_officiel": domaine_officiel,
                "menaces_ocr": menaces_ocr,
                "score_textuel": round(score_textuel or 0.0, 3),
            }
        )

    return {
        "images": images,
        "count": len(images),
        "results": results,
        "expediteur": expediteur,
        "domaine_expediteur": domaine_expediteur,
    }


def build_fusion(image_result: Dict[str, Any], text_result: Dict[str, Any], url_result: Dict[str, Any]) -> Dict[str, Any]:
    vision_score = None
    if image_result["results"]:
        vision_score = max(item["score_final"] for item in image_result["results"])
    nlp_score = text_result.get("score_nlp")
    url_score = None
    if url_result["analyses"]:
        url_score = max(item.get("score_url", 0.0) for item in url_result["analyses"])

    score = calculer_score_fusion(vision_score, nlp_score, url_score)
    statut = statut_fusion(score, {
        "statut_vision": "ALERTE" if vision_score and vision_score >= 0.6 else "SAIN",
        "statut_nlp": text_result.get("statut_nlp"),
    })

    return {
        "score_fusion": round(score, 3),
        "statut_fusion": statut,
        "vision_score": vision_score,
        "nlp_score": nlp_score,
        "url_score": url_score,
    }


def render_image_results(image_result: Dict[str, Any]) -> None:
    if image_result["count"] == 0:
        st.info("✅ Aucune image trouvée dans cet email - pas de risque de faux logo")
        return

    st.subheader("📸 Analyse des Logos")
    st.markdown("*PhishWatch examine chaque image pour voir si elle ressemble à un faux logo phishing*")
    
    for i, result in enumerate(image_result["results"], 1):
        with st.expander(f"Image {i}: {Path(result['image']).name}", expanded=(i==1)):
            col1, col2 = st.columns([1, 2])
            with col1:
                try:
                    st.image(Image.open(result["image"]), use_column_width=True)
                except Exception:
                    st.warning("Impossible d'afficher l'image")
            
            with col2:
                score = result['score_final']
                
                # Affichage du statut en clair
                if score >= 0.60:
                    st.error(f"⚠️ **DANGER** - Score: {score:.0%}")
                    st.markdown(f"Cette image ressemble **probablement à un faux logo** (ressemble à: *{result['meilleur_logo']}*)")
                else:
                    st.success(f"✅ **SÛRE** - Score: {score:.0%}")
                    st.markdown("Cette image ne semble pas être un faux logo")
                
                # Explications
                st.markdown("**Détails de l'analyse:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Ressemblance visuelle", f"{result['visual_score']:.0%}")
                with col_b:
                    st.metric("Domaine", "Officiel ✅" if result['domaine_officiel'] else "Douteux ⚠️")
                
                if result["menaces_ocr"]:
                    st.warning(f"🔍 Texte suspect détecté: {', '.join(result['menaces_ocr'][:2])}")
    
    # Résumé images
    alertes_images = sum(1 for r in image_result["results"] if r['score_final'] >= 0.60)
    st.markdown(f"**Résumé:** {alertes_images}/{image_result['count']} image(s) suspecte(s)")


def render_text_results(text_result: Dict[str, Any]) -> None:
    st.subheader("📝 Analyse du Texte")
    st.markdown("*Cherche des mots ou phrases suspectes typiques des arnaqueurs*")
    
    score = text_result.get('score_nlp', 0.0)
    
    # Statut principal
    if score >= 0.60:
        st.error(f"⚠️ **TEXTE SUSPECT** - Score de risque: {score:.0%}")
        st.markdown("Le message contient **plusieurs signaux d'alerte** typiques du phishing.")
    else:
        st.success(f"✅ **TEXTE NORMAL** - Score de risque: {score:.0%}")
        st.markdown("Le message semble **légitime** et ne contient pas de mots d'alerte typiques.")
    
    # Mots suspects trouvés
    if text_result.get("mots_detectes"):
        st.info(f"🚩 Mots suspects trouvés: **{', '.join(text_result['mots_detectes'][:5])}**")
        st.markdown("*Exemples: vérifier, confirmer, urgent, cliquez, mot de passe, etc.*")
    
    with st.expander("📖 Voir le texte complet du message"):
        texte = text_result.get("texte_extrait", "")
        if texte:
            st.text_area("Texte extrait:", value=texte, height=200, disabled=True)
        else:
            st.info("Pas de texte à afficher")


def render_url_results(url_result: Dict[str, Any]) -> None:
    st.subheader("🔗 Analyse des Liens")
    st.markdown("*Vérifie si les adresses web ressemblent à des faux sites*")
    
    st.write(f"**Nombre de liens trouvés:** {url_result['urls_count']}")
    
    if not url_result["analyses"] or url_result['urls_count'] == 0:
        st.success("✅ Aucun lien trouvé dans cet email")
        return

    score = url_result.get("score_url", 0.0) if url_result["analyses"] else 0.0
    
    if score >= 0.60:
        st.error(f"⚠️ **LIENS SUSPECTS DÉTECTÉS** - Score de risque: {score:.0%}")
    else:
        st.success(f"✅ **LIENS NORMAUX** - Score de risque: {score:.0%}")
    
    # Afficher quelques URLs
    with st.expander(f"📍 Voir les {url_result['urls_count']} lien(s) trouvé(s)", expanded=False):
        for i, url_data in enumerate(url_result["analyses"][:5], 1):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Lien {i}:** `{url_data['url'][:60]}...`" if len(url_data['url']) > 60 else f"**Lien {i}:** `{url_data['url']}`")
                st.caption(f"Domaine: {url_data.get('domain', 'inconnu')}")
            with col2:
                risk = url_data.get('score_url', 0)
                if risk >= 0.60:
                    st.error(f"⚠️ Risque {risk:.0%}")
                else:
                    st.success(f"✅ {risk:.0%}")
        
        if url_result['urls_count'] > 5:
            st.caption(f"... et {url_result['urls_count'] - 5} autre(s) lien(s)")


def main() -> None:
    init_app()

    st.sidebar.header("📤 Téléversez votre Email")
    st.sidebar.markdown("""
    **Deux options:**
    1. Cliquez sur "Parcourir" pour sélectionner un fichier `.eml`
    2. Collez le texte brut d'un email
    """)
    
    uploaded_file = st.sidebar.file_uploader("📎 Fichier EML", type=["eml"])
    raw_email = st.sidebar.text_area("📋 Ou collez l'email brut ici", height=150, 
                                      placeholder="Exemple: From: sender@example.com\nSubject: Vérifiez votre compte...")
    analyze_button = st.sidebar.button("🔍 Analyser l'email", use_container_width=True)

    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = OUTPUT_DIR
        st.session_state.temp_dir.mkdir(parents=True, exist_ok=True)

    logos = load_logos()
    st.sidebar.success(f"✅ {len(logos)} logos de référence chargés")
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Comment ça marche?**
    1. Téléversez un email
    2. PhishWatch l'analyse en 3 secondes
    3. Vous voyez le verdict: SÛRE, À VÉRIFIER, ou DANGER
    4. Explications détaillées pour chaque vérification
    """)

    if analyze_button:
        if not uploaded_file and not raw_email:
            st.sidebar.warning("Veuillez fournir un fichier EML ou coller un email.")
            return

        eml_path = None
        if uploaded_file:
            eml_path = save_eml_file(uploaded_file, st.session_state.temp_dir)
        else:
            eml_path = save_raw_email(raw_email, st.session_state.temp_dir)

        if not eml_path or not eml_path.exists():
            st.error("Impossible de sauvegarder l'email pour l'analyse.")
            return

        with st.spinner("Extraction et analyse en cours..."):
            output_images_dir = st.session_state.temp_dir / "images"
            output_images_dir.mkdir(parents=True, exist_ok=True)

            image_result = analyze_images(eml_path, output_images_dir, logos)
            text_result = analyze_text(eml_path)
            url_result = analyze_urls(eml_path)
            fusion = build_fusion(image_result, text_result, url_result)

            output_data = {
                "email": eml_path.name,
                "fusion": fusion,
                "vision": image_result,
                "nlp": text_result,
                "url": url_result,
            }
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = OUTPUT_DIR / f"resultats_{get_email_id(eml_path)}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            st.session_state.last_output_file = str(output_file)

        st.success("✅ Analyse terminée")
        st.markdown("---")

        # === RÉSUMÉ GLOBAL - Version non-technicienne ===
        st.subheader("🎯 Verdict Final")
        
        fusion_score = fusion['score_fusion']
        fusion_status = fusion['statut_fusion']
        
        # Affichage principal avec couleur
        col_verdict_left, col_verdict_right = st.columns([2, 1])
        with col_verdict_left:
            if fusion_status == "PHISHING":
                st.error(f"🚨 **DANGER - C'EST PROBABLEMENT DU PHISHING**")
                st.markdown(f"""
                **Cet email est suspect.** Il combine plusieurs signaux d'alerte:
                - Logos qui ressemblent à des faux
                - Texte avec demandes suspectes
                - Liens vers des sites douteux
                
                **Action recommandée:** Ne cliquez pas sur les liens, ne rentrez pas vos identifiants. Supprimez l'email.
                """)
            elif fusion_status == "SUSPECT":
                st.warning(f"⚠️ **À VÉRIFIER - RISQUE MODÉRÉ**")
                st.markdown("""
                **Cet email a plusieurs signaux d'alerte** mais n'est pas certain. 
                Soyez prudent avant de cliquer ou d'ouvrir des pièces jointes.
                """)
            else:  # SAIN
                st.success(f"✅ **SÛRE - PAS DE RISQUE DÉTECTÉ**")
                st.markdown("Cet email semble légitime. Aucun signal d'alerte majeur détecté.")
        
        with col_verdict_right:
            st.metric("Score de Risque", f"{fusion_score:.0%}")
            if fusion_score < 0.5:
                st.write("🟢 Très faible risque")
            elif fusion_score < 0.6:
                st.write("🟡 Risque modéré")
            else:
                st.write("🔴 Risque élevé")
        
        # Explication du score
        st.markdown("---")
        st.subheader("📊 Comment PhishWatch fonctionne")
        st.markdown("""
        PhishWatch combine 3 vérifications:
        
        | Vérification | Rôle | Score de cet email |
        |---|---|---|
        | 📸 **Logos** | Détecte les faux logos d'entreprises | {:.0%} |
        | 📝 **Texte** | Cherche les mots suspects typiques du phishing | {:.0%} |
        | 🔗 **Liens** | Vérifie si les adresses web sont douteuses | {:.0%} |
        
        **Score final = moyenne des 3 vérifications**
        """.format(
            fusion['vision_score'] or 0,
            fusion['nlp_score'] or 0,
            fusion['url_score'] or 0
        ))
        
        # Load and display formal metrics if available
        metrics_file = Path(__file__).resolve().parent / "metrics_formels.json"
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics_data = json.load(f)
            st.markdown("---")
            st.subheader("📈 Fiabilité de PhishWatch (sur tous les emails testés)")
            st.markdown("*Ces chiffres montrent comment PhishWatch fonctionne sur l'ensemble du dataset*")
            
            cols_metrics = st.columns(4)
            scores = metrics_data.get('scores', {})
            
            cols_metrics[0].metric(
                "Précision", 
                f"{scores.get('precision', 0):.1%}",
                help="Sur 100 emails marqués PHISHING, combien sont vrais phishing"
            )
            cols_metrics[1].metric(
                "Couverture", 
                f"{scores.get('accuracy', 0):.1%}",
                help="Exactitude globale de la détection"
            )
            cols_metrics[2].metric(
                "Faux Positifs", 
                f"{scores.get('false_positive_rate', 0):.1%}",
                help="Risque qu'un email sûr soit marqué comme phishing"
            )
            cols_metrics[3].metric(
                "Fiabilité", 
                "⭐⭐⭐" if scores.get('accuracy', 0) > 0.90 else "⭐⭐",
                help="Note globale de fiabilité"
            )
            
            # KPI CDC
            kpi = metrics_data.get('kpi_cdc', {})
            st.markdown("**Objectifs atteints:**")
            col_kpi1, col_kpi2 = st.columns(2)
            with col_kpi1:
                if kpi.get('met_false_positives', False):
                    st.success(f"✅ Faux positifs < 10% (**{kpi.get('actual_false_positives_percent', 0):.1f}%**)")
                else:
                    st.warning(f"⚠️ Faux positifs cible < 10% (réel: {kpi.get('actual_false_positives_percent', 0):.1f}%)")
            
            with col_kpi2:
                if kpi.get('met_precision', False):
                    st.success(f"✅ Précision > 90% (**{kpi.get('actual_precision', 0):.1%}**)")
                else:
                    st.info(f"🔄 Précision cible > 90% (en amélioration: {kpi.get('actual_precision', 0):.1%})")

        st.markdown("<small>Note: le score global est une moyenne pondérée des modules Vision, NLP et URL.</small>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            render_image_results(image_result)
        with col2:
            render_text_results(text_result)
            render_url_results(url_result)

        with st.expander("Voir le résultat complet JSON", expanded=False):
            st.json({
                "email": eml_path.name,
                "fusion": fusion,
                "vision": image_result,
                "nlp": text_result,
                "url": url_result,
            })

        if hasattr(st.session_state, 'last_output_file') and st.session_state.last_output_file:
            st.success(f"Résultats enregistrés dans : {st.session_state.last_output_file}")

if __name__ == "__main__":
    main()
