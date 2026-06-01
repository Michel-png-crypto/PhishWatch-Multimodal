import mailbox
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MBOX_PATH = BASE_DIR / "phishing-2025.mbox"
SORTIE_DIR = BASE_DIR / "emails_extraits"

SORTIE_DIR.mkdir(parents=True, exist_ok=True)

mbox = mailbox.mbox(str(MBOX_PATH))
compteur = 0

for i, message in enumerate(mbox):
    chemin_eml = SORTIE_DIR / f"email_{i:04d}.eml"
    with open(str(chemin_eml), "wb") as f:
        f.write(message.as_bytes())
    compteur += 1

print(f"✅ {compteur} emails extraits dans {SORTIE_DIR}")