import base64
import io
import json
import os
import re
import runpy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent


def make_png_bytes(color=(220, 20, 20), size=(64, 64)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def create_sample_eml(path: Path, subject: str, url: str, image_bytes: bytes):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"

    html = (
        f"<html><body>"
        f"<p>{subject}</p>"
        f"<p>Veuillez visiter <a href=\"{url}\">{url}</a></p>"
        f"<img src=\"data:image/png;base64,{base64.b64encode(image_bytes).decode()}\"/>"
        f"</body></html>"
    )

    part_html = MIMEText(html, "html", "utf-8")
    msg.attach(part_html)

    path.write_bytes(msg.as_bytes())


@pytest.fixture
def sample_pipeline_dataset(tmp_path, monkeypatch):
    emails_avec_images = tmp_path / "emails_avec_images"
    emails_extraits = tmp_path / "emails_extraits"
    images_extraites = tmp_path / "images_extraites"
    logos_dir = tmp_path / "logos"

    emails_avec_images.mkdir(parents=True)
    emails_extraits.mkdir(parents=True)
    images_extraites.mkdir(parents=True)
    logos_dir.mkdir(parents=True)

    image_bytes = make_png_bytes()
    urls = [
        "https://example.com/login",
        "https://secure-example.com/verify",
        "https://login-example.com/update"
    ]

    for idx, url in enumerate(urls, start=1):
        email_id = f"email_{idx:04d}"
        subject = f"Action requise pour {email_id}"
        eml_path = emails_avec_images / f"{email_id}.eml"
        create_sample_eml(eml_path, subject, url, image_bytes)

        # Copier le même email dans emails_extraits pour le NLP/URL
        target = emails_extraits / f"{email_id}.eml"
        target.write_bytes(eml_path.read_bytes())

    # Créer un logo de test isolé pour comparer_logos.py
    logo_path = logos_dir / "brand_logo.png"
    Image.new("RGB", (64, 64), (220, 20, 20)).save(str(logo_path), format="PNG")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VIRUSTOTAL_API_KEY", "")

    return {
        "base": tmp_path,
        "emails_avec_images": emails_avec_images,
        "emails_extraits": emails_extraits,
        "images_extraites": images_extraites,
        "logos_dir": logos_dir,
        "resultats_json": tmp_path / "resultats.json",
        "stats_comparaison_json": tmp_path / "stats_comparaison.json",
        "resultats_texte_json": tmp_path / "resultats_texte_v2.json",
        "resultats_urls_json": tmp_path / "resultats_urls.json",
        "resultats_fusion_json": tmp_path / "resultats_fusion.json",
        "metrics_formels_json": tmp_path / "metrics_formels.json",
    }


def patch_paths_in_script(content: str, replacements: dict) -> str:
    for key, value in replacements.items():
        if key == "BASE_DIR":
            continue
        exact_old_r = f'{key} = r"C:\\logos_reference\\{key.lower()}"'
        exact_old = f'{key} = "C:\\logos_reference\\{key.lower()}"'
        if exact_old_r in content:
            content = content.replace(exact_old_r, f'{key} = r"{value}"')
        elif exact_old in content:
            content = content.replace(exact_old, f'{key} = "{value}"')

    # patch known patterns for extraire_images.py and comparer_logos.py
    content = content.replace(
        'EMAILS_DIR = r"C:\\logos_reference\\emails_avec_images"',
        f'EMAILS_DIR = r"{replacements.get("EMAILS_DIR", "")}"',
    )
    content = content.replace(
        'SORTIE_DIR = r"C:\\logos_reference\\images_extraites"',
        f'SORTIE_DIR = r"{replacements.get("SORTIE_DIR", "")}"',
    )
    content = content.replace(
        'LOG_FILE = r"C:\\logos_reference\\extraction_log.json"',
        f'LOG_FILE = r"{replacements.get("LOG_FILE", "")}"',
    )
    content = content.replace(
        'LOGOS_DIR = r"C:\\logos_reference"',
        f'LOGOS_DIR = r"{replacements.get("LOGOS_DIR", "")}"',
    )
    content = content.replace(
        'IMAGES_DIR = r"C:\\logos_reference\\images_extraites"',
        f'IMAGES_DIR = r"{replacements.get("IMAGES_DIR", "")}"',
    )
    content = content.replace(
        'RESULTATS_FILE = r"C:\\logos_reference\\resultats.json"',
        f'RESULTATS_FILE = r"{replacements.get("RESULTATS_FILE", "")}"',
    )
    content = content.replace(
        'STATS_FILE = r"C:\\logos_reference\\stats_comparaison.json"',
        f'STATS_FILE = r"{replacements.get("STATS_FILE", "")}"',
    )
    return content


def run_script_with_overrides(src_path: Path, dest_dir: Path, overrides: dict):
    dest_path = dest_dir / src_path.name
    lines = src_path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        replaced = False
        for key, value in overrides.items():
            if stripped.startswith(f"{key} ="):
                if key in {"EMAILS_DIR", "SORTIE_DIR", "LOG_FILE"}:
                    new_lines.append(f'{key} = Path(r"{value}")')
                else:
                    new_lines.append(f'{key} = r"{value}"')
                replaced = True
                break
        if not replaced:
            new_lines.append(line)
    dest_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return dest_path


def load_json(path: Path):
    assert path.exists(), f"JSON file not found: {path}"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data not in ({}, [], None), f"JSON file is empty or invalid: {path}"
    return data


class TestPipelineIntegration:
    def test_pipeline_complet_debout_a_bout(self, sample_pipeline_dataset, monkeypatch):
        data = sample_pipeline_dataset
        extraire_path = run_script_with_overrides(
            ROOT / "extraire_images.py",
            data["base"],
            {
                "EMAILS_DIR": str(data["emails_avec_images"]),
                "SORTIE_DIR": str(data["images_extraites"]),
                "LOG_FILE": str(data["base"] / "extraction_log.json"),
            },
        )

        runpy.run_path(str(extraire_path), init_globals={"__name__": "__main__"})

        assert any(data["images_extraites"].glob("*.png")), "Aucune image extraite après extraire_images.py"

        comparer_path = run_script_with_overrides(
            ROOT / "comparer_logos.py",
            data["base"],
            {
                "LOGOS_DIR": str(data["logos_dir"]),
                "IMAGES_DIR": str(data["images_extraites"]),
                "EMAILS_DIR": str(data["emails_avec_images"]),
                "RESULTATS_FILE": str(data["resultats_json"]),
                "STATS_FILE": str(data["stats_comparaison_json"]),
            },
        )
        runpy.run_path(str(comparer_path), init_globals={"__name__": "__main__"})

        resultats = load_json(data["resultats_json"])
        assert isinstance(resultats, list), "resultats.json doit être une liste"
        assert len(resultats) > 0, "resultats.json doit contenir au moins un résultat"

        import generer_resultats_texte_v2 as texte_mod

        monkeypatch.chdir(data["base"])
        success = texte_mod.generer_resultats_texte_v2()
        assert success is True, "generer_resultats_texte_v2.py a échoué"

        texte_data = load_json(data["resultats_texte_json"])
        assert isinstance(texte_data, dict)
        assert "metadata" in texte_data and "resultats" in texte_data
        assert len(texte_data["resultats"]) == 3

        import generer_resultats_urls as urls_mod

        monkeypatch.setattr(urls_mod, "VIRUSTOTAL_API_KEY", "")
        monkeypatch.setattr(
            urls_mod,
            "check_virustotal",
            lambda domain, cached_only=False: {
                "malicious": 0,
                "suspicious": 0,
                "undetected": 0,
                "verdict": "UNKNOWN",
                "from_cache": False,
            },
        )

        success = urls_mod.generer_resultats_urls()
        assert success is True, "generer_resultats_urls.py a échoué"

        urls_data = load_json(data["resultats_urls_json"])
        assert isinstance(urls_data, dict)
        assert "metadata" in urls_data and "resultats" in urls_data
        assert len(urls_data["resultats"]) == 3
        assert sum(entry.get("urls_analysees", 0) for entry in urls_data["resultats"]) > 0

        import fusion_multimodale as fusion_mod

        monkeypatch.setattr(fusion_mod, "FICHIER_VISION", data["resultats_json"])
        monkeypatch.setattr(fusion_mod, "FICHIER_NLP", data["resultats_texte_json"])
        monkeypatch.setattr(fusion_mod, "FICHIER_URL", data["resultats_urls_json"])
        monkeypatch.setattr(fusion_mod, "FICHIER_FUSION", data["resultats_fusion_json"])

        fusion_data = fusion_mod.fusionner()
        assert data["resultats_fusion_json"].exists(), "resultats_fusion.json n'a pas été généré"
        assert isinstance(fusion_data, dict)
        assert "meta" in fusion_data and "resultats" in fusion_data
        assert len(fusion_data["resultats"]) == 3
        assert fusion_data["meta"]["nb_emails"] == 3

        # Vérifier que les scores de fusion sont recalculables à partir des sous-scores
        nlp_index = {row["email"]: row for row in texte_data["resultats"]}
        vision_index = {}
        for image_row in resultats:
            email_id = image_row["image"].split("_")[0] + "_" + image_row["image"].split("_")[1]
            if email_id not in vision_index or image_row["score_final"] > vision_index[email_id]["score_final"]:
                vision_index[email_id] = image_row

        for row in fusion_data["resultats"]:
            scores = row["scores"]
            expected_score = fusion_mod.calculer_score_fusion(
                scores.get("vision"),
                scores.get("nlp"),
                scores.get("url"),
            )
            assert pytest.approx(expected_score, abs=1e-3) == row["score_fusion"], (
                f"Score fusion incohérent pour {row['email_id']}: attendu {expected_score}, obtenu {row['score_fusion']}"
            )

            email_id = row["email_id"]
            vision_status = "ALERTE" if vision_index[email_id]["statut"] == "ALERTE" else "SAIN"
            nlp_status = nlp_index[email_id]["statut_nlp"]
            expected_status = fusion_mod.statut_fusion(
                row["score_fusion"],
                {"statut_vision": vision_status, "statut_nlp": nlp_status},
            )
            assert row["statut_fusion"] == expected_status, (
                f"Statut fusion incorrect pour {email_id}: attendu {expected_status}, obtenu {row['statut_fusion']}"
            )

        import generer_metrics as metrics_mod

        monkeypatch.chdir(data["base"])
        success = metrics_mod.generer_metrics()
        assert success is True, "generer_metrics.py a échoué"

        metrics_data = load_json(data["metrics_formels_json"])
        assert isinstance(metrics_data, dict)
        assert "confusion_matrix" in metrics_data and "scores" in metrics_data

    def test_generer_resultats_texte_v2_echoue_proprement_si_pas_d_emails(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "emails_extraits").mkdir()

        import generer_resultats_texte_v2 as texte_mod

        success = texte_mod.generer_resultats_texte_v2()
        assert success is False, "Le script devrait retourner False lorsqu'il n'y a pas d'emails à analyser"
