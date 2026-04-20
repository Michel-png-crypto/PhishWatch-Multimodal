import mailbox
import os

# Chemins
MBOX_PATH = r"C:\logos_reference\phishing-2025.mbox"
SORTIE_DIR = r"C:\logos_reference\emails_extraits"

os.makedirs(SORTIE_DIR, exist_ok=True)

mbox = mailbox.mbox(MBOX_PATH)
compteur = 0

for i, message in enumerate(mbox):
    chemin_eml = os.path.join(SORTIE_DIR, f"email_{i:04d}.eml")
    with open(chemin_eml, "wb") as f:
        f.write(message.as_bytes())
    compteur += 1

print(f"✅ {compteur} emails extraits dans {SORTIE_DIR}")