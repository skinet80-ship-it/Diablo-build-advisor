import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "diablo.db")


def get_conn(db_path=None):
    """Apre una connessione al database SQLite con chiavi esterne attive.
    
    Se db_path è fornito, lo usa al posto di DB_PATH (utile per test su database temporanei).
    """
    path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Converte una riga SQLite in dizionario."""
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def verifica_database():
    """Restituisce la lista delle tabelle presenti nel database."""
    conn = get_conn()
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def inizializza_database():
    """Crea le tabelle necessarie se non esistono, inclusa la tabella personaggi."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS personaggi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                classe TEXT NOT NULL,
                modalita TEXT NOT NULL CHECK (modalita IN ('Eterno', 'Stagionale')),
                numero_stagione INTEGER,
                livello_personaggio INTEGER NOT NULL CHECK (livello_personaggio BETWEEN 1 AND 60),
                livello_paragon INTEGER NOT NULL DEFAULT 0,
                obiettivo TEXT,
                note TEXT,
                data_creazione TEXT NOT NULL,
                data_modifica TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                versione INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            "INSERT OR IGNORE INTO schema_version (id, versione) VALUES (1, 1)"
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def crea_personaggio(
    nome,
    classe,
    modalita,
    numero_stagione=None,
    livello_personaggio=1,
    livello_paragon=0,
    obiettivo=None,
    note=None,
):
    """Crea un nuovo personaggio e restituisce il suo id."""
    from datetime import datetime

    adesso = datetime.now().isoformat()
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO personaggi
            (nome, classe, modalita, numero_stagione, livello_personaggio,
             livello_paragon, obiettivo, note, data_creazione, data_modifica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome,
                classe,
                modalita,
                numero_stagione,
                livello_personaggio,
                livello_paragon,
                obiettivo,
                note,
                adesso,
                adesso,
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def leggi_personaggi():
    """Restituisce tutti i personaggi ordinati per data di modifica decrescente."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, nome, classe, modalita, numero_stagione,
                   livello_personaggio, livello_paragon, obiettivo, note,
                   data_creazione, data_modifica
            FROM personaggi
            ORDER BY data_modifica DESC
            """
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_personaggio_per_id(personaggio_id):
    """Restituisce un personaggio per id, o None se non esiste."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, nome, classe, modalita, numero_stagione,
                   livello_personaggio, livello_paragon, obiettivo, note,
                   data_creazione, data_modifica
            FROM personaggi
            WHERE id = ?
            """,
            (personaggio_id,),
        )
        r = cur.fetchone()
        return dict_from_row(r)
    finally:
        conn.close()


