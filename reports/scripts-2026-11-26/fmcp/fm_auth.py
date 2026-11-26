# Sans Authlib : import de l'OAuthProxy et vérification d'un JWT signé localement (RSAKeyPair, aucun réseau).
import asyncio, importlib.metadata as md
from fastmcp.server.auth import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair
kp = RSAKeyPair.generate()
v = JWTVerifier(public_key=kp.public_key, issuer="https://iss.test", audience="veille")
ok = kp.create_token(subject="u1", issuer="https://iss.test", audience="veille")
bad = kp.create_token(subject="u1", issuer="https://iss.test", audience="autre")
async def go():
    print("fastmcp", md.version("fastmcp"), "OAuthProxy importé:", OAuthProxy.__name__)
    a = await v.verify_token(ok); print("jeton valide ->", a.client_id if a else None)
    print("mauvaise audience ->", await v.verify_token(bad))
asyncio.run(go())
