import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generer_resultats_urls import extraire_urls_email

phish_file = Path('phishing_urls.txt')
emails_dir = Path('emails_extraits')

if not phish_file.exists():
    print('phishing_urls.txt not found')
    raise SystemExit(2)
if not emails_dir.exists():
    print('emails_extraits not found')
    raise SystemExit(3)

phish = set(l.strip() for l in phish_file.read_text(encoding='utf-8').splitlines() if l.strip())

matches = []
no_match = 0
for eml in sorted(emails_dir.glob('email_*.eml')):
    urls = extraire_urls_email(str(eml))
    found = []
    for u in urls:
        for p in phish:
            if p in u or u in p:
                found.append(u)
                break
    if found:
        matches.append({'email': eml.stem, 'matches': found})
    else:
        no_match += 1

print('Emails total:', len(list(emails_dir.glob('email_*.eml'))))
print('Emails with phish URLs:', len(matches))
print('Emails without phish URLs:', no_match)
if matches:
    print('\nExamples (up to 10):')
    for m in matches[:10]:
        print(m)