def modifica_personaggio(
    personaggio_id,
    nome,
    classe,
    modalita,
    numero_stagione=None,
    livello_personaggio=1,
    livello_paragon=0,
    obiettivo=None,
    note=None,
):
    """Modifica un personaggio esistente. Solleva ValueError se non esiste."""
    from datetime import datetime

    adesso = datetime.now().isoformat()
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE personaggi
            SET nome = ?, classe = ?, modalita = ?, numero_stagione = ?,
                livello_personaggio = ?, livello_paragon = ?,
                obiettivo = ?, note = ?, data_modifica = ?
            WHERE id = ?
            """,
            (
                nome,
                classe,
                modalita,
                numero_stagione,
                livello_personaggio,
                livello_paragon,
                obiettivo,
                note,
                adesso,
                personaggio_id,
            ),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Personaggio con id {personaggio_id} non trovato.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def elimina_personaggio(personaggio_id):
    """Elimina un personaggio con audit pre-CASCADE."""
    return elimina_personaggio_con_audit(personaggio_id)


def inizializza_consigli_stagioni():
    """Crea le tabelle per consigli build e stagioni se non esistono."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS consigli (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personaggio_id INTEGER,
                build_id INTEGER,
                tipo TEXT NOT NULL CHECK (tipo IN ('abilita', 'equipaggiamento', 'aspetti_leggendari', 'tempra', 'paragon', 'generale')),
                contenuto TEXT NOT NULL,
                fonte TEXT,
                data_verifica TEXT,
                stato TEXT NOT NULL CHECK (stato IN ('verificata', 'da_verificare', 'obsoleta')),
                data_creazione TEXT NOT NULL,
                FOREIGN KEY (personaggio_id) REFERENCES personaggi(id) ON DELETE CASCADE,
                FOREIGN KEY (build_id) REFERENCES build(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stagioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER NOT NULL,
                nome TEXT NOT NULL,
                stato_attivo INTEGER NOT NULL DEFAULT 0,
                meccaniche TEXT,
                note TEXT,
                fonte TEXT,
                data_verifica TEXT,
                stato TEXT NOT NULL CHECK (stato IN ('verificata', 'da_verificare', 'obsoleta'))
            )
            """
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def aggiungi_consiglio(personaggio_id, build_id, tipo, contenuto, fonte, data_verifica, stato):
    """Aggiunge un consiglio per un personaggio o una build."""
    from datetime import datetime
    adesso = datetime.now().isoformat()
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO consigli
            (personaggio_id, build_id, tipo, contenuto, fonte, data_verifica, stato, data_creazione)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (personaggio_id, build_id, tipo, contenuto, fonte, data_verifica, stato, adesso),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def leggi_consigli_personaggio(personaggio_id):
    """Restituisce tutti i consigli di un personaggio."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, personaggio_id, build_id, tipo, contenuto, fonte, data_verifica, stato, data_creazione
            FROM consigli
            WHERE personaggio_id = ?
            ORDER BY data_creazione DESC
            """,
            (personaggio_id,),
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_consigli_build(build_id):
    """Restituisce tutti i consigli di una build."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, personaggio_id, build_id, tipo, contenuto, fonte, data_verifica, stato, data_creazione
            FROM consigli
            WHERE build_id = ?
            ORDER BY data_creazione DESC
            """,
            (build_id,),
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def inizializza_stagioni():
    """Crea la tabella stagioni se non esiste. Nessun dato di esempio inserito."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stagioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER NOT NULL,
                nome TEXT NOT NULL,
                stato_attivo INTEGER NOT NULL DEFAULT 0,
                meccaniche TEXT,
                note TEXT,
                fonte TEXT,
                data_verifica TEXT,
                stato TEXT NOT NULL CHECK (stato IN ('verificata', 'da_verificare', 'obsoleta'))
            )
            """
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def leggi_build_attiva_personaggio(personaggio_id):
    """Restituisce la build attiva di un personaggio, o None se non ce n'è una."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, personaggio_id, nome_build, obiettivo, abilita, equipaggiamento,
                   aspetti_leggendari, tempra, paragon, note,
                   build_attiva, data_creazione, data_modifica
            FROM build
            WHERE personaggio_id = ? AND build_attiva = 1
            ORDER BY data_creazione DESC
            LIMIT 1
            """,
            (personaggio_id,),
        )
        r = cur.fetchone()
        return dict_from_row(r)
    finally:
        conn.close()


def leggi_stagioni():
    """Restituisce tutte le stagioni."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, numero, nome, stato_attivo, meccaniche, note, fonte, data_verifica, stato
            FROM stagioni
            ORDER BY numero DESC
            """
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_stagione_attiva():
    """Restituisce la stagione attiva, o None se non ce n'è una."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, numero, nome, stato_attivo, meccaniche, note, fonte, data_verifica, stato
            FROM stagioni
            WHERE stato_attivo = 1
            LIMIT 1
            """
        )
        r = cur.fetchone()
        return dict_from_row(r)
    finally:
        conn.close()


def inizializza_build():
    """Crea la tabella build se non esiste."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS build (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personaggio_id INTEGER NOT NULL,
                nome_build TEXT NOT NULL,
                obiettivo TEXT,
                abilita TEXT,
                equipaggiamento TEXT,
                aspetti_leggendari TEXT,
                tempra TEXT,
                paragon TEXT,
                note TEXT,
                build_attiva INTEGER NOT NULL DEFAULT 0,
                data_creazione TEXT NOT NULL,
                data_modifica TEXT NOT NULL,
                FOREIGN KEY (personaggio_id) REFERENCES personaggi(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def crea_build(
    personaggio_id,
    nome_build,
    obiettivo=None,
    abilita=None,
    equipaggiamento=None,
    aspetti_leggendari=None,
    tempra=None,
    paragon=None,
    note=None,
    build_attiva=False,
    conn=None,
):
    """Crea una nuova build per un personaggio. Se build_attiva=True, disattiva le altre build dello stesso personaggio."""
    from datetime import datetime

    adesso = datetime.now().isoformat()
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        cur = conn.cursor()
        # Se la nuova build è attiva, disattiva le altre dello stesso personaggio
        if build_attiva:
            cur.execute(
                "UPDATE build SET build_attiva = 0 WHERE personaggio_id = ?",
                (personaggio_id,),
            )
        cur.execute(
            """
            INSERT INTO build
            (personaggio_id, nome_build, obiettivo, abilita, equipaggiamento,
             aspetti_leggendari, tempra, paragon, note, build_attiva,
             data_creazione, data_modifica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                personaggio_id,
                nome_build,
                obiettivo,
                abilita,
                equipaggiamento,
                aspetti_leggendari,
                tempra,
                paragon,
                note,
                1 if build_attiva else 0,
                adesso,
                adesso,
            ),
        )
        if conn_creata_da_noi:
            conn.commit()
        return cur.lastrowid
    except Exception:
        if conn_creata_da_noi:
            conn.rollback()
        raise
    finally:
        if conn_creata_da_noi:
            conn.close()


def leggi_build_personaggio(personaggio_id):
    """Restituisce tutte le build di un personaggio, con quella attiva per prima."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, personaggio_id, nome_build, obiettivo, abilita, equipaggiamento,
                   aspetti_leggendari, tempra, paragon, note,
                   build_attiva, data_creazione, data_modifica
            FROM build
            WHERE personaggio_id = ?
            ORDER BY build_attiva DESC, data_creazione DESC
            """,
            (personaggio_id,),
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_build_per_id(build_id):
    """Restituisce una build per id, o None se non esiste."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, personaggio_id, nome_build, obiettivo, abilita, equipaggiamento,
                   aspetti_leggendari, tempra, paragon, note,
                   build_attiva, data_creazione, data_modifica
            FROM build
            WHERE id = ?
            """,
            (build_id,),
        )
        r = cur.fetchone()
        return dict_from_row(r)
    finally:
        conn.close()


def modifica_build(
    build_id,
    nome_build,
    obiettivo=None,
    abilita=None,
    equipaggiamento=None,
    aspetti_leggendari=None,
    tempra=None,
    paragon=None,
    note=None,
    build_attiva=False,
):
    """Modifica una build esistente. Se build_attiva=True, disattiva le altre build dello stesso personaggio."""
    from datetime import datetime

    adesso = datetime.now().isoformat()
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Recupera il personaggio_id della build
        cur.execute("SELECT personaggio_id FROM build WHERE id = ?", (build_id,))
        r = cur.fetchone()
        if r is None:
            raise ValueError(f"Build con id {build_id} non trovata.")
        personaggio_id = r[0]

        # Se attiva, disattiva le altre
        if build_attiva:
            cur.execute(
                "UPDATE build SET build_attiva = 0 WHERE personaggio_id = ? AND id != ?",
                (personaggio_id, build_id),
            )

        cur.execute(
            """
            UPDATE build
            SET nome_build = ?, obiettivo = ?, abilita = ?, equipaggiamento = ?,
                aspetti_leggendari = ?, tempra = ?, paragon = ?, note = ?,
                build_attiva = ?, data_modifica = ?
            WHERE id = ?
            """,
            (
                nome_build,
                obiettivo,
                abilita,
                equipaggiamento,
                aspetti_leggendari,
                tempra,
                paragon,
                note,
                1 if build_attiva else 0,
                adesso,
                build_id,
            ),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Build con id {build_id} non trovata.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def elimina_build(build_id):
    """Elimina una build con audit pre-CASCADE."""
    return elimina_build_con_audit(build_id)


def crea_build_con_base_protetta(
    personaggio_id,
    nome_build,
    obiettivo=None,
    abilita=None,
    equipaggiamento=None,
    aspetti_leggendari=None,
    tempra=None,
    paragon=None,
    note=None,
    build_attiva=False,
):
    """
    Crea una build personale e il relativo record build_base in un'unica transazione atomica.
    La classe viene derivata esclusivamente dal personaggio collegato.

    Parametri:
    - personaggio_id: id del personaggio proprietario
    - nome_build, obiettivo, abilita, equipaggiamento, aspetti_leggendari,
      tempra, paragon, note: campi della build
    - build_attiva: booleano

    Returns:
        tuple (build_id, build_base_id)

    Raises:
        ValueError: personaggio inesistente, classe non riconosciuta, origine duplicata
        RuntimeError: errore di transazione o database
    """
    conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            # 1. Verifica esistenza personaggio
            cur.execute("SELECT id FROM personaggi WHERE id = ?", (personaggio_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Personaggio con id {personaggio_id} non trovato.")

            # 2. Crea la build (usa conn già aperta, nessun commit autonomo)
            build_id = crea_build(
                personaggio_id=personaggio_id,
                nome_build=nome_build,
                obiettivo=obiettivo,
                abilita=abilita,
                equipaggiamento=equipaggiamento,
                aspetti_leggendari=aspetti_leggendari,
                tempra=tempra,
                paragon=paragon,
                note=note,
                build_attiva=build_attiva,
                conn=conn,
            )

            # 3. Crea la build_base (classe derivata esclusivamente dall'origine)
            build_base_id = crea_build_base_protetta(
                conn=conn,
                origine_tipo="personale",
                origine_id=build_id,
            )

            return build_id, build_base_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def crea_build_base_protetta(conn, origine_tipo, origine_id):
    """
    Crea una riga in build_base con verifica di coerenza classe ↔ origine.

    La classe viene ricavata esclusivamente dall'origine, mai accettata
    come parametro dal chiamante.

    Parametri:
    - conn: connessione SQLite attiva
    - origine_tipo: 'personale' o 'esterna'
    - origine_id: id del record di origine (build o build_esterna)

    Returns:
        id della nuova riga in build_base

    Raises:
        ValueError: origine_tipo non valido, origine inesistente,
                    classe non trovata, origine duplicata.
        RuntimeError: errore di database o transazione.
    """
    if origine_tipo not in ("personale", "esterna"):
        raise ValueError(
            f"origine_tipo non valido: '{origine_tipo}'. "
            f"Valori ammessi: 'personale', 'esterna'."
        )

    with transazione_sqlite(conn) as cur:
        if origine_tipo == "personale":
            # Verifica che la build personale esista
            cur.execute("SELECT id, personaggio_id FROM build WHERE id = ?", (origine_id,))
            riga_build = cur.fetchone()
            if riga_build is None:
                raise ValueError(f"Build personale con id {origine_id} non trovata.")
            personaggio_id = riga_build[1]

            # Recupera la classe testuale del personaggio
            cur.execute(
                "SELECT classe FROM personaggi WHERE id = ?", (personaggio_id,)
            )
            riga_personaggio = cur.fetchone()
            if riga_personaggio is None:
                raise ValueError(
                    f"Personaggio con id {personaggio_id} non trovato per la build {origine_id}."
                )
            classe_testo = riga_personaggio[0]

            # Mappa la classe testuale al catalogo classi
            classe_id = mappa_classe_personaggio_a_id(conn, classe_testo)

            build_personale_id = origine_id
            build_esterna_id = None

        else:  # origine_tipo == "esterna"
            # Verifica che la build esterna esista
            cur.execute(
                "SELECT id, classe_id FROM build_esterna WHERE id = ?", (origine_id,)
            )
            riga_esterna = cur.fetchone()
            if riga_esterna is None:
                raise ValueError(f"Build esterna con id {origine_id} non trovata.")
            classe_id = riga_esterna[1]

            # Verifica che la classe della build esterna sia valida (esista in classi)
            cur.execute("SELECT id FROM classi WHERE id = ?", (classe_id,))
            if cur.fetchone() is None:
                raise ValueError(
                    f"La classe_id {classe_id} della build esterna {origine_id} "
                    f"non esiste nel catalogo classi."
                )

            build_personale_id = None
            build_esterna_id = origine_id

        # Verifica che non esista già una build_base per questa origine
        if origine_tipo == "personale":
            cur.execute(
                "SELECT id FROM build_base WHERE build_personale_id = ?",
                (origine_id,),
            )
        else:
            cur.execute(
                "SELECT id FROM build_base WHERE build_esterna_id = ?",
                (origine_id,),
            )
        if cur.fetchone() is not None:
            raise ValueError(
                f"Esiste già una build_base per l'origine {origine_tipo} con id {origine_id}."
            )

        adesso = datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO build_base
            (build_personale_id, build_esterna_id, classe_id, data_creazione)
            VALUES (?, ?, ?, ?)
            """,
            (build_personale_id, build_esterna_id, classe_id, adesso),
        )
        build_base_id = cur.lastrowid

        return build_base_id


def modifica_personaggio(
    personaggio_id,
    nome,
    classe,
    modalita,
    numero_stagione=None,
    livello_personaggio=1,
    livello_paragon=0,
    obiettivo=None,
    note=None,
    conn=None,
):
    """Modifica un personaggio esistente. Solleva ValueError se non esiste."""
    adesso = datetime.now().isoformat()
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM personaggi WHERE id = ?", (personaggio_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Personaggio con id {personaggio_id} non trovato.")

        # Protezione: se si modifica la classe, verificare coerenza con build_base collegate
        if classe is not None and classe.strip():
            nuova_classe = classe.strip()
            # Recupera tutte le build collegate al personaggio
            cur.execute(
                "SELECT id FROM build WHERE personaggio_id = ?", (personaggio_id,)
            )
            build_righe = cur.fetchall()

            for riga_build in build_righe:
                build_id = riga_build[0]
                # Verifica se esiste una build_base collegata a questa build
                cur.execute(
                    "SELECT id, classe_id FROM build_base WHERE build_personale_id = ?",
                    (build_id,),
                )
                riga_base = cur.fetchone()
                if riga_base is not None:
                    build_base_id = riga_base[0]
                    classe_id_base = riga_base[1]
                    # Mappa la nuova classe al catalogo
                    nuovo_classe_id = mappa_classe_personaggio_a_id(
                        conn, nuova_classe
                    )
                    if nuovo_classe_id != classe_id_base:
                        raise ValueError(
                            f"Impossibile modificare la classe del personaggio {personaggio_id}: "
                            f"la build_base {build_base_id} (collegata alla build {build_id}) "
                            f"ha classe_id={classe_id_base}, incompatibile con la nuova classe "
                            f"'{nuova_classe}' (classe_id={nuovo_classe_id}). "
                            f"Aggiornare prima le build collegate."
                        )

        cur.execute(
            """
            UPDATE personaggi
            SET nome = ?, classe = ?, modalita = ?, numero_stagione = ?,
                livello_personaggio = ?, livello_paragon = ?,
                obiettivo = ?, note = ?, data_modifica = ?
            WHERE id = ?
            """,
            (
                nome,
                classe,
                modalita,
                numero_stagione,
                livello_personaggio,
                livello_paragon,
                obiettivo,
                note,
                adesso,
                personaggio_id,
            ),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Personaggio con id {personaggio_id} non trovato.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        if conn_creata_da_noi:
            conn.close()


def inizializza_catalogo():
    """Crea le tabelle del catalogo Diablo 4 se non esistono.
    Nessun dato di gioco viene inserito automaticamente.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS classi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                fonte TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versione TEXT NOT NULL UNIQUE,
                data_rilascio TEXT,
                fonte TEXT,
                note TEXT,
                stato TEXT NOT NULL CHECK (stato IN ('verificata', 'da_verificare', 'obsoleta'))
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fonte_informativa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                url TEXT,
                tipologia TEXT NOT NULL CHECK (tipologia IN ('ufficiale', 'community')),
                affidabilita TEXT,
                note TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS slot_equipaggiamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                codice_slot TEXT NOT NULL UNIQUE
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS abilita (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                classe_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                codice_identificativo TEXT NOT NULL UNIQUE,
                FOREIGN KEY (classe_id) REFERENCES classi(id) ON DELETE CASCADE
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS abilita_versioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abilita_id INTEGER NOT NULL,
                patch_id INTEGER,
                stagione_id INTEGER,
                tipo TEXT NOT NULL CHECK (tipo IN ('attiva', 'passiva', 'definitiva')),
                descrizione TEXT,
                livello_sblocco INTEGER,
                fonte_id INTEGER,
                data_verifica TEXT,
                stato TEXT NOT NULL CHECK (stato IN ('verificata', 'da_verificare', 'obsoleta')),
                FOREIGN KEY (abilita_id) REFERENCES abilita(id) ON DELETE CASCADE,
                FOREIGN KEY (patch_id) REFERENCES patch(id),
                FOREIGN KEY (stagione_id) REFERENCES stagioni(id),
                FOREIGN KEY (fonte_id) REFERENCES fonte_informativa(id)
            )
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_abilita_classe ON abilita(classe_id)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_abilita_versioni_abilita ON abilita_versioni(abilita_id)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_abilita_versioni_patch ON abilita_versioni(patch_id)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_abilita_versioni_stagione ON abilita_versioni(stagione_id)
            """
        )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def leggi_classi():
    """Restituisce tutte le classi ordinate per nome."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, nome, slug, fonte
            FROM classi
            ORDER BY nome
            """
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_abilita_per_classe(classe_id):
    """Restituisce tutte le abilità di una classe con l'ultima versione nota."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT a.id, a.nome, a.codice_identificativo,
                   v.tipo, v.descrizione, v.livello_sblocco,
                   v.stato, v.data_verifica, p.versione AS patch_versione
            FROM abilita a
            LEFT JOIN abilita_versioni v ON v.abilita_id = a.id
            LEFT JOIN patch p ON v.patch_id = p.id
            WHERE a.classe_id = ?
            ORDER BY a.nome, v.data_verifica DESC
            """
            , (classe_id,)
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_patch():
    """Restituisce tutte le patch ordinate per versione decrescente."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, versione, data_rilascio, fonte, note, stato
            FROM patch
            ORDER BY versione DESC
            """
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_fonti():
    """Restituisce tutte le fonti informative."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, nome, url, tipologia, affidabilita, note
            FROM fonte_informativa
            ORDER BY nome
            """
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def leggi_slot_equipaggiamento():
    """Restituisce tutti gli slot di equipaggiamento."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, nome, codice_slot
            FROM slot_equipaggiamento
            ORDER BY nome
            """
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ============================================================================
# NUOVE FUNZIONI TRANSAZIONALI (TASK D037)
# ============================================================================

