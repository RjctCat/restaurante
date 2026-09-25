# =========================================================
# RESTAURANTE CONTROL — LA ESQUINA
# Sistema en un solo archivo
# Flask + SQLite
# =========================================================

import os
import sqlite3
from datetime import datetime, date

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    g,
    render_template_string,
    flash
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

app = Flask(__name__)

app.secret_key = "cambiar-esta-clave-en-produccion"

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "restaurante.db"
)


# =========================================================
# BASE DE DATOS
# =========================================================

def get_db():
    """
    Obtiene una conexión SQLite asociada a la petición actual.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """
    Cierra la conexión al finalizar la petición.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """
    Crea las tablas de la aplicación.
    """

    db = sqlite3.connect(DB_PATH)

    db.executescript("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            telefono TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            personas INTEGER NOT NULL,
            mesa TEXT,
            nota TEXT,
            estado TEXT NOT NULL DEFAULT 'pendiente'
        );

        CREATE TABLE IF NOT EXISTS mesas (
            id TEXT PRIMARY KEY,
            zona TEXT NOT NULL,
            capacidad INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'disponible'
        );

        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            hora TEXT NOT NULL,
            metodo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            estado TEXT NOT NULL
        );
    """)

    db.commit()
    db.close()


def seed_data():
    """
    Inserta datos iniciales únicamente si la base de datos está vacía.
    """

    db = sqlite3.connect(DB_PATH)

    cantidad_mesas = db.execute(
        "SELECT COUNT(*) FROM mesas"
    ).fetchone()[0]

    cantidad_reservas = db.execute(
        "SELECT COUNT(*) FROM reservas"
    ).fetchone()[0]

    cantidad_movimientos = db.execute(
        "SELECT COUNT(*) FROM movimientos"
    ).fetchone()[0]

    hoy = date.today().isoformat()

    # -----------------------------------------------------
    # MESAS
    # -----------------------------------------------------

    if cantidad_mesas == 0:

        mesas = [
            ("T1", "Terraza", 2, "ocupada"),
            ("T2", "Terraza", 2, "disponible"),
            ("T3", "Terraza", 4, "limpieza"),

            ("S1", "Salón", 2, "disponible"),
            ("S2", "Salón", 4, "reservada"),
            ("S4", "Salón", 6, "reservada"),
            ("S6", "Salón", 8, "disponible"),

            ("B1", "Barra", 2, "reservada"),
            ("B2", "Barra", 2, "disponible"),
        ]

        db.executemany("""
            INSERT INTO mesas
            (id, zona, capacidad, estado)
            VALUES (?, ?, ?, ?)
        """, mesas)

    # -----------------------------------------------------
    # RESERVAS
    # -----------------------------------------------------

    if cantidad_reservas == 0:

        reservas = [
            (
                "Marisol Aguirre",
                "71234567",
                hoy,
                "13:00",
                4,
                "S2",
                "Cumpleaños",
                "confirmada"
            ),
            (
                "Diego Choque",
                "76543210",
                hoy,
                "13:30",
                2,
                "B1",
                "",
                "pendiente"
            ),
            (
                "Familia Rojas",
                "69988776",
                hoy,
                "19:00",
                6,
                "S4",
                "Silla para bebé",
                "confirmada"
            ),
            (
                "Elena Vargas",
                "77112233",
                hoy,
                "20:00",
                2,
                "T1",
                "",
                "atendida"
            ),
            (
                "Grupo Andino",
                "78899001",
                hoy,
                "21:00",
                8,
                "S6",
                "Mesa larga",
                "cancelada"
            )
        ]

        db.executemany("""
            INSERT INTO reservas
            (cliente, telefono, fecha, hora, personas, mesa, nota, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, reservas)

    # -----------------------------------------------------
    # MOVIMIENTOS
    # -----------------------------------------------------

    if cantidad_movimientos == 0:

        movimientos = [
            (
                "Mesa T1 — almuerzo",
                145,
                "12:40",
                "tarjeta",
                "ingreso",
                "cobrado"
            ),
            (
                "Mesa S2 — bebidas",
                38,
                "13:05",
                "efectivo",
                "ingreso",
                "cobrado"
            ),
            (
                "Compra de servilletas",
                22,
                "11:15",
                "efectivo",
                "egreso",
                "pagado"
            ),
            (
                "Mesa B1 — aperitivos",
                64,
                "13:40",
                "QR",
                "ingreso",
                "pendiente"
            ),
            (
                "Mesa S4 — cena",
                210,
                "14:02",
                "QR",
                "ingreso",
                "pendiente"
            )
        ]

        db.executemany("""
            INSERT INTO movimientos
            (concepto, monto, hora, metodo, tipo, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, movimientos)

    db.commit()
    db.close()


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def hoy():
    return date.today().isoformat()


def hora_actual():
    return datetime.now().strftime("%H:%M")


def cap(texto):
    if not texto:
        return ""

    return texto[0].upper() + texto[1:]


# =========================================================
# PLANTILLA BASE
# =========================================================

BASE = r"""
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
               initial-scale=1,
               viewport-fit=cover">

<title>Restaurante Control — La Esquina</title>

<link rel="preconnect"
      href="https://fonts.googleapis.com">

<link rel="preconnect"
      href="https://fonts.gstatic.com"
      crossorigin>

<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Work+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
      rel="stylesheet">

<style>

:root{

    --cream:#f2ede2;
    --paper:#faf7f0;

    --charcoal:#2a2520;
    --charcoal-soft:#5b544a;

    --terracotta:#bd5a37;
    --terracotta-soft:#f0d9cd;

    --mustard:#bf8c2b;
    --mustard-soft:#f2e4bd;

    --sage:#748258;
    --sage-soft:#dde4cd;

    --line:#e2d9c7;

    --sidebar:#221e19;
    --sidebar-text:#cfc6b6;

    --danger:#a8412c;
}

*{
    box-sizing:border-box;
}

html{
    scroll-padding-top:
        env(safe-area-inset-top,0px);
}

body{

    margin:0;

    background:var(--cream);

    color:var(--charcoal);

    font-family:
        'Work Sans',
        sans-serif;

    -webkit-font-smoothing:antialiased;
}

h1,
h2,
h3{

    font-family:
        'Fraunces',
        serif;

    font-weight:600;

    margin:0;
}

.mono{

    font-family:
        'IBM Plex Mono',
        monospace;
}

button{

    font-family:inherit;
    cursor:pointer;
}

input,
select,
textarea{

    font-family:inherit;
}

:focus-visible{

    outline:
        2px solid
        var(--terracotta);

    outline-offset:2px;
}


/* =====================================================
   LAYOUT
   ===================================================== */

.app{

    display:flex;

    min-height:100vh;
}

.sidebar{

    width:220px;

    background:
        var(--sidebar);

    color:
        var(--sidebar-text);

    padding:
        28px 18px;

    flex-shrink:0;

    display:flex;

    flex-direction:column;

    gap:28px;

    padding-top:
        calc(
            28px +
            env(safe-area-inset-top,0px)
        );
}

.brand{

    font-family:
        'Fraunces',
        serif;

    font-size:1.3rem;

    color:#f2ede2;

    font-weight:600;

    line-height:1.2;
}

.brand span{

    display:block;

    font-family:
        'Work Sans',
        sans-serif;

    font-size:.68rem;

    letter-spacing:.03em;

    color:#8c8272;

    margin-top:4px;

    font-weight:400;
}

.navlist{

    display:flex;

    flex-direction:column;

    gap:4px;
}

.navlink{

    display:flex;

    align-items:center;

    gap:10px;

    padding:10px 12px;

    border-radius:8px;

    background:none;

    border:none;

    color:var(--sidebar-text);

    text-align:left;

    font-size:.94rem;

    transition:
        background .15s;
}

.navlink:hover{

    background:#332c24;
}

.navlink.active{

    background:
        var(--terracotta);

    color:#fff;
}

.main{

    flex:1;

    min-width:0;

    padding:
        32px 36px 100px;

    max-width:1100px;
}

.topline{

    display:flex;

    justify-content:space-between;

    align-items:baseline;

    margin-bottom:22px;

    flex-wrap:wrap;

    gap:10px;
}

.topline h1{

    font-size:1.6rem;
}

.subtitle{

    color:
        var(--charcoal-soft);

    font-size:.92rem;

    margin-top:4px;
}


/* =====================================================
   CARDS
   ===================================================== */

.grid-stats{

    display:grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(150px,1fr)
        );

    gap:14px;

    margin-bottom:22px;
}

