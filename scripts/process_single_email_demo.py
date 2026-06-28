import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from extraire_images_v2 import extraire_images_email_v2
import comparer_logos
from comparer_logos import charger_logos, analyser_image, verifier_domaine, calculer_score_final
from generer_resultats_texte_v2 import extraire_texte_email, analyser_email_texte_v2
from generer_resultats_urls import extraire_urls_email, analyser_url
from fusion_multimodale import calculer_score_fusion, statut_fusion
import json

EMAIL = Path('emails_avec_images/email_0002.eml')
OUTDIR = Path('scripts/demo_output')
OUTDIR.mkdir(parents=True, exist_ok=True)

email_id = EMAIL.stem

# helper: extract sender domain locally to avoid importer issues
import re
from email import message_from_bytes

def extract_sender_domain(eml_path):
    try:
        with open(eml_path, 'rb') as f:
            msg = message_from_bytes(f.read())
        sender = msg.get('From', '')
        m = re.search(r'@([\w.\-]+)', sender)
        if m:
            return sender, m.group(1).lower()
        return sender, ''
    except Exception:
        return '', ''

# 1) images
images = extraire_images_email_v2(str(EMAIL), email_id, str(OUTDIR))
logos = charger_logos()
image_results = []
expediteur, domaine = extract_sender_domain(str(EMAIL))
for img in images:
    meilleur_logo, visual_score, details = analyser_image(img, logos)
    domaine_off = False
    if visual_score is not None and visual_score >= 0.55:
        domaine_off = verifier_domaine(domaine, meilleur_logo or "")
    # calculer_score_final runtime signature may differ; use available two-arg signature
    try:
        final_score = comparer_logos.calculer_score_final(visual_score or 0.0, domaine_off)
    except TypeError:
        # fallback: use provided function imported earlier
        final_score, menaces_ocr, score_textuel = calculer_score_final(visual_score or 0.0, domaine_off, img)
    # get OCR details via ocr_analyzer
    try:
        from ocr_analyzer import analyser_image_complete
        ocr = analyser_image_complete(img)
        menaces_ocr = ocr.get('menaces_detectees', [])
        score_textuel = ocr.get('score_textuel', 0.0)
    except Exception:
        menaces_ocr = []
        score_textuel = 0.0

    image_results.append({
        'image': img,
        'meilleur_logo': meilleur_logo,
        'visual_score': round(visual_score or 0.0, 3),
        'score_final': round(float(final_score or 0.0), 3),
        'details': details,
        'domaine_expediteur': domaine,
        'domaine_officiel': domaine_off,
        'menaces_ocr': menaces_ocr,
        'score_textuel': round(score_textuel or 0.0, 3),
    })

# 2) text
texte = extraire_texte_email(str(EMAIL))
text_res = analyser_email_texte_v2(email_id, texte)
text_res['texte_extrait'] = texte

# 3) urls
urls = extraire_urls_email(str(EMAIL))
analyses = [analyser_url(email_id, u) for u in urls]
url_res = {'urls': urls, 'analyses': analyses, 'urls_count': len(urls)}

# 4) fusion
vision_score = max((it['score_final'] for it in image_results), default=None)
nlp_score = text_res.get('score_nlp')
url_score = max((a.get('score_url',0) for a in analyses), default=None) if analyses else None
score = calculer_score_fusion(vision_score, nlp_score, url_score)
stat = statut_fusion(score, {'statut_vision': 'ALERTE' if vision_score and vision_score>=0.6 else 'SAIN','statut_nlp': text_res.get('statut_nlp')})

out = {
    'email': EMAIL.name,
    'vision': image_results,
    'nlp': text_res,
    'url': url_res,
    'fusion': {'score_fusion': score, 'statut_fusion': stat}
}

with open(OUTDIR / f'{email_id}_demo.json','w',encoding='utf-8') as f:
    json.dump(out,f,indent=2,ensure_ascii=False)

print('Demo output written to', OUTDIR / f'{email_id}_demo.json')
print('Summary: images', len(image_results), 'urls', len(urls), 'nlp_score', nlp_score)
