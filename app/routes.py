from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Pagina iniziale dell'applicazione con dashboard."""
    db.inizializza_database()
    db.inizializza_stagioni()
    personaggi = db.leggi_personaggi()
    stagione_attiva = db.leggi_stagione_attiva()
    return render_template("index.html", personaggi=personaggi, stagione_attiva=stagione_attiva)


@bp.route("/personaggi")
def personaggi():
    """Elenco personaggi e form per crearne uno nuovo."""
    db.inizializza_database()
    personaggi = db.leggi_personaggi()
    return render_template("personaggi.html", personaggi=personaggi)


@bp.route("/personaggi/nuovo", methods=["POST"])
def nuovo_personaggio():
    """Crea un nuovo personaggio."""
    try:
        db.crea_personaggio(
            nome=request.form.get("nome", "").strip(),
            classe=request.form.get("classe", "").strip(),
            modalita=request.form.get("modalita", "").strip(),
            numero_stagione=request.form.get("numero_stagione") or None,
            livello_personaggio=int(request.form.get("livello_personaggio", 1)),
            livello_paragon=int(request.form.get("livello_paragon", 0)),
            obiettivo=request.form.get("obiettivo", "").strip() or None,
            note=request.form.get("note", "").strip() or None,
        )
        flash("Personaggio creato con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la creazione: {e}", "errore")
    return redirect(url_for("main.personaggi"))


@bp.route("/personaggi/<int:personaggio_id>/modifica", methods=["POST"])
def modifica_personaggio(personaggio_id):
    """Modifica un personaggio esistente."""
    try:
        db.modifica_personaggio(
            personaggio_id,
            nome=request.form.get("nome", "").strip(),
            classe=request.form.get("classe", "").strip(),
            modalita=request.form.get("modalita", "").strip(),
            numero_stagione=request.form.get("numero_stagione") or None,
            livello_personaggio=int(request.form.get("livello_personaggio", 1)),
            livello_paragon=int(request.form.get("livello_paragon", 0)),
            obiettivo=request.form.get("obiettivo", "").strip() or None,
            note=request.form.get("note", "").strip() or None,
        )
        flash("Personaggio aggiornato con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la modifica: {e}", "errore")
    return redirect(url_for("main.personaggi"))


@bp.route("/personaggi/<int:personaggio_id>/elimina", methods=["POST"])
def elimina_personaggio(personaggio_id):
    """Elimina un personaggio."""
    try:
        db.elimina_personaggio(personaggio_id)
        flash("Personaggio eliminato con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'eliminazione: {e}", "errore")
    return redirect(url_for("main.personaggi"))


@bp.route("/build")
def build_sel_personaggio():
    """Pagina di selezione personaggio per la gestione build."""
    db.inizializza_database()
    personaggi = db.leggi_personaggi()
    return render_template("build_sel_personaggio.html", personaggi=personaggi)


@bp.route("/personaggi/<int:personaggio_id>/build")
def lista_build(personaggio_id):
    """Elenco build di un personaggio."""
    db.inizializza_build()
    db.inizializza_storico_abilita_build()
    personaggio = db.leggi_personaggio_per_id(personaggio_id)
    if personaggio is None:
        flash("Personaggio non trovato.", "errore")
        return redirect(url_for("main.personaggi"))
    build_list = db.leggi_build_personaggio(personaggio_id)
    # Carica versioni con abilità per ogni build
    build_versioni_map = {}
    for b in build_list:
        build_versioni_map[b['id']] = db.leggi_build_versioni_con_abilita(b['id'])
    # Carica classi e abilità per i dropdown di selezione
    classi = db.leggi_classi()
    abilita_per_classe = {}
    for c in classi:
        abilita_per_classe[c['id']] = db.leggi_abilita_per_classe(c['id'])
    return render_template("build.html", personaggio=personaggio, build_list=build_list, build_versioni_map=build_versioni_map, classi=classi, abilita_per_classe=abilita_per_classe)