.card{

    background:
        var(--paper);

    border:
        1px solid var(--line);

    border-radius:10px;

    padding:16px 18px;
}

.stat-label{

    font-size:.78rem;

    color:
        var(--charcoal-soft);

    margin-bottom:6px;
}

.stat-value{

    font-family:
        'IBM Plex Mono',
        monospace;

    font-size:1.5rem;

    font-weight:500;
}

.stat-value.terracotta{

    color:
        var(--terracotta);
}

.stat-value.sage{

    color:
        var(--sage);
}

.stat-value.mustard{

    color:
        var(--mustard);
}

.row2{

    display:grid;

    grid-template-columns:
        1.4fr 1fr;

    gap:16px;

    align-items:start;
}

@media(max-width:820px){

    .row2{

        grid-template-columns:1fr;
    }
}


/* =====================================================
   BOTONES
   ===================================================== */

.btn{

    border:none;

    border-radius:8px;

    padding:10px 18px;

    font-size:.9rem;

    font-weight:500;

    transition:
        opacity .15s;
}

.btn:hover{

    opacity:.88;
}

.btn-primary{

    background:
        var(--terracotta);

    color:#fff;
}

.btn-secondary{

    background:transparent;

    border:
        1px solid var(--line);

    color:
        var(--charcoal);
}

.btn-danger{

    background:
        var(--danger);

    color:#fff;
}

.btn-sm{

    padding:
        6px 12px;

    font-size:.8rem;

    border-radius:6px;
}


/* =====================================================
   TOOLBAR
   ===================================================== */

.toolbar{

    display:flex;

    gap:10px;

    flex-wrap:wrap;

    margin-bottom:18px;

    align-items:center;

    justify-content:space-between;
}

.toolbar-left{

    display:flex;

    gap:10px;

    flex-wrap:wrap;

    flex:1;
}

input[type=text],
input[type=search],
input[type=tel],
input[type=date],
input[type=time],
input[type=number],
select,
textarea{

    border:
        1px solid var(--line);

    background:
        var(--paper);

    color:
        var(--charcoal);

    border-radius:8px;

    padding:
        9px 12px;

    font-size:.88rem;
}

input[type=search]{

    min-width:200px;

    flex:1;
}


/* =====================================================
   TABLAS
   ===================================================== */

table{

    width:100%;

    border-collapse:collapse;

    font-size:.87rem;
}

th{

    text-align:left;

    font-weight:500;

    color:
        var(--charcoal-soft);

    font-size:.76rem;

    letter-spacing:.02em;

    padding:8px 10px;

    border-bottom:
        1px solid var(--line);
}

td{

    padding:10px;

    border-bottom:
        1px solid var(--line);
}

.tablewrap{

    overflow-x:auto;

    background:
        var(--paper);

    border:
        1px solid var(--line);

    border-radius:10px;
}

.tablewrap table{

    min-width:560px;
}


/* =====================================================
   BADGES
   ===================================================== */

.badge{

    display:inline-block;

    padding:
        3px 10px;

    border-radius:999px;

    font-size:.74rem;

    font-weight:500;
}

.badge-confirmada{

    background:
        var(--sage-soft);

    color:#3f4a2c;
}