@contextmanager
def transazione_sqlite(conn):
    """
    Context manager per transazioni SQLite con supporto SAVEPOINT annidati.

    Se la connessione ha già una transazione aperta, crea un SAVEPOINT.
    Altrimenti inizia una transazione con BEGIN IMMEDIATE.

    Qualunque eccezione (incluso ValueError) provoca rollback prima di essere
    rilanciata con il suo tipo originale.
    """
    cur = conn.cursor()
    transazione_già_aperta = conn.in_transaction
    savepoint_name = None
    transazione_iniziata = False
    savepoint_creato = False

    try:
        if transazione_già_aperta:
            savepoint_name = f"sp_{id(cur)}"
            cur.execute(f"SAVEPOINT {savepoint_name}")
            savepoint_creato = True
        else:
            cur.execute("PRAGMA foreign_keys")
            if cur.fetchone()[0] != 1:
                raise RuntimeError("PRAGMA foreign_keys non attivo: impossibile iniziare transazione")
            cur.execute("BEGIN IMMEDIATE")
            transazione_iniziata = True

        yield cur

        # Successo
        if transazione_già_aperta:
            cur.execute(f"RELEASE SAVEPOINT {savepoint_name}")
        else:
            conn.commit()

    except BaseException as e:
        recupero_ok = True

        if transazione_già_aperta and savepoint_creato:
            try:
                cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                cur.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            except Exception as e_rec:
                recupero_ok = False
                raise RuntimeError(
                    f"Errore originale: {type(e).__name__}: {e}; "
                    f"errore durante il rollback del savepoint: {type(e_rec).__name__}: {e_rec}"
                ) from e
        elif transazione_iniziata:
            try:
                conn.rollback()
            except Exception as e_rec:
                recupero_ok = False
                raise RuntimeError(
                    f"Errore originale: {type(e).__name__}: {e}; "
                    f"errore durante il rollback della transazione: {type(e_rec).__name__}: {e_rec}"
                ) from e

        raise


def mappa_classe_personaggio_a_id(conn, nome_classe_personaggio):
    """
    Converte il nome della classe di un personaggio in un id classe esistente.

    Regole:
    - Confronto senza distinzione tra maiuscole e minuscole.
    - Elimina spazi iniziali e finali.
    - Conta gli ID di classe distinti (senza duplicare se nome e slug coincidono).
    - Solleva ValueError se non trova corrispondenze.
    - Solleva ValueError se trova più classi distinte.
    - Non crea automaticamente nuove classi.

    Parametri:
    - conn: connessione SQLite attiva
    - nome_classe_personaggio: nome classe dal personaggio (testo libero)

    Returns:
        classe_id: identificativo della classe nel catalogo

    Raises:
        ValueError: se non trova corrispondenza o se c'è ambiguità
    """
    if nome_classe_personaggio is None:
        raise ValueError("Il nome della classe non può essere None")

    nome_normalizzato = nome_classe_personaggio.strip().lower()

    if not nome_normalizzato:
        raise ValueError("Il nome della classe non può essere vuoto o solo spazi")

    cur = conn.cursor()
    cur.execute("SELECT id, nome, slug FROM classi")
    righe = cur.fetchall()

    corrispondenze = []
    for riga in righe:
        classe_id, nome_classe, slug_classe = riga
        if nome_classe.lower() == nome_normalizzato:
            corrispondenze.append((classe_id, nome_classe, slug_classe, "nome"))
        if slug_classe.lower() == nome_normalizzato:
            corrispondenze.append((classe_id, nome_classe, slug_classe, "slug"))

    # Deduplica per classe_id (se nome e slug coincidono, conta una sola volta)
    classi_distinte = {}
    for classe_id, nome_classe, slug_classe, tipo_match in corrispondenze:
        if classe_id not in classi_distinte:
            classi_distinte[classe_id] = (nome_classe, slug_classe)

    if len(classi_distinte) == 0:
        raise ValueError(f"Classe '{nome_classe_personaggio}' non trovata nel catalogo.")

    if len(classi_distinte) > 1:
        classi_nomi = ", ".join([f"{v[0]} ({v[1]})" for v in classi_distinte.values()])
        raise ValueError(
            f"Ambiguità: '{nome_classe_personaggio}' corrisponde a più classi: {classi_nomi}"
        )

    return list(classi_distinte.keys())[0]


def valida_abilita_per_build_versione(conn, build_versione_id, abilita_id):
    """
    Verifica che l'abilità appartenga alla stessa classe della build di origine
    della versione. Solleva ValueError se incompatibile o se i riferimenti
    non esistono. Non cancella né modifica automaticamente abilità.

    Parametri:
    - conn: connessione SQLite attiva
    - build_versione_id: id della versione di build
    - abilita_id: id dell'abilità da associare

    Returns:
        True se la validazione ha successo

    Raises:
        ValueError: se versione, build base o abilità non esistono,
                    o se le classi non coincidono
    """
    with transazione_sqlite(conn) as cur:
        # Recupera build_base_id dalla versione
        cur.execute("SELECT build_base_id FROM build_versioni WHERE id = ?", (build_versione_id,))
        riga = cur.fetchone()
        if riga is None:
            raise ValueError(f"Versione {build_versione_id} non trovata")
        build_base_id = riga[0]

        # Recupera classe_id dalla build base
        cur.execute("SELECT classe_id FROM build_base WHERE id = ?", (build_base_id,))
        riga = cur.fetchone()
        if riga is None:
            raise ValueError(f"Build base {build_base_id} non trovata")
        classe_id_build = riga[0]

        # Recupera classe_id dall'abilità
        cur.execute("SELECT classe_id FROM abilita WHERE id = ?", (abilita_id,))
        riga = cur.fetchone()
        if riga is None:
            raise ValueError(f"Abilità {abilita_id} non trovata")
        classe_id_abilita = riga[0]

        if classe_id_build != classe_id_abilita:
            raise ValueError(
                f"Incompatibilità classe: versione {build_versione_id} "
                f"(build_base.classe_id={classe_id_build}) non può usare "
                f"l'abilità {abilita_id} (abilita.classe_id={classe_id_abilita})"
            )

        return True


