# usage: measure.py <cmd...> ; lance la commande, affiche RSS max des enfants (Kio) et durée
import resource, subprocess, sys, time
t = time.monotonic(); rc = subprocess.call(sys.argv[1:])
print(f"rss_max_kio={resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss} duree_s={time.monotonic()-t:.1f}", file=sys.stderr)
sys.exit(rc)
