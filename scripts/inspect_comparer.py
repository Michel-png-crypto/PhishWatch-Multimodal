import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comparer_logos
import inspect
print('Module file:', comparer_logos.__file__)
print('Has extraire_expediteur:', hasattr(comparer_logos, 'extraire_expediteur'))
if hasattr(comparer_logos, 'extraire_expediteur'):
    print('Source:')
    print(inspect.getsource(comparer_logos.extraire_expediteur))
else:
    # list functions that contain 'exped' substring
    print([n for n in dir(comparer_logos) if 'exped' in n.lower()])
    print('Available attrs sample:', [n for n in dir(comparer_logos) if not n.startswith('_')][:80])
    # Print file snippet around definition
    import io
    p = comparer_logos.__file__
    try:
        with open(p,'r',encoding='utf-8') as f:
            lines = f.readlines()
            for i in range(120,141):
                print(i+1, lines[i].rstrip())
    except Exception as e:
        print('Could not read file snippet:', e)
