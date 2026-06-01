"""Tests unitaires — extraire_images.py (Florient / module vision)."""

import base64
import email
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import pytest
from PIL import Image

import extraire_images as ex


class TestValidationImage:
    def test_rejette_image_trop_petite(self):
        img = Image.new("RGB", (8, 8), color=(0, 0, 0))
        optimisee, raison = ex.valider_et_optimiser_image(img)
        assert optimisee is None
        assert "Trop petite" in raison

    def test_accepte_image_valide_grayscale(self):
        img = Image.new("RGB", (64, 64), color=(100, 100, 100))
        optimisee, raison = ex.valider_et_optimiser_image(img)
        assert raison is None
        assert optimisee.mode == "L"


class TestExtractionSauvegarde:
    def test_sauvegarde_png(self, image_png_bytes, tmp_sortie):
        ok, nom, _ = ex.extraire_et_sauvegarder_image(
            image_png_bytes, "test_email", "part", 0, sortie_dir=tmp_sortie
        )
        assert ok is True
        assert (tmp_sortie / nom).exists()

    def test_rejette_donnees_invalides(self, tmp_sortie):
        ok, msg, eco = ex.extraire_et_sauvegarder_image(
            b"pas une image", "test_email", "part", 0, sortie_dir=tmp_sortie
        )
        assert ok is False
        assert eco == 0


class TestExtractionDepuisEml:
    def test_piece_jointe_image(self, image_png_bytes, tmp_sortie):
        msg = MIMEMultipart()
        msg.attach(MIMEImage(image_png_bytes, name="logo.png"))

        raw = msg.as_bytes()
        parsed = email.message_from_bytes(raw)

        for i, part in enumerate(parsed.walk()):
            if part.get_content_type().startswith("image/"):
                data = part.get_payload(decode=True)
                ok, nom, _ = ex.extraire_et_sauvegarder_image(
                    data, "email_test", "part", i, sortie_dir=tmp_sortie
                )
                assert ok is True
                assert (tmp_sortie / nom).exists()
                return

        pytest.fail("Aucune pièce jointe image trouvée")

    def test_image_base64_html(self, image_png_bytes, tmp_sortie):
        b64 = base64.b64encode(image_png_bytes).decode("ascii")
        html = f'<html><body><img src="data:image/png;base64,{b64}"/></body></html>'

        ok, nom, _ = ex.extraire_et_sauvegarder_image(
            image_png_bytes, "email_html", "html", 0, sortie_dir=tmp_sortie
        )
        assert ok is True
        assert "html" in nom
