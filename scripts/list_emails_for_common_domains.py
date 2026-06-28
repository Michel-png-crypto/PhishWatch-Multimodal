import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlparse
from generer_resultats_urls import extraire_urls_email

phish = [l.strip() for l in Path('phishing_urls.txt').read_text(encoding='utf-8').splitlines() if l.strip()]
phish_domains = set(urlparse(u).netloc.lower() for u in phish)

emails_dir = Path('emails_extraits')

common_domains = set()
for eml in sorted(emails_dir.glob('email_*.eml')):
    urls = extraire_urls_email(str(eml))
    for u in urls:
        try:
            d = urlparse(u).netloc.lower()
        except Exception:
            continue
        if d in phish_domains:
            common_domains.add(d)

print('Common domains found in emails:', common_domains)

for domain in common_domains:
    print('\n--- Domain:', domain)
    for eml in sorted(emails_dir.glob('email_*.eml')):
        urls = extraire_urls_email(str(eml))
        found = []
        for u in urls:
            try:
                if urlparse(u).netloc.lower() == domain:
                    found.append(u)
            except Exception:
                continue
        if found:
            print(eml.stem, found)