@bp.route("/personaggi/<int:personaggio_id>/build/nuovo", methods=["POST"])
def nuovo_build(personaggio_id):
    """Crea una nuova build per un personaggio."""
    try:
        db.crea_build_con_base_protetta(
            personaggio_id=personaggio_id,
            nome_build=request.form.get("nome_build", "").strip(),
            obiettivo=request.form.get("obiettivo", "").strip() or None,
            abilita=request.form.get("abilita", "").strip() or None,
            equipaggiamento=request.form.get("equipaggiamento", "").strip() or None,
            aspetti_leggendari=request.form.get("aspetti_leggendari", "").strip() or None,
            tempra=request.form.get("tempra", "").strip() or None,
            paragon=request.form.get("paragon", "").strip() or None,
            note=request.form.get("note", "").strip() or None,
            build_attiva=request.form.get("build_attiva") == "1",
        )
        flash("Build creata con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la creazione: {e}", "errore")
    return redirect(url_for("main.lista_build", personaggio_id=personaggio_id))


@bp.route("/build/<int:build_id>/modifica", methods=["POST"])
def modifica_build(build_id):
    """Modifica una build esistente."""
    try:
        db.modifica_build(
            build_id,
            nome_build=request.form.get("nome_build", "").strip(),
            obiettivo=request.form.get("obiettivo", "").strip() or None,
            abilita=request.form.get("abilita", "").strip() or None,
            equipaggiamento=request.form.get("equipaggiamento", "").strip() or None,
            aspetti_leggendari=request.form.get("aspetti_leggendari", "").strip() or None,
            tempra=request.form.get("tempra", "").strip() or None,
            paragon=request.form.get("paragon", "").strip() or None,
            note=request.form.get("note", "").strip() or None,
            build_attiva=request.form.get("build_attiva") == "1",
        )
        flash("Build aggiornata con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la modifica: {e}", "errore")
    build = db.leggi_build_per_id(build_id)
    return redirect(url_for("main.lista_build", personaggio_id=build["personaggio_id"]))


@bp.route("/build/<int:build_id>/elimina", methods=["POST"])
def elimina_build_route(build_id):
    """Elimina una build."""
    build = None
    try:
        build = db.leggi_build_per_id(build_id)
        if build is None:
            raise ValueError("Build non trovata.")
        personaggio_id = build["personaggio_id"]
        db.elimina_build(build_id)
        flash("Build eliminata con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'eliminazione: {e}", "errore")
        if build:
            return redirect(url_for("main.lista_build", personaggio_id=build["personaggio_id"]))
        return redirect(url_for("main.personaggi"))
    return redirect(url_for("main.lista_build", personaggio_id=build["personaggio_id"]))


@bp.route("/confronto")
def confronto():
    """Confronto build (in sviluppo)."""
    return render_template("confronto.html", sviluppo=True)


@bp.route("/stagioni")
def stagioni():
    """Elenco stagioni con meccaniche e fonti."""
    db.inizializza_stagioni()
    stagione_attiva = db.leggi_stagione_attiva()
    stagione_list = db.leggi_stagioni()
    return render_template("stagioni.html", stagione_attiva=stagione_attiva, stagione_list=stagione_list)


@bp.route("/fonti")
def fonti():
    """Elenco fonti e informazioni di verifica."""
    return render_template("fonti.html", sviluppo=True)


@bp.route("/catalogo")
def catalogo():
    """Catalogo Diablo 4: classi, abilità, patch, fonti e slot equipaggiamento."""
    db.inizializza_catalogo()
    classi = db.leggi_classi()
    patch_list = db.leggi_patch()
    fonti = db.leggi_fonti()
    slot_list = db.leggi_slot_equipaggiamento()
    return render_template(
        "catalogo.html",
        classi=classi,
        patch_list=patch_list,
        fonti=fonti,
        slot_list=slot_list,
    )


