import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib
import io
import json
import base64

st.set_page_config(
    page_title="PROMETHEUS · Coevaluación Misión 04",
    page_icon="◈",
    layout="wide"
)

# ============================================================
# CONFIGURACIÓN
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "estudiantes.csv"

# GitHub Secrets expected:
# GITHUB_TOKEN = "..."
# GITHUB_REPO = "usuario/repositorio"
# GITHUB_BRANCH = "main"

students = pd.read_csv(DATA_FILE, dtype={"id": str})
students["id"] = students["id"].astype(str).str.strip()

if "mision04" not in students.columns:
    st.error("El archivo estudiantes.csv debe contener la columna 'mision04'.")
    st.stop()

students["mision04"] = students["mision04"].astype(str).str.strip()

ROLE_RESPONSIBILITIES = {
    "Coordinador(a) del equipo": [
        "Distribuyó las tareas y dio seguimiento al trabajo del equipo.",
        "Aseguró que se siguieran las instrucciones y criterios de la Misión 04.",
        "Coordinó la integración final del trabajo.",
        "Facilitó la comunicación y la toma de decisiones del equipo.",
    ],
    "Analista anatómico(a)": [
        "Identificó correctamente las estructuras anatómicas y utilizó nomenclatura adecuada.",
        "Ubicó las estructuras en la región o cavidad correspondiente y utilizó orientación anatómica correcta.",
        "Describió las relaciones anatómicas relevantes para el caso.",
        "Sustentó la identificación de las estructuras con evidencia anatómica.",
    ],
    "Cartógrafo(a) anatómico(a)": [
        "Construyó el mapa anatómico mediante dibujos, imágenes o modelos tridimensionales.",
        "Mantuvo la orientación anatómica y la señalización correctas.",
        "Representó y nombró adecuadamente las estructuras relevantes.",
        "Integró las relaciones anatómicas en una representación clara.",
    ],
    "Analista biomédico(a)": [
        "Relacionó el caso anatómico con una aplicación de Ingeniería Biomédica.",
        "Identificó características anatómicas relevantes para la aplicación.",
        "Explicó cómo la anatomía condiciona el diseño o uso de una solución biomédica.",
        "Contribuyó con información anatómica necesaria para la aplicación propuesta.",
    ],
    "Documentador(a) y redactor(a)": [
        "Integró la información aportada por los integrantes del equipo.",
        "Organizó la redacción de manera clara y coherente.",
        "Integró las fuentes y referencias correspondientes.",
        "Contribuyó a que el documento final estuviera completo y correctamente presentado.",
    ],
    "Revisor(a) de calidad": [
        "Revisó la precisión anatómica y el sustento de las identificaciones.",
        "Verificó nomenclatura, orientación y relaciones anatómicas.",
        "Detectó información faltante, errores o inconsistencias.",
        "Revisó la calidad de imágenes, citas y formato del producto final.",
    ],
}

LEVELS = {
    4: "Profesional — Desempeñó las responsabilidades de su rol de manera clara, constante y autónoma, con una participación que contribuyó directamente al avance del equipo.",
    3: "Competente todavía con áreas de oportunidad — Desempeñó adecuadamente las responsabilidades de su rol y realizó las tareas esperadas, aunque pudo haber aspectos por fortalecer.",
    2: "Adecuado pero evidentemente en desarrollo — Cumplió parcialmente las responsabilidades de su rol o necesitó apoyo, recordatorios o seguimiento para completar su participación.",
    1: "Solamente fue testigo del proceso — Su participación observable fue mínima y no permitió identificar un desempeño efectivo de las responsabilidades del rol.",
}

ROLES = [
    "Coordinador(a) del equipo",
    "Analista anatómico(a)",
    "Cartógrafo(a) anatómico(a)",
    "Analista biomédico(a)",
    "Documentador(a) y redactor(a)",
    "Revisor(a) de calidad",
]

# ============================================================
# ESTILO
# ============================================================
st.markdown("""
<style>
.stApp { background:#071018; color:#EAF7FF; }
.block-container { max-width:1150px; padding-top:1.5rem; }
h1,h2,h3 { color:#55D9FF; }
.case-card {
    border:1px solid #16485C; border-radius:14px; padding:18px;
    background:linear-gradient(135deg,#09151F,#071018); margin-bottom:14px;
}
.role-card {
    border:1px solid #4A2C6E; border-radius:14px; padding:16px;
    background:linear-gradient(135deg,#171022,#0B1018); margin-bottom:12px;
}
.small-note { color:#B9D5E2; font-size:0.92rem; }
</style>
""", unsafe_allow_html=True)

