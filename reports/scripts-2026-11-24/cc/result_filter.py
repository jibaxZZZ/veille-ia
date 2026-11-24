# usage: ... | python3 -I result_filter.py ; garde 5 champs du JSON de résultat de claude -p, recopie les autres lignes (coupées à 300 car.)
import sys, json
for l in sys.stdin:
    l = l.rstrip()
    if l.startswith('{'):
        d = json.loads(l); print({k: d.get(k) for k in ('subtype', 'is_error', 'num_turns', 'result', 'errors')})
    else:
        print(l[:300])
