import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlparse
from generer_resultats_urls import extraire_urls_email

phish = [l.strip() for l in Path('phishing_urls.txt').read_text(encoding='utf-8').splitlines() if l.strip()]
phish_domains = set()
for u in phish:
    try:
        d = urlparse(u).netloc.lower()
        if d:
            phish_domains.add(d)
    except Exception:
        continue

emails_dir = Path('emails_extraits')
positive_emails = []
for eml in sorted(emails_dir.glob('email_*.eml')):
    urls = extraire_urls_email(str(eml))
    is_positive = False
    for u in urls:
        try:
            d = urlparse(u).netloc.lower()
        except Exception:
            continue
        if d in phish_domains:
            is_positive = True
            break
    if is_positive:
        positive_emails.append(eml.stem)

print('Total emails:', len(list(emails_dir.glob('email_*.eml'))))
print('Positive emails by domain match:', len(positive_emails))
if positive_emails:
    print('Examples:', positive_emails[:20])
