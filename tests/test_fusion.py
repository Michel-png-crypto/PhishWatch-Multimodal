"""Tests fusion multimodale."""

import json

import fusion_multimodale as fm


def test_normaliser_email_id():
    assert fm.normaliser_email_id("email_0041_part3.png") == "email_0041"
    assert fm.normaliser_email_id("email_0042.eml") == "email_0042"


def test_fusion_score_partiel():
    attendu = round((0.8 * 0.35 + 0.4 * 0.3) / (0.35 + 0.3), 3)
    assert fm.calculer_score_fusion(0.8, None, 0.4) == attendu


def test_fusion_score_complet():
    s = fm.calculer_score_fusion(0.6, 0.8, 0.2)
    attendu = round(0.6 * 0.35 + 0.8 * 0.35 + 0.2 * 0.3, 3)
    assert s == attendu


def test_agreger_vision_prend_le_max(tmp_path):
    lignes = [
        {"image": "email_0001_part1.png", "score_final": 0.3, "statut": "SAIN"},
        {"image": "email_0001_part2.png", "score_final": 0.9, "statut": "ALERTE", "ressemble_a": "apple.png"},
    ]
    agg = fm.agreger_vision(lignes)
    assert agg["email_0001"]["score_vision"] == 0.9
    assert agg["email_0001"]["statut_vision"] == "ALERTE"


def test_fusionner_produit_fichier(tmp_path, monkeypatch):
    vision = [{"image": "email_0099_part1.png", "score_final": 0.85, "statut": "ALERTE", "visual_score": 0.7, "ressemble_a": "x.png"}]
    nlp = [{"fichier": "email_0099.eml", "score_nlp": 0.9, "statut_nlp": "SUSPECT", "menaces_detectees": []}]
    url = [{"email": "email_0099.eml", "url_score": 0.5, "urls_analysees": 2, "alertes": []}]

    monkeypatch.setattr(fm, "FICHIER_VISION", tmp_path / "resultats.json")
    monkeypatch.setattr(fm, "FICHIER_NLP", tmp_path / "resultats_texte.json")
    monkeypatch.setattr(fm, "FICHIER_URL", tmp_path / "resultats_urls.json")
    monkeypatch.setattr(fm, "FICHIER_FUSION", tmp_path / "resultats_fusion.json")

    (tmp_path / "resultats.json").write_text(json.dumps(vision), encoding="utf-8")
    (tmp_path / "resultats_texte.json").write_text(json.dumps(nlp), encoding="utf-8")
    (tmp_path / "resultats_urls.json").write_text(json.dumps(url), encoding="utf-8")

    data = fm.fusionner()
    assert len(data["resultats"]) == 1
    r = data["resultats"][0]
    assert r["email_id"] == "email_0099"
    assert r["modules_presents"] == {"vision": True, "nlp": True, "url": True}
    assert r["statut_fusion"] == "PHISHING"