@bp.route("/personaggi/<int:personaggio_id>/consigli")
def consigli_personaggio(personaggio_id):
    """Mostra i consigli per un personaggio, analizzando la build attiva."""
    personaggio = db.leggi_personaggio_per_id(personaggio_id)
    if personaggio is None:
        flash("Personaggio non trovato.", "errore")
        return redirect(url_for("main.personaggi"))
    consigli = db.leggi_consigli_personaggio(personaggio_id)
    build_attiva = db.leggi_build_attiva_personaggio(personaggio_id)

    # Analisi dei dati mancanti nella build attiva
    dati_mancanti = []
    if build_attiva:
        if not build_attiva.get("abilita"):
            dati_mancanti.append("Abilità")
        if not build_attiva.get("equipaggiamento"):
            dati_mancanti.append("Equipaggiamento")
        if not build_attiva.get("aspetti_leggendari"):
            dati_mancanti.append("Aspetti leggendari")
        if not build_attiva.get("tempra"):
            dati_mancanti.append("Tempra")
        if not build_attiva.get("paragon"):
            dati_mancanti.append("Paragon e glifi")
    else:
        dati_mancanti.append("Nessuna build attiva definita")

    return render_template(
        "consigli.html",
        personaggio=personaggio,
        consigli=consigli,
        build_attiva=build_attiva,
        dati_mancanti=dati_mancanti,
    )


@bp.route("/personaggi/<int:personaggio_id>/consigli/nuovo", methods=["POST"])
def nuovo_consiglio(personaggio_id):
    """Aggiunge un consiglio per un personaggio."""
    try:
        db.aggiungi_consiglio(
            personaggio_id=personaggio_id,
            build_id=None,
            tipo=request.form.get("tipo", "").strip(),
            contenuto=request.form.get("contenuto", "").strip(),
            fonte=request.form.get("fonte", "").strip() or None,
            data_verifica=request.form.get("data_verifica", "").strip() or None,
            stato=request.form.get("stato", "da_verificare").strip(),
        )
        flash("Consiglio aggiunto con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'aggiunta: {e}", "errore")
    return redirect(url_for("main.consigli_personaggio", personaggio_id=personaggio_id))


# ============================================================================
# TASK D085 — ROUTE GESTIONE ABILITÀ-NELLE-BUILD
# ============================================================================

@bp.route(
    "/build_versioni/<int:build_versione_id>/abilita/aggiungi",
    methods=["POST"],
)
def aggiungi_abilita_build_versione(build_versione_id):
    """Aggiunge un'abilità a una versione della build."""
    try:
        db.inizializza_storico_abilita_build()
        risultato = db.aggiungi_abilita_a_build_versione(
            conn=None,
            build_versione_id=build_versione_id,
            abilita_id=int(request.form.get("abilita_id")),
            abilita_versioni_id=int(request.form.get("abilita_versioni_id")),
            livello=int(request.form.get("livello", 1)),
            nota=request.form.get("nota", "").strip() or None,
            utente="sistema",
            motivo="Aggiunta abilità via interfaccia web",
        )
        flash(
            f"Abilità aggiunta (esito temporale: {risultato['esito_temporale']}).",
            "successo",
        )
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'aggiunta: {e}", "errore")

    bv = db.leggi_build_versione_per_id(build_versione_id) if hasattr(db, 'leggi_build_versione_per_id') else None
    if bv:
        return redirect(url_for("main.lista_build", personaggio_id=bv.get("personaggio_id", 0)))
    flash("Versione build non trovata.", "errore")
    return redirect(url_for("main.index"))


@bp.route(
    "/build_versioni_abilita/<int:associazione_id>/modifica",
    methods=["POST"],
)
def modifica_abilita_build_versione_route(associazione_id):
    """Modifica livello e nota di un'associazione abilità-build."""
    personaggio_id = db.leggi_personaggio_id_da_associazione_abilita(associazione_id)
    try:
        db.inizializza_storico_abilita_build()
        db.modifica_abilita_build_versione(
            conn=None,
            associazione_id=associazione_id,
            livello=int(request.form.get("livello")) if request.form.get("livello") else None,
            nota=request.form.get("nota", "").strip() or None,
            utente="sistema",
            motivo="Modifica abilità via interfaccia web",
        )
        flash("Abilità aggiornata con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la modifica: {e}", "errore")
    if personaggio_id:
        return redirect(url_for("main.lista_build", personaggio_id=personaggio_id))
    return redirect(url_for("main.index"))


