import os
import requests
from urllib.parse import urlparse
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

API_KEY = os.getenv('VIRUSTOTAL_API_KEY')
if not API_KEY:
    # Fallback: parse .env manually if python-dotenv not available or not loaded
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Remove BOM if present, then strip
                    ln = line.lstrip('\ufeff').strip()
                    if ln.startswith('VIRUSTOTAL_API_KEY'):
                        parts = ln.split('=', 1)
                        if len(parts) == 2:
                            API_KEY = parts[1].strip().strip('"').strip("'")
                            break
    except Exception:
        pass
if not API_KEY:
    print('ERROR: VIRUSTOTAL_API_KEY missing')
    raise SystemExit(2)

print('Loading OpenPhish feed...')
resp = requests.get('https://openphish.com/feed.txt', timeout=30)
feed = [l.strip() for l in resp.text.splitlines() if l.strip()]
if not feed:
    print('ERROR: no feed lines')
    raise SystemExit(3)

sample = feed[0]
print('Sample URL:', sample)

domain = urlparse(sample).netloc
print('Domain:', domain)

headers = {'x-apikey': API_KEY}
url = f'https://www.virustotal.com/api/v3/domains/{domain}'
print('Querying VirusTotal:', url)
try:
    r = requests.get(url, headers=headers, timeout=15)
    print('Status code:', r.status_code)
    try:
        data = r.json()
        # Print compact summary
        attrs = data.get('data', {}).get('attributes', {})
        stats = attrs.get('last_analysis_stats') if attrs else None
        print('last_analysis_stats:', stats)
    except Exception as e:
        print('Response text:', r.text[:1000])
except Exception as e:
    print('Request failed:', e)
    raise
