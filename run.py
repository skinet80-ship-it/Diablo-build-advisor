import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import app
from app.config import HOST, PORT

if __name__ == "__main__":
    from waitress import serve
    print(f"Avvio Diablo Build Advisor su http://{HOST}:{PORT}")
    serve(app, host=HOST, port=PORT)