st.title("PROMETHEUS")
st.caption("COEVALUACIÓN · MISIÓN 04 · PROTOCOLO DE OXIGENACIÓN")

if "evaluator" not in st.session_state:
    st.session_state.evaluator = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "receipt_bytes" not in st.session_state:
    st.session_state.receipt_bytes = None
if "receipt_code" not in st.session_state:
    st.session_state.receipt_code = None

# ============================================================
# GITHUB
# ============================================================
def github_config():
    github_secrets = st.secrets.get("github", {})
    token = github_secrets.get("GITHUB_TOKEN", "")
    repo_name = github_secrets.get("GITHUB_REPO", "Alejandra-LozC/mision04")
    branch = github_secrets.get("GITHUB_BRANCH", "main")
    return token, repo_name, branch

def github_upload_bytes(path, data_bytes, message):
    """Create/update a file in GitHub through the Contents API."""
    import requests

    token, repo_name, branch = github_config()
    if not token or not repo_name:
        raise RuntimeError(
            "Faltan GITHUB_TOKEN y/o GITHUB_REPO en Streamlit Secrets."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    api = f"https://api.github.com/repos/{repo_name}/contents/{path}"

    encoded = base64.b64encode(data_bytes).decode("utf-8")
    payload = {
        "message": message,
        "content": encoded,
        "branch": branch,
    }

    # If the file already exists, obtain SHA so it can be updated.
    r = requests.get(api, headers=headers, params={"ref": branch}, timeout=20)
    if r.status_code == 200:
        payload["sha"] = r.json()["sha"]
    elif r.status_code != 404:
        raise RuntimeError(f"GitHub GET error {r.status_code}: {r.text[:500]}")

    r = requests.put(api, headers=headers, json=payload, timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub PUT error {r.status_code}: {r.text[:700]}")
    return r.json()

# ============================================================
# CSV CONSOLIDADO EN GITHUB
# ============================================================
def github_get_file(path):
    import requests
    token, repo_name, branch = github_config()
    if not token or not repo_name:
        raise RuntimeError("Faltan GITHUB_TOKEN y/o GITHUB_REPO en Streamlit Secrets.")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    api = f"https://api.github.com/repos/{repo_name}/contents/{path}"
    r = requests.get(api, headers=headers, params={"ref": branch}, timeout=20)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise RuntimeError(f"GitHub GET error {r.status_code}: {r.text[:500]}")
    return r.json()

def update_results_csv(new_rows):
    csv_path = "results.csv"
    existing = github_get_file(csv_path)

    if existing:
        old_bytes = base64.b64decode(existing["content"].replace("\n", ""))
        old_df = pd.read_csv(io.BytesIO(old_bytes), dtype=str)
    else:
        old_df = pd.DataFrame()

    new_df = pd.DataFrame(new_rows)

    if not old_df.empty and "evaluador_id" in old_df.columns and "equipo" in old_df.columns:
        evaluator_id = str(new_rows[0]["evaluador_id"])
        team = str(new_rows[0]["equipo"])
        old_df = old_df[
            ~(
                old_df["evaluador_id"].astype(str).eq(evaluator_id)
                & old_df["equipo"].astype(str).eq(team)
            )
        ]

    combined = pd.concat([old_df, new_df], ignore_index=True)
    github_upload_bytes(
        csv_path,
        combined.to_csv(index=False, encoding="utf-8-sig").encode("utf-8"),
        "Misión 04: actualizar results.csv"
    )

# ============================================================
# PDF COMPROBANTE
# ============================================================
def make_receipt_pdf(ev, role, classmates_count, timestamp, receipt_code):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], alignment=TA_CENTER,
        fontSize=20, leading=24, textColor=colors.HexColor("#0B2A4A")
    )
    subtitle = ParagraphStyle(
        "Sub", parent=styles["Normal"], alignment=TA_CENTER,
        fontSize=11, leading=15, textColor=colors.HexColor("#345")
    )
    body = ParagraphStyle(
        "BodyCustom", parent=styles["Normal"], fontSize=10.5, leading=15
    )

    story = [
        Paragraph("PROMETHEUS", title),
        Paragraph("Misión 04 · Protocolo de Oxigenación", title),
        Spacer(1, 0.25*cm),
        Paragraph("COMPROBANTE DE REALIZACIÓN DE COEVALUACIÓN", subtitle),
        Spacer(1, 0.5*cm),
    ]

    data = [
        ["Alumno", str(ev["nombre_completo"])],
        ["ID institucional", str(ev["id"])],
        ["Equipo", str(ev["mision04"])],
        ["Rol declarado", role],
        ["Compañeros evaluados", str(classmates_count)],
        ["Fecha y hora", timestamp],
        ["Código de comprobación", receipt_code],
    ]
    table = Table(data, colWidths=[5*cm, 12.5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EAF4FA")),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#123")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#9BB8C8")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph(
        "Este documento acredita que el alumno completó y envió la "
        "coevaluación correspondiente a la Misión 04. No muestra las "
        "calificaciones otorgadas a sus compañeros.",
        body
    ))
    story.append(Spacer(1, 0.35*cm))
    story.append(Paragraph(
        "El registro de la coevaluación queda asociado al código de "
        "comprobación y al repositorio institucional configurado para la aplicación.",
        body
    ))
    doc.build(story)
    return buf.getvalue()

