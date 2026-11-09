import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "diablo.db")

# Avvio server locale (accessibile anche dalla rete Wi-Fi privata)
HOST = "0.0.0.0"
PORT = 5098
DEBUG = False

# Nota di sicurezza: HOST = 0.0.0.0 espone il server su tutte le interfacce di rete.
# La regola firewall Windows è limitata al profilo "Privato" (rete Wi-Fi domestica)
# e alla subnet locale (RemoteAddress LocalSubnet). Non aprire porte sul router
# e non esporre il servizio a Internet.

# Segreto per sessione e protezione CSRF
SECRET_KEY_FILE = os.path.join(DATA_DIR, "secret.key")
if os.path.isfile(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "rb") as _f:
        SECRET_KEY = _f.read()
else:
    SECRET_KEY = secrets.token_bytes(32)
    print("AVVISO: chiave segreta generata temporaneamente in memoria")

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(f"Chiave segreta non valida in {SECRET_KEY_FILE}: deve contenere almeno 32 byte")

# Dimensione massima per upload (riservata)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Verifica che la directory dati esista
if not os.path.isdir(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)