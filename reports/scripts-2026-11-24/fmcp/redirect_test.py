# usage: redirect_test.py ; appelle matches_allowed_pattern(uri, motif) sur des cas tirés des notes de 4.2.5
import fastmcp
from fastmcp.server.auth.redirect_validation import matches_allowed_pattern
cases = [
    ("https://app.example/", "https://app.example/"),
    ("https://app.example/callback", "https://app.example/"),
    ("https://app.example/callback", "https://app.example/*"),
    ("https://app.example/cb?x=1", "https://app.example/cb?x=1"),
    ("https://app.example/cb?x=2", "https://app.example/cb?x=1"),
    ("https://app.example/cb#frag", "https://app.example/cb"),
    ("http://localhost:5555/cb", "http://localhost/cb"),
]
print("fastmcp", fastmcp.__version__)
for u, p in cases:
    print(f"{matches_allowed_pattern(u, p)!s:5}  uri={u:32} motif={p}")
