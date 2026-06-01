"""Tests unitaires — comparer_logos.py (Florient / module vision)."""

import cv2
import numpy as np
import pytest

import comparer_logos as cl


class TestHashEtScores:
    def test_hash_identique_score_un(self, image_grayscale_64):
        h = cl.hash_perceptuel(image_grayscale_64)
        assert cl.score_hash(h, h) == 1.0

    def test_hash_different_score_inferieur_un(self, image_grayscale_64):
        h1 = cl.hash_perceptuel(image_grayscale_64)
        inverse = 255 - image_grayscale_64
        h2 = cl.hash_perceptuel(inverse)
        assert cl.score_hash(h1, h2) < 1.0

    def test_score_combine_poids(self):
        assert cl.score_combine(1.0, 0.0) == 0.6
        assert cl.score_combine(0.0, 1.0) == 0.4

    def test_score_ssim_image_identique(self, image_grayscale_64):
        assert cl.score_ssim(image_grayscale_64, image_grayscale_64) >= 0.99


class TestDomaineEtScoreFinal:
    def test_domaine_apple_officiel(self):
        assert cl.verifier_domaine("mail.apple.com", "Apple_Icon_6.png") is True

    def test_domaine_apple_suspect(self):
        assert cl.verifier_domaine("phishing.evil.ru", "Apple_Icon_6.png") is False

    def test_domaine_paypal_officiel(self):
        assert cl.verifier_domaine("service.paypal.com", "PayPal_Icon_15.jpeg") is True

    def test_score_faible_inchange(self):
        assert cl.calculer_score_final(0.40, False) == 0.40

    def test_score_fort_domaine_officiel_reduit(self):
        assert cl.calculer_score_final(0.80, True) == 0.4

    def test_score_fort_domaine_suspect_augmente(self):
        assert cl.calculer_score_final(0.70, False) == pytest.approx(0.84)

    def test_statut_alerte_seuil(self):
        score = cl.calculer_score_final(0.75, False)
        assert score >= cl.SEUIL_ALERTE


class TestAnalyserImage:
    def test_image_identique_au_logo(self, logo_test_path, tmp_path):
        copie = tmp_path / "copie.png"
        img = cv2.imread(str(logo_test_path), cv2.IMREAD_GRAYSCALE)
        cv2.imwrite(str(copie), img)

        logos = {"test_brand.png": img}
        meilleur, score, _ = cl.analyser_image(str(copie), logos)

        assert meilleur == "test_brand.png"
        assert score >= 0.95

    def test_fichier_inexistant(self):
        meilleur, score, details = cl.analyser_image("fichier_inexistant.png", {})
        assert meilleur is None
        assert score is None
        assert details is None


@pytest.mark.skipif(
    not (cl.BASE_DIR / "Apple_Icon_6.png").exists(),
    reason="Logo Apple absent du dépôt local",
)
class TestIntegrationLogosProjet:
    def test_logo_apple_charge_et_compare(self, tmp_path):
        logos = cl.charger_logos()
        assert any("apple" in k.lower() for k in logos)

        apple_nom = next(k for k in logos if "apple" in k.lower())
        chemin = tmp_path / "apple_copy.png"
        cv2.imwrite(str(chemin), logos[apple_nom])

        meilleur, score, _ = cl.analyser_image(str(chemin), logos)
        assert meilleur == apple_nom
        assert score >= 0.9