@bp.route(
    "/build_versioni_abilita/<int:associazione_id>/rimuovi",
    methods=["POST"],
)
def rimuovi_abilita_build_versione_route(associazione_id):
    """Rimuove un'associazione abilità-build."""
    personaggio_id = db.leggi_personaggio_id_da_associazione_abilita(associazione_id)
    try:
        db.inizializza_storico_abilita_build()
        db.rimuovi_abilita_da_build_versione(
            conn=None,
            associazione_id=associazione_id,
            utente="sistema",
            motivo="Rimozione abilità via interfaccia web",
        )
        flash("Abilità rimossa con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la rimozione: {e}", "errore")
    if personaggio_id:
        return redirect(url_for("main.lista_build", personaggio_id=personaggio_id))
    return redirect(url_for("main.index"))


# ============================================================================
# TASK D087b — PAGINA DEDICATA GESTIONE ABILITÀ
# ============================================================================

@bp.route(
    "/build_versioni/<int:build_versione_id>/abilita",
    methods=["GET"],
)
def gestione_abilita_build_versione(build_versione_id):
    """Pagina dedicata alla gestione delle abilità di una versione build."""
    db.inizializza_build()
    db.inizializza_storico_abilita_build()

    bv = db.leggi_build_versione_per_id(build_versione_id)
    if bv is None:
        flash("Versione build non trovata.", "errore")
        return redirect(url_for("main.index"))

    personaggio_id = bv["personaggio_id"]

    conn = db.get_conn()
    try:
        abilita_list = db.leggi_abilita_di_build_versione(conn, build_versione_id)
    finally:
        conn.close()

    classi = db.leggi_classi()
    abilita_per_classe = {}
    for c in classi:
        abilita_per_classe[c["id"]] = db.leggi_abilita_per_classe(c["id"])

    return render_template(
        "build_abilita.html",
        build_versione=bv,
        personaggio_id=personaggio_id,
        abilita_list=abilita_list,
        classi=classi,
        abilita_per_classe=abilita_per_classe,
    )


# ============================================================================
# TASK D087 — API PER CARICAMENTO VERSIONI ABILITÀ
# ============================================================================

@bp.route("/api/abilita/<int:abilita_id>/versioni", methods=["GET"])
def api_abilita_versioni(abilita_id):
    """Restituisce le versioni storiche di un'abilità in formato JSON."""
    try:
        versioni = db.leggi_abilita_versioni_per_abilita(abilita_id)
        return {
            "versioni": [
                {
                    "id": v["id"],
                    "descrizione": v["descrizione"] or "",
                    "stato": v["stato"],
                    "tipo": v["tipo"],
                }
                for v in versioni
            ]
        }
    except Exception as e:
        return {"error": str(e)}, 500


# ============================================================================
# TASK D123 — GESTIONE EQUIPAGGIAMENTO BUILD PERSONALE
# ============================================================================

@bp.route("/build_versioni/<int:build_versione_id>/equipaggiamento", methods=["GET"])
def gestione_equipaggiamento_build_versione(build_versione_id):
    """Pagina gestione equipaggiamento di una versione build personale."""
    db.inizializza_build()
    bv = db.leggi_build_versione_per_id(build_versione_id)
    if bv is None:
        flash("Versione build non trovata.", "errore")
        return redirect(url_for("main.index"))

    personaggio_id = bv["personaggio_id"]
    conn = db.get_conn()
    try:
        db.inizializza_slot_build_versione(conn, build_versione_id)
        slot_list = db.leggi_slot_di_build_versioni(conn, build_versione_id)
        oggetti = db.leggi_oggetti_catalogo()
    finally:
        conn.close()

    return render_template(
        "equipaggiamento.html",
        build_versione=bv,
        personaggio_id=personaggio_id,
        slot_list=slot_list,
        oggetti=oggetti,
    )


