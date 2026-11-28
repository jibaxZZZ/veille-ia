"""Cas limites de l'écrivain de réglages de Hermes v0.23.4 (save_plugin_settings)."""
import os, sys
from pathlib import Path
from hermes_cli.plugins_settings import save_plugin_settings, plugin_settings_fields
pdir = Path(os.environ["HERMES_HOME"]) / "plugins" / "demo-config"
essais = [
    {"retries": 5, "mode": "careful"},     # valide
    {"retries": True},                     # bool pour un int
    {"retries": "5"},                      # chaîne pour un int
    {"mode": "turbo"},                     # hors choices
    {"api_key": "faux-jeton-de-test"},     # secret : refus attendu
    {"inconnu": 1},                        # clé non déclarée
    {"retries": 7, "mode": "turbo"},       # lot avec une erreur : rien ne doit être écrit
]
for v in essais:
    try:
        print("  OK  ", v, "->", save_plugin_settings("demo-config", pdir, v))
    except Exception as e:
        print("  REFUS", v, "->", type(e).__name__, e)
print("  valeurs relues :", {f["key"]: f.get("value", "(secret, has_value=%s)" % f.get("has_value")) for f in plugin_settings_fields("demo-config", pdir)})
cfg = Path(os.environ["HERMES_HOME"]) / "config.yaml"
txt = cfg.read_text() if cfg.exists() else ""
print("  config.yaml contient 'faux-jeton' :", "faux-jeton" in txt)
print("  extrait config.yaml :", [l for l in txt.splitlines() if "retries" in l or "mode:" in l or "demo-config" in l][:6])