# ============================================================
# ACCESO
# ============================================================
with st.sidebar:
    st.header("Acceso")
    entered_id = st.text_input("ID institucional", max_chars=30, type="password")

    if st.button("Ingresar", use_container_width=True):
        match = students[students["id"] == entered_id.strip()]
        if match.empty:
            st.error("ID no encontrado.")
        else:
            st.session_state.evaluator = match.iloc[0].to_dict()
            st.session_state.submitted = False
            st.session_state.receipt_bytes = None
            st.session_state.receipt_code = None
            st.rerun()

    if st.session_state.evaluator:
        ev = st.session_state.evaluator
        st.divider()
        st.write(f"**Equipo {ev['mision04']}**")
        st.write(ev["nombre_completo"])

        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.evaluator = None
            st.session_state.submitted = False
            st.session_state.receipt_bytes = None
            st.session_state.receipt_code = None
            st.rerun()

if not st.session_state.evaluator:
    st.info("Ingresa tu ID institucional desde el panel lateral para comenzar.")
    st.stop()

ev = st.session_state.evaluator
group = str(ev["mision04"])

classmates = students[
    (students["mision04"] == group) &
    (students["id"] != str(ev["id"]))
].sort_values("nombre_completo")

# ============================================================
# INTRODUCCIÓN
# ============================================================
st.markdown(
    f'<div class="case-card"><h3>Misión 04 · Equipo {group}</h3>'
    '<div>Coevalúa el desempeño observado durante el desarrollo del '
    'Protocolo de Oxigenación. Evalúa conductas y aportaciones, no '
    'personalidad, afinidad o popularidad.</div></div>',
    unsafe_allow_html=True
)

with st.expander("Consultar responsabilidades de los roles"):
    for role_name, responsibilities in ROLE_RESPONSIBILITIES.items():
        st.markdown(f"**{role_name}**")
        for item in responsibilities:
            st.markdown(f"- {item}")

# ============================================================
# ROL DEL EVALUADOR
# ============================================================
st.subheader("1. Indica el rol que desempeñaste")

role = st.selectbox(
    "Selecciona el rol que realmente desempeñaste durante la Misión 04:",
    ["Selecciona un rol"] + ROLES
)

if role != "Selecciona un rol":
    st.markdown(
        f'<div class="role-card"><strong>Rol declarado:</strong> {role}'
        '<br><span class="small-note">Esta información se incluirá en tu registro de coevaluación y en tu comprobante.</span></div>',
        unsafe_allow_html=True
    )

st.subheader("2. Coevalúa a tus compañeros")

if classmates.empty:
    st.warning("No hay compañeros registrados en tu equipo.")
    st.stop()

all_results = []

for _, person in classmates.iterrows():
    st.subheader(person["nombre_completo"])

    evaluated_role = st.selectbox(
        "Rol que realmente desempeñó en la Misión 04",
        ["Selecciona el rol..."] + ROLES,
        key=f"{person['id']}_role",
    )

    level = None
    evidence = ""
    improvement = ""

    if evaluated_role != "Selecciona el rol...":
        st.markdown("**Responsabilidades que corresponden a este rol:**")
        for responsibility in ROLE_RESPONSIBILITIES[evaluated_role]:
            st.markdown(f"- {responsibility}")

        st.markdown("**Desempeño del rol**")
        level = st.radio(
            "Selecciona el nivel que mejor describe el desempeño observado:",
            [4, 3, 2, 1],
            format_func=lambda x: f"{x} — {LEVELS[x]}",
            key=f"{person['id']}_level",
        )

        evidence = st.text_area(
            "¿Qué podrías señalar como la evidencia más concreta de su participación, que te hizo calificar así?",
            key=f"{person['id']}_evidence",
            placeholder="Describe una conducta, aportación o evidencia observable.",
        )

        improvement = st.text_area(
            "¿Qué observación tienes sobre lo que podría mejorar al trabajar en grupo?",
            key=f"{person['id']}_improvement",
            placeholder="Escribe una observación concreta y útil.",
        )

    all_results.append((person, evaluated_role, level, evidence, improvement))
    st.divider()