def aggiungi_versione_con_fonte(
    conn,
    build_id,
    nome_build,
    stagione_dichiarata,
    patch_dichiarata,
    stagione_id,
    patch_id,
    stato,
    fonte_id,
    fonte_url,
    autore,
    data_pubblicazione,
    data_verifica,
    note=None,
):
    """
    Inserisce una versione e la sua prima fonte in un'unica transazione SQLite.
    Se l'inserimento della fonte fallisce, la versione viene annullata.
    Nessuna versione può essere creata senza fonte.

    Parametri:
    - conn: connessione SQLite attiva
    - build_id: identificativo della build_base di riferimento
    - nome_build: nome della versione
    - stagione_dichiarata: stagione dichiarata dalla fonte (testo libero)
    - patch_dichiarata: patch dichiarata dalla fonte (testo libero)
    - stagione_id: FK verso stagioni (nullable)
    - patch_id: FK verso patch (nullable)
    - stato: 'verificata', 'da_verificare' o 'obsoleta'
    - fonte_id: FK verso fonte_informativa (obbligatorio)
    - fonte_url: URL della fonte
    - autore: autore della fonte
    - data_pubblicazione: data di pubblicazione della fonte
    - data_verifica: data di verifica della fonte
    - note: note opzionali

    Returns:
        build_versione_id: l'id della versione creata

    Raises:
        ValueError: errore di validazione
        sqlite3.Error: errore di database
        RuntimeError: errore generico dell'operazione
    """
    adesso = datetime.now().isoformat()

    with transazione_sqlite(conn) as cur:
        cur.execute(
            """
            INSERT INTO build_versioni
            (build_base_id, nome_build, stagione_dichiarata, patch_dichiarata,
             stagione_id, patch_id, stato, data_creazione, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                build_id,
                nome_build,
                stagione_dichiarata,
                patch_dichiarata,
                stagione_id,
                patch_id,
                stato,
                adesso,
                note,
            )
        )
        build_versione_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO build_versioni_fonti
            (build_versione_id, fonte_id, fonte_url, autore,
             data_pubblicazione, data_verifica, stato, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                build_versione_id,
                fonte_id,
                fonte_url,
                autore,
                data_pubblicazione,
                data_verifica,
                stato,
                note,
            )
        )

        return build_versione_id


def aggiungi_fonte_a_versione(
    conn,
    build_versione_id,
    fonte_id,
    fonte_url,
    autore,
    data_pubblicazione,
    data_verifica,
    stato,
    note=None,
):
    """
    Aggiunge una fonte a una versione esistente.

    Parametri:
    - conn: connessione SQLite attiva
    - build_versione_id: identificativo della versione esistente
    - fonte_id: identificativo della fonte (FK verso fonte_informativa)
    - fonte_url: URL della fonte
    - autore: autore della fonte
    - data_pubblicazione: data di pubblicazione della fonte
    - data_verifica: data di verifica della fonte
    - stato: 'verificata', 'da_verificare' o 'obsoleta'
    - note: note opzionali

    Returns:
        True se l'operazione ha successo

    Raises:
        ValueError: se versione o fonte non esistono, o se fonte già associata
        RuntimeError: se l'operazione fallisce
    """
    with transazione_sqlite(conn) as cur:
        # Verifica che la versione esista
        cur.execute("SELECT id FROM build_versioni WHERE id = ?", (build_versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione {build_versione_id} non trovata")

        # Verifica che la fonte esista
        cur.execute("SELECT id FROM fonte_informativa WHERE id = ?", (fonte_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Fonte {fonte_id} non trovata")

        # Verifica che non esista già questa associazione
        cur.execute(
            "SELECT id FROM build_versioni_fonti WHERE build_versione_id = ? AND fonte_id = ?",
            (build_versione_id, fonte_id)
        )
        if cur.fetchone() is not None:
            raise ValueError(
                f"La fonte {fonte_id} è già associata alla versione {build_versione_id}"
            )

        adesso = datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO build_versioni_fonti
            (build_versione_id, fonte_id, fonte_url, autore,
             data_pubblicazione, data_verifica, stato, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                build_versione_id,
                fonte_id,
                fonte_url,
                autore,
                data_pubblicazione,
                data_verifica,
                stato,
                note,
            )
        )

        return True


def sostituisci_fonte_di_versione(
    conn,
    build_versione_id,
    fonte_id_attuale,
    nuovo_fonte_id,
    nuovo_fonte_url,
    nuovo_autore,
    nuova_data_pubblicazione,
    nuova_data_verifica,
    nuovo_stato,
    nuova_nota=None,
):
    """
    Sostituisce una fonte esistente di una versione con una nuova.

    Comportamento quando nuovo_fonte_id == fonte_id_attuale:
    l'operazione è valida (aggiorna i metadati mantenendo almeno una fonte
    associata alla versione). Non crea duplicati.

    Parametri:
    - conn: connessione SQLite attiva
    - build_versione_id: identificativo della versione esistente
    - fonte_id_attuale: identificativo della fonte da sostituire
    - nuovo_fonte_id: identificativo della nuova fonte
    - nuovo_fonte_url: URL della nuova fonte
    - nuovo_autore: autore della nuova fonte
    - nuova_data_pubblicazione: data di pubblicazione della nuova fonte
    - nuova_data_verifica: data di verifica della nuova fonte
    - nuovo_stato: stato della nuova fonte
    - nuova_nota: note opzionali

    Raises:
        ValueError: se versione o fonte non esistenti, o se la nuova fonte è già associata
        RuntimeError: se l'operazione fallisce
    """
    with transazione_sqlite(conn) as cur:
        # Verifica che la versione esista
        cur.execute("SELECT id FROM build_versioni WHERE id = ?", (build_versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione {build_versione_id} non trovata")

        # Verifica che la fonte attuale sia associata a questa versione
        cur.execute(
            "SELECT id FROM build_versioni_fonti WHERE build_versione_id = ? AND fonte_id = ?",
            (build_versione_id, fonte_id_attuale)
        )
        riga_attuale = cur.fetchone()
        if riga_attuale is None:
            raise ValueError(
                f"Fonte {fonte_id_attuale} non associata alla versione {build_versione_id}"
            )

        # Verifica che la nuova fonte esista
        cur.execute("SELECT id FROM fonte_informativa WHERE id = ?", (nuovo_fonte_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Fonte {nuovo_fonte_id} non trovata")

        # Verifica assenza di duplicato (se nuova fonte diversa dall'attuale)
        if nuovo_fonte_id != fonte_id_attuale:
            cur.execute(
                "SELECT id FROM build_versioni_fonti WHERE build_versione_id = ? AND fonte_id = ?",
                (build_versione_id, nuovo_fonte_id)
            )
            if cur.fetchone() is not None:
                raise ValueError(
                    f"La fonte {nuovo_fonte_id} è già associata alla versione {build_versione_id}"
                )

        # Esegue l'UPDATE
        cur.execute(
            """
            UPDATE build_versioni_fonti
            SET fonte_id = ?, fonte_url = ?, autore = ?,
                data_pubblicazione = ?, data_verifica = ?,
                stato = ?, note = ?
            WHERE build_versione_id = ? AND fonte_id = ?
            """,
            (
                nuovo_fonte_id,
                nuovo_fonte_url,
                nuovo_autore,
                nuova_data_pubblicazione,
                nuova_data_verifica,
                nuovo_stato,
                nuova_nota,
                build_versione_id,
                fonte_id_attuale,
            )
        )

        if cur.rowcount != 1:
            raise ValueError(
                f"L'UPDATE non ha modificato esattamente una riga "
                f"(rowcount={cur.rowcount}) per versione {build_versione_id} "
                f"e fonte {fonte_id_attuale}"
            )


def elimina_fonte_da_versione(
    conn,
    build_versione_id,
    build_versione_fonte_id,
):
    """
    Elimina una fonte da una versione, solo se rimane almeno un'altra fonte.

    La riga da eliminare viene identificata tramite la chiave primaria
    build_versione_fonte_id (id della riga in build_versioni_fonti).

    Parametri:
    - conn: connessione SQLite attiva
    - build_versione_id: identificativo della versione
    - build_versione_fonte_id: identificativo della riga fonte da eliminare

    Raises:
        ValueError: se versione o fonte non esistenti, o se è l'unica fonte
        RuntimeError: se l'operazione fallisce
    """
    with transazione_sqlite(conn) as cur:
        # Verifica che la versione esista
        cur.execute("SELECT id FROM build_versioni WHERE id = ?", (build_versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione {build_versione_id} non trovata")

        # Verifica che la riga fonte esista e appartenga a questa versione
        cur.execute(
            "SELECT id FROM build_versioni_fonti WHERE id = ? AND build_versione_id = ?",
            (build_versione_fonte_id, build_versione_id)
        )
        if cur.fetchone() is None:
            raise ValueError(
                f"Fonte {build_versione_fonte_id} non associata alla versione {build_versione_id}"
            )

        # Verifica che non sia l'unica fonte
        cur.execute(
            "SELECT COUNT(*) FROM build_versioni_fonti WHERE build_versione_id = ?",
            (build_versione_id,)
        )
        conteggio = cur.fetchone()[0]
        if conteggio <= 1:
            raise ValueError(
                f"Impossibile eliminare l'unica fonte ({build_versione_fonte_id}) "
                f"dalla versione {build_versione_id}. "
                f"Ogni versione deve avere almeno una fonte."
            )

        # Esegue l'eliminazione usando la chiave primaria
        cur.execute(
            "DELETE FROM build_versioni_fonti WHERE id = ?",
            (build_versione_fonte_id,)
        )

        if cur.rowcount != 1:
            raise ValueError(
                f"Il DELETE non ha eliminato esattamente una riga "
                f"(rowcount={cur.rowcount}) per id {build_versione_fonte_id}"
            )


# ============================================================================
# TASK D085 — TABELLA STORICO ASSOCIAZIONI ABILITÀ-BUILD
# ============================================================================

def inizializza_storico_abilita_build(conn=None):
    """
    Crea la tabella build_versioni_abilita_storico se non esiste.
    Nessuna FK verso tabelle operative: lo storico sopravvive alle cancellazioni.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS build_versioni_abilita_storico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operazione TEXT NOT NULL CHECK (operazione IN ('INSERT', 'UPDATE', 'DELETE')),
                data_operazione TEXT NOT NULL,
                associazione_id INTEGER,
                build_versione_id INTEGER,
                abilita_id INTEGER,
                abilita_versioni_id INTEGER,
                livello INTEGER,
                livello_prev INTEGER,
                nota TEXT,
                nota_prev TEXT,
                utente TEXT DEFAULT 'sistema',
                motivo TEXT
            )
        """)
        if conn_creata_da_noi:
            conn.commit()
        return True
    except Exception:
        if conn_creata_da_noi:
            conn.rollback()
        raise
    finally:
        if conn_creata_da_noi:
            conn.close()


def _registra_storico_abilita_build(
    conn,
    operazione,
    associazione_id=None,
    build_versione_id=None,
    abilita_id=None,
    abilita_versioni_id=None,
    livello=None,
    livello_prev=None,
    nota=None,
    nota_prev=None,
    utente='sistema',
    motivo=None,
):
    """Registra un'operazione nello storico associazioni abilità-build."""
    adesso = datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO build_versioni_abilita_storico
        (operazione, data_operazione, associazione_id, build_versione_id,
         abilita_id, abilita_versioni_id, livello, livello_prev,
         nota, nota_prev, utente, motivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        operazione, adesso, associazione_id, build_versione_id,
        abilita_id, abilita_versioni_id, livello, livello_prev,
        nota, nota_prev, utente, motivo,
    ))
    return cur.lastrowid