.badge-pendiente{

    background:
        var(--mustard-soft);

    color:#6b4f14;
}

.badge-atendida{

    background:
        #dcdcd6;

    color:#44403a;
}

.badge-cancelada{

    background:
        #f2d6ce;

    color:var(--danger);
}

.badge-disponible{

    background:
        var(--sage-soft);

    color:#3f4a2c;
}

.badge-ocupada{

    background:
        var(--terracotta-soft);

    color:#7c3a1f;
}

.badge-reservada{

    background:
        var(--mustard-soft);

    color:#6b4f14;
}

.badge-limpieza{

    background:
        #dcdcd6;

    color:#44403a;
}


/* =====================================================
   ACTIVIDAD
   ===================================================== */

.section-title{

    font-size:1.05rem;

    margin-bottom:12px;
}

.activity-item{

    display:flex;

    justify-content:space-between;

    padding:9px 0;

    border-bottom:
        1px solid var(--line);

    font-size:.88rem;
}

.activity-item:last-child{

    border-bottom:none;
}

.activity-time{

    color:
        var(--charcoal-soft);

    font-family:
        'IBM Plex Mono',
        monospace;

    font-size:.8rem;
}


/* =====================================================
   MESAS
   ===================================================== */

.zone{

    margin-bottom:26px;
}

.zone h3{

    margin-bottom:12px;

    font-size:1rem;
}

.tablecards{

    display:grid;

    grid-template-columns:
        repeat(
            auto-fill,
            minmax(160px,1fr)
        );

    gap:12px;
}

.tablecard{

    background:
        var(--paper);

    border:
        1px solid var(--line);

    border-radius:10px;

    padding:14px;
}

.tablecard .num{

    font-family:
        'IBM Plex Mono',
        monospace;

    font-size:1.1rem;
}

.tablecard .cap{

    font-size:.8rem;

    color:
        var(--charcoal-soft);

    margin:4px 0 10px;
}

.tablecard select{

    width:100%;
}


/* =====================================================
   MODAL
   ===================================================== */

.modal-overlay{

    position:fixed;

    inset:0;

    background:
        rgba(20,17,13,.5);

    display:none;

    align-items:center;

    justify-content:center;

    padding:20px;

    z-index:50;
}

.modal{

    background:
        var(--paper);

    border-radius:12px;

    padding:24px;

    width:100%;

    max-width:440px;

    max-height:88vh;

    overflow-y:auto;
}

.modal h2{

    font-size:1.2rem;

    margin-bottom:16px;
}

.modal-overlay.open{

    display:flex;
}

.field{

    margin-bottom:12px;

    display:flex;

    flex-direction:column;

    gap:5px;
}

.field label{

    font-size:.8rem;

    color:
        var(--charcoal-soft);
}

.field input,
.field select,
.field textarea{

    width:100%;
}

.modal-actions{

    display:flex;

    justify-content:flex-end;

    gap:10px;

    margin-top:18px;
}


/* =====================================================
   TOAST
   ===================================================== */

.toast{

    position:fixed;

    bottom:24px;

    left:50%;

    transform:
        translateX(-50%);

    background:
        var(--charcoal);

    color:
        var(--cream);

    padding:
        11px 20px;

    border-radius:8px;

    font-size:.86rem;

    z-index:100;
}


/* =====================================================
   ALERTAS
   ===================================================== */

.alert{

    padding:12px 15px;

    border-radius:8px;

    margin-bottom:18px;

    font-size:.88rem;
}

.alert-success{

    background:
        var(--sage-soft);

    color:#3f4a2c;
}

.alert-danger{

    background:
        #f2d6ce;

    color:var(--danger);
}

.alert-info{

    background:
        var(--mustard-soft);

    color:#6b4f14;
}


/* =====================================================
   QR
   ===================================================== */

.qr-note{

    background:
        var(--mustard-soft);

    border:
        1px solid var(--mustard);

    border-radius:8px;

    padding:
        12px 14px;

    font-size:.82rem;

    color:#5c430f;

    margin-bottom:16px;
}


/* =====================================================
   EMPTY
   ===================================================== */

.empty{

    padding:
        30px 10px;

    text-align:center;

    color:
        var(--charcoal-soft);

    font-size:.9rem;
}


/* =====================================================
   BOTTOM NAV
   ===================================================== */

.bottomnav{

    display:none;
}

@media(max-width:860px){

    .sidebar{

        display:none;
    }

    .main{

        padding:
            24px 16px 90px;

        max-width:100%;
    }

    .bottomnav{

        display:flex;

        position:fixed;

        bottom:0;

        left:0;

        right:0;

        background:
            var(--sidebar);

        padding:
            8px 6px
            calc(
                8px +
                env(safe-area-inset-bottom,0px)
            );

        justify-content:space-around;

        z-index:40;
    }

    .bottomnav a{

        background:none;

        border:none;

        color:
            var(--sidebar-text);

        font-size:.68rem;

        text-decoration:none;

        display:flex;

        flex-direction:column;

        align-items:center;

        gap:4px;

        padding:6px 8px;

        border-radius:8px;
    }

    .bottomnav a.active{

        color:#fff;

        background:
            var(--terracotta);
    }

    .topline h1{

        font-size:1.4rem;
    }
}

</style>

</head>

<body>

