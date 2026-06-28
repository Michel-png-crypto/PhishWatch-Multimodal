from urllib.parse import urlparse
from pathlib import Path
phish = [l.strip() for l in Path('phishing_urls.txt').read_text(encoding='utf-8').splitlines() if l.strip()]
phish_domains = set(urlparse(u).netloc.lower() for u in phish)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generer_resultats_urls import extraire_urls_email

emails_dir = Path('emails_extraits')
email_domains = set()
for eml in sorted(emails_dir.glob('email_*.eml')):
    urls = extraire_urls_email(str(eml))
    for u in urls:
        try:
            d = urlparse(u).netloc.lower()
            if d:
                email_domains.add(d)
        except Exception:
            pass

common = phish_domains & email_domains
print('Phish domains count:', len(phish_domains))
print('Email domains count:', len(email_domains))
print('Common domains:', len(common))
if common:
    for d in list(common)[:20]:
        print(' -', d)
else:
    print('No domain overlap found')