@bp.route("/build_versioni/<int:build_versione_id>/equipaggiamento/associa", methods=["POST"])
def associa_oggetto_build_versione(build_versione_id):
    """Associa o sostituisce l'oggetto di uno slot."""
    try:
        conn = db.get_conn()
        try:
            associazione_id = db.associa_oggetto_a_slot(
                conn=conn,
                build_versione_id=build_versione_id,
                slot_id=int(request.form.get("slot_id")),
                oggetto_id=int(request.form.get("oggetto_id")) if request.form.get("oggetto_id") else None,
                stato_slot=request.form.get("stato_slot", "mancante").strip() or "mancante",
            )
            flash("Oggetto associato allo slot.", "successo")
        finally:
            conn.close()
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'associazione: {e}", "errore")
    return redirect(url_for("main.gestione_equipaggiamento_build_versione", build_versione_id=build_versione_id))


@bp.route("/build_versioni/<int:build_versione_id>/equipaggiamento/<int:associazione_id>/rimuovi", methods=["POST"])
def rimuovi_oggetto_build_versione(build_versione_id, associazione_id):
    """Rimuove l'oggetto da uno slot."""
    try:
        conn = db.get_conn()
        try:
            db.rimuovi_oggetto_da_slot(conn=conn, associazione_id=associazione_id)
            flash("Oggetto rimosso dallo slot.", "successo")
        finally:
            conn.close()
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la rimozione: {e}", "errore")
    return redirect(url_for("main.gestione_equipaggiamento_build_versione", build_versione_id=build_versione_id))


@bp.route("/build_versioni/<int:build_versione_id>/equipaggiamento/<int:associazione_id>/dettaglio", methods=["POST"])
def aggiungi_dettaglio_build_versione(build_versione_id, associazione_id):
    """Aggiunge un dettaglio (aspetto/affisso/tempra) a uno slot."""
    tipo_dettaglio = request.form.get("tipo_dettaglio", "").strip()
    dati = {}
    if tipo_dettaglio == "aspetto":
        dati = {
            "nome_aspetto": request.form.get("nome_aspetto", "").strip(),
            "tipo_aspetto": request.form.get("tipo_aspetto", "").strip(),
            "verificato": request.form.get("verificato") == "1",
        }
    elif tipo_dettaglio == "affisso":
        dati = {
            "nome_affisso": request.form.get("nome_affisso", "").strip(),
            "valore_affisso": request.form.get("valore_affisso", "").strip(),
            "livello_affisso": int(request.form.get("livello_affisso")) if request.form.get("livello_affisso") else None,
            "verificato": request.form.get("verificato") == "1",
        }
    elif tipo_dettaglio == "tempra":
        dati = {
            "tipo_tempra": request.form.get("tipo_tempra", "").strip(),
            "livello_tempra": int(request.form.get("livello_tempra")) if request.form.get("livello_tempra") else None,
            "verificato": request.form.get("verificato") == "1",
        }
    else:
        flash("Tipo dettaglio non valido.", "errore")
        return redirect(url_for("main.gestione_equipaggiamento_build_versione", build_versione_id=build_versione_id))

    try:
        conn = db.get_conn()
        try:
            db.aggiungi_dettaglio_slot(
                conn=conn,
                associazione_id=associazione_id,
                tipo_dettaglio=tipo_dettaglio,
                dati=dati,
            )
            flash(f"Dettaglio {tipo_dettaglio} aggiunto.", "successo")
        finally:
            conn.close()
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'aggiunta del dettaglio: {e}", "errore")
    return redirect(url_for("main.gestione_equipaggiamento_build_versione", build_versione_id=build_versione_id))


