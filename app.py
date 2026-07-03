import os
import re
import json
import tempfile
from pathlib import Path
from datetime import date
from typing import List, Dict, Any
from email import message_from_file

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
GROUND_TRUTH_FILE = ROOT_DIR / "ground_truth.json"
RESULTATS_FUSION_FILE = ROOT_DIR / "resultats_fusion.json"


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
    st.info(
        "Auto-évaluation incluse : le système peut afficher les métriques internes et la validation PhishTank si les fichiers `metrics_formels.json` et `validation_phishtank.json` existent."
    )
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
    max_score = max((item.get("score_url", 0.0) for item in analyses), default=0.0)
    statut_url = (
        "MALVEILLANT" if max_score >= 0.6
        else "SUSPECT" if max_score >= 0.4
        else "SAIN"
    )
    alertes = [item.get("url") for item in analyses if item.get("score_url", 0.0) >= 0.4]
    return {
        "urls": urls,
        "analyses": analyses,
        "urls_extraites": urls,
        "urls_count": len(urls),
        "score_url": round(max_score, 3),
        "statut_url": statut_url,
        "alertes": alertes,
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


def extract_email_metadata(eml_path: str) -> Dict[str, Any]:
    try:
        with open(eml_path, 'r', encoding='utf-8', errors='ignore') as f:
            msg = message_from_file(f)
        return {
            'from': msg.get('From', 'inconnu'),
            'subject': msg.get('Subject', 'Sans sujet'),
            'date': msg.get('Date', 'Date inconnue'),
        }
    except Exception:
        return {'from': 'inconnu', 'subject': 'Sans sujet', 'date': 'Date inconnue'}


def load_ground_truth() -> List[Dict[str, Any]]:
    if not GROUND_TRUTH_FILE.exists():
        GROUND_TRUTH_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_ground_truth(entries: List[Dict[str, Any]]) -> None:
    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def get_ground_truth_by_email(email_id: str, entries: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for entry in entries:
        if entry.get("email_id") == email_id:
            return entry
    return None


def update_ground_truth(email_id: str, label: str, note: str, fusion: Dict[str, Any]) -> None:
    entries = load_ground_truth()
    existing = get_ground_truth_by_email(email_id, entries)
    record = {
        "email_id": email_id,
        "label_humain": label,
        "note": note,
        "valide_par": "Florient",
        "date_validation": date.today().isoformat(),
        "score_fusion_au_moment_validation": fusion.get("score_fusion", 0.0),
        "statut_fusion_au_moment_validation": fusion.get("statut_fusion", "SAIN"),
    }
    if existing:
        entries = [record if entry.get("email_id") == email_id else entry for entry in entries]
    else:
        entries.append(record)
    save_ground_truth(entries)


def count_ground_truth() -> tuple[int, int, int, int]:
    entries = load_ground_truth()
    total = len(entries)
    phishing = sum(1 for entry in entries if entry.get("label_humain") == "PHISHING")
    legitimate = sum(1 for entry in entries if entry.get("label_humain") == "LEGITIME")
    uncertain = sum(1 for entry in entries if entry.get("label_humain") == "INCERTAIN")
    return total, phishing, legitimate, uncertain


def load_resultats_fusion() -> List[Dict[str, Any]]:
    if not RESULTATS_FUSION_FILE.exists():
        return []
    try:
        with open(RESULTATS_FUSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("resultats", []) if isinstance(data, dict) else []
    except Exception:
        return []


def get_next_batch_email(index: int, sorted_emails: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if 0 <= index < len(sorted_emails):
        return sorted_emails[index]
    return None


def render_validation_section(email_id: str, fusion: Dict[str, Any]) -> None:
    st.markdown("---")
    st.subheader("🧪 Validation manuelle")
    st.write(f"**Statut système actuel :** {fusion.get('statut_fusion', 'SAIN')} — **Score fusion :** {fusion.get('score_fusion', 0.0):.0%}")

    entries = load_ground_truth()
    existing = get_ground_truth_by_email(email_id, entries)
    existing_note = ""
    if existing:
        existing_note = existing.get("note", "")
        st.info(f"Label actuel dans ground_truth.json : {existing.get('label_humain')} ({existing.get('date_validation')})")
        if existing_note:
            st.write(f"**Note actuelle:** {existing_note}")

    note = st.text_area("Note / justification (optionnel)", value=existing_note, key=f"note_{email_id}")
    col1, col2, col3 = st.columns(3)
    if col1.button("✅ Confirmer PHISHING", key=f"phishing_{email_id}"):
        update_ground_truth(email_id, "PHISHING", note, fusion)
        st.success("Validation enregistrée : PHISHING")
    if col2.button("❌ Confirmer LEGITIME", key=f"legitime_{email_id}"):
        update_ground_truth(email_id, "LEGITIME", note, fusion)
        st.success("Validation enregistrée : LEGITIME")
    if col3.button("🤷 Incertain / Skip", key=f"incertain_{email_id}"):
        update_ground_truth(email_id, "INCERTAIN", note, fusion)
        st.success("Validation enregistrée : INCERTAIN")


def render_batch_validation(sorted_emails: List[Dict[str, Any]]) -> None:
    st.markdown("---")
    st.subheader("📋 Validation en lot")
    total_validated, phishing_count, legitimate_count, uncertain_count = count_ground_truth()
    st.write(f"**{total_validated} emails validés** — {phishing_count} PHISHING, {legitimate_count} LEGITIME, {uncertain_count} INCERTAIN")
    st.write(f"Affichage trié par score décroissant — {len(sorted_emails)} emails disponibles")

    if "batch_index" not in st.session_state:
        st.session_state.batch_index = 0

    index = st.session_state.batch_index
    current = get_next_batch_email(index, sorted_emails)
    if not current:
        st.warning("Aucun email à valider. Vérifiez que resultats_fusion.json existe et contient des résultats.")
        return

    email_id = current.get("email_id") or current.get("fichier")
    fusion = {
        "score_fusion": current.get("score_fusion", 0.0),
        "statut_fusion": current.get("statut_fusion", "SAIN"),
    }
    entries = load_ground_truth()
    existing = get_ground_truth_by_email(email_id, entries)

    eml_path = ROOT_DIR / "emails_extraits" / f"{email_id}.eml"
    metadata = extract_email_metadata(str(eml_path)) if eml_path.exists() else {'from': 'inconnu', 'subject': 'Sans sujet', 'date': 'Date inconnue'}

    st.write(f"### Email {index + 1} / {len(sorted_emails)} — {email_id}")
    st.write(f"Score fusion: {fusion['score_fusion']:.0%} — Statut: {fusion['statut_fusion']}")
    st.markdown(
        f"**Expéditeur:** {metadata['from']}  \n"
        f"**Sujet:** {metadata['subject']}  \n"
        f"**Date:** {metadata['date']}"
    )
    if existing:
        st.success(f"Email déjà validé : {existing.get('label_humain')} (le {existing.get('date_validation')})")
        if existing.get("note"):
            st.write(f"**Note précédente:** {existing.get('note')}")

    # Résumé du mail / éléments à valider
    detail_nlp = current.get("detail_nlp", {}) or {}
    detail_url = current.get("detail_url", {}) or {}
    nlp_menaces = detail_nlp.get("menaces", [])
    url_alertes = detail_url.get("alertes", [])
    urls_analysees = detail_url.get("urls_analysees", 0)
    statut_vision = current.get("statut_vision") or "ABSENT"
    statut_nlp = current.get("statut_nlp") or "ABSENT"
    statut_url = current.get("statut_url") or "ABSENT"

    st.markdown("#### Résumé rapide du mail")
    col_summary, col_metrics = st.columns([3, 1])
    with col_summary:
        st.write(f"**Vision**: {statut_vision}")
        st.write(f"**NLP**: {statut_nlp}")
        st.write(f"**URL**: {statut_url}")
        if nlp_menaces:
            st.write("**Mots / expressions suspectes** : " + ", ".join(nlp_menaces))
        else:
            st.write("**Aucune menace textuelle détectée.**")
        if url_alertes:
            st.write("**Liens suspects** :")
            for url in url_alertes:
                st.write(f"- {url}")
        else:
            st.write("**Aucun lien suspect détecté.**")

        # Ajouter aperçu image si disponible et si image extraite
        detail_vision = current.get("detail_vision", {}) or {}
        images_alertes = detail_vision.get("images_alertes", [])
        if images_alertes:
            st.markdown("**Images suspectes extraites** :")
            for image_name in images_alertes[:2]:
                image_path = ROOT_DIR / "images_extraites" / image_name
                if image_path.exists():
                    try:
                        st.image(str(image_path), caption=image_name, use_column_width=True)
                    except Exception:
                        st.write(f"- {image_name} (image non chargée)")
                else:
                    st.write(f"- {image_name} (fichier manquant)")
        elif detail_vision.get("nb_images"):
            st.write(f"**Images extraites** : {detail_vision.get('nb_images')} (aucune alerte visuelle spécifique)")
        else:
            st.write("**Aucune image extraite / analyse visuelle absente.**")
    with col_metrics:
        st.metric("URLs analysées", urls_analysees)
        st.metric("Menaces NLP", len(nlp_menaces))
        st.metric("Liens suspects", len(url_alertes))

    note_value = existing.get("note", "") if existing else ""
    note = st.text_area("Note / justification (optionnel)", value=note_value, key=f"batch_note_{email_id}")
    col_buttons, col_nav = st.columns([3, 1])
    with col_buttons:
        col1, col2, col3 = st.columns(3)
        if col1.button("✅ Confirmer PHISHING", key=f"batch_phishing_{email_id}"):
            update_ground_truth(email_id, "PHISHING", note, fusion)
            st.success("Validation enregistrée : PHISHING")
        if col2.button("❌ Confirmer LEGITIME", key=f"batch_legitime_{email_id}"):
            update_ground_truth(email_id, "LEGITIME", note, fusion)
            st.success("Validation enregistrée : LEGITIME")
        if col3.button("🤷 Incertain / Skip", key=f"batch_incertain_{email_id}"):
            update_ground_truth(email_id, "INCERTAIN", note, fusion)
            st.success("Validation enregistrée : INCERTAIN")
    with col_nav:
        if st.button("⬅️ Précédent", key=f"batch_prev_{email_id}"):
            st.session_state.batch_index = max(index - 1, 0)
            st.rerun()
        if st.button("➡️ Email suivant", key=f"batch_next_{email_id}"):
            st.session_state.batch_index = min(index + 1, len(sorted_emails) - 1)
            st.rerun()


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

    url_status = url_result.get("statut_url", "SAIN")
    score = calculer_score_fusion(vision_score, nlp_score, url_score)
    statut = statut_fusion(score, {
        "statut_vision": "ALERTE" if vision_score and vision_score >= 0.6 else "SAIN",
        "statut_nlp": text_result.get("statut_nlp"),
        "statut_url": url_status,
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
    st.write(f"**Statut URL global:** {url_result.get('statut_url', 'SAIN')}")

    if not url_result["analyses"] or url_result['urls_count'] == 0:
        st.success("✅ Aucun lien trouvé dans cet email")
        return

    score = url_result.get("score_url", 0.0)
    suspicious_links = sum(1 for item in url_result.get("analyses", []) if item.get("score_url", 0.0) >= 0.4)
    if suspicious_links:
        st.warning(f"🔎 {suspicious_links} lien(s) suspect(s) sur {url_result['urls_count']}")

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

    st.sidebar.header("📤 Mode de travail")
    mode = st.sidebar.radio(
        "Choisir un mode",
        ["Analyse unique", "Validation en lot"],
        index=0,
    )
    st.sidebar.markdown("""
    **Deux options:**
    1. Analyse unique : téléversez un email et validez-le.
    2. Validation en lot : parcourez les emails suspects depuis resultats_fusion.json.
    """)

    total_validated, phishing_count, legitimate_count, uncertain_count = count_ground_truth()
    st.sidebar.markdown("---")
    st.sidebar.write(f"**Validation manuelle :** {total_validated} labels enregistrés")
    resultats = load_resultats_fusion()
    st.sidebar.write(f"**Emails disponibles en lot :** {len(resultats)}")
    st.sidebar.write(f"PHISHING: {phishing_count}, LEGITIME: {legitimate_count}, INCERTAIN: {uncertain_count}")

    if mode == "Analyse unique":
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
    else:
        uploaded_file = None
        raw_email = ""
        analyze_button = False

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
            if fusion_status == "PHISHING":
                st.write("🔴 Risque élevé")
                if fusion_score < 0.6:
                    st.caption(
                        "⚠️ Attention : l’un des modules a identifié un signal fort (par exemple un lien malveillant), ce qui force l’alerte même si le score moyen reste bas."
                    )
            elif fusion_status == "SUSPECT":
                st.write("🟡 Risque modéré")
            elif fusion_score < 0.5:
                st.write("🟢 Très faible risque")
            elif fusion_score < 0.6:
                st.write("🟡 Risque modéré")
            else:
                st.write("🔴 Risque élevé")
        
        # Explication du score
        st.markdown("---")
        render_validation_section(get_email_id(eml_path), fusion)
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
            if scores.get('precision', 0) == 0 and scores.get('false_positive_rate', 0) > 0:
                st.info(
                    "🔎 Précision 0 % : vérifiez que `metrics_formels.json` est à jour "
                    "(`python fusion_multimodale.py` puis `python generer_metrics.py`). "
                    "Voir `SCORING_GUIDE.md` pour le détail."
                )
            elif metrics_data.get('interpretation', {}).get('note'):
                st.caption(metrics_data['interpretation']['note'])
        st.markdown("<small>Note: le score global est une moyenne pondérée des modules Vision, NLP et URL.</small>", unsafe_allow_html=True)

        validation_file = Path(__file__).resolve().parent / "validation_phishtank.json"
        if validation_file.exists():
            with open(validation_file, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
            validation_metrics = validation_data.get('metrics', {})
            validation_meta = validation_data.get('metadata', {})

            st.markdown("---")
            st.subheader("🧪 Validation PhishTank / OpenPhish")
            st.markdown("*Vérification des liens suspects sur un dataset phishing réel.*")

            cols_val = st.columns(4)
            cols_val[0].metric(
                "Précision PhishTank",
                f"{validation_metrics.get('precision', 0):.1%}",
                help="Sur 100 alertes URL, combien sont confirmées comme phishing."
            )
            cols_val[1].metric(
                "Recall PhishTank",
                f"{validation_metrics.get('recall', 0):.1%}",
                help="Sur 100 URLs phishing réelles, combien ont été détectées."
            )
            cols_val[2].metric(
                "Accuracy PhishTank",
                f"{validation_metrics.get('accuracy', 0):.1%}",
                help="Exactitude globale sur le dataset de validation."
            )
            cols_val[3].metric(
                "Faux positifs PhishTank",
                f"{validation_metrics.get('false_positive_rate', 0):.1%}",
                help="Pourcentage de liens sûrs marqués comme phishing."
            )

            st.write(f"Références PhishTank/OpenPhish : {validation_meta.get('reference_urls', 0)} URLs")
            detected = validation_meta.get('phishing_detected', 0)
            if detected > 0:
                st.success(f"{detected} correspondance(s) phishing détectée(s) dans le dataset de validation.")
            else:
                st.warning(
                    "Aucune correspondance PhishTank trouvée. Cela peut indiquer que "
                    "les URLs extraites ne correspondent pas exactement aux adresses de référence ou que le dataset n'inclut pas ces menaces."
                )

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

    if mode == "Validation en lot":
        sorted_resultats = sorted(resultats, key=lambda row: row.get("score_fusion", 0.0), reverse=True)
        render_batch_validation(sorted_resultats)

if __name__ == "__main__":
    main()