<div class="app">

    <!-- =================================================
         SIDEBAR
         ================================================= -->

    <nav class="sidebar">

        <div class="brand">

            La Esquina

            <span>
                Restaurante Control
            </span>

        </div>

        <div class="navlist">

            <a
                class="navlink {% if active == 'resumen' %}active{% endif %}"
                href="{{ url_for('index') }}"
            >
                Resumen
            </a>

            <a
                class="navlink {% if active == 'reservas' %}active{% endif %}"
                href="{{ url_for('reservas') }}"
            >
                Reservas
            </a>

            <a
                class="navlink {% if active == 'mesas' %}active{% endif %}"
                href="{{ url_for('mesas') }}"
            >
                Mesas
            </a>

            <a
                class="navlink {% if active == 'caja' %}active{% endif %}"
                href="{{ url_for('caja') }}"
            >
                Caja
            </a>

        </div>

    </nav>


    <!-- =================================================
         CONTENIDO
         ================================================= -->

    <main class="main">

        {% with messages = get_flashed_messages(with_categories=true) %}

            {% for category, message in messages %}

                <div class="alert alert-{{ category }}">
                    {{ message }}
                </div>

            {% endfor %}

        {% endwith %}

        {{ body|safe }}

    </main>

</div>


<!-- =====================================================
     NAVEGACIÓN MÓVIL
     ===================================================== -->

<nav class="bottomnav">

    <a
        href="{{ url_for('index') }}"
        class="{% if active == 'resumen' %}active{% endif %}"
    >
        Resumen
    </a>

    <a
        href="{{ url_for('reservas') }}"
        class="{% if active == 'reservas' %}active{% endif %}"
    >
        Reservas
    </a>

    <a
        href="{{ url_for('mesas') }}"
        class="{% if active == 'mesas' %}active{% endif %}"
    >
        Mesas
    </a>

    <a
        href="{{ url_for('caja') }}"
        class="{% if active == 'caja' %}active{% endif %}"
    >
        Caja
    </a>

</nav>

</body>

</html>
"""


def render(body, active="resumen"):

    return render_template_string(
        BASE,
        body=body,
        active=active
    )


# =========================================================
# RESUMEN
# =========================================================

@app.route("/")
def index():

    db = get_db()

    fecha_hoy = hoy()

    ventas_hoy = db.execute("""
        SELECT COALESCE(SUM(monto), 0)
        FROM movimientos
        WHERE tipo='ingreso'
        AND estado != 'pendiente'
    """).fetchone()[0]

    reservas_hoy = db.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE fecha=?
    """, (fecha_hoy,)).fetchone()[0]

    mesas_libres = db.execute("""
        SELECT COUNT(*)
        FROM mesas
        WHERE estado='disponible'
    """).fetchone()[0]

    qr_pendientes = db.execute("""
        SELECT COUNT(*)
        FROM movimientos
        WHERE metodo='QR'
        AND estado='pendiente'
    """).fetchone()[0]

    movimientos = db.execute("""
        SELECT *
        FROM movimientos
        ORDER BY hora DESC
        LIMIT 6
    """).fetchall()

    reservas = db.execute("""
        SELECT *
        FROM reservas
        ORDER BY hora DESC
        LIMIT 6
    """).fetchall()

    actividad = []

    for m in movimientos:

        texto_tipo = (
            "Cobro"
            if m["tipo"] == "ingreso"
            else "Gasto"
        )

        actividad.append({
            "texto":
                f"{texto_tipo}: "
                f"{m['concepto']} "
                f"({m['metodo']})",
            "hora": m["hora"]
        })

    for r in reservas:

        actividad.append({
            "texto":
                f"Reserva de "
                f"{r['cliente']} — "
                f"{r['estado']}",
            "hora": r["hora"]
        })

    actividad.sort(
        key=lambda x: x["hora"],
        reverse=True
    )

    actividad = actividad[:6]

    actividades_html = ""

    for a in actividad:

        actividades_html += f"""
        <div class="activity-item">
            <span>{a['texto']}</span>
            <span class="activity-time">
                {a['hora']}
            </span>
        </div>
        """

    if not actividades_html:

        actividades_html = """
        <div class="empty">
            Aún no hay actividad registrada.
        </div>
        """

    body = f"""

    <div class="topline">

        <div>

            <h1>
                Buen turno, equipo de La Esquina
            </h1>

            <div class="subtitle">
                Estado del servicio de hoy,
                {fecha_hoy}.
            </div>

        </div>

        <a
            class="btn btn-primary"
            href="{url_for('crear_reserva')}"
        >
            Nueva reserva
        </a>

    </div>


    <div class="grid-stats">

        <div class="card">

            <div class="stat-label">
                Ventas del día
            </div>

            <div class="stat-value terracotta mono">
                Bs {ventas_hoy:.2f}
            </div>

        </div>


        <div class="card">

            <div class="stat-label">
                Reservas de hoy
            </div>

            <div class="stat-value mono">
                {reservas_hoy}
            </div>

        </div>


        <div class="card">

            <div class="stat-label">
                Mesas libres
            </div>

            <div class="stat-value sage mono">
                {mesas_libres}
            </div>

        </div>


        <div class="card">

            <div class="stat-label">
                Pagos QR pendientes
            </div>

            <div class="stat-value mustard mono">
                {qr_pendientes}
            </div>

        </div>

    </div>


    <div class="row2">

        <div class="card">

            <h3 class="section-title">
                Estado de las mesas
            </h3>

            <div class="tablecards">
    """

    mesas = db.execute("""
        SELECT *
        FROM mesas
        ORDER BY zona, id
    """).fetchall()

    for mesa in mesas:

        body += f"""

            <div class="tablecard">

                <div class="num">
                    {mesa['id']}
                </div>

                <div class="cap">
                    {mesa['zona']}
                    · Cap. {mesa['capacidad']}
                </div>

                <span class="badge badge-{mesa['estado']}">
                    {cap(mesa['estado'])}
                </span>

            </div>
        """

    body += """

            </div>

        </div>


        <div class="card">

            <h3 class="section-title">
                Actividad reciente
            </h3>

    """

    body += actividades_html

    body += """

        </div>

    </div>
    """

    return render(body, "resumen")


# =========================================================
# RESERVAS
# =========================================================

