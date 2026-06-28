import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comparer_logos
import inspect
print('has calculer_score_final:', hasattr(comparer_logos,'calculer_score_final'))
if hasattr(comparer_logos,'calculer_score_final'):
    print('signature:', inspect.signature(comparer_logos.calculer_score_final))
    import textwrap
    try:
        src = inspect.getsource(comparer_logos.calculer_score_final)
        print('source excerpt:\n', '\n'.join(textwrap.wrap(src, 120)))
    except Exception as e:
        print('Cannot get source:', e)
