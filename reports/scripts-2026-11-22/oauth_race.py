# Deux échanges concurrents du même code d'autorisation client sur OAuthProxy (sans réseau).
import asyncio, sys, time, logging, fastmcp
from key_value.aio.stores.memory import MemoryStore
from fastmcp.server.auth.oauth_proxy import OAuthProxy
from fastmcp.server.auth.oauth_proxy.models import ClientCode
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from mcp.server.auth.provider import AuthorizationCode
from mcp.shared.auth import OAuthClientInformationFull
logging.disable(logging.CRITICAL)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 2
class SlowStore(MemoryStore):
    """MemoryStore avec une latence de 10 ms par get/delete, comme un store réseau partagé (Redis…)."""
    async def get(self, *a, **k):
        await asyncio.sleep(0.01); return await super().get(*a, **k)
    async def delete(self, *a, **k):
        await asyncio.sleep(0.01); return await super().delete(*a, **k)
STORE = sys.argv[2] if len(sys.argv) > 2 else "slow"
print("fastmcp", fastmcp.__version__, "| store:", STORE, "| redemptions concurrentes:", N)
async def main():
    p = OAuthProxy(upstream_authorization_endpoint="http://127.0.0.1:9/auth", upstream_token_endpoint="http://127.0.0.1:9/token",
        upstream_client_id="cid", upstream_client_secret="faux-secret-test",
        token_verifier=StaticTokenVerifier(tokens={"upstream-at": {"client_id": "u", "scopes": ["read"]}}),
        base_url="http://127.0.0.1:8000", client_storage=(SlowStore() if STORE == "slow" else MemoryStore()), jwt_signing_key="cle-jwt-factice-de-test-0123456789",
        require_authorization_consent=False)
    p.get_routes()  # initialise l'émetteur JWT, comme au démarrage du serveur
    client = OAuthClientInformationFull(client_id="client-1", redirect_uris=["http://127.0.0.1:5555/cb"])
    await p.register_client(client)
    now = time.time()
    await p._code_store.put(key="CODE1", value=ClientCode(code="CODE1", client_id="client-1", redirect_uri="http://127.0.0.1:5555/cb",
        code_challenge=None, code_challenge_method="S256", scopes=["read"],
        idp_tokens={"access_token": "upstream-at", "refresh_token": "upstream-rt", "expires_in": 3600, "token_type": "Bearer"},
        expires_at=now + 300, created_at=now), ttl=300)
    ac = AuthorizationCode(code="CODE1", scopes=["read"], expires_at=now + 300, client_id="client-1", code_challenge="x",
        redirect_uri="http://127.0.0.1:5555/cb", redirect_uri_provided_explicitly=True)
    res = await asyncio.gather(*[p.exchange_authorization_code(client, ac) for _ in range(N)], return_exceptions=True)
    ok = [r for r in res if not isinstance(r, Exception)]
    for i, r in enumerate(res):
        print(f"  #{i}:", ("ERREUR " + type(r).__name__ + " " + str(getattr(r, 'error', '')) + " " + str(getattr(r, 'error_description', r))[:60]) if isinstance(r, Exception) else ("jetons émis (access_token len=%d, refresh=%s)" % (len(r.access_token), bool(r.refresh_token))))
    print("jeux de jetons émis:", len(ok), "/", N)
    # Rejeu séquentiel après coup
    try:
        await p.exchange_authorization_code(client, ac); print("rejeu séquentiel: jetons émis")
    except Exception as e:
        print("rejeu séquentiel: ERREUR", type(e).__name__, getattr(e, "error", ""), getattr(e, "error_description", "")) 
asyncio.run(main())