@app.route("/reservas")
def reservas():

    db = get_db()

    texto = request.args.get(
        "buscar",
        ""
    ).strip()

    estado = request.args.get(
        "estado",
        "todos"
    )

    sql = """
        SELECT *
        FROM reservas
        WHERE 1=1
    """

    params = []

    if texto:

        sql += """
            AND (
                cliente LIKE ?
                OR telefono LIKE ?
            )
        """

        buscar = f"%{texto}%"

        params.extend([
            buscar,
            buscar
        ])

    if estado != "todos":

        sql += """
            AND estado=?
        """

        params.append(estado)

    sql += """
        ORDER BY fecha, hora
    """

    lista = db.execute(
        sql,
        params
    ).fetchall()

    filas = ""

    for r in lista:

        filas += f"""

        <tr>

            <td>

                <strong>
                    {r['cliente']}
                </strong>

                {
                    f'<div class="subtitle">{r["nota"]}</div>'
                    if r["nota"]
                    else ""
                }

            </td>

            <td class="mono">
                {r['telefono']}
            </td>

            <td class="mono">
                {r['fecha']}
            </td>

            <td class="mono">
                {r['hora']}
            </td>

            <td class="mono">
                {r['personas']}
            </td>

            <td class="mono">
                {r['mesa'] or '—'}
            </td>

            <td>

                <span class="badge badge-{r['estado']}">
                    {cap(r['estado'])}
                </span>

            </td>

            <td>

                <a
                    class="btn btn-secondary btn-sm"
                    href="{url_for('editar_reserva', rid=r['id'])}"
                >
                    Editar
                </a>

            </td>

        </tr>

        """

    if not filas:

        filas = """
        <tr>
            <td colspan="8">
                <div class="empty">
                    No se encontraron reservas.
                </div>
            </td>
        </tr>
        """

    body = f"""

    <div class="topline">

        <div>

            <h1>
                Reservas
            </h1>

            <div class="subtitle">
                Gestiona las reservas del restaurante.
            </div>

        </div>

        <a
            class="btn btn-primary"
            href="{url_for('crear_reserva')}"
        >
            Nueva reserva
        </a>

    </div>


    <div class="toolbar">

        <form
            method="get"
            class="toolbar-left"
        >

            <input
                type="search"
                name="buscar"
                placeholder="Buscar por nombre o teléfono"
                value="{texto}"
            >

            <select name="estado">

                <option value="todos"
                    {"selected" if estado == "todos" else ""}>
                    Todos los estados
                </option>

                <option value="confirmada"
                    {"selected" if estado == "confirmada" else ""}>
                    Confirmada
                </option>

                <option value="pendiente"
                    {"selected" if estado == "pendiente" else ""}>
                    Pendiente
                </option>

                <option value="atendida"
                    {"selected" if estado == "atendida" else ""}>
                    Atendida
                </option>

                <option value="cancelada"
                    {"selected" if estado == "cancelada" else ""}>
                    Cancelada
                </option>

            </select>

            <button class="btn btn-secondary">
                Buscar
            </button>

        </form>

    </div>


    <div class="tablewrap">

        <table>

            <thead>

                <tr>

                    <th>Cliente</th>
                    <th>Teléfono</th>
                    <th>Fecha</th>
                    <th>Hora</th>
                    <th>Personas</th>
                    <th>Mesa</th>
                    <th>Estado</th>
                    <th></th>

                </tr>

            </thead>

            <tbody>

                {filas}

            </tbody>

        </table>

    </div>

    """

    return render(body, "reservas")


# =========================================================
# CREAR RESERVA
# =========================================================

