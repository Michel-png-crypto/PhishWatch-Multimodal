"""Fixtures partagées pour les tests du module vision."""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def projet_root():
    return ROOT


@pytest.fixture
def tmp_sortie(tmp_path):
    return tmp_path / "images_extraites"


@pytest.fixture
def image_grayscale_64():
    """Carré 64x64 avec dégradé — pour tests hash/SSIM."""
    arr = np.linspace(0, 255, 64 * 64, dtype=np.uint8).reshape(64, 64)
    return arr


@pytest.fixture
def image_png_bytes():
    """PNG 32x32 rouge valide."""
    img = Image.new("RGB", (32, 32), color=(220, 20, 20))
    buf = __import__("io").BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def logo_test_path(tmp_path, image_grayscale_64):
    """Fichier logo temporaire sur disque."""
    chemin = tmp_path / "test_brand.png"
    cv2.imwrite(str(chemin), image_grayscale_64)
    return chemin
