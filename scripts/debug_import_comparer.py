import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import comparer_logos
    print('Imported comparer_logos OK')
    print([n for n in dir(comparer_logos) if not n.startswith('_')][:60])
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR:', e)