@app.route(
    "/reserva/crear",
    methods=["GET", "POST"]
)
def crear_reserva():

    db = get_db()

    if request.method == "POST":

        cliente = request.form.get(
            "cliente",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        fecha = request.form.get(
            "fecha",
            ""
        )

        hora = request.form.get(
            "hora",
            ""
        )

        personas = request.form.get(
            "personas",
            "1"
        )

        mesa = request.form.get(
            "mesa",
            ""
        )

        nota = request.form.get(
            "nota",
            ""
        ).strip()

        if not cliente or not telefono:

            flash(
                "Completa cliente y teléfono.",
                "danger"
            )

            return redirect(
                url_for("crear_reserva")
            )

        try:

            personas = int(personas)

            if personas < 1:
                raise ValueError

        except ValueError:

            flash(
                "La cantidad de personas no es válida.",
                "danger"
            )

            return redirect(
                url_for("crear_reserva")
            )

        db.execute("""
            INSERT INTO reservas
            (
                cliente,
                telefono,
                fecha,
                hora,
                personas,
                mesa,
                nota,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente,
            telefono,
            fecha,
            hora,
            personas,
            mesa or None,
            nota,
            "pendiente"
        ))

        if mesa:

            db.execute("""
                UPDATE mesas
                SET estado='reservada'
                WHERE id=?
            """, (mesa,))

        db.commit()

        flash(
            "Reserva creada correctamente.",
            "success"
        )

        return redirect(
            url_for("reservas")
        )

    mesas = db.execute("""
        SELECT *
        FROM mesas
        WHERE estado='disponible'
        ORDER BY zona, id
    """).fetchall()

    opciones_mesas = ""

    for mesa in mesas:

        opciones_mesas += f"""
        <option value="{mesa['id']}">
            {mesa['id']} —
            {mesa['zona']}
            (cap. {mesa['capacidad']})
        </option>
        """

    body = f"""

    <div class="topline">

        <div>

            <h1>
                Nueva reserva
            </h1>

            <div class="subtitle">
                Registrar una nueva reserva.
            </div>

        </div>

    </div>


    <form
        method="post"
        class="card"
    >

        <div class="field">

            <label>
                Cliente
            </label>

            <input
                required
                type="text"
                name="cliente"
            >

        </div>


        <div class="field">

            <label>
                Teléfono
            </label>

            <input
                required
                type="tel"
                name="telefono"
            >

        </div>


        <div class="field">

            <label>
                Fecha
            </label>

            <input
                required
                type="date"
                name="fecha"
                value="{hoy()}"
            >

        </div>


        <div class="field">

            <label>
                Hora
            </label>

            <input
                required
                type="time"
                name="hora"
                value="{hora_actual()}"
            >

        </div>


        <div class="field">

            <label>
                Cantidad de personas
            </label>

            <input
                required
                type="number"
                min="1"
                name="personas"
                value="2"
            >

        </div>


        <div class="field">

            <label>
                Mesa
            </label>

            <select name="mesa">

                <option value="">
                    Sin asignar
                </option>

                {opciones_mesas}

            </select>

        </div>


        <div class="field">

            <label>
                Nota
            </label>

            <textarea
                name="nota"
                rows="3"
            ></textarea>

        </div>


        <div class="modal-actions">

            <a
                href="{url_for('reservas')}"
                class="btn btn-secondary"
            >
                Cancelar
            </a>

            <button
                type="submit"
                class="btn btn-primary"
            >
                Guardar reserva
            </button>

        </div>

    </form>

    """

    return render(body, "reservas")


# =========================================================
# EDITAR RESERVA
# =========================================================

@app.route(
    "/reserva/<int:rid>/editar",
    methods=["GET", "POST"]
)
def editar_reserva(rid):

    db = get_db()

    reserva = db.execute("""
        SELECT *
        FROM reservas
        WHERE id=?
    """, (rid,)).fetchone()

    if reserva is None:

        flash(
            "Reserva no encontrada.",
            "danger"
        )

        return redirect(
            url_for("reservas")
        )

    if request.method == "POST":

        cliente = request.form["cliente"].strip()
        telefono = request.form["telefono"].strip()
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        personas = int(request.form["personas"])
        mesa_nueva = request.form.get("mesa") or None
        nota = request.form.get("nota", "").strip()
        estado = request.form["estado"]

        mesa_anterior = reserva["mesa"]

        db.execute("""
            UPDATE reservas
            SET
                cliente=?,
                telefono=?,
                fecha=?,
                hora=?,
                personas=?,
                mesa=?,
                nota=?,
                estado=?
            WHERE id=?
        """, (
            cliente,
            telefono,
            fecha,
            hora,
            personas,
            mesa_nueva,
            nota,
            estado,
            rid
        ))

        # Liberar mesa anterior
        if (
            mesa_anterior
            and mesa_anterior != mesa_nueva
        ):

            db.execute("""
                UPDATE mesas
                SET estado='disponible'
                WHERE id=?
            """, (mesa_anterior,))

        # Reservar nueva mesa
        if mesa_nueva:

            db.execute("""
                UPDATE mesas
                SET estado='reservada'
                WHERE id=?
            """, (mesa_nueva,))

        db.commit()

        flash(
            "Reserva actualizada.",
            "success"
        )

        return redirect(
            url_for("reservas")
        )

    mesas = db.execute("""
        SELECT *
        FROM mesas
        ORDER BY zona, id
    """).fetchall()

    opciones_mesas = ""

    for mesa in mesas:

        selected = (
            "selected"
            if mesa["id"] == reserva["mesa"]
            else ""
        )

        opciones_mesas += f"""
        <option
            value="{mesa['id']}"
            {selected}
        >
            {mesa['id']} —
            {mesa['zona']}
            (cap. {mesa['capacidad']})
        </option>
        """

    body = f"""

    <div class="topline">

        <div>

            <h1>
                Editar reserva
            </h1>

            <div class="subtitle">
                Reserva #{reserva['id']}
            </div>

        </div>

    </div>


    <form
        method="post"
        class="card"
    >

        <div class="field">

            <label>
                Cliente
            </label>

            <input
                required
                type="text"
                name="cliente"
                value="{reserva['cliente']}"
            >

        </div>


        <div class="field">

            <label>
                Teléfono
            </label>

            <input
                required
                type="tel"
                name="telefono"
                value="{reserva['telefono']}"
            >

        </div>


        <div class="field">

            <label>
                Fecha
            </label>

            <input
                required
                type="date"
                name="fecha"
                value="{reserva['fecha']}"
            >

        </div>


        <div class="field">

            <label>
                Hora
            </label>

            <input
                required
                type="time"
                name="hora"
                value="{reserva['hora']}"
            >

        </div>


        <div class="field">

            <label>
                Personas
            </label>

            <input
                required
                type="number"
                min="1"
                name="personas"
                value="{reserva['personas']}"
            >

        </div>


        <div class="field">

            <label>
                Mesa
            </label>

            <select name="mesa">

                <option value="">
                    Sin asignar
                </option>

                {opciones_mesas}

            </select>

        </div>


        <div class="field">

            <label>
                Estado
            </label>

            <select name="estado">

                <option
                    value="confirmada"
                    {"selected" if reserva["estado"] == "confirmada" else ""}
                >
                    Confirmada
                </option>

                <option
                    value="pendiente"
                    {"selected" if reserva["estado"] == "pendiente" else ""}
                >
                    Pendiente
                </option>

                <option
                    value="atendida"
                    {"selected" if reserva["estado"] == "atendida" else ""}
                >
                    Atendida
                </option>

                <option
                    value="cancelada"
                    {"selected" if reserva["estado"] == "cancelada" else ""}
                >
                    Cancelada
                </option>

            </select>

        </div>


        <div class="field">

            <label>
                Nota
            </label>

            <textarea
                name="nota"
                rows="3"
            >{reserva['nota'] or ''}</textarea>

        </div>


        <div class="modal-actions">

            <a
                href="{url_for('reservas')}"
                class="btn btn-secondary"
            >
                Cancelar
            </a>

            <button
                type="submit"
                class="btn btn-primary"
            >
                Guardar cambios
            </button>

        </div>

    </form>

    """

    return render(body, "reservas")


# =========================================================
# MESAS
# =========================================================

@app.route("/mesas")
def mesas():

    db = get_db()

    lista = db.execute("""
        SELECT *
        FROM mesas
        ORDER BY zona, id
    """).fetchall()

    zonas = {}

    for mesa in lista:

        zona = mesa["zona"]

        if zona not in zonas:
            zonas[zona] = []

        zonas[zona].append(mesa)

    body = """

    <div class="topline">

        <div>

            <h1>
                Mesas
            </h1>

            <div class="subtitle">
                Consulta y actualiza el estado
                de cada mesa.
            </div>

        </div>

    </div>

    """

    for zona, mesas_zona in zonas.items():

        body += f"""

        <div class="zone">

            <h3>
                {zona}
            </h3>

            <div class="tablecards">

        """

        for mesa in mesas_zona:

            body += f"""

            <div class="tablecard">

                <div class="num">
                    {mesa['id']}
                </div>

                <div class="cap">
                    Capacidad:
                    {mesa['capacidad']}
                </div>

                <span class="badge badge-{mesa['estado']}">
                    {cap(mesa['estado'])}
                </span>

                <form
                    method="post"
                    action="{url_for('cambiar_estado_mesa', mesa_id=mesa['id'])}"
                    style="margin-top:10px;"
                >

                    <select
                        name="estado"
                        onchange="this.form.submit()"
                    >

        """

            estados = [
                "disponible",
                "ocupada",
                "reservada",
                "limpieza"
            ]

            for estado in estados:

                selected = (
                    "selected"
                    if estado == mesa["estado"]
                    else ""
                )

                body += f"""

                        <option
                            value="{estado}"
                            {selected}
                        >
                            {cap(estado)}
                        </option>

                """

            body += """

                    </select>

                </form>

            </div>

            """

        body += """

            </div>

        </div>

        """

    return render(body, "mesas")


# =========================================================
# CAMBIAR ESTADO DE MESA
# =========================================================

@app.route(
    "/mesa/<mesa_id>/estado",
    methods=["POST"]
)
def cambiar_estado_mesa(mesa_id):

    estado = request.form.get(
        "estado"
    )

    estados_validos = [
        "disponible",
        "ocupada",
        "reservada",
        "limpieza"
    ]

    if estado not in estados_validos:

        flash(
            "Estado de mesa no válido.",
            "danger"
        )

        return redirect(
            url_for("mesas")
        )

    db = get_db()

    db.execute("""
        UPDATE mesas
        SET estado=?
        WHERE id=?
    """, (
        estado,
        mesa_id
    ))

    db.commit()

    flash(
        f"Mesa {mesa_id} actualizada.",
        "success"
    )

    return redirect(
        url_for("mesas")
    )


# =========================================================
# CAJA
# =========================================================

@app.route("/caja")
def caja():

    db = get_db()

    ingresos = db.execute("""
        SELECT COALESCE(SUM(monto),0)
        FROM movimientos
        WHERE tipo='ingreso'
        AND estado!='pendiente'
    """).fetchone()[0]

    egresos = db.execute("""
        SELECT COALESCE(SUM(monto),0)
        FROM movimientos
        WHERE tipo='egreso'
    """).fetchone()[0]

    total = ingresos - egresos

    qr_pendientes = db.execute("""
        SELECT *
        FROM movimientos
        WHERE metodo='QR'
        AND estado='pendiente'
        ORDER BY hora DESC
    """).fetchall()

    movimientos = db.execute("""
        SELECT *
        FROM movimientos
        ORDER BY hora DESC, id DESC
    """).fetchall()

    body = f"""

    <div class="topline">

        <div>

            <h1>
                Caja
            </h1>

            <div class="subtitle">
                Resumen de ingresos, egresos
                y movimientos del turno.
            </div>

        </div>

        <a
            class="btn btn-primary"
            href="{url_for('crear_movimiento')}"
        >
            Registrar movimiento
        </a>

    </div>


    <div class="grid-stats">

        <div class="card">

            <div class="stat-label">
                Total del día
            </div>

            <div class="stat-value terracotta mono">
                Bs {total:.2f}
            </div>

        </div>


        <div class="card">

            <div class="stat-label">
                Ingresos
            </div>

            <div class="stat-value sage mono">
                Bs {ingresos:.2f}
            </div>

        </div>


        <div class="card">

            <div class="stat-label">
                Egresos
            </div>

            <div class="stat-value mono">
                Bs {egresos:.2f}
            </div>

        </div>

    </div>


    <div class="qr-note">

        Los pagos QR de esta versión son
        un registro de demostración.
        Marcar un pago como cobrado dentro
        de la aplicación no confirma una
        transferencia bancaria real.

        Verifica siempre el ingreso en la
        cuenta antes de dar el pedido
        por pagado.

    </div>


    <h3 class="section-title">
        Pagos QR pendientes
    </h3>


    <div
        class="tablewrap"
        style="margin-bottom:24px;"
    >

        <table>

            <thead>

                <tr>

                    <th>
                        Concepto
                    </th>

                    <th>
                        Monto
                    </th>

                    <th>
                        Hora
                    </th>

                    <th>
                    </th>

                </tr>

            </thead>

            <tbody>
    """

    if qr_pendientes:

        for m in qr_pendientes:

            body += f"""

                <tr>

                    <td>
                        {m['concepto']}
                    </td>

                    <td class="mono">
                        Bs {m['monto']:.2f}
                    </td>

                    <td class="mono">
                        {m['hora']}
                    </td>

                    <td>

                        <form
                            method="post"
                            action="{url_for('marcar_cobrado', mid=m['id'])}"
                        >

                            <button
                                class="btn btn-secondary btn-sm"
                            >
                                Marcar como cobrado
                            </button>

                        </form>

                    </td>

                </tr>

            """

    else:

        body += """

                <tr>

                    <td colspan="4">

                        <div class="empty">
                            No hay pagos QR pendientes.
                        </div>

                    </td>

                </tr>

        """

    body += """

            </tbody>

        </table>

    </div>


    <h3 class="section-title">
        Movimientos del día
    </h3>


    <div class="tablewrap">

        <table>

            <thead>

                <tr>

                    <th>
                        Concepto
                    </th>

                    <th>
                        Monto
                    </th>

                    <th>
                        Hora
                    </th>

                    <th>
                        Método
                    </th>

                    <th>
                        Tipo
                    </th>

                    <th>
                        Estado
                    </th>

                </tr>

            </thead>

            <tbody>

    """

    if movimientos:

        for m in movimientos:

            signo = (
                "−"
                if m["tipo"] == "egreso"
                else ""
            )

            badge_estado = (
                "pendiente"
                if m["estado"] == "pendiente"
                else "confirmada"
            )

            body += f"""

                <tr>

                    <td>
                        {m['concepto']}
                    </td>

                    <td class="mono">
                        {signo}Bs {m['monto']:.2f}
                    </td>

                    <td class="mono">
                        {m['hora']}
                    </td>

                    <td>
                        {m['metodo']}
                    </td>

                    <td>
                        {cap(m['tipo'])}
                    </td>

                    <td>

                        <span
                            class="badge badge-{badge_estado}"
                        >
                            {cap(m['estado'])}
                        </span>

                    </td>

                </tr>

            """

    else:

        body += """

                <tr>

                    <td colspan="6">

                        <div class="empty">
                            No hay movimientos.
                        </div>

                    </td>

                </tr>

        """

    body += """

            </tbody>

        </table>

    </div>

    """

    return render(body, "caja")


# =========================================================
# CREAR MOVIMIENTO
# =========================================================

@app.route(
    "/movimiento/crear",
    methods=["GET", "POST"]
)
def crear_movimiento():

    if request.method == "POST":

        concepto = request.form.get(
            "concepto",
            ""
        ).strip()

        monto_texto = request.form.get(
            "monto",
            "0"
        )

        tipo = request.form.get(
            "tipo"
        )

        metodo = request.form.get(
            "metodo"
        )

        if not concepto:

            flash(
                "Ingresa un concepto.",
                "danger"
            )

            return redirect(
                url_for("crear_movimiento")
            )

        try:

            monto = float(monto_texto)

            if monto <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Ingresa un monto válido.",
                "danger"
            )

            return redirect(
                url_for("crear_movimiento")
            )

        if tipo not in [
            "ingreso",
            "egreso"
        ]:

            flash(
                "Tipo de movimiento inválido.",
                "danger"
            )

            return redirect(
                url_for("crear_movimiento")
            )

        if metodo not in [
            "efectivo",
            "tarjeta",
            "QR"
        ]:

            flash(
                "Método de pago inválido.",
                "danger"
            )

            return redirect(
                url_for("crear_movimiento")
            )

        if metodo == "QR":

            estado = "pendiente"

        elif tipo == "egreso":

            estado = "pagado"

        else:

            estado = "cobrado"

        db = get_db()

        db.execute("""
            INSERT INTO movimientos
            (
                concepto,
                monto,
                hora,
                metodo,
                tipo,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            concepto,
            monto,
            hora_actual(),
            metodo,
            tipo,
            estado
        ))

        db.commit()

        if metodo == "QR":

            flash(
                "Movimiento QR registrado como pendiente.",
                "success"
            )

        else:

            flash(
                "Movimiento registrado correctamente.",
                "success"
            )

        return redirect(
            url_for("caja")
        )

    body = f"""

    <div class="topline">

        <div>

            <h1>
                Registrar movimiento
            </h1>

            <div class="subtitle">
                Añadir un ingreso o egreso.
            </div>

        </div>

    </div>


    <form
        method="post"
        class="card"
    >

        <div class="field">

            <label>
                Concepto
            </label>

            <input
                required
                type="text"
                name="concepto"
                placeholder="Ej. Mesa S4 — cena"
            >

        </div>


        <div class="field">

            <label>
                Monto (Bs)
            </label>

            <input
                required
                type="number"
                min="0.01"
                step="0.01"
                name="monto"
            >

        </div>


        <div class="field">

            <label>
                Tipo
            </label>

            <select name="tipo">

                <option value="ingreso">
                    Ingreso
                </option>

                <option value="egreso">
                    Egreso
                </option>

            </select>

        </div>


        <div class="field">

            <label>
                Método de pago
            </label>

            <select name="metodo">

                <option value="efectivo">
                    Efectivo
                </option>

                <option value="tarjeta">
                    Tarjeta
                </option>

                <option value="QR">
                    QR
                </option>

            </select>

        </div>


        <div class="modal-actions">

            <a
                href="{url_for('caja')}"
                class="btn btn-secondary"
            >
                Cancelar
            </a>

            <button
                type="submit"
                class="btn btn-primary"
            >
                Guardar
            </button>

        </div>

    </form>

    """

    return render(body, "caja")


# =========================================================
# MARCAR QR COMO COBRADO
# =========================================================

@app.route(
    "/movimiento/<int:mid>/cobrado",
    methods=["POST"]
)
def marcar_cobrado(mid):

    db = get_db()

    movimiento = db.execute("""
        SELECT *
        FROM movimientos
        WHERE id=?
    """, (mid,)).fetchone()

    if movimiento is None:

        flash(
            "Movimiento no encontrado.",
            "danger"
        )

        return redirect(
            url_for("caja")
        )

    db.execute("""
        UPDATE movimientos
        SET estado='cobrado'
        WHERE id=?
    """, (mid,))

    db.commit()

    flash(
        "Pago QR marcado como cobrado en la aplicación.",
        "success"
    )

    return redirect(
        url_for("caja")
    )


# =========================================================
# ARRANQUE
# =========================================================

if __name__ == "__main__":

    init_db()

    seed_data()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