# ============================================================================
# TASK D085 — VALIDAZIONE ABILITÀ PER BUILD VERSIONE
# ============================================================================

def valida_abilita_versioni_per_build_versione(
    conn, build_versione_id, abilita_id, abilita_versioni_id
):
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    """
    Verifica coerenza tra versione di build, abilità e versione storica dell'abilità.

    Controlli:
    1. La versione di build esiste
    2. La build_base collegata esiste e ha classe_id
    3. L'abilità esiste
    4. La versione storica dell'abilità esiste e appartiene a quell'abilità
    5. Classe compatibile: build_base.classe_id == abilita.classe_id
    6. Compatibilità temporale: se sia build_versioni che abilita_versioni
       hanno stagione_id/patch_id, devono coincidere.
       Se non determinabile → esito DA_VERIFICARE (non blocca).

    Returns:
        dict con chiavi: valida (bool), esito_temporale (str), dettagli (str)

    Raises:
        ValueError: se riferimenti inesistenti o classe incompatibile
    """
    with transazione_sqlite(conn) as cur:
        # 1. Versione di build
        cur.execute(
            "SELECT build_base_id, stagione_id, patch_id FROM build_versioni WHERE id = ?",
            (build_versione_id,),
        )
        riga_bv = cur.fetchone()
        if riga_bv is None:
            raise ValueError(f"Versione build {build_versione_id} non trovata")
        build_base_id = riga_bv[0]
        stagione_id_bv = riga_bv[1]
        patch_id_bv = riga_bv[2]

        # 2. Build base e classe
        cur.execute(
            "SELECT classe_id FROM build_base WHERE id = ?", (build_base_id,)
        )
        riga_bb = cur.fetchone()
        if riga_bb is None:
            raise ValueError(f"Build base {build_base_id} non trovata")
        classe_id_build = riga_bb[0]

        # 3. Abilità e classe
        cur.execute(
            "SELECT classe_id FROM abilita WHERE id = ?", (abilita_id,)
        )
        riga_ab = cur.fetchone()
        if riga_ab is None:
            raise ValueError(f"Abilità {abilita_id} non trovata")
        classe_id_abilita = riga_ab[0]

        # 4. Versione storica abilita_versioni
        cur.execute(
            "SELECT stagione_id, patch_id FROM abilita_versioni WHERE id = ? AND abilita_id = ?",
            (abilita_versioni_id, abilita_id),
        )
        riga_av = cur.fetchone()
        if riga_av is None:
            raise ValueError(
                f"Versione abilità {abilita_versioni_id} non trovata "
                f"per abilità {abilita_id}"
            )
        stagione_id_av = riga_av[0]
        patch_id_av = riga_av[1]

        # 5. Classe compatibile
        if classe_id_build != classe_id_abilita:
            raise ValueError(
                f"Incompatibilità classe: build_base.classe_id={classe_id_build} "
                f"non può usare abilità {abilita_id} (classe_id={classe_id_abilita})"
            )

        # 6. Compatibilità temporale
        esito_temporale = "COMPATIBILE_VERIFICATA"
        if stagione_id_bv is not None and stagione_id_av is not None:
            if stagione_id_bv != stagione_id_av:
                esito_temporale = "INCOMPATIBILE"
        if patch_id_bv is not None and patch_id_av is not None:
            if patch_id_bv != patch_id_av:
                esito_temporale = "INCOMPATIBILE"
        if esito_temporale == "COMPATIBILE_VERIFICATA":
            if (stagione_id_bv is None or stagione_id_av is None) and \
               (patch_id_bv is None or patch_id_av is None):
                esito_temporale = "DA_VERIFICARE"

        return {
            "valida": True,
            "esito_temporale": esito_temporale,
            "dettagli": (
                f"classe_id={classe_id_build}, stagione_bv={stagione_id_bv}, "
                f"patch_bv={patch_id_bv}, stagione_av={stagione_id_av}, "
                f"patch_av={patch_id_av}"
            ),
        }


# ============================================================================
# TASK D085 — FUNZIONI GESTIONE ASSOCIAZIONI ABILITÀ-BUILD
# ============================================================================

def aggiungi_abilita_a_build_versione(
    conn=None, build_versione_id=None, abilita_id=None, abilita_versioni_id=None,
    livello=None, nota=None, utente='sistema', motivo=None
):
    """
    Aggiunge un'abilità a una versione della build.

    Esegue controlli di coerenza prima dell'inserimento:
    - classe dell'abilità compatibile con la build base
    - versione storica dell'abilità valida e appartenente all'abilità
    - compatibilità temporale (se non determinabile → DA_VERIFICARE, non blocca)
    - assenza di duplicati (UNIQUE build_versione_id, abilita_id)

    Non usa mai un valore arbitrario per abilita_versioni_id.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            # Validazione coerenza
            validazione = valida_abilita_versioni_per_build_versione(
                conn, build_versione_id, abilita_id, abilita_versioni_id
            )

            # Verifica assenza duplicato
            cur.execute(
                "SELECT id FROM build_versioni_abilita "
                "WHERE build_versione_id = ? AND abilita_id = ?",
                (build_versione_id, abilita_id),
            )
            if cur.fetchone() is not None:
                raise ValueError(
                    f"L'abilità {abilita_id} è già associata alla "
                    f"versione build {build_versione_id}"
                )

            adesso = datetime.now().isoformat()
            cur.execute("""
                INSERT INTO build_versioni_abilita
                (build_versione_id, abilita_id, abilita_versioni_id, livello, nota)
                VALUES (?, ?, ?, ?, ?)
            """, (build_versione_id, abilita_id, abilita_versioni_id, livello, nota))
            associazione_id = cur.lastrowid

            # Audit INSERT
            _registra_storico_abilita_build(
                conn, 'INSERT', associazione_id=associazione_id,
                build_versione_id=build_versione_id, abilita_id=abilita_id,
                abilita_versioni_id=abilita_versioni_id, livello=livello,
                livello_prev=None, nota=nota, nota_prev=None,
                utente=utente, motivo=motivo,
            )

        return {
            "associazione_id": associazione_id,
            "esito_temporale": validazione["esito_temporale"],
        }
    finally:
        if conn_creata_da_noi:
            conn.close()


def modifica_abilita_build_versione(
    conn=None, associazione_id=None, livello=None, nota=None,
    utente='sistema', motivo=None
):
    """
    Modifica livello e nota di un'associazione abilità-build versione esistente.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            cur.execute(
                "SELECT build_versione_id, abilita_id, abilita_versioni_id, livello, nota "
                "FROM build_versioni_abilita WHERE id = ?",
                (associazione_id,),
            )
            riga = cur.fetchone()
            if riga is None:
                raise ValueError(f"Associazione {associazione_id} non trovata")

            build_versione_id = riga[0]
            abilita_id = riga[1]
            abilita_versioni_id = riga[2]
            livello_prev = riga[3]
            nota_prev = riga[4]

            nuovo_livello = livello if livello is not None else livello_prev
            nuova_nota = nota if nota is not None else nota_prev

            cur.execute(
                "UPDATE build_versioni_abilita SET livello = ?, nota = ? WHERE id = ?",
                (nuovo_livello, nuova_nota, associazione_id),
            )
            if cur.rowcount != 1:
                raise ValueError(
                    f"UPDATE associazione {associazione_id}: "
                    f"rowcount={cur.rowcount}, atteso 1"
                )

            # Audit UPDATE
            _registra_storico_abilita_build(
                conn, 'UPDATE', associazione_id=associazione_id,
                build_versione_id=build_versione_id, abilita_id=abilita_id,
                abilita_versioni_id=abilita_versioni_id,
                livello=nuovo_livello, livello_prev=livello_prev,
                nota=nuova_nota, nota_prev=nota_prev,
                utente=utente, motivo=motivo,
            )

        return True
    finally:
        if conn_creata_da_noi:
            conn.close()