submitted = st.button("ENVIAR COEVALUACIÓN", use_container_width=True)

# ============================================================
# ENVÍO
# ============================================================
if submitted:
    if role == "Selecciona un rol":
        st.error("Selecciona primero el rol que desempeñaste.")
        st.stop()

    rows = []
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    for person, evaluated_role, level, evidence, improvement in all_results:
        if evaluated_role == "Selecciona el rol..." or level is None:
            st.error(f"Selecciona el rol y la calificación de {person['nombre_completo']}.")
            st.stop()

        rows.append({
            "timestamp": timestamp,
            "evaluador_id": str(ev["id"]),
            "evaluador_nombre": ev["nombre_completo"],
            "equipo": group,
            "rol_evaluador": role,
            "evaluado_id": str(person["id"]),
            "evaluado_nombre": person["nombre_completo"],
            "rol_evaluado": evaluated_role,
            "calificacion": int(level),
            "nivel": LEVELS[level],
            "evidencia_participacion": evidence.strip(),
            "observacion_trabajo_grupo": improvement.strip(),
        })

    # Unique submission code based on all submitted data.
    payload = json.dumps(
        {
            "timestamp": timestamp,
            "evaluator": str(ev["id"]),
            "team": group,
            "role": role,
            "rows": rows,
        },
        ensure_ascii=False,
        sort_keys=True
    ).encode("utf-8")

    receipt_code = hashlib.sha256(payload).hexdigest()[:16].upper()

    record = {
        "mission": "04",
        "mission_name": "Protocolo de Oxigenación",
        "submitted_at": timestamp,
        "evaluator_id": str(ev["id"]),
        "evaluator_name": ev["nombre_completo"],
        "team": group,
        "role": role,
        "receipt_code": receipt_code,
        "evaluations": rows,
    }

    record_bytes = json.dumps(
        record, ensure_ascii=False, indent=2
    ).encode("utf-8")

    safe_id = "".join(
        ch for ch in str(ev["id"])
        if ch.isalnum() or ch in "-_"
    )

    json_path = f"respuestas/mision04_{safe_id}.json"

    try:
        github_upload_bytes(
            json_path,
            record_bytes,
            f"Misión 04: coevaluación del alumno {safe_id}"
        )

        update_results_csv(rows)

        pdf_bytes = make_receipt_pdf(
            ev, role, len(classmates), timestamp, receipt_code
        )

        pdf_path = f"comprobantes/mision04_{safe_id}.pdf"

        github_upload_bytes(
            pdf_path,
            pdf_bytes,
            f"Misión 04: comprobante de coevaluación {safe_id}"
        )

        st.session_state.submitted = True
        st.session_state.receipt_bytes = pdf_bytes
        st.session_state.receipt_code = receipt_code

        st.success("Coevaluación registrada correctamente en GitHub.")
        st.balloons()

    except Exception as e:
        st.error(
            "La coevaluación NO se pudo registrar. No entregues el comprobante "
            "hasta resolver el problema de conexión con GitHub."
        )
        st.code(str(e))

# ============================================================
# COMPROBANTE
# ============================================================
if st.session_state.submitted and st.session_state.receipt_bytes:
    st.divider()
    st.subheader("3. Evidencia de realización")

    st.success(
        f"Registro confirmado. Código de comprobación: "
        f"**{st.session_state.receipt_code}**"
    )

    st.write(
        "Descarga el comprobante PDF y entrégalo en Brightspace "
        "como evidencia de que realizaste la coevaluación."
    )

    st.download_button(
        "DESCARGAR COMPROBANTE PDF",
        data=st.session_state.receipt_bytes,
        file_name=f"PROMETHEUS_M04_Coevaluacion_{ev['id']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.info(
        "El comprobante confirma la realización de la coevaluación, "
        "pero no muestra las puntuaciones otorgadas a tus compañeros."
    )