@bp.route(
    "/build_versioni/<int:build_versione_id>/equipaggiamento/<int:associazione_id>/dettaglio/<int:dettaglio_id>/rimuovi/<tipo_dettaglio>",
    methods=["POST"],
)
def rimuovi_dettaglio_build_versione(build_versione_id, associazione_id, dettaglio_id, tipo_dettaglio):
    """Rimuove un singolo dettaglio (aspetto/affisso/tempra) da uno slot."""
    if tipo_dettaglio not in ("aspetto", "affisso", "tempra"):
        flash("Tipo dettaglio non valido.", "errore")
        return redirect(url_for("main.gestione_equipaggiamento_build_versione", build_versione_id=build_versione_id))

    try:
        conn = db.get_conn()
        try:
            db.rimuovi_dettaglio_slot(
                conn=conn,
                dettaglio_id=dettaglio_id,
                tipo_dettaglio=tipo_dettaglio,
                associazione_id=associazione_id,
            )
            flash(f"Dettaglio {tipo_dettaglio} rimosso.", "successo")
        finally:
            conn.close()
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la rimozione del dettaglio: {e}", "errore")
    return redirect(url_for("main.gestione_equipaggiamento_build_versione", build_versione_id=build_versione_id))


# ============================================================================
# TASK D127 — GESTIONE CATALOGO OGGETTI
# ============================================================================

@bp.route("/catalogo/oggetti", methods=["GET"])
def lista_oggetti():
    """Lista oggetti del catalogo Diablo 4."""
    db.inizializza_catalogo()
    oggetti = db.leggi_oggetti_catalogo()
    return render_template("oggetti.html", oggetti=oggetti)


@bp.route("/catalogo/oggetti/nuovo", methods=["POST"])
def nuovo_oggetto():
    """Inserisce un nuovo oggetto nel catalogo."""
    try:
        db.inserisci_oggetto(
            nome_oggetto=request.form.get("nome_oggetto", "").strip(),
            tipo_oggetto=request.form.get("tipo_oggetto", "").strip() or None,
            livello_oggetto=int(request.form.get("livello_oggetto")) if request.form.get("livello_oggetto") else None,
            fonte=request.form.get("fonte", "").strip() or None,
            verificato=request.form.get("verificato") == "1",
        )
        flash("Oggetto inserito con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'inserimento: {e}", "errore")
    return redirect(url_for("main.lista_oggetti"))


@bp.route("/catalogo/oggetti/<int:oggetto_id>/modifica", methods=["POST"])
def modifica_oggetto_route(oggetto_id):
    """Modifica un oggetto esistente del catalogo."""
    try:
        db.modifica_oggetto(
            oggetto_id=oggetto_id,
            nome_oggetto=request.form.get("nome_oggetto", "").strip() or None,
            tipo_oggetto=request.form.get("tipo_oggetto", "").strip() or None,
            livello_oggetto=int(request.form.get("livello_oggetto")) if request.form.get("livello_oggetto") else None,
            fonte=request.form.get("fonte", "").strip() or None,
            verificato=request.form.get("verificato") == "1",
        )
        flash("Oggetto aggiornato con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la modifica: {e}", "errore")
    return redirect(url_for("main.lista_oggetti"))


@bp.route("/catalogo/oggetti/<int:oggetto_id>/rimuovi", methods=["POST"])
def rimuovi_oggetto_route(oggetto_id):
    """Rimuove un oggetto dal catalogo se non utilizzato in build."""
    try:
        db.rimuovi_oggetto(oggetto_id)
        flash("Oggetto rimosso con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la rimozione: {e}", "errore")
    return redirect(url_for("main.lista_oggetti"))


# ============================================================================
# TASK D130 — GESTIONE CATALOGO ABILITÀ
# ============================================================================

@bp.route("/catalogo/abilita", methods=["GET"])
def lista_abilita():
    """Lista abilità del catalogo Diablo 4."""
    db.inizializza_catalogo()
    abilita = db.leggi_abilita_catalogo()
    classi = db.leggi_classi()
    return render_template("catalogo_abilita.html", abilita=abilita, classi=classi)


@bp.route("/catalogo/abilita/nuovo", methods=["POST"])
def nuovo_abilita():
    """Inserisce una nuova abilità nel catalogo."""
    try:
        db.inserisci_abilita(
            classe_id=int(request.form.get("classe_id")),
            nome=request.form.get("nome", "").strip(),
            codice_identificativo=request.form.get("codice_identificativo", "").strip(),
        )
        flash("Abilità inserita con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'inserimento: {e}", "errore")
    return redirect(url_for("main.lista_abilita"))


