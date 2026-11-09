import os
from flask import Flask
from markupsafe import Markup
from app.config import HOST, PORT, SECRET_KEY

from . import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DATABASE"] = db.DB_PATH

    db.inizializza_database()
    db.inizializza_build()
    db.inizializza_consigli_stagioni()
    db.inizializza_stagioni()
    db.inizializza_catalogo()
    db.inizializza_storico_abilita_build()

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # --- Funzione classe_icona: SVG distinto per ogni classe ---
    def classe_icona(classe):
        svg_map = {
            "Barbaro": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#8b1a1a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            "Druido": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#228b22" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 6L12 18M6 12L18 12" stroke="#228b22" stroke-width="2" stroke-linecap="round"/></svg>',
            "Negromante": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#4b0082" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8L12 16M8 12L16 12" stroke="#4b0082" stroke-width="2" stroke-linecap="round"/></svg>',
            "Paladino": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#d4af37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            "Incantatore": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#a855f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 6L12 18M6 12L18 12" stroke="#a855f7" stroke-width="2" stroke-linecap="round"/></svg>',
            "Spiritista": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#a855f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8L12 16M8 12L16 12" stroke="#a855f7" stroke-width="2" stroke-linecap="round"/></svg>',
            "Stregone": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#a52a2a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8L12 16M8 12L16 12" stroke="#a52a2a" stroke-width="2" stroke-linecap="round"/></svg>',
            "Tagliagole": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#8b4513" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8L12 16M8 12L16 12" stroke="#8b4513" stroke-width="2" stroke-linecap="round"/></svg>',
        }
        return Markup(svg_map.get(classe, '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#d4af37" stroke-width="2"/></svg>'))

    app.jinja_env.globals['classe_icona'] = classe_icona

    return app


app = create_app()