def rimuovi_abilita_da_build_versione(
    conn=None, associazione_id=None, utente='sistema', motivo=None
):
    """
    Rimuove un'associazione abilità-build versione.
    Registra l'operazione nello storico prima dell'eliminazione.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            cur.execute(
                "SELECT build_versione_id, abilita_id, abilita_versioni_id, livello, nota "
                "FROM build_versioni_abilita WHERE id = ?",
                (associazione_id,),
            )
            riga = cur.fetchone()
            if riga is None:
                raise ValueError(f"Associazione {associazione_id} non trovata")

            build_versione_id = riga[0]
            abilita_id = riga[1]
            abilita_versioni_id = riga[2]
            livello = riga[3]
            nota = riga[4]

            cur.execute("DELETE FROM build_versioni_abilita WHERE id = ?", (associazione_id,))
            if cur.rowcount != 1:
                raise ValueError(
                    f"DELETE associazione {associazione_id}: "
                    f"rowcount={cur.rowcount}, atteso 1"
                )

            # Audit DELETE
            _registra_storico_abilita_build(
                conn, 'DELETE', associazione_id=associazione_id,
                build_versione_id=build_versione_id, abilita_id=abilita_id,
                abilita_versioni_id=abilita_versioni_id,
                livello=None, livello_prev=livello,
                nota=None, nota_prev=nota,
                utente=utente, motivo=motivo,
            )

        return True
    finally:
        if conn_creata_da_noi:
            conn.close()


def leggi_abilita_di_build_versione(conn, build_versione_id):
    """
    Restituisce tutte le abilità associate a una versione di build,
    con i dati della versione storica dell'abilità.
    """
    cur = conn.execute("""
        SELECT bva.id, bva.abilita_id, bva.abilita_versioni_id,
               bva.livello, bva.nota,
               a.nome AS abilita_nome, a.codice_identificativo,
               av.tipo AS versione_tipo, av.descrizione AS versione_descrizione,
               av.livello_sblocco, av.stato AS versione_stato
        FROM build_versioni_abilita bva
        JOIN abilita a ON bva.abilita_id = a.id
        JOIN abilita_versioni av ON bva.abilita_id = av.abilita_id
            AND bva.abilita_versioni_id = av.id
        WHERE bva.build_versione_id = ?
        ORDER BY a.nome
    """, (build_versione_id,))
    return [dict_from_row(r) for r in cur.fetchall()]


def leggi_personaggio_id_da_associazione_abilita(associazione_id, conn=None):
    """
    Recupera il personaggio_id a partire da un'associazione build_versioni_abilita.
    Attraversa: associazione → build_versione → build_base → build → personaggio.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT b.personaggio_id
            FROM build_versioni_abilita bva
            JOIN build_versioni bv ON bva.build_versione_id = bv.id
            JOIN build_base bb ON bv.build_base_id = bb.id
            JOIN build b ON bb.build_personale_id = b.id
            WHERE bva.id = ?
        """, (associazione_id,))
        riga = cur.fetchone()
        return riga[0] if riga else None
    finally:
        if conn_creata_da_noi:
            conn.close()


def leggi_build_versioni_con_abilita(build_id, conn=None):
    """
    Restituisce tutte le versioni di build per una build, con le relative abilità associate.
    Ogni versione include la lista delle abilità (via leggi_abilita_di_build_versione).
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT bv.id, bv.nome_build, bv.stagione_id, bv.patch_id, bv.stato,
                   bv.data_creazione, bb.classe_id
            FROM build_versioni bv
            JOIN build_base bb ON bv.build_base_id = bb.id
            WHERE bb.build_personale_id = ?
            ORDER BY bv.data_creazione DESC
        """, (build_id,))
        versioni = []
        for riga in cur.fetchall():
            versione_id = riga[0]
            abilita = leggi_abilita_di_build_versione(conn, versione_id)
            versioni.append({
                'id': riga[0],
                'nome_build': riga[1],
                'stagione_id': riga[2],
                'patch_id': riga[3],
                'stato': riga[4],
                'data_creazione': riga[5],
                'classe_id': riga[6],
                'abilita': abilita,
            })
        return versioni
    finally:
        if conn_creata_da_noi:
            conn.close()


# ============================================================================
# TASK D085 — PROTEZIONE CANCELLAZIONI CON AUDIT PRE-CASCADE
# ============================================================================

def elimina_personaggio_con_audit(personaggio_id, utente='sistema', conn=None):
    """
    Elimina un personaggio recuperando prima tutte le associazioni
    abilità-build che verranno eliminate dalle CASCADE.
    Le associazioni vengono registrate nello storico prima della cancellazione.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            # Verifica esistenza
            cur.execute("SELECT id FROM personaggi WHERE id = ?", (personaggio_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Personaggio {personaggio_id} non trovato")

            # Recupera tutte le associazioni che saranno eliminate dalle CASCADE
            # personaggi → build → build_base → build_versioni → build_versioni_abilita
            cur.execute("""
                SELECT bva.id, bva.build_versione_id, bva.abilita_id,
                       bva.abilita_versioni_id, bva.livello, bva.nota
                FROM build_versioni_abilita bva
                JOIN build_versioni bv ON bva.build_versione_id = bv.id
                JOIN build_base bb ON bv.build_base_id = bb.id
                JOIN build b ON bb.build_personale_id = b.id
                WHERE b.personaggio_id = ?
            """, (personaggio_id,))
            associazioni = cur.fetchall()

            # Registra ogni associazione nello storico (DELETE)
            adesso = datetime.now().isoformat()
            for a in associazioni:
                _registra_storico_abilita_build(
                    conn, 'DELETE',
                    associazione_id=a[0],
                    build_versione_id=a[1],
                    abilita_id=a[2],
                    abilita_versioni_id=a[3],
                    livello=None, livello_prev=a[4],
                    nota=None, nota_prev=a[5],
                    utente=utente,
                    motivo=f"Eliminazione personaggio {personaggio_id} (CASCADE)",
                )

            # Elimina il personaggio (CASCADE eliminerà build, build_base, build_versioni, bva)
            cur.execute("DELETE FROM personaggi WHERE id = ?", (personaggio_id,))
            if cur.rowcount == 0:
                raise ValueError(f"Personaggio {personaggio_id} non trovato")

        return {
            "associazioni_archiviate": len(associazioni),
        }
    except Exception:
        if conn_creata_da_noi:
            conn.rollback()
        raise
    finally:
        if conn_creata_da_noi:
            conn.close()


def elimina_build_con_audit(build_id, utente='sistema', conn=None):
    """
    Elimina una build recuperando prima tutte le associazioni
    abilità-build che verranno eliminate dalle CASCADE.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            # Verifica esistenza e recupera personaggio_id
            cur.execute("SELECT personaggio_id FROM build WHERE id = ?", (build_id,))
            riga = cur.fetchone()
            if riga is None:
                raise ValueError(f"Build {build_id} non trovata")
            personaggio_id = riga[0]

            # Recupera tutte le associazioni che saranno eliminate dalle CASCADE
            # build → build_base → build_versioni → build_versioni_abilita
            cur.execute("""
                SELECT bva.id, bva.build_versione_id, bva.abilita_id,
                       bva.abilita_versioni_id, bva.livello, bva.nota
                FROM build_versioni_abilita bva
                JOIN build_versioni bv ON bva.build_versione_id = bv.id
                JOIN build_base bb ON bv.build_base_id = bb.id
                WHERE bb.build_personale_id = ?
            """, (build_id,))
            associazioni = cur.fetchall()

            # Registra ogni associazione nello storico (DELETE)
            adesso = datetime.now().isoformat()
            for a in associazioni:
                _registra_storico_abilita_build(
                    conn, 'DELETE',
                    associazione_id=a[0],
                    build_versione_id=a[1],
                    abilita_id=a[2],
                    abilita_versioni_id=a[3],
                    livello=None, livello_prev=a[4],
                    nota=None, nota_prev=a[5],
                    utente=utente,
                    motivo=f"Eliminazione build {build_id} (CASCADE)",
                )

            # Elimina la build (CASCADE eliminerà build_base, build_versioni, bva)
            cur.execute("DELETE FROM build WHERE id = ?", (build_id,))
            if cur.rowcount == 0:
                raise ValueError(f"Build {build_id} non trovata")

        return {
            "personaggio_id": personaggio_id,
            "associazioni_archiviate": len(associazioni),
        }
    except Exception:
        if conn_creata_da_noi:
            conn.rollback()
        raise
    finally:
        if conn_creata_da_noi:
            conn.close()


def elimina_build_versione_con_audit(build_versione_id, utente='sistema', conn=None):
    """
    Elimina una singola versione di build recuperando prima le associazioni
    abilità-build che verranno eliminate dalle CASCADE.
    """
    conn_creata_da_noi = conn is None
    if conn is None:
        conn = get_conn()
    try:
        with transazione_sqlite(conn) as cur:
            # Verifica esistenza
            cur.execute("SELECT id FROM build_versioni WHERE id = ?", (build_versione_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Versione build {build_versione_id} non trovata")

            # Recupera associazioni che saranno eliminate
            cur.execute("""
                SELECT id, abilita_id, abilita_versioni_id, livello, nota
                FROM build_versioni_abilita
                WHERE build_versione_id = ?
            """, (build_versione_id,))
            associazioni = cur.fetchall()

            # Registra nello storico
            adesso = datetime.now().isoformat()
            for a in associazioni:
                _registra_storico_abilita_build(
                    conn, 'DELETE',
                    associazione_id=a[0],
                    build_versione_id=build_versione_id,
                    abilita_id=a[1],
                    abilita_versioni_id=a[2],
                    livello=None, livello_prev=a[3],
                    nota=None, nota_prev=a[4],
                    utente=utente,
                    motivo=f"Eliminazione versione build {build_versione_id} (CASCADE)",
                )

            # Elimina la versione (CASCADE eliminerà bva)
            cur.execute("DELETE FROM build_versioni WHERE id = ?", (build_versione_id,))
            if cur.rowcount == 0:
                raise ValueError(f"Versione build {build_versione_id} non trovata")

        return {
            "associazioni_archiviate": len(associazioni),
        }
    except Exception:
        if conn_creata_da_noi:
            conn.rollback()
        raise
    finally:
        if conn_creata_da_noi:
            conn.close()


# Aggiorna le funzioni elimina_personaggio ed elimina_build esistenti
# per usare la versione con audit
_elimina_personaggio_originale = elimina_personaggio
_elimina_build_originale = elimina_build


def leggi_build_versione_per_id(build_versione_id):
    """Restituisce una versione di build per id, con personaggio_id."""
    conn = get_conn()
    try:
        cur = conn.execute("""
            SELECT bv.id, bv.build_base_id, bv.nome_build, bv.stagione_id, bv.patch_id,
                   bv.stato, bv.data_creazione, bv.note,
                   bb.id AS build_base_id, bb.build_personale_id, bb.classe_id,
                   b.id AS build_id, b.personaggio_id
            FROM build_versioni bv
            JOIN build_base bb ON bv.build_base_id = bb.id
            JOIN build b ON bb.build_personale_id = b.id
            WHERE bv.id = ?
        """, (build_versione_id,))
        r = cur.fetchone()
        return dict_from_row(r)
    finally:
        conn.close()


def leggi_abilita_versioni_per_abilita(abilita_id):
    """Restituisce tutte le versioni storiche di un'abilità."""
    conn = get_conn()
    try:
        cur = conn.execute("""
            SELECT id, abilita_id, stagione_id, patch_id, tipo, descrizione,
                   livello_sblocco, fonte_id, data_verifica, stato, versione_corrente
            FROM abilita_versioni
            WHERE abilita_id = ?
            ORDER BY id DESC
        """, (abilita_id,))
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ============================================================================
# TASK D127 — GESTIONE CATALOGO OGGETTI
# ============================================================================

def inserisci_oggetto(nome_oggetto, tipo_oggetto=None, livello_oggetto=None, fonte=None, verificato=False):
    """Inserisce un nuovo oggetto nel catalogo. Restituisce l'id creato."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO oggetto (nome_oggetto, tipo_oggetto, livello_oggetto, fonte, verificato)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nome_oggetto.strip(),
                tipo_oggetto.strip() if tipo_oggetto else None,
                livello_oggetto,
                fonte.strip() if fonte else None,
                1 if verificato else 0,
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def modifica_oggetto(oggetto_id, nome_oggetto=None, tipo_oggetto=None, livello_oggetto=None, fonte=None, verificato=None):
    """Modifica un oggetto esistente. Solleva ValueError se non esiste."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM oggetto WHERE id = ?", (oggetto_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Oggetto {oggetto_id} non trovato.")

        campi = []
        valori = []
        if nome_oggetto is not None:
            campi.append("nome_oggetto = ?")
            valori.append(nome_oggetto.strip())
        if tipo_oggetto is not None:
            campi.append("tipo_oggetto = ?")
            valori.append(tipo_oggetto.strip() if tipo_oggetto else None)
        if livello_oggetto is not None:
            campi.append("livello_oggetto = ?")
            valori.append(livello_oggetto)
        if fonte is not None:
            campi.append("fonte = ?")
            valori.append(fonte.strip() if fonte else None)
        if verificato is not None:
            campi.append("verificato = ?")
            valori.append(1 if verificato else 0)

        if not campi:
            raise ValueError("Nessun campo da modificare.")

        valori.append(oggetto_id)
        cur.execute(
            f"UPDATE oggetto SET {', '.join(campi)} WHERE id = ?",
            valori,
        )
        if cur.rowcount == 0:
            raise ValueError(f"Oggetto {oggetto_id} non trovato.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rimuovi_oggetto(oggetto_id):
    """Rimuove un oggetto dal catalogo se non è utilizzato in nessuna build.
    Solleva ValueError se l'oggetto è referenziato o non esiste."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM oggetto WHERE id = ?", (oggetto_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Oggetto {oggetto_id} non trovato.")

        cur.execute(
            "SELECT COUNT(*) FROM build_personale_slot_equipaggiamento WHERE oggetto_id = ?",
            (oggetto_id,),
        )
        conteggio_personale = cur.fetchone()[0]
        if conteggio_personale > 0:
            raise ValueError(
                f"Impossibile eliminare l'oggetto {oggetto_id}: "
                f"è utilizzato in {conteggio_personale} slot di build personali."
            )

        cur.execute(
            "SELECT COUNT(*) FROM build_esterna_slot_equipaggiamento WHERE oggetto_id = ?",
            (oggetto_id,),
        )
        conteggio_esterna = cur.fetchone()[0]
        if conteggio_esterna > 0:
            raise ValueError(
                f"Impossibile eliminare l'oggetto {oggetto_id}: "
                f"è utilizzato in {conteggio_esterna} slot di build esterne."
            )

        cur.execute("DELETE FROM oggetto WHERE id = ?", (oggetto_id,))
        if cur.rowcount == 0:
            raise ValueError(f"Oggetto {oggetto_id} non trovato.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================================
# TASK D123 — GESTIONE EQUIPAGGIAMENTO BUILD PERSONALE
# ============================================================================

def leggi_slot_di_build_versioni(conn, build_versione_id):
    """Restituisce tutti gli slot di una versione build personale con oggetto e dettagli."""
    cur = conn.execute("""
        SELECT bps.id AS associazione_id, bps.build_versioni_id, bps.slot_id,
               bps.stato_slot, bps.oggetto_id,
               s.nome AS slot_nome, s.codice_slot,
               o.id AS oggetto_id, o.nome_oggetto, o.tipo_oggetto,
               o.livello_oggetto, o.fonte, o.verificato AS oggetto_verificato
        FROM build_personale_slot_equipaggiamento bps
        JOIN slot_equipaggiamento s ON bps.slot_id = s.id
        LEFT JOIN oggetto o ON bps.oggetto_id = o.id
        WHERE bps.build_versioni_id = ?
        ORDER BY s.nome
    """, (build_versione_id,))
    risultati = []
    for r in cur.fetchall():
        slot = dict_from_row(r)
        associazione_id = slot['associazione_id']
        slot['aspetti'] = leggi_dettagli_slot(conn, associazione_id, 'aspetto')
        slot['affissi'] = leggi_dettagli_slot(conn, associazione_id, 'affisso')
        slot['tempra'] = leggi_dettagli_slot(conn, associazione_id, 'tempra')
        risultati.append(slot)
    return risultati


def leggi_dettagli_slot(conn, associazione_id, tipo_dettaglio):
    """Legge dettagli (aspetto/affisso/tempra) di uno slot associazione."""
    tabella = {
        'aspetto': 'oggetto_aspetto_personale',
        'affisso': 'oggetto_affisso_personale',
        'tempra': 'oggetto_tempra_personale',
    }[tipo_dettaglio]
    chiave = 'slot_personale_id'
    cur = conn.execute(
        f"SELECT * FROM {tabella} WHERE {chiave} = ? ORDER BY id",
        (associazione_id,),
    )
    return [dict_from_row(r) for r in cur.fetchall()]


def leggi_oggetti_catalogo():
    """Restituisce tutti gli oggetti del catalogo (lista vuota se catalogo vuoto)."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "SELECT id, nome_oggetto, tipo_oggetto, livello_oggetto, fonte, verificato "
            "FROM oggetto ORDER BY nome_oggetto"
        )
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def inizializza_slot_build_versione(conn, build_versione_id):
    """Inserisce righe slot per tutti gli slot del catalogo se non esistono già per la versione."""
    with transazione_sqlite(conn) as cur:
        # Verifica che la versione esista ed è personale
        cur.execute("""
            SELECT bv.id FROM build_versioni bv
            JOIN build_base bb ON bv.build_base_id = bb.id
            JOIN build b ON bb.build_personale_id = b.id
            WHERE bv.id = ?
        """, (build_versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione build {build_versione_id} non trovata o non personale")

        # Slot già presenti per questa versione
        cur.execute(
            "SELECT slot_id FROM build_personale_slot_equipaggiamento WHERE build_versioni_id = ?",
            (build_versione_id,),
        )
        esistenti = {r[0] for r in cur.fetchall()}

        # Tutti gli slot del catalogo
        cur.execute("SELECT id FROM slot_equipaggiamento ORDER BY nome")
        tutti = cur.fetchall()

        for (slot_id,) in tutti:
            if slot_id not in esistenti:
                cur.execute(
                    """
                    INSERT INTO build_personale_slot_equipaggiamento
                    (build_versioni_id, slot_id, stato_slot, oggetto_id)
                    VALUES (?, ?, 'mancante', NULL)
                    """,
                    (build_versione_id, slot_id),
                )
    return True


def associa_oggetto_a_slot(conn, build_versione_id, slot_id, oggetto_id, stato_slot):
    """Associa o sostituisce l'oggetto di uno slot (upsert). Ritorna l'id dell'associazione."""
    with transazione_sqlite(conn) as cur:
        # Verifica che la versione sia personale
        cur.execute("""
            SELECT bv.id FROM build_versioni bv
            JOIN build_base bb ON bv.build_base_id = bb.id
            JOIN build b ON bb.build_personale_id = b.id
            WHERE bv.id = ?
        """, (build_versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione build {build_versione_id} non trovata o non personale")

        # Verifica slot
        cur.execute("SELECT id FROM slot_equipaggiamento WHERE id = ?", (slot_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Slot {slot_id} non trovato")

        # Verifica oggetto (se fornito)
        if oggetto_id is not None:
            cur.execute("SELECT id FROM oggetto WHERE id = ?", (oggetto_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Oggetto {oggetto_id} non trovato")

        # Coerenza CHECK: verificato richiede oggetto_id NOT NULL; mancante/non_applicabile richiede NULL
        if stato_slot == 'verificato' and oggetto_id is None:
            raise ValueError("Uno slot verificato deve avere un oggetto associato")
        if stato_slot in ('mancante', 'non_applicabile') and oggetto_id is not None:
            raise ValueError("Uno slot mancante/non applicabile non deve avere oggetto")

        # Upsert: prova UPDATE, se non esiste INSERT
        cur.execute(
            """
            UPDATE build_personale_slot_equipaggiamento
            SET oggetto_id = ?, stato_slot = ?
            WHERE build_versioni_id = ? AND slot_id = ?
            """,
            (oggetto_id, stato_slot, build_versione_id, slot_id),
        )
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO build_personale_slot_equipaggiamento
                (build_versioni_id, slot_id, stato_slot, oggetto_id)
                VALUES (?, ?, ?, ?)
                """,
                (build_versione_id, slot_id, stato_slot, oggetto_id),
            )

        cur.execute(
            "SELECT id FROM build_personale_slot_equipaggiamento WHERE build_versioni_id = ? AND slot_id = ?",
            (build_versione_id, slot_id),
        )
        return cur.fetchone()[0]


def rimuovi_oggetto_da_slot(conn, associazione_id):
    """Rimuove l'oggetto da uno slot (oggetto_id NULL, stato_slot 'mancante').
    Fallisce se esistono dettagli collegati (protetto da trigger)."""
    with transazione_sqlite(conn) as cur:
        cur.execute(
            "SELECT build_versioni_id FROM build_personale_slot_equipaggiamento WHERE id = ?",
            (associazione_id,),
        )
        riga = cur.fetchone()
        if riga is None:
            raise ValueError(f"Associazione slot {associazione_id} non trovata")

        # Verifica che sia personale (tramite build_versioni -> build_base -> build)
        cur.execute("""
            SELECT bv.id FROM build_versioni bv
            JOIN build_base bb ON bv.build_base_id = bb.id
            JOIN build b ON bb.build_personale_id = b.id
            WHERE bv.id = ?
        """, (riga[0],))
        if cur.fetchone() is None:
            raise ValueError("L'associazione non appartiene a una build personale")

        cur.execute(
            """
            UPDATE build_personale_slot_equipaggiamento
            SET oggetto_id = NULL, stato_slot = 'mancante'
            WHERE id = ?
            """,
            (associazione_id,),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Associazione slot {associazione_id} non trovata")
    return True


def aggiungi_dettaglio_slot(conn, associazione_id, tipo_dettaglio, dati):
    """Aggiunge un dettaglio (aspetto/affisso/tempra) a uno slot.
    Fallisce se lo slot non è verificato (protetto da trigger)."""
    tabella = {
        'aspetto': 'oggetto_aspetto_personale',
        'affisso': 'oggetto_affisso_personale',
        'tempra': 'oggetto_tempra_personale',
    }[tipo_dettaglio]

    with transazione_sqlite(conn) as cur:
        # Verifica che l'associazione sia personale
        cur.execute(
            "SELECT build_versioni_id FROM build_personale_slot_equipaggiamento WHERE id = ?",
            (associazione_id,),
        )
        riga = cur.fetchone()
        if riga is None:
            raise ValueError(f"Associazione slot {associazione_id} non trovata")
        cur.execute("""
            SELECT bv.id FROM build_versioni bv
            JOIN build_base bb ON bv.build_base_id = bb.id
            JOIN build b ON bb.build_personale_id = b.id
            WHERE bv.id = ?
        """, (riga[0],))
        if cur.fetchone() is None:
            raise ValueError("L'associazione non appartiene a una build personale")

        if tipo_dettaglio == 'aspetto':
            cur.execute(
                f"""
                INSERT INTO {tabella}
                (slot_personale_id, nome_aspetto, tipo_aspetto, verificato)
                VALUES (?, ?, ?, ?)
                """,
                (
                    associazione_id,
                    dati.get('nome_aspetto', ''),
                    dati.get('tipo_aspetto', ''),
                    1 if dati.get('verificato') else 0,
                ),
            )
        elif tipo_dettaglio == 'affisso':
            cur.execute(
                f"""
                INSERT INTO {tabella}
                (slot_personale_id, nome_affisso, valore_affisso, livello_affisso, verificato)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    associazione_id,
                    dati.get('nome_affisso', ''),
                    dati.get('valore_affisso', ''),
                    dati.get('livello_affisso'),
                    1 if dati.get('verificato') else 0,
                ),
            )
        elif tipo_dettaglio == 'tempra':
            cur.execute(
                f"""
                INSERT INTO {tabella}
                (slot_personale_id, tipo_tempra, livello_tempra, verificato)
                VALUES (?, ?, ?, ?)
                """,
                (
                    associazione_id,
                    dati.get('tipo_tempra', ''),
                    dati.get('livello_tempra'),
                    1 if dati.get('verificato') else 0,
                ),
            )
    return True


def rimuovi_dettaglio_slot(conn, dettaglio_id, tipo_dettaglio, associazione_id=None):
    """Rimuove un dettaglio da uno slot.
    Se associazione_id è fornito, verifica che il dettaglio appartenga a quella associazione."""
    tabella = {
        'aspetto': 'oggetto_aspetto_personale',
        'affisso': 'oggetto_affisso_personale',
        'tempra': 'oggetto_tempra_personale',
    }[tipo_dettaglio]

    with transazione_sqlite(conn) as cur:
        cur.execute(
            f"SELECT slot_personale_id FROM {tabella} WHERE id = ?",
            (dettaglio_id,),
        )
        riga = cur.fetchone()
        if riga is None:
            raise ValueError(f"Dettaglio {tipo_dettaglio} {dettaglio_id} non trovato")
        # Verifica che il dettaglio appartenga all'associazione specificata (se fornita)
        if associazione_id is not None and riga[0] != associazione_id:
            raise ValueError(
                f"Il dettaglio {tipo_dettaglio} {dettaglio_id} non appartiene allo slot {associazione_id}"
            )
        # Verifica personale
        cur.execute(
            "SELECT build_versioni_id FROM build_personale_slot_equipaggiamento WHERE id = ?",
            (riga[0],),
        )
        if cur.fetchone() is None:
            raise ValueError("Il dettaglio non appartiene a una build personale")
        cur.execute(
            f"DELETE FROM {tabella} WHERE id = ?",
            (dettaglio_id,),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Dettaglio {tipo_dettaglio} {dettaglio_id} non trovato")
    return True


# ============================================================================
# TASK D130 — GESTIONE CATALOGO ABILITÀ
# ============================================================================

def leggi_abilita_catalogo():
    """Restituisce tutte le abilità con nome classe, ordinate per classe e nome."""
    conn = get_conn()
    try:
        cur = conn.execute("""
            SELECT a.id, a.nome, a.codice_identificativo, a.classe_id,
                   c.nome AS classe_nome, c.slug AS classe_slug
            FROM abilita a
            JOIN classi c ON a.classe_id = c.id
            ORDER BY c.nome, a.nome
        """)
        return [dict_from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def inserisci_abilita(classe_id, nome, codice_identificativo):
    """Inserisce una nuova abilità nel catalogo. Restituisce l'id creato."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO abilita (classe_id, nome, codice_identificativo)
            VALUES (?, ?, ?)
            """,
            (classe_id, nome.strip(), codice_identificativo.strip()),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def modifica_abilita(abilita_id, nome=None, codice_identificativo=None, classe_id=None):
    """Modifica un'abilità esistente. Solleva ValueError se non esiste."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM abilita WHERE id = ?", (abilita_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Abilità {abilita_id} non trovata.")
        campi = []
        valori = []
        if nome is not None:
            campi.append("nome = ?")
            valori.append(nome.strip())
        if codice_identificativo is not None:
            campi.append("codice_identificativo = ?")
            valori.append(codice_identificativo.strip())
        if classe_id is not None:
            campi.append("classe_id = ?")
            valori.append(classe_id)
        if not campi:
            raise ValueError("Nessun campo da modificare.")
        valori.append(abilita_id)
        cur.execute(f"UPDATE abilita SET {', '.join(campi)} WHERE id = ?", valori)
        if cur.rowcount == 0:
            raise ValueError(f"Abilità {abilita_id} non trovata.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rimuovi_abilita(abilita_id):
    """Rimuove un'abilità dal catalogo se non ha versioni né associazioni attive."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM abilita WHERE id = ?", (abilita_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Abilità {abilita_id} non trovata.")
        cur.execute("SELECT COUNT(*) FROM abilita_versioni WHERE abilita_id = ?", (abilita_id,))
        n_versioni = cur.fetchone()[0]
        if n_versioni > 0:
            raise ValueError(
                f"Impossibile eliminare l'abilità {abilita_id}: "
                f"ha {n_versioni} versione/i storica/e associata/e."
            )
        cur.execute("SELECT COUNT(*) FROM build_versioni_abilita WHERE abilita_id = ?", (abilita_id,))
        n_assoc = cur.fetchone()[0]
        if n_assoc > 0:
            raise ValueError(
                f"Impossibile eliminare l'abilità {abilita_id}: "
                f"è usata in {n_assoc} associazione/i build."
            )
        cur.execute("DELETE FROM abilita WHERE id = ?", (abilita_id,))
        if cur.rowcount == 0:
            raise ValueError(f"Abilità {abilita_id} non trovata.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inserisci_abilita_versioni(abilita_id, patch_id, stagione_id, tipo, descrizione,
                               livello_sblocco, fonte_id, data_verifica, stato, versione_corrente=0):
    """Inserisce una nuova versione storica per un'abilità. Restituisce l'id creato."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO abilita_versioni
            (abilita_id, patch_id, stagione_id, tipo, descrizione,
             livello_sblocco, fonte_id, data_verifica, stato, versione_corrente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                abilita_id,
                patch_id,
                stagione_id,
                tipo,
                descrizione,
                livello_sblocco,
                fonte_id,
                data_verifica,
                stato,
                1 if versione_corrente else 0,
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def modifica_abilita_versioni(versione_id, patch_id=None, stagione_id=None, tipo=None,
                              descrizione=None, livello_sblocco=None, fonte_id=None,
                              data_verifica=None, stato=None, versione_corrente=None):
    """Modifica una versione storica di abilità. Solleva ValueError se non esiste."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM abilita_versioni WHERE id = ?", (versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione abilità {versione_id} non trovata.")
        campi = []
        valori = []
        if patch_id is not None:
            campi.append("patch_id = ?")
            valori.append(patch_id)
        if stagione_id is not None:
            campi.append("stagione_id = ?")
            valori.append(stagione_id)
        if tipo is not None:
            campi.append("tipo = ?")
            valori.append(tipo)
        if descrizione is not None:
            campi.append("descrizione = ?")
            valori.append(descrizione)
        if livello_sblocco is not None:
            campi.append("livello_sblocco = ?")
            valori.append(livello_sblocco)
        if fonte_id is not None:
            campi.append("fonte_id = ?")
            valori.append(fonte_id)
        if data_verifica is not None:
            campi.append("data_verifica = ?")
            valori.append(data_verifica)
        if stato is not None:
            campi.append("stato = ?")
            valori.append(stato)
        if versione_corrente is not None:
            campi.append("versione_corrente = ?")
            valori.append(1 if versione_corrente else 0)
        if not campi:
            raise ValueError("Nessun campo da modificare.")
        valori.append(versione_id)
        cur.execute(f"UPDATE abilita_versioni SET {', '.join(campi)} WHERE id = ?", valori)
        if cur.rowcount == 0:
            raise ValueError(f"Versione abilità {versione_id} non trovata.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rimuovi_abilita_versioni(versione_id):
    """Rimuove una versione storica di abilità se non usata in build."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM abilita_versioni WHERE id = ?", (versione_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Versione abilità {versione_id} non trovata.")
        cur.execute("SELECT COUNT(*) FROM build_versioni_abilita WHERE abilita_versioni_id = ?", (versione_id,))
        n_assoc = cur.fetchone()[0]
        if n_assoc > 0:
            raise ValueError(
                f"Impossibile eliminare la versione {versione_id}: "
                f"è usata in {n_assoc} associazione/i build."
            )
        cur.execute("DELETE FROM abilita_versioni WHERE id = ?", (versione_id,))
        if cur.rowcount == 0:
            raise ValueError(f"Versione abilità {versione_id} non trovata.")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