@bp.route("/catalogo/abilita/<int:abilita_id>/modifica", methods=["POST"])
def modifica_abilita_route(abilita_id):
    """Modifica un'abilità esistente del catalogo."""
    try:
        db.modifica_abilita(
            abilita_id=abilita_id,
            nome=request.form.get("nome", "").strip() or None,
            codice_identificativo=request.form.get("codice_identificativo", "").strip() or None,
            classe_id=int(request.form.get("classe_id")) if request.form.get("classe_id") else None,
        )
        flash("Abilità aggiornata con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la modifica: {e}", "errore")
    return redirect(url_for("main.lista_abilita"))


@bp.route("/catalogo/abilita/<int:abilita_id>/rimuovi", methods=["POST"])
def rimuovi_abilita_route(abilita_id):
    """Rimuove un'abilità dal catalogo se non ha versioni né associazioni."""
    try:
        db.rimuovi_abilita(abilita_id)
        flash("Abilità rimossa con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la rimozione: {e}", "errore")
    return redirect(url_for("main.lista_abilita"))


@bp.route("/catalogo/abilita/<int:abilita_id>/versioni/nuovo", methods=["POST"])
def nuovo_abilita_versioni(abilita_id):
    """Aggiunge una versione storica a un'abilità."""
    try:
        db.inserisci_abilita_versioni(
            abilita_id=abilita_id,
            patch_id=int(request.form.get("patch_id")) if request.form.get("patch_id") else None,
            stagione_id=int(request.form.get("stagione_id")) if request.form.get("stagione_id") else None,
            tipo=request.form.get("tipo", "").strip(),
            descrizione=request.form.get("descrizione", "").strip() or None,
            livello_sblocco=int(request.form.get("livello_sblocco")) if request.form.get("livello_sblocco") else None,
            fonte_id=int(request.form.get("fonte_id")) if request.form.get("fonte_id") else None,
            data_verifica=request.form.get("data_verifica", "").strip() or None,
            stato=request.form.get("stato", "da_verificare").strip(),
            versione_corrente=request.form.get("versione_corrente") == "1",
        )
        flash("Versione abilità inserita con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante l'inserimento: {e}", "errore")
    return redirect(url_for("main.lista_abilita"))


@bp.route("/catalogo/abilita/versioni/<int:versione_id>/modifica", methods=["POST"])
def modifica_abilita_versioni_route(versione_id):
    """Modifica una versione storica di abilità."""
    try:
        db.modifica_abilita_versioni(
            versione_id=versione_id,
            patch_id=int(request.form.get("patch_id")) if request.form.get("patch_id") else None,
            stagione_id=int(request.form.get("stagione_id")) if request.form.get("stagione_id") else None,
            tipo=request.form.get("tipo", "").strip() or None,
            descrizione=request.form.get("descrizione", "").strip() or None,
            livello_sblocco=int(request.form.get("livello_sblocco")) if request.form.get("livello_sblocco") else None,
            fonte_id=int(request.form.get("fonte_id")) if request.form.get("fonte_id") else None,
            data_verifica=request.form.get("data_verifica", "").strip() or None,
            stato=request.form.get("stato", "").strip() or None,
            versione_corrente=request.form.get("versione_corrente") == "1",
        )
        flash("Versione abilità aggiornata con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la modifica: {e}", "errore")
    return redirect(url_for("main.lista_abilita"))


@bp.route("/catalogo/abilita/versioni/<int:versione_id>/rimuovi", methods=["POST"])
def rimuovi_abilita_versioni_route(versione_id):
    """Rimuove una versione storica di abilità se non usata in build."""
    try:
        db.rimuovi_abilita_versioni(versione_id)
        flash("Versione abilità rimossa con successo.", "successo")
    except ValueError as e:
        flash(str(e), "errore")
    except Exception as e:
        flash(f"Errore durante la rimozione: {e}", "errore")
    return redirect(url_for("main.lista_abilita"))