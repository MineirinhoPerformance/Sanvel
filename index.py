"""
Dashboard de Faturamento Semanal — Tema Escuro
Versão 3.0 — Administração SQLite · Depósitos · Pedidos Transparentes · Kg/Un por Produto
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import io
import os
from dotenv import load_dotenv

load_dotenv()  # carrega o .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Faturamento Semanal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PALETA DARK ───────────────────────────────────────────────────────────────
BG_APP     = "#080E1C"
BG_CARD    = "#0F1929"
BG_PLOT    = "#0B1220"
BG_SIDEBAR = "#060C18"
BORDER     = "#1A2E50"

C_CYAN   = "#38BDF8"
C_TEAL   = "#2DD4BF"
C_GREEN  = "#4ADE80"
C_RED    = "#F87171"
C_AMBER  = "#FBBF24"
C_VIOLET = "#A78BFA"
C_ORANGE = "#FB923C"

TXT_H  = "#F1F5F9"
TXT_M  = "#CBD5E1"
TXT_S  = "#64748B"
GRID   = "#1E3A5F"

PROD_COLORS = [C_CYAN, C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN, "#EC4899"]

# ── CORES POR SKU ─────────────────────────────────────────────────────────────
SKU_COLORS = {
    "40105": "#9E9E9E",   # Cinza
    "30105": "#8B5E3C",   # Marrom
    "30615": "#4169E1",   # Azul Royal
    "30625": "#E8446E",   # Goiaba
    "30645": "#8B0000",   # Vermelho Fechado
}
SKU_COLOR_OUTROS = "#555555"  # Preto/Cinza escuro (visível no dark theme)


def sku_color(prod_key):
    """Retorna cor baseada no codigo SKU do produto."""
    s = str(prod_key).strip()
    for sku, color in SKU_COLORS.items():
        if s.startswith(sku):
            return color
        parts = s.split(chr(8211))  # –
        if not parts:
            parts = s.split("-")
        if parts and parts[0].strip() == sku:
            return color
    return SKU_COLOR_OUTROS

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"],
[data-testid="stHeader"], .main, .block-container {{
    background-color: {BG_APP} !important;
    color: {TXT_M};
    font-family: 'Inter', sans-serif;
}}
h1,h2,h3,h4 {{ font-family: 'Montserrat', sans-serif; color: {TXT_H}; }}

[data-testid="stSidebar"] > div:first-child {{
    background: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: {TXT_M} !important; }}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background: {C_CYAN}22 !important; border: 1px solid {C_CYAN}55 !important;
    color: {C_CYAN} !important;
}}

/* Tags: grow to fit their text; only show ellipsis when the container is too narrow */
[data-baseweb="tag"] {{
    max-width: 100% !important;
    box-sizing: border-box !important;
    flex-shrink: 1 !important;
    min-width: 0 !important;
}}
[data-baseweb="tag"] > span:first-child {{
    overflow: hidden !important;
    white-space: nowrap !important;
    text-overflow: ellipsis !important;
    display: block !important;
    min-width: 0 !important;
}}
/* Make the multiselect value container wrap tags to new lines */
[data-baseweb="select"] > div:first-child {{
    flex-wrap: wrap !important;
    min-height: 42px !important;
}}

[data-testid="stTabs"] [role="tab"] {{
    background: transparent; color: {TXT_S}; border-bottom: 2px solid transparent;
    font-family: 'Inter', sans-serif; font-weight: 500;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {C_CYAN}; border-bottom: 2px solid {C_CYAN};
}}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {{
    background: transparent !important;
}}

[data-testid="stDataFrame"] {{ background: {BG_CARD}; border-radius: 12px; }}
[data-testid="stDataFrame"] th {{
    background: {BG_SIDEBAR} !important; color: {C_CYAN} !important;
    font-family: 'Montserrat', sans-serif; font-size: .78rem; letter-spacing: .05em;
}}
[data-testid="stDataFrame"] td {{ color: {TXT_M} !important; }}
[data-testid="stDataFrame"] tr:hover td {{ background: {BORDER} !important; }}

[data-testid="stTextInput"] input {{
    background: {BG_CARD} !important; color: {TXT_M} !important;
    border: 1px solid {BORDER} !important; border-radius: 8px;
}}
[data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div {{
    background: {BG_CARD} !important; color: {TXT_M} !important;
}}

.kpi-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-top: 3px solid var(--accent);
    border-radius: 14px;
    padding: 20px 22px 16px;
    position: relative;
    overflow: hidden;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 100px; height: 100px;
    background: var(--accent);
    opacity: .05;
    border-radius: 50%;
}}
.kpi-icon {{ font-size: 1.5rem; margin-bottom: 6px; }}
.kpi-label {{
    font-size: .68rem; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; color: {TXT_S}; margin-bottom: 6px;
    font-family: 'Montserrat', sans-serif;
}}
.kpi-value {{
    font-family: 'Montserrat', sans-serif;
    font-size: 1.75rem; font-weight: 800; color: {TXT_H};
    line-height: 1.1;
}}
.kpi-sub {{
    font-size: .75rem; color: {TXT_S}; margin-top: 5px;
    font-family: 'Inter', sans-serif;
}}

.sec-header {{
    font-family: 'Montserrat', sans-serif;
    font-size: 1rem; font-weight: 700; color: {TXT_H};
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0 8px;
    border-bottom: 1px solid {BORDER};
    margin: 28px 0 14px;
}}
.sec-header span {{ color: {C_CYAN}; }}

.pill {{
    display: inline-block;
    background: {C_CYAN}18; border: 1px solid {C_CYAN}40;
    color: {C_CYAN}; border-radius: 20px;
    padding: 3px 12px; font-size: .75rem;
    margin: 2px 4px; font-weight: 600;
}}
.tip {{ font-size: .76rem; color: {TXT_S}; font-style: italic; margin: 4px 0 12px; }}

[data-testid="stButton"] > button {{
    background: {BORDER}; color: {TXT_M};
    border: 1px solid {BORDER}; border-radius: 8px;
    font-family: 'Inter', sans-serif;
    transition: all .2s;
}}
[data-testid="stButton"] > button:hover {{
    background: {C_CYAN}22; border-color: {C_CYAN}55; color: {C_CYAN};
}}

.admin-card {{
    background: {BG_CARD}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 20px 24px; margin-bottom: 18px;
}}
.badge-com {{
    background: {C_GREEN}22; color: {C_GREEN}; border: 1px solid {C_GREEN}44;
    border-radius: 12px; padding: 2px 10px; font-size: .72rem; font-weight: 600;
}}
.badge-sem {{
    background: {C_AMBER}22; color: {C_AMBER}; border: 1px solid {C_AMBER}44;
    border-radius: 12px; padding: 2px 10px; font-size: .72rem; font-weight: 600;
}}

/* ── Botao icone de IA ─────────────────────────────────────────────────── */
div[data-testid="stMarkdownContainer"]:has(.ia-btn-marker)
  + div[data-testid="stHorizontalBlock"]
  div[data-testid="stColumn"]:first-child
  button {{
    border-radius: 12px !important;
    min-width: 160px !important;
    height: 44px !important;
    padding: 0 16px !important;
    font-size: .85rem !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    background: linear-gradient(135deg, rgba(56,189,248,0.12), rgba(45,212,191,0.10)) !important;
    border: 1.5px solid rgba(56,189,248,0.50) !important;
    color: {C_CYAN} !important;
    box-shadow: 0 2px 8px rgba(56,189,248,0.10) !important;
    transition: all .25s ease !important;
    letter-spacing: .03em !important;
    font-family: 'Inter', sans-serif !important;
}}
div[data-testid="stMarkdownContainer"]:has(.ia-btn-marker)
  + div[data-testid="stHorizontalBlock"]
  div[data-testid="stColumn"]:first-child
  button:hover {{
    background: linear-gradient(135deg, rgba(56,189,248,0.22), rgba(45,212,191,0.18)) !important;
    border-color: {C_CYAN} !important;
    box-shadow: 0 4px 16px rgba(56,189,248,0.30) !important;
    transform: translateY(-1px) !important;
}}
div[data-testid="stMarkdownContainer"]:has(.ia-btn-marker)
  + div[data-testid="stHorizontalBlock"]
  div[data-testid="stColumn"]:first-child
  button p {{
    margin: 0 !important;
    line-height: 1 !important;
}}
</style>
""", unsafe_allow_html=True)

# ── SPINNER MODERNO (substitui o ícone padrão do Streamlit) ──────────────────
st.markdown("""
<style>
/* Esconde o indicador padrão do Streamlit (ciclista) */
[data-testid="stStatusWidget"] { display: none !important; }
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }

/* Spinner customizado */
#custom-loader {
    position: fixed;
    top: 12px;
    right: 16px;
    width: 26px;
    height: 26px;
    border: 3px solid rgba(56,189,248,0.12);
    border-top: 3px solid #38BDF8;
    border-radius: 50%;
    z-index: 99999;
    display: none;
    animation: cspin 0.75s linear infinite;
    box-shadow: 0 0 8px rgba(56,189,248,0.3);
}
@keyframes cspin { to { transform: rotate(360deg); } }
</style>

<div id="custom-loader"></div>

<script>
(function() {
    const loader = document.getElementById('custom-loader');
    if (!loader) return;

    // Detecta quando Streamlit está processando via MutationObserver no body
    const observer = new MutationObserver(() => {
        const stale = document.querySelector('[data-stale="true"]')
                   || document.querySelector('.stSpinner')
                   || document.querySelector('[data-testid="stStatusWidget"]');
        loader.style.display = stale ? 'block' : 'none';
    });

    // Também captura eventos de fetch/XHR para mostrar spinner
    const origFetch = window.fetch;
    let pendingReqs = 0;
    window.fetch = function(...args) {
        pendingReqs++;
        loader.style.display = 'block';
        return origFetch.apply(this, args).finally(() => {
            pendingReqs--;
            if (pendingReqs <= 0) {
                pendingReqs = 0;
                setTimeout(() => { loader.style.display = 'none'; }, 200);
            }
        });
    };

    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
})();
</script>
""", unsafe_allow_html=True)



# ── PLOTLY DEFAULTS ──────────────────────────────────────────────────────────
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=BG_PLOT,
    font=dict(family="Inter, sans-serif", color=TXT_M, size=11),
    title=dict(text="", font=dict(family="Montserrat, sans-serif", color=TXT_H, size=13)),
    xaxis=dict(
        showgrid=False, zeroline=False,
        tickcolor=TXT_S, linecolor=BORDER,
        tickfont=dict(color=TXT_S, size=10),
    ),
    yaxis=dict(
        showgrid=True, gridcolor=GRID, zeroline=False,
        tickcolor=TXT_S, linecolor=BORDER,
        tickfont=dict(color=TXT_S, size=10),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
        font=dict(color=TXT_M, size=10),
    ),
    hoverlabel=dict(
        bgcolor=BG_SIDEBAR, bordercolor=BORDER,
        font=dict(family="Inter, sans-serif", color=TXT_H, size=12),
    ),
    margin=dict(t=45, b=10, l=10, r=10),
)


def fig_layout(fig, **extra):
    d = {**LAYOUT_BASE, **extra}
    fig.update_layout(**d)
    return fig


# ── SQLITE ────────────────────────────────────────────────────────────────────
DB_PATH = "produtos.db"


def _db_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _db_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produto_caracteristicas (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            V_uso                INTEGER,
            MARCA                TEXT,
            DESCRICAO            TEXT,
            COD_PRODUTO          TEXT,
            PCT_CX               REAL,
            UN_PCT               REAL,
            PESO_PCT             REAL,
            CLASSIFICACAO_PRODUTO TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def db_count():
    conn = _db_conn()
    try:
        n = conn.execute("SELECT COUNT(*) FROM produto_caracteristicas").fetchone()[0]
    except Exception:
        n = 0
    conn.close()
    return n


def db_load():
    conn = _db_conn()
    try:
        df = pd.read_sql(
            "SELECT V_uso, MARCA, DESCRICAO, COD_PRODUTO, PCT_CX, UN_PCT, "
            "PESO_PCT, CLASSIFICACAO_PRODUTO FROM produto_caracteristicas "
            "ORDER BY CAST(COD_PRODUTO AS INTEGER)",
            conn,
        )
    except Exception:
        df = pd.DataFrame(columns=["V_uso","MARCA","DESCRICAO","COD_PRODUTO",
                                    "PCT_CX","UN_PCT","PESO_PCT","CLASSIFICACAO_PRODUTO"])
    conn.close()
    return df


def db_save(df: pd.DataFrame):
    conn = _db_conn()
    conn.execute("DELETE FROM produto_caracteristicas")
    keep = ["V_uso","MARCA","DESCRICAO","COD_PRODUTO","PCT_CX","UN_PCT",
            "PESO_PCT","CLASSIFICACAO_PRODUTO"]
    df[[c for c in keep if c in df.columns]].to_sql(
        "produto_caracteristicas", conn, if_exists="append", index=False
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()


# ── FORMATAÇÃO BR ─────────────────────────────────────────────────────────────
def fmt_br(v, dec=2):
    """Formato brasileiro: 1.123,45"""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    s = f"{float(v):,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_peso(v):
    """Formata peso no padrão BR: <1kg vira gramas"""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if v < 1:
        return fmt_br(v * 1000, 0) + " g"
    else:
        return fmt_br(v, 1) + " kg"


# ── SESSION STATE ─────────────────────────────────────────────────────────────
_defaults = {
    "xf_produto": set(), "xf_cliente": set(),
    "xf_situacao": set(), "xf_transacao": set(), "xf_semana": set(),
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _update_xf(key, val):
    if val != st.session_state[key]:
        st.session_state[key] = val
        return True
    return False


def _handle_event(event, key, dim):
    if not (event and hasattr(event, "selection") and event.selection):
        return False
    pts = event.selection.get("points", [])
    if not pts:
        return _update_xf(key, set())
    vals = set()
    for p in pts:
        v = p.get(dim) or p.get("label") or p.get("x") or p.get("y")
        if v is not None:
            vals.add(str(v))
    if vals == st.session_state[key]:
        return _update_xf(key, set())
    return _update_xf(key, vals)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(base_file_bytes: bytes):
    df = pd.read_excel(io.BytesIO(base_file_bytes))

    df_char = db_load()

    df["emissao"]      = pd.to_datetime(df["emissao"], dayfirst=True)
    df["ano"]          = df["emissao"].dt.isocalendar().year.astype(int)
    df["Numero_Semana"] = df["emissao"].dt.isocalendar().week.astype(int)
    df["semana_sort"]  = df["ano"] * 100 + df["Numero_Semana"]
    df["semana_label"] = (
        "S" + df["Numero_Semana"].astype(str).str.zfill(2)
        + "/" + df["ano"].astype(str).str[-2:]
    )
    df["transacao_str"] = df["transacao_produto"].astype(str)
    df["codigo_str"]    = df["codigo_produto"].astype(str)
    # prod_nome = apenas o código do produto (sem concatenar descrição)
    df["prod_nome"] = df["codigo_str"]

    # Merge com características
    if not df_char.empty:
        df_char["COD_PRODUTO"] = df_char["COD_PRODUTO"].astype(str)
        df["codigo_str"] = df["codigo_produto"].astype(str)
        df = df.merge(
            df_char[["COD_PRODUTO","PCT_CX","UN_PCT","PESO_PCT","MARCA","DESCRICAO"]],
            left_on="codigo_str",
            right_on="COD_PRODUTO",
            how="left",
        )
    else:
        for col in ["PCT_CX","UN_PCT","PESO_PCT","MARCA","DESCRICAO"]:
            df[col] = np.nan

    df["kilos"]    = df["unid_faturado"] * df["PESO_PCT"].fillna(0)
    df["caixas"]   = df["unid_faturado"] / df["PCT_CX"].replace(0, np.nan)
    df["unidades"] = df["unid_faturado"] * df["UN_PCT"].fillna(0)

    # Depósito (anteriormente chamado "loja")
    df["deposito"] = df["deposito_faturamento"].fillna("Sem Depósito").str.strip()
    df.loc[df["deposito"] == "", "deposito"] = "Sem Depósito"

    # Semana → range de datas
    wk_range = (
        df.groupby("semana_sort")["emissao"]
        .agg(d_min="min", d_max="max")
        .reset_index()
    )
    wk_range["date_range"] = (
        wk_range["d_min"].dt.strftime("%d/%m")
        + " – "
        + wk_range["d_max"].dt.strftime("%d/%m/%Y")
    )
    wk_map = wk_range.set_index("semana_sort")["date_range"].to_dict()
    df["date_range"] = df["semana_sort"].map(wk_map)

    # Pedido cliente
    df["pedido_clean"] = df["pedido_cliente"].astype(str).str.strip()
    df["tem_pedido"]   = df["pedido_clean"].apply(
        lambda x: x not in ["", "nan", "NaN", "None", " "]
    )

    return df, wk_map


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _hex_to_rgba(hex_color, alpha=0.80):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def _darken_hex(hex_color, factor=0.50):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r2, g2, b2 = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r2:02x}{g2:02x}{b2:02x}"

def sec(icon, title):
    st.markdown(
        f'<div class="sec-header"><span>{icon}</span> {title}</div>',
        unsafe_allow_html=True,
    )


def prod_color_map(prods):
    return {p: sku_color(p) for p in prods}


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR: NAVEGAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown(
    f"<div style='font-family:Montserrat,sans-serif;font-size:1.1rem;"
    f"font-weight:800;color:{TXT_H};padding:12px 0 4px;letter-spacing:.04em'>"
    f"📊 FATURAMENTO</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:6px 0 14px'>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard", "⚙️ Administração"],
    key="nav_page",
    label_visibility="collapsed",
)

st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)

# Indicador de status do banco de características
n_char = db_count()
if n_char > 0:
    st.sidebar.markdown(
        f"<div style='font-size:.75rem;color:{C_GREEN};padding:4px 0 8px'>"
        f"✅ {n_char} produtos no banco de características</div>",
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        f"<div style='font-size:.75rem;color:{C_AMBER};padding:4px 0 8px'>"
        f"⚠️ Banco de características vazio — vá em Administração para importar</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  PÁGINA: ADMINISTRAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
if page == "⚙️ Administração":
    st.markdown(
        f"<h2 style='font-family:Montserrat,sans-serif;color:{TXT_H};"
        f"font-size:1.6rem;font-weight:800;margin-bottom:4px'>"
        f"⚙️ Administração — Características dos Produtos</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Importe, edite e exporte a tabela de características dos produtos. Os dados ficam armazenados em banco SQLite local.")

    st.markdown(f"<hr style='border-color:{BORDER};margin:10px 0 20px'>", unsafe_allow_html=True)

    # ── IMPORTAR ──────────────────────────────────────────────────────────────
    with st.expander("📥 Importar Planilha de Características (.xlsx)", expanded=(n_char == 0)):
        st.markdown(
            f"<div style='font-size:.85rem;color:{TXT_S};margin-bottom:12px'>"
            f"Carregue o arquivo <b style='color:{C_CYAN}'>Característica_dos_Produtos.xlsx</b>. "
            f"A importação <b>substituirá</b> todos os dados atuais no banco.</div>",
            unsafe_allow_html=True,
        )
        char_up = st.file_uploader(
            "Selecionar arquivo", type=["xlsx"], key="admin_char_up",
            label_visibility="collapsed",
        )
        if char_up:
            try:
                df_preview = pd.read_excel(char_up)
                st.markdown(
                    f"<div style='font-size:.85rem;color:{C_AMBER};margin:8px 0'>"
                    f"📋 Prévia: <b>{len(df_preview)}</b> produtos encontrados</div>",
                    unsafe_allow_html=True,
                )
                st.dataframe(df_preview.head(10), height=220)

                col_imp1, col_imp2 = st.columns([2, 8])
                with col_imp1:
                    if st.button("✅ Confirmar Importação", use_container_width=True, type="primary"):
                        try:
                            db_save(df_preview)
                            st.success(f"✅ {len(df_preview)} produtos importados com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro na importação: {e}")
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── EDITAR ────────────────────────────────────────────────────────────────
    df_admin = db_load()
    if df_admin.empty:
        st.info("Nenhum dado no banco. Use a importação acima para começar.")
    else:
        sec("✏️", f"Editar Tabela de Características  ·  {len(df_admin)} produtos")

        st.markdown(
            f"<div style='font-size:.82rem;color:{TXT_S};margin-bottom:10px'>"
            f"Edite os valores diretamente na tabela. Clique em <b style='color:{C_CYAN}'>Salvar alterações</b> para persistir no banco.</div>",
            unsafe_allow_html=True,
        )

        edited = st.data_editor(
            df_admin,
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            column_config={
                "V_uso": st.column_config.NumberColumn("Ordem", format="%d"),
                "MARCA": st.column_config.TextColumn("Marca"),
                "DESCRICAO": st.column_config.TextColumn("Descrição", width="large"),
                "COD_PRODUTO": st.column_config.TextColumn("Código"),
                "PCT_CX": st.column_config.NumberColumn("PCT/Cx", format="%.0f", help="Pacotes por caixa"),
                "UN_PCT": st.column_config.NumberColumn("Un/PCT", format="%.0f", help="Unidades por pacote"),
                "PESO_PCT": st.column_config.NumberColumn("Peso PCT (kg)", format="%.3f", help="Peso do pacote em kg"),
                "CLASSIFICACAO_PRODUTO": st.column_config.SelectboxColumn(
                    "Classificação",
                    options=["ATIVO", "EXCLUSIVO", "INATIVO"],
                ),
            },
            key="admin_editor",
        )

        col_sv1, col_sv2, col_sv3 = st.columns([2, 2, 8])
        with col_sv1:
            if st.button("💾 Salvar alterações", use_container_width=True, type="primary"):
                try:
                    db_save(edited)
                    st.success("✅ Alterações salvas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        # ── EXPORTAR ──────────────────────────────────────────────────────────
        with col_sv2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_admin.to_excel(writer, index=False, sheet_name="Planilha1")
            buf.seek(0)
            st.download_button(
                "📤 Exportar .xlsx",
                data=buf,
                file_name="Característica_dos_Produtos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        # ── RESUMO TABELA ─────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        sec("📊", "Resumo do Banco de Características")

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        kpis_adm = [
            (C_CYAN,   "📦", "TOTAL PRODUTOS",    fmt_br(len(df_admin), 0),     ""),
            (C_TEAL,   "🏷️", "MARCAS",            fmt_br(df_admin["MARCA"].nunique(), 0), ""),
            (C_GREEN,  "✅", "ATIVOS",
             fmt_br((df_admin["CLASSIFICACAO_PRODUTO"] == "ATIVO").sum(), 0), ""),
            (C_AMBER,  "🌟", "EXCLUSIVOS",
             fmt_br((df_admin["CLASSIFICACAO_PRODUTO"] == "EXCLUSIVO").sum(), 0), ""),
        ]
        for col, (acc, icon, lbl, val, sub) in zip([col_r1, col_r2, col_r3, col_r4], kpis_adm):
            col.markdown(
                f"""<div class="kpi-card" style="--accent:{acc}">
                  <div class="kpi-icon">{icon}</div>
                  <div class="kpi-label">{lbl}</div>
                  <div class="kpi-value">{val}</div>
                  <div class="kpi-sub">{sub}</div></div>""",
                unsafe_allow_html=True,
            )

        # Tabela de médias por classificação
        st.markdown("<br>", unsafe_allow_html=True)
        grp = (
            df_admin.groupby("CLASSIFICACAO_PRODUTO")
            .agg(
                Produtos=("COD_PRODUTO","count"),
                Peso_Médio=("PESO_PCT","mean"),
                Un_Médio=("UN_PCT","mean"),
                CX_Médio=("PCT_CX","mean"),
            )
            .reset_index()
        )
        grp["Peso_Médio"] = grp["Peso_Médio"].apply(lambda v: fmt_br(v, 3) + " kg")
        grp["Un_Médio"]   = grp["Un_Médio"].apply(lambda v: fmt_br(v, 1) + " un")
        grp["CX_Médio"]   = grp["CX_Médio"].apply(lambda v: fmt_br(v, 1) + " cx")
        grp = grp.rename(columns={"CLASSIFICACAO_PRODUTO": "Classificação",
                                   "Peso_Médio": "Peso Médio/PCT",
                                   "Un_Médio": "Un Médio/PCT",
                                   "CX_Médio": "PCT Médio/CX"})
        st.dataframe(grp, use_container_width=True, hide_index=True)

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# 📊  PÁGINA: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
base_up = st.sidebar.file_uploader("Carregar Base (.xlsx)", type=["xlsx"])

if not base_up:
    st.markdown(
        f"<div style='text-align:center;padding:80px 20px;"
        f"color:{TXT_S};font-family:Inter,sans-serif'>"
        f"<div style='font-size:3rem'>📂</div>"
        f"<div style='font-family:Montserrat,sans-serif;font-size:1.4rem;"
        f"font-weight:700;color:{TXT_H};margin:12px 0 8px'>Dashboard de Faturamento</div>"
        f"<div>Faça upload da <b style='color:{C_CYAN}'>Base.xlsx</b> na barra lateral</div>"
        f"<div style='margin-top:12px;font-size:.85rem'>"
        f"As <b style='color:{C_TEAL}'>características dos produtos</b> são gerenciadas em "
        f"<b>⚙️ Administração</b></div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.stop()

if n_char == 0:
    st.warning("⚠️ Banco de características vazio. Acesse **⚙️ Administração** e importe a planilha de características para que os indicadores de Kg, Caixas e Unidades sejam calculados corretamente.")

df_raw, wk_map = load_data(base_up.read())

# ── FILTROS GLOBAIS ───────────────────────────────────────────────────────────
st.sidebar.markdown(
    f"<div style='font-size:.8rem;font-weight:600;color:{C_CYAN};letter-spacing:.06em;margin-bottom:8px'>"
    f"🔍 FILTROS GLOBAIS</div>",
    unsafe_allow_html=True,
)

sit_opts = sorted(df_raw["situacao_NF"].dropna().unique())
sit_sel  = st.sidebar.multiselect("Situação NF", sit_opts, default=sit_opts, key="fs_sit")

tra_opts = sorted(df_raw["transacao_str"].dropna().unique())
tra_sel  = st.sidebar.multiselect("Transação Produto", tra_opts, default=tra_opts, key="fs_tra")

semanas_disp = sorted(df_raw["semana_sort"].unique())
lbl_map = {
    r["semana_sort"]: r["semana_label"]
    for _, r in df_raw[["semana_sort","semana_label"]].drop_duplicates().iterrows()
}
sel_range = st.sidebar.select_slider(
    "Intervalo de Semanas",
    options=semanas_disp,
    value=(semanas_disp[0], semanas_disp[-1]),
    format_func=lambda x: lbl_map[x],
    key="fs_range",
)

cli_opts  = sorted(df_raw["nome_cliente"].dropna().unique())
cli_sel   = st.sidebar.multiselect("Clientes", cli_opts, default=cli_opts, key="fs_cli")

prod_opts = sorted(df_raw["prod_nome"].dropna().unique())
prod_sel  = st.sidebar.multiselect("Produtos", prod_opts, default=prod_opts, key="fs_prod")

dep_opts = sorted(df_raw["deposito"].dropna().unique())
dep_sel  = st.sidebar.multiselect("Depósito", dep_opts, default=dep_opts, key="fs_dep")

# ── FILTRO DE DATAS ───────────────────────────────────────────────────────────
date_min_v = df_raw["emissao"].dt.date.min()
date_max_v = df_raw["emissao"].dt.date.max()

# ── Botões de mês clicáveis ──────────────────────────────────────────────────
import calendar
_meses_pt = {
    1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
    7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"
}
_meses_cheio = {
    1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
    7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"
}

# Obtém os meses disponíveis nos dados
_meses_disp = (
    df_raw[["emissao"]]
    .assign(ano=df_raw["emissao"].dt.year, mes=df_raw["emissao"].dt.month)
    [["ano","mes"]].drop_duplicates().sort_values(["ano","mes"])
)

st.sidebar.markdown(
    f"<div style='font-size:.75rem;font-weight:600;color:{TXT_S};letter-spacing:.05em;"
    f"margin-bottom:6px'>📅 FILTRAR POR MÊS</div>",
    unsafe_allow_html=True,
)

# Renderiza botões de mês em grade de 4 colunas
_mes_cols = st.sidebar.columns(4)
for _i, (_, _row) in enumerate(_meses_disp.iterrows()):
    _ano, _mes = int(_row["ano"]), int(_row["mes"])
    _btn_label = f"{_meses_pt[_mes]}/{str(_ano)[-2:]}"
    with _mes_cols[_i % 4]:
        if st.button(_btn_label, key=f"btn_mes_{_ano}_{_mes}", use_container_width=True):
            import datetime as _dt
            _last_day = calendar.monthrange(_ano, _mes)[1]
            st.session_state["fs_date_from"] = _dt.date(_ano, _mes, 1)
            st.session_state["fs_date_to"]   = _dt.date(_ano, _mes, _last_day)
            st.session_state["fs_month"]      = f"{_meses_cheio[_mes]}/{_ano}"

st.sidebar.markdown(f"<div style='margin-top:8px'></div>", unsafe_allow_html=True)

date_from = st.sidebar.date_input(
    "Data inicial",
    value=date_min_v,
    min_value=date_min_v,
    max_value=date_max_v,
    key="fs_date_from",
    format="DD/MM/YYYY",
)
date_to = st.sidebar.date_input(
    "Data final",
    value=date_max_v,
    min_value=date_min_v,
    max_value=date_max_v,
    key="fs_date_to",
    format="DD/MM/YYYY",
)
# garante ordem correta
if date_from > date_to:
    date_from, date_to = date_to, date_from

st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)

# ── FILTRAGEM ─────────────────────────────────────────────────────────────────
df_base = df_raw[
    df_raw["situacao_NF"].isin(sit_sel)
    & df_raw["transacao_str"].isin(tra_sel)
    & df_raw["semana_sort"].between(sel_range[0], sel_range[1])
    & df_raw["emissao"].dt.date.between(date_from, date_to)
    & df_raw["nome_cliente"].isin(cli_sel)
    & df_raw["prod_nome"].isin(prod_sel)
    & df_raw["deposito"].isin(dep_sel)
].copy()


def apply_xf(df):
    if st.session_state.xf_produto:
        df = df[df["prod_nome"].isin(st.session_state.xf_produto)]
    if st.session_state.xf_cliente:
        df = df[df["nome_cliente"].isin(st.session_state.xf_cliente)]
    if st.session_state.xf_situacao:
        df = df[df["situacao_NF"].isin(st.session_state.xf_situacao)]
    if st.session_state.xf_transacao:
        df = df[df["transacao_str"].isin(st.session_state.xf_transacao)]
    if st.session_state.xf_semana:
        df = df[df["semana_label"].isin(st.session_state.xf_semana)]
    return df


df = apply_xf(df_base)

# ── SEMANAS CANÔNICAS DO INTERVALO SELECIONADO ────────────────────────────────
# Todas as semanas do df_raw que estão dentro do intervalo (sel_range) e do
# filtro de datas — independentemente de qualquer outro filtro.  Usadas para
# reindexar e garantir semanas zeradas em todos os gráficos.
_raw_in_range = df_raw[
    df_raw["semana_sort"].between(sel_range[0], sel_range[1])
    & df_raw["emissao"].dt.date.between(date_from, date_to)
]
ALL_RANGE_SORTS: list = sorted(_raw_in_range["semana_sort"].unique())
_wk_canon = (
    _raw_in_range[["semana_sort", "semana_label", "date_range"]]
    .drop_duplicates()
    .sort_values("semana_sort")
)


def _reindex_to_all_weeks(df_agg: "pd.DataFrame", extra_keys: list = None) -> "pd.DataFrame":
    """Garante que df_agg contém uma linha por cada semana em ALL_RANGE_SORTS.

    df_agg deve ter 'semana_sort' como coluna.  Se extra_keys for passado
    (e.g. ['deposito']), o produto cartesiano semana × extra_keys é usado.
    Colunas numéricas ausentes ficam 0; strings ficam ''.
    """
    meta_cols = ["semana_sort", "semana_label", "date_range"]

    if extra_keys:
        # produto cartesiano: todas as semanas × todos os valores de cada chave
        key_vals = [df_agg[k].dropna().unique().tolist() for k in extra_keys]
        import itertools
        combos = list(itertools.product(ALL_RANGE_SORTS, *key_vals))
        idx_cols = ["semana_sort"] + extra_keys
        full_idx = pd.DataFrame(combos, columns=idx_cols)
        merged = full_idx.merge(df_agg, on=idx_cols, how="left")
    else:
        full_idx = pd.DataFrame({"semana_sort": ALL_RANGE_SORTS})
        merged = full_idx.merge(df_agg, on="semana_sort", how="left")

    # preenche numéricos com 0, strings com ''
    for col in merged.columns:
        if col in meta_cols + (extra_keys or []):
            continue
        if pd.api.types.is_numeric_dtype(merged[col]):
            merged[col] = merged[col].fillna(0)
        else:
            merged[col] = merged[col].fillna("")

    # reatacha semana_label e date_range canônicos
    merged = merged.merge(_wk_canon, on="semana_sort", how="left", suffixes=("", "_can"))
    for c in ["semana_label", "date_range"]:
        if f"{c}_can" in merged.columns:
            merged[c] = merged[f"{c}_can"].fillna(merged.get(c, ""))
            merged.drop(columns=[f"{c}_can"], inplace=True)

    return merged.sort_values("semana_sort").reset_index(drop=True)

any_xf = any([
    st.session_state.xf_produto, st.session_state.xf_cliente,
    st.session_state.xf_situacao, st.session_state.xf_transacao,
    st.session_state.xf_semana,
    len(sit_sel) < len(sit_opts),
    len(tra_sel) < len(tra_opts),
    len(cli_sel) < len(cli_opts),
    len(prod_sel) < len(prod_opts),
    len(dep_sel) < len(dep_opts),
    sel_range != (semanas_disp[0], semanas_disp[-1]),
    date_from != date_min_v or date_to != date_max_v,
])

# ── HEADER ────────────────────────────────────────────────────────────────────
h_col, btn_col = st.columns([8, 1])
with h_col:
    st.markdown(
        f"<h2 style='font-family:Montserrat,sans-serif;color:{TXT_H};"
        f"font-size:1.6rem;font-weight:800;margin-bottom:2px'>"
        f"📊 Dashboard de Faturamento Semanal</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"**{fmt_br(len(df), 0)}** registros · "
        f"**{df['semana_sort'].nunique()}** semanas · "
        f"**{df['nome_cliente'].nunique()}** clientes · "
        f"**{df['codigo_produto'].nunique()}** produtos"
    )
with btn_col:
    # ==============================================
    # CORREÇÃO: Remover as chaves dos widgets de filtro
    # em vez de tentar reatribuir valores diretamente.
    # ==============================================
    if st.button("🗑️ Limpar\nFiltros", use_container_width=True, disabled=not any_xf):
        # Limpa os filtros de seleção por clique (xf_*)
        for k in ["xf_produto","xf_cliente","xf_situacao","xf_transacao","xf_semana"]:
            st.session_state[k] = set()
        
        # Remove as chaves dos widgets de filtro para que voltem ao default
        for k in ["fs_sit", "fs_tra", "fs_cli", "fs_prod", "fs_dep", "fs_range",
                  "fs_date_from", "fs_date_to", "fs_month"]:
            if k in st.session_state:
                del st.session_state[k]
        
        st.rerun()

if any_xf:
    pills = ""
    for k, label in [
        ("xf_produto","Produto"),("xf_cliente","Cliente"),
        ("xf_situacao","Situação"),("xf_transacao","Transação"),("xf_semana","Semana"),
    ]:
        for v in sorted(st.session_state[k]):
            pills += f'<span class="pill">⬡ {label}: {v}</span>'
    st.markdown(f'<div style="margin:4px 0 8px">{pills}</div>', unsafe_allow_html=True)

st.markdown(
    f'<p class="tip">💡 Clique em qualquer barra ou ponto para filtrar o relatório. '
    f'Clique novamente para remover o filtro.</p>',
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("Nenhum dado com os filtros ativos.")
    st.stop()


# ── KPIs ──────────────────────────────────────────────────────────────────────
total_kg   = df["kilos"].sum()
total_cx   = df["caixas"].sum()
total_un   = df["unidades"].sum()
n_semanas  = df["semana_sort"].nunique()
avg_kg_sem = total_kg / n_semanas if n_semanas else 0
n_pedidos  = df[df["tem_pedido"]]["pedido_clean"].nunique()

kpis = [
    (C_CYAN,   "⚖️",  "TOTAL KILOS",       f"{fmt_br(total_kg, 1)} kg",       ""),
    (C_TEAL,   "📦",  "TOTAL CAIXAS",       f"{fmt_br(total_cx, 1)} cx",       ""),
    (C_AMBER,  "🔢",  "TOTAL UNIDADES",     f"{fmt_br(total_un, 0)} un",       ""),
    (C_VIOLET, "🛒",  "PEDIDOS",            fmt_br(n_pedidos, 0),              f"{df['nome_cliente'].nunique()} clientes"),
    (C_ORANGE, "🏭",  "DEPÓSITOS ATIVOS",   f"{df['deposito'].nunique()}",     f"{df['codigo_produto'].nunique()} produtos"),
]
cols_kpi = st.columns(5)
for col, (accent, icon, label, val, sub) in zip(cols_kpi, kpis):
    col.markdown(
        f"""<div class="kpi-card" style="--accent:{accent}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-sub">{sub}</div></div>""",
        unsafe_allow_html=True,
    )

# ── CARDS DE MÉDIA ─────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
avg_cols = st.columns(3)
avg_kpis = [
    (C_CYAN,   "📈", "MÉDIA KG/SEM",  f"{fmt_br(avg_kg_sem, 1)} kg",
     f"{n_semanas} semanas no período"),
    (C_TEAL,   "📈", "MÉDIA CX/SEM",  f"{fmt_br(total_cx / n_semanas, 1)} cx" if n_semanas else "—",
     "caixas por semana"),
    (C_AMBER,  "📈", "MÉDIA UN/SEM",  f"{fmt_br(total_un / n_semanas, 0)} un" if n_semanas else "—",
     "unidades por semana"),
]
for col, (accent, icon, label, val, sub) in zip(avg_cols, avg_kpis):
    col.markdown(
        f"""<div class="kpi-card" style="--accent:{accent}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-sub">{sub}</div></div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ── COR POR DEPÓSITO ──────────────────────────────────────────────────────────
dep_list   = sorted(df_raw["deposito"].dropna().unique())
dep_colors = {d: c for d, c in zip(dep_list, [C_CYAN, C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN])}


# ══════════════════════════════════════════════════════════════════════════════
# ABAS PRINCIPAIS DO DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# 🤖  MOTOR DE INTELIGÊNCIA COMERCIAL
# ══════════════════════════════════════════════════════════════════════════════
import json  as _json
import math  as _math

# ── Helpers estatísticos ──────────────────────────────────────────────────────

def _ai_mean(vals):
    v = [x for x in vals if x is not None and not _math.isnan(float(x))]
    return round(sum(v) / len(v), 2) if v else 0.0

def _ai_median(vals):
    v = sorted(x for x in vals if x is not None and not _math.isnan(float(x)))
    if not v: return 0.0
    n = len(v)
    return round(v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2, 2)

def _ai_std(vals):
    v = [x for x in vals if x is not None and not _math.isnan(float(x))]
    if len(v) < 2: return 0.0
    m = sum(v) / len(v)
    return round(_math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)), 2)

def _ai_cv(vals):
    # Coeficiente de variacao (%)
    m, s = _ai_mean(vals), _ai_std(vals)
    return round(s / m * 100, 1) if m else 0.0

def _ai_iqr(vals):
    v = sorted(x for x in vals if x is not None and not _math.isnan(float(x)))
    if len(v) < 4: return 0.0
    q1 = v[len(v) // 4]
    q3 = v[3 * len(v) // 4]
    return round(q3 - q1, 2)

def _ai_outliers_iqr(vals):
    # Indices dos outliers via IQR
    v = [x for x in vals if x is not None and not _math.isnan(float(x))]
    if len(v) < 4: return []
    mid = len(v) // 2
    q1 = _ai_median(v[:mid])
    q3 = _ai_median(v[mid + (len(v) % 2):])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [i for i, x in enumerate(v) if x < lo or x > hi]

def _ai_conc_top1(vals):
    # Percentual do maior item sobre o total
    t = sum(x for x in vals if x and not _math.isnan(float(x)))
    return round(max(vals) / t * 100, 1) if t else 0.0

def _ai_conc_hhi(vals):
    # HHI normalizado 0-100 (0 = distribuido, 100 = um unico item)
    t = sum(x for x in vals if x and not _math.isnan(float(x)))
    if not t or len(vals) < 2: return 0.0
    shares = [x / t for x in vals if x and not _math.isnan(float(x))]
    n = len(shares)
    hhi = sum(s ** 2 for s in shares)
    return round(((hhi - 1 / n) / (1 - 1 / n)) * 100, 1) if n > 1 else 100.0

def _ai_slope(vals):
    # Inclinacao da reta de tendencia linear (kg/periodo)
    if len(vals) < 3: return 0.0
    xs = list(range(len(vals)))
    xm, ym = _ai_mean(xs), _ai_mean(vals)
    num = sum((x - xm) * (y - ym) for x, y in zip(xs, vals))
    den = sum((x - xm) ** 2 for x in xs)
    return round(num / den, 2) if den else 0.0


# ── Score de viabilidade comercial ────────────────────────────────────────────

def _calc_viability_score(freq_s, rec_s, vol_s, avg_vol_s, trend_s,
                           conc_pen, first_pen, seas_pen):
    # Score 0-100: frequencia*0.25 + recorrencia*0.20 + volume*0.15
    # vol_medio*0.10 + tendencia*0.10 - concentracao*0.10
    # primeiro_pedido*0.10 - sazonalidade*0.10
    raw = (freq_s * 0.25 + rec_s * 0.20 + vol_s * 0.15 + avg_vol_s * 0.10
           + trend_s * 0.10 - conc_pen * 0.10 - first_pen * 0.10 - seas_pen * 0.10)
    return max(0, min(100, round(raw)))

def _score_label(score):
    if score >= 80: return "Cliente estrategico",  C_GREEN
    if score >= 60: return "Cliente relevante",    C_CYAN
    if score >= 40: return "Cliente oportunista",  C_AMBER
    return "Cliente de baixo valor", C_RED


# ── Benchmark da base ─────────────────────────────────────────────────────────

def build_client_benchmark(df_b):
    # Calcula benchmarks de volume e frequencia para toda a base de clientes.
    if df_b is None or df_b.empty:
        return {}
    cs = (
        df_b.groupby("nome_cliente")
        .agg(
            kg_total=("kilos", "sum"),
            n_sem=("semana_sort", "nunique"),
            n_ped=("pedido_clean", lambda x: x[df_b.loc[x.index, "tem_pedido"]].nunique()),
        )
        .reset_index()
    )
    kg_l = cs["kg_total"].tolist()
    top5 = cs.nlargest(5, "kg_total")[["nome_cliente", "kg_total"]].to_dict("records")
    return {
        "n_clientes_base": len(cs),
        "kg_media_base": _ai_mean(kg_l),
        "kg_mediana_base": _ai_median(kg_l),
        "kg_top5_min": round(sorted(kg_l, reverse=True)[min(4, len(kg_l) - 1)], 1),
        "kg_desvio_base": _ai_std(kg_l),
        "pedidos_media_base": _ai_mean(cs["n_ped"].tolist()),
        "semanas_media_base": _ai_mean(cs["n_sem"].tolist()),
        "top5_clientes": [{"cliente": r["nome_cliente"], "kg": round(r["kg_total"], 1)} for r in top5],
    }


# ── Construtor de contexto enriquecido ────────────────────────────────────────

def build_ai_context(analysis_type, chart_name, df_f, df_b, df_r, periodo=None, extra=None):
    # Monta payload JSON rico para envio a IA.
    # analysis_type: 'semanal' | 'cliente' | 'produto' | 'deposito' | 'pedido' | 'volume'
    ctx = {
        "grafico": chart_name,
        "tipo_analise": analysis_type,
        "periodo": periodo or f"{str(date_from)} a {str(date_to)}",
        "n_registros": int(len(df_f)),
        "totais": {
            "kg_total": round(float(df_f["kilos"].sum()), 1),
            "cx_total": round(float(df_f["caixas"].sum()), 1),
            "un_total": round(float(df_f["unidades"].sum()), 0),
        },
    }

    bm = build_client_benchmark(df_b)
    ctx["benchmark_base"] = bm

    # ── Semanal ───────────────────────────────────────────────────────────────
    if analysis_type == "semanal":
        wk = (
            df_f.groupby(["semana_sort", "semana_label"])
            .agg(kg=("kilos", "sum"), cx=("caixas", "sum"),
                 un=("unidades", "sum"), n_cli=("nome_cliente", "nunique"))
            .reset_index().sort_values("semana_sort")
        )
        kg_s = wk["kg"].tolist()
        slope = _ai_slope(kg_s)
        ctx["serie_temporal"] = wk[["semana_label", "kg", "cx", "un", "n_cli"]].to_dict("records")
        ctx["metricas"] = {
            "kg_media_semana":   _ai_mean(kg_s),
            "kg_mediana_semana": _ai_median(kg_s),
            "kg_desvio":         _ai_std(kg_s),
            "coef_variacao_pct": _ai_cv(kg_s),
            "n_semanas":         len(kg_s),
            "n_semanas_zeradas": int(sum(1 for x in kg_s if x == 0)),
            "pico_kg":           round(max(kg_s), 1) if kg_s else 0,
            "minimo_kg":         round(min(x for x in kg_s if x > 0), 1) if any(x > 0 for x in kg_s) else 0,
            "outliers_indices":  _ai_outliers_iqr(kg_s),
            "tendencia_slope":   slope,
            "tendencia_dir":     "crescimento" if slope > 0 else "queda" if slope < 0 else "estavel",
        }
        ctx["vs_base"] = {
            "media_base": bm.get("kg_media_base"),
            "relacao_pct": round((ctx["metricas"]["kg_media_semana"] / bm["kg_media_base"] - 1) * 100, 1)
                           if bm.get("kg_media_base") else None,
        }

    # ── Cliente ───────────────────────────────────────────────────────────────
    elif analysis_type == "cliente":
        clientes = sorted(df_f["nome_cliente"].dropna().unique())
        cli_data = []
        for cli in clientes:
            dc  = df_f[df_f["nome_cliente"] == cli]
            dcb = df_b[df_b["nome_cliente"] == cli]

            wk_c = (
                dc.groupby(["semana_sort", "semana_label"])
                .agg(kg=("kilos", "sum"), cx=("caixas", "sum"), un=("unidades", "sum"))
                .reset_index().sort_values("semana_sort")
            )
            kg_s = wk_c["kg"].tolist()

            ped    = dcb[dcb["tem_pedido"]].copy()
            ped_agg = ped.groupby("pedido_clean").agg(
                kg=("kilos", "sum"), dt=("emissao", "min")
            ).sort_values("dt") if not ped.empty else pd.DataFrame()

            kg_ped_s = ped_agg["kg"].tolist() if not ped_agg.empty else []
            n_ped    = len(kg_ped_s)

            intv = []
            if len(ped_agg) >= 2:
                dts = pd.to_datetime(ped_agg["dt"]).tolist()
                intv = [(dts[i+1] - dts[i]).days for i in range(len(dts) - 1)]
            freq_med = _ai_mean(intv)

            infl_ratio, infl_flag = 0.0, False
            if len(kg_ped_s) >= 2:
                resto = _ai_mean(kg_ped_s[1:])
                if resto > 0:
                    infl_ratio = round(kg_ped_s[0] / resto, 2)
                    infl_flag  = infl_ratio >= 2.0

            conc1 = _ai_conc_top1(kg_ped_s) if kg_ped_s else 0.0
            hhi   = _ai_conc_hhi(kg_ped_s)  if kg_ped_s else 0.0

            n_sem_t  = len(kg_s)
            n_sem_a  = int(sum(1 for x in kg_s if x > 0))
            rec_pct  = round(n_sem_a / n_sem_t * 100, 1) if n_sem_t else 0.0
            cv_kg    = _ai_cv(kg_s)
            saz_flag = cv_kg > 60
            slope    = _ai_slope(kg_s)

            if n_ped == 0 or not intv:
                freq_cls = "Sem pedidos identificados"
            elif freq_med <= 7:   freq_cls = f"Alta ({round(freq_med,1)} dias media)"
            elif freq_med <= 21:  freq_cls = f"Media ({round(freq_med,1)} dias media)"
            else:                 freq_cls = f"Baixa ({round(freq_med,1)} dias media)"

            freq_s = (100 if freq_med<=7 else 80 if freq_med<=14
                      else 60 if freq_med<=21 else 40 if freq_med<=30 else 20) if intv else 0
            rec_s  = rec_pct
            kg_tot = float(dc["kilos"].sum())
            vol_s  = min(100, round(kg_tot / bm["kg_media_base"] * 50)) if bm.get("kg_media_base") else 50
            avg_s  = min(100, round(_ai_mean(kg_ped_s) / max(
                        bm.get("kg_media_base", 1) / max(bm.get("pedidos_media_base", 1), 1), 1) * 50))
            tr_s   = 80 if slope > 0 else 50 if slope == 0 else max(0, 50 + slope)
            cp     = 100 if conc1 > 70 else 50 if conc1 > 50 else 0
            fp     = min(100, round(infl_ratio * 30)) if infl_flag else 0
            sp     = min(100, round((cv_kg - 60) * 1.5)) if saz_flag else 0

            score = _calc_viability_score(freq_s, rec_s, vol_s, avg_s, tr_s, cp, fp, sp)

            if score >= 80:
                cli_cls = "Consistente" if rec_pct > 70 else "Em crescimento real"
            elif score >= 60:
                cli_cls = "Em crescimento real" if slope > 0 else ("Sazonal" if saz_flag else "Consistente")
            elif score >= 40:
                cli_cls = "Sazonal" if saz_flag else "Oportunista"
            else:
                cli_cls = ("Inflado (alto volume sem recorrencia)" if infl_flag
                           else "Em queda" if slope < 0 else "Oportunista")

            cli_data.append({
                "cliente":                    cli,
                "kg_total":                   round(kg_tot, 1),
                "n_semanas_periodo":          n_sem_t,
                "n_semanas_ativas":           n_sem_a,
                "taxa_recorrencia_pct":       rec_pct,
                "n_pedidos":                  n_ped,
                "kg_por_pedido_serie":        [round(x, 1) for x in kg_ped_s],
                "kg_medio_pedido":            round(_ai_mean(kg_ped_s), 1),
                "intervalo_medio_dias":       round(freq_med, 1),
                "frequencia_classificacao":   freq_cls,
                "primeiro_pedido_kg":         round(kg_ped_s[0], 1) if kg_ped_s else 0,
                "primeiro_pedido_inflado":    infl_flag,
                "ratio_1o_pedido":            infl_ratio,
                "concentracao_top1_pct":      conc1,
                "concentracao_hhi":           hhi,
                "coef_variacao_pct":          round(cv_kg, 1),
                "sazonalidade_flag":          saz_flag,
                "outliers_semanas_idx":       _ai_outliers_iqr(kg_s),
                "tendencia_slope_kg_sem":     slope,
                "tendencia_dir":              "crescimento" if slope > 0 else "queda" if slope < 0 else "estavel",
                "serie_semanal_kg":           [round(x, 1) for x in kg_s],
                "semanas":                    wk_c["semana_label"].tolist(),
                "score_viabilidade":          score,
                "classificacao_cliente":      cli_cls,
                "vs_media_base_pct":          round((kg_tot / bm["kg_media_base"] - 1) * 100, 1) if bm.get("kg_media_base") else None,
                "esta_no_top5":               kg_tot >= bm.get("kg_top5_min", float("inf")),
            })

        ctx["clientes"] = cli_data
        ctx["top5_base"] = bm.get("top5_clientes", [])

    # ── Produto ───────────────────────────────────────────────────────────────
    elif analysis_type == "produto":
        ps = (
            df_f.groupby(["prod_nome", "codigo_produto"])
            .agg(kg=("kilos","sum"), cx=("caixas","sum"), un=("unidades","sum"),
                 n_cli=("nome_cliente","nunique"), n_sem=("semana_sort","nunique"))
            .reset_index().sort_values("kg", ascending=False)
        )
        kg_l = ps["kg"].tolist()
        ctx["ranking_produtos"] = ps.head(20).to_dict("records")
        ctx["metricas"] = {
            "n_produtos":            len(ps),
            "concentracao_top1_pct": _ai_conc_top1(kg_l),
            "concentracao_hhi":      _ai_conc_hhi(kg_l),
            "kg_media_produto":      _ai_mean(kg_l),
            "kg_mediana_produto":    _ai_median(kg_l),
            "coef_variacao_pct":     _ai_cv(kg_l),
        }
        if not ps.empty:
            top_prod = ps.iloc[0]["prod_nome"]
            wk_tp = (
                df_f[df_f["prod_nome"] == top_prod]
                .groupby(["semana_sort", "semana_label"])["kilos"].sum()
                .reset_index().sort_values("semana_sort")
            )
            ctx["evolucao_produto_ancora"] = {
                "produto": top_prod,
                "serie_kg": wk_tp["kilos"].tolist(),
                "semanas":  wk_tp["semana_label"].tolist(),
                "slope":    _ai_slope(wk_tp["kilos"].tolist()),
            }
        if extra:
            ctx["metrica_exibida"] = extra.get("metrica_rank", "kilos")

    # ── Deposito ──────────────────────────────────────────────────────────────
    elif analysis_type == "deposito":
        ds = (
            df_f.groupby("deposito")
            .agg(kg=("kilos","sum"), cx=("caixas","sum"), un=("unidades","sum"),
                 n_cli=("nome_cliente","nunique"), n_sem=("semana_sort","nunique"))
            .reset_index().sort_values("kg", ascending=False)
        )
        kg_l = ds["kg"].tolist()
        ctx["depositos"] = ds.to_dict("records")
        ctx["metricas"] = {
            "n_depositos":            len(ds),
            "concentracao_top1_pct":  _ai_conc_top1(kg_l),
            "concentracao_hhi":       _ai_conc_hhi(kg_l),
            "deposito_principal":     ds.iloc[0]["deposito"] if not ds.empty else "",
        }
        wk_d = (
            df_f.groupby(["semana_sort", "semana_label", "deposito"])["kilos"]
            .sum().reset_index().sort_values(["semana_sort", "deposito"])
        )
        ctx["serie_temporal_por_deposito"] = wk_d.to_dict("records")

    # ── Pedido ────────────────────────────────────────────────────────────────
    elif analysis_type == "pedido":
        ped = df_f[df_f["tem_pedido"]].copy() if not df_f.empty else df_f
        if not ped.empty:
            pa = (
                ped.groupby(["pedido_clean", "nome_cliente"])
                .agg(kg=("kilos","sum"), cx=("caixas","sum"),
                     n_notas=("numero_nota","nunique"), dt=("emissao","min"))
                .reset_index().sort_values("kg", ascending=False)
            )
            kg_l = pa["kg"].tolist()
            ctx["pedidos"]  = pa.head(30).assign(dt=pa["dt"].astype(str)).to_dict("records")
            ctx["metricas"] = {
                "n_pedidos":             len(pa),
                "kg_media_pedido":       _ai_mean(kg_l),
                "kg_mediana_pedido":     _ai_median(kg_l),
                "coef_variacao_pct":     _ai_cv(kg_l),
                "concentracao_top1_pct": _ai_conc_top1(kg_l),
                "outliers_indices":      _ai_outliers_iqr(kg_l),
            }
            primeiros = pa.sort_values("dt").groupby("nome_cliente").first().reset_index()
            flags = []
            for _, r in primeiros.iterrows():
                outros = pa[(pa["nome_cliente"] == r["nome_cliente"]) &
                            (pa["pedido_clean"] != r["pedido_clean"])]["kg"].tolist()
                if outros:
                    ratio = round(r["kg"] / _ai_mean(outros), 2) if _ai_mean(outros) else 0
                    if ratio >= 2:
                        flags.append({"cliente": r["nome_cliente"],
                                      "1o_pedido_kg": round(r["kg"], 1),
                                      "media_demais_kg": round(_ai_mean(outros), 1),
                                      "ratio": ratio})
            ctx["alertas_primeiro_pedido_inflado"] = flags

    # ── Volume ────────────────────────────────────────────────────────────────
    elif analysis_type == "volume":
        vc = (
            df_f.groupby("nome_cliente")
            .agg(kg=("kilos","sum"), cx=("caixas","sum"), un=("unidades","sum"),
                 n_sem=("semana_sort","nunique"),
                 n_ped=("pedido_clean", lambda x: x[df_f.loc[x.index, "tem_pedido"]].nunique()))
            .reset_index().sort_values("kg", ascending=False)
        )
        kg_l = vc["kg"].tolist()
        ctx["volume_por_cliente"] = vc.to_dict("records")
        ctx["metricas"] = {
            "kg_media":              _ai_mean(kg_l),
            "kg_mediana":            _ai_median(kg_l),
            "coef_variacao_pct":     _ai_cv(kg_l),
            "concentracao_top1_pct": _ai_conc_top1(kg_l),
            "concentracao_hhi":      _ai_conc_hhi(kg_l),
        }

    if extra:
        ctx["contexto_extra"] = extra

    return _json.dumps(ctx, ensure_ascii=False, default=str, indent=2)


# ── Prompts especializados por tipo de analise ────────────────────────────────

_STAT_TERMS_GLOSSARY = (
    "\n\nGLOSSARIO — ao citar termos estatisticos, inclua uma breve explicacao entre parenteses para leigos:\n"
    "- Media (soma de todos os valores dividida pela quantidade)\n"
    "- Mediana (valor central quando todos sao ordenados — metade esta acima, metade abaixo)\n"
    "- Desvio padrao (o quanto os valores variam em relacao a media — quanto maior, mais irregular)\n"
    "- Coeficiente de variacao / CV (variabilidade percentual — acima de 60% indica comportamento muito instavel)\n"
    "- IQR / Amplitude interquartil (faixa onde estao os 50% centrais dos dados, ignora extremos)\n"
    "- HHI / Indice Herfindahl (mede concentracao — 0 = distribuido igualmente, 100 = totalmente concentrado em um item)\n"
    "- Slope / Inclinacao (direcao da tendencia linear — positivo = crescimento, negativo = queda)\n"
    "- Outlier (valor atipico que foge muito do padrao dos demais)\n"
    "Sempre que mencionar esses termos na analise, coloque a explicacao em parenteses logo apos.\n"
)

_AI_PRECALC_NOTICE = (
    "\n\nIMPORTANTE: Todos os calculos estatisticos ja foram realizados previamente pelo sistema. "
    "Voce deve APENAS interpretar os numeros fornecidos. NAO recalcule medias, desvios, slopes ou qualquer metrica. "
    "Use os valores exatos do JSON.\n"
)

_SYSTEM_COMMERCIAL = (
    "Voce e um analista senior de inteligencia comercial especializado em distribuicao de alimentos/produtos.\n"
    "Sua funcao e diagnosticar se clientes sao viaveis, recorrentes e estrategicos para o negocio.\n"
    "Voce NAO descreve dados - voce toma DECISOES comerciais baseadas neles.\n\n"
    "REGRAS OBRIGATORIAS:\n"
    "- Diferencie recorrencia real de compra pontual (nao confunda n_pedidos=1 com recorrencia)\n"
    "- Primeiro pedido >= 2x media dos demais = formacao de estoque (penalize)\n"
    "- Frequencia alta: <=7 dias; media: 8-21 dias; baixa: >21 dias\n"
    "- Concentracao >50% em 1 pedido = risco; >70% = risco critico\n"
    "- CV >60% = alta variabilidade/sazonalidade potencial (confirme se padrao se repete)\n"
    "- Pico isolado NAO e tendencia de crescimento - exija consistencia\n"
    "- Compare SEMPRE com benchmark_base e top5_clientes\n"
    "- Toda conclusao deve ter base numerica explicita\n"
    "- Nao use 'monitorar' sem uma acao especifica e mensuravel\n\n"
    "FORMATO OBRIGATORIO (markdown, portugues brasileiro, numeros no formato BR):\n"
    "### Resumo Executivo\n"
    "(2-3 frases com a conclusao principal - responda direto se o cliente vale a pena)\n\n"
    "### Diagnostico Quantitativo\n"
    "(frequencia, recorrencia, volume, variabilidade - com numeros)\n\n"
    "### Frequencia e Recorrencia\n"
    "(intervalo medio entre pedidos, taxa de recorrencia, semanas ativas vs. total)\n\n"
    "### Comparacao com a Base\n"
    "(vs. media da base, mediana, top 5 - com percentuais explicitos)\n\n"
    "### Riscos e Distorcoes\n"
    "(primeiro pedido inflado? concentracao? sazonalidade? outliers?)\n\n"
    "### Ciclo de Vida e Tendencia\n"
    "(crescimento estrutural, queda, estagnacao, sazonalidade recorrente?)\n\n"
    "### Acoes Recomendadas\n"
    "(maximo 3, especificas, mensuraveis, com prazo implicito)\n\n"
    "### Score e Conclusao Comercial\n"
    "Score calculado pelo sistema: {score}/100\n"
    "**Classificacao:** (Consistente / Em crescimento real / Sazonal / Oportunista / Inflado / Em queda)\n"
    "**Decisao:** (manter / expandir / priorizar / reclassificar / despriorizar)\n"
    "**Justificativa:** (1-2 frases baseadas em dados)"
    + _STAT_TERMS_GLOSSARY + _AI_PRECALC_NOTICE
)

_SYSTEM_GENERAL = (
    "Voce e um analista senior de inteligencia comercial especializado em distribuicao de alimentos/produtos.\n"
    "Voce NAO descreve dados visiveis - extrai insights decisorios e acionaveis.\n"
    "Responda em portugues brasileiro, com markdown estruturado e numeros no formato BR.\n"
    "Foque em: tendencias reais, concentracoes, riscos operacionais e oportunidades comerciais.\n"
    "Compare com a media da base quando disponivel.\n"
    "Toda conclusao deve ter base numerica. Nao use linguagem generica."
    + _STAT_TERMS_GLOSSARY + _AI_PRECALC_NOTICE
)

# ── Prompts especificos por tipo de grafico ──────────────────────────────────
_CHART_SPECIFIC_INSTRUCTIONS = {
    "semanal": (
        "FOCO DESTA ANALISE: Tendencia e sazonalidade SEMANAL.\n"
        "Voce esta analisando a EVOLUCAO TEMPORAL semana a semana. Concentre-se em:\n"
        "- Identificar tendencias de crescimento ou queda ao longo das semanas\n"
        "- Detectar sazonalidade ou padroes ciclicos\n"
        "- Avaliar estabilidade vs. volatilidade semanal\n"
        "- Comparar semanas recentes vs. historico\n"
        "NAO analise clientes individuais — foque na visao temporal consolidada."
    ),
    "cliente": (
        "FOCO DESTA ANALISE: Viabilidade comercial de CLIENTES.\n"
        "Voce esta analisando clientes especificos. Concentre-se em:\n"
        "- Diagnostico individual de cada cliente listado\n"
        "- Recorrencia, frequencia e volume de cada um\n"
        "- Comparacao entre clientes e com a base geral\n"
        "- Score de viabilidade e classificacao comercial\n"
        "NAO analise produtos ou depositos — foque nos clientes."
    ),
    "produto": (
        "FOCO DESTA ANALISE: Desempenho e concentracao de PRODUTOS.\n"
        "Voce esta analisando produtos. Concentre-se em:\n"
        "- Ranking e participacao de cada produto\n"
        "- Concentracao (poucos produtos dominam o volume?)\n"
        "- Evolucao dos produtos principais\n"
        "- Diversificacao do mix de produtos\n"
        "NAO analise clientes individuais — foque nos produtos."
    ),
    "deposito": (
        "FOCO DESTA ANALISE: Distribuicao por DEPOSITO/FILIAL.\n"
        "Voce esta analisando depositos. Concentre-se em:\n"
        "- Dependencia de um deposito especifico\n"
        "- Distribuicao do volume entre depositos\n"
        "- Evolucao temporal por deposito\n"
        "- Riscos de concentracao logistica\n"
        "NAO analise clientes ou produtos — foque nos depositos."
    ),
    "pedido": (
        "FOCO DESTA ANALISE: Padrao e consistencia de PEDIDOS.\n"
        "Voce esta analisando pedidos. Concentre-se em:\n"
        "- Volume e frequencia de pedidos por cliente\n"
        "- Deteccao de primeiro pedido inflado\n"
        "- Consistencia no tamanho dos pedidos\n"
        "- Padrao temporal de realizacao de pedidos\n"
        "NAO analise produtos ou depositos — foque nos pedidos."
    ),
    "volume": (
        "FOCO DESTA ANALISE: Volume e benchmark por CLIENTE.\n"
        "Voce esta analisando o volume total dos clientes. Concentre-se em:\n"
        "- Ranking de clientes por volume\n"
        "- Concentracao (poucos clientes dominam?)\n"
        "- Comparacao com media e mediana da base\n"
        "- Eficiencia (kg por pedido, kg por semana)\n"
        "NAO analise produtos ou depositos — foque no volume por cliente."
    ),
}


# ── Gerador de PDF ────────────────────────────────────────────────────────────

def _generate_pdf(analysis_md: str, chart_name: str, scores_info=None):
    """Gera PDF da analise mantendo cores e formatacao."""
    from fpdf import FPDF
    import re as _re
    import tempfile as _tmp

    _UNICODE_MAP = {
        '\u2014': '-', '\u2013': '-', '\u2012': '-',
        '\u2018': "'", '\u2019': "'", '\u201C': '"', '\u201D': '"',
        '\u2026': '...', '\u2022': '*', '\u2023': '>',
        '\u2039': '<', '\u203A': '>', '\u00AB': '<<', '\u00BB': '>>',
        '\u2190': '<-', '\u2192': '->', '\u2194': '<->',
        '\u2265': '>=', '\u2264': '<=', '\u2260': '!=',
        '\u221E': 'inf', '\u00B2': '2', '\u00B3': '3',
        '\u2070': '0', '\u00B9': '1',
        '\u0394': 'Delta', '\u03B1': 'alpha', '\u03B2': 'beta',
        '\u2211': 'Sum', '\u221A': 'sqrt',
        '\u20AC': 'EUR', '\u00A3': 'GBP', '\u00A5': 'JPY',
    }

    def _safe(txt: str) -> str:
        """Sanitiza texto para latin-1 (compatibilidade FPDF Helvetica)."""
        for uc, repl in _UNICODE_MAP.items():
            txt = txt.replace(uc, repl)
        return txt.encode('latin-1', errors='replace').decode('latin-1')

    class _AnalysisPDF(FPDF):
        def header(self):
            self.set_fill_color(8, 14, 28)
            self.rect(0, 0, 210, 297, 'F')
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(56, 189, 248)
            self.cell(0, 10, _safe("INTELIGENCIA COMERCIAL"), ln=True, align="C")
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(241, 245, 249)
            self.cell(0, 8, _safe(chart_name), ln=True, align="C")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 6, _safe(f"Periodo: {str(date_from)} a {str(date_to)}"), ln=True, align="C")
            self.ln(4)
            self.set_draw_color(26, 46, 80)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-25)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(100, 116, 139)
            self.cell(0, 4, _safe("Lembrete: Toda Inteligencia Artificial pode cometer erros."), ln=True, align="C")
            self.cell(0, 4, _safe("E importante revisar a analise apresentada antes de tomar decisoes."), ln=True, align="C")
            self.cell(0, 4, _safe(f"GPT-4o-mini  |  Pagina {self.page_no()}"), ln=True, align="C")

    pdf = _AnalysisPDF()
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.add_page()

    if scores_info:
        for cli_name, score, label, color_hex in scores_info:
            r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
            pdf.set_draw_color(r, g, b)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(r, g, b)
            pdf.cell(0, 6, _safe(f"Score: {score}/100 - {label} | {cli_name}"), ln=True)
        pdf.ln(4)

    lines = analysis_md.split("\n") if analysis_md else []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(56, 189, 248)
            pdf.cell(0, 7, _safe(stripped[4:]), ln=True)
        elif stripped.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(56, 189, 248)
            pdf.cell(0, 8, _safe(stripped[3:]), ln=True)
        elif stripped.startswith("**") and stripped.endswith("**"):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(241, 245, 249)
            pdf.cell(0, 5, _safe(stripped.replace("**", "")), ln=True)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(203, 213, 225)
            clean = _re.sub(r'\*\*(.*?)\*\*', r'\1', stripped[2:])
            pdf.cell(5)
            pdf.multi_cell(0, 5, _safe(f"  {clean}"))
        elif stripped:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(203, 213, 225)
            clean = _re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)
            pdf.multi_cell(0, 5, _safe(clean))

    fp = _tmp.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(fp.name)
    return fp.name


# ── Modal de analise ──────────────────────────────────────────────────────────

# Cache key helper — gera chave unica por grafico + filtros ativos
def _cache_key(chart_name: str):
    """Gera chave de cache unica por grafico e filtros ativos."""
    import hashlib as _hl
    _filter_sig = _json.dumps({
        "clientes": sorted(st.session_state.get("xf_cliente", set())),
        "produtos": sorted(st.session_state.get("xf_produto", set())),
        "depositos": sorted(st.session_state.get("xf_deposito", set())),
        "semanas": sorted(st.session_state.get("xf_semana", set())),
        "date_from": str(date_from),
        "date_to": str(date_to),
    }, default=str)
    return f"ai_cache_{_hl.md5((chart_name + _filter_sig).encode()).hexdigest()}"

# Inicializa cache de analises no session_state
if "_ai_analysis_cache" not in st.session_state:
    st.session_state["_ai_analysis_cache"] = {}


@st.dialog("Inteligencia Comercial", width="large")
def _show_ai_analysis(chart_name: str, context_json: str, analysis_type: str = "geral"):
    # Modal de analise - so chamada ao clicar no botao, NUNCA automaticamente.
    import openai as _oa
    import os     as _os2

    _api_key = _os2.environ.get("OPENAI_API_KEY", "")
    if not _api_key:
        st.warning("OPENAI_API_KEY nao encontrada. Configure no .env e reinicie.")
        return
    _oa.api_key = _api_key

    # ── Cabecalho ─────────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:.72rem;font-weight:700;color:{C_CYAN};"
        f"letter-spacing:.09em;margin-bottom:2px'>INTELIGENCIA COMERCIAL</div>"
        f"<div style='font-size:1rem;color:{TXT_H};font-weight:700;"
        f"margin-bottom:2px'>{chart_name}</div>"
        f"<div style='font-size:.75rem;color:{TXT_S};margin-bottom:14px'>"
        f"Analise baseada nos dados filtrados atualmente no dashboard &nbsp;&middot;&nbsp; "
        f"Periodo: {str(date_from)} a {str(date_to)}</div>",
        unsafe_allow_html=True,
    )

    # ── Identificacao explicita de clientes analisados ────────────────────────
    try:
        _ctx_parsed = _json.loads(context_json)
    except Exception:
        _ctx_parsed = {}

    _clientes_filtrados = sorted(st.session_state.get("xf_cliente", set()))
    if _clientes_filtrados:
        _cli_str = ", ".join(str(c) for c in _clientes_filtrados)
        _n_cli = len(_clientes_filtrados)
        st.markdown(
            f"<div style='background:{BG_CARD};border:1px solid {BORDER};border-left:3px solid {C_CYAN};"
            f"border-radius:8px;padding:10px 14px;margin-bottom:12px'>"
            f"<div style='font-size:.68rem;color:{TXT_S};font-weight:700;"
            f"letter-spacing:.06em;margin-bottom:3px'>CLIENTES ANALISADOS ({_n_cli})</div>"
            f"<div style='font-size:.82rem;color:{TXT_H}'>{_cli_str}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    elif analysis_type in ("cliente", "volume") and "clientes" in _ctx_parsed:
        _all_cli = [c.get("cliente", "") for c in _ctx_parsed["clientes"]]
        if _all_cli:
            _cli_str = ", ".join(str(c) for c in _all_cli)
            st.markdown(
                f"<div style='background:{BG_CARD};border:1px solid {BORDER};border-left:3px solid {C_TEAL};"
                f"border-radius:8px;padding:10px 14px;margin-bottom:12px'>"
                f"<div style='font-size:.68rem;color:{TXT_S};font-weight:700;"
                f"letter-spacing:.06em;margin-bottom:3px'>CLIENTES ANALISADOS ({len(_all_cli)}) — Todos do filtro atual</div>"
                f"<div style='font-size:.82rem;color:{TXT_H}'>{_cli_str}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Score pre-calculado + explicacao do indice ────────────────────────────
    _pre_scores = []
    _scores_for_pdf = []
    if analysis_type == "cliente" and "clientes" in _ctx_parsed:
        for _cd in _ctx_parsed["clientes"]:
            _sc  = _cd.get("score_viabilidade", 0)
            _lbl, _col = _score_label(_sc)
            _cls = _cd.get("classificacao_cliente", "")
            _pre_scores.append((_cd["cliente"], _sc, _lbl, _col, _cls))
            _scores_for_pdf.append((_cd["cliente"], _sc, _lbl, _col))

    if _pre_scores:
        # Mostra scores em colunas (max 4 por linha)
        _max_cols = min(len(_pre_scores), 4)
        for _chunk_start in range(0, len(_pre_scores), _max_cols):
            _chunk = _pre_scores[_chunk_start:_chunk_start + _max_cols]
            _scols = st.columns(len(_chunk))
            for _ci, (_cn, _sc, _lbl, _col, _cls) in enumerate(_chunk):
                with _scols[_ci]:
                    _bar_w = int(_sc)
                    st.markdown(
                        f"<div style='background:{BG_CARD};border:1px solid {BORDER};"
                        f"border-top:3px solid {_col};border-radius:10px;padding:12px 14px;"
                        f"margin-bottom:10px'>"
                        f"<div style='font-size:.65rem;color:{TXT_S};font-weight:700;"
                        f"letter-spacing:.07em;margin-bottom:4px'>SCORE VIABILIDADE</div>"
                        f"<div style='font-size:1.9rem;font-weight:800;color:{_col};"
                        f"font-family:Montserrat,sans-serif;line-height:1'>{_sc}"
                        f"<span style='font-size:.9rem'>/100</span></div>"
                        f"<div style='background:{BORDER};border-radius:4px;height:5px;"
                        f"margin:7px 0 5px'>"
                        f"<div style='background:{_col};width:{_bar_w}%;height:5px;"
                        f"border-radius:4px'></div></div>"
                        f"<div style='font-size:.72rem;font-weight:700;color:{_col}'>{_lbl}</div>"
                        f"<div style='font-size:.68rem;color:{TXT_S};margin-top:3px'>{_cls}</div>"
                        f"<div style='font-size:.70rem;color:{TXT_S};margin-top:2px;"
                        f"font-style:italic'>{_cn}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        # Explicacao de como o score e gerado
        st.markdown(
            f"<details style='margin-bottom:12px'>"
            f"<summary style='font-size:.72rem;color:{C_CYAN};cursor:pointer;font-weight:600'>"
            f"Como o Score de Viabilidade e calculado?</summary>"
            f"<div style='font-size:.70rem;color:{TXT_S};padding:8px 12px;line-height:1.6;"
            f"background:{BG_CARD};border:1px solid {BORDER};border-radius:8px;margin-top:6px'>"
            f"O <b style='color:{TXT_H}'>Score de Viabilidade</b> e um indice de 0 a 100 calculado "
            f"automaticamente pelo sistema com base em <b>8 fatores ponderados</b>:<br><br>"
            f"<b style='color:{C_GREEN}'>Fatores positivos:</b><br>"
            f"&bull; <b>Frequencia de compra (25%)</b> — quanto menor o intervalo entre pedidos, maior a pontuacao<br>"
            f"&bull; <b>Recorrencia (20%)</b> — percentual de semanas em que o cliente esteve ativo<br>"
            f"&bull; <b>Volume total (15%)</b> — volume em kg comparado com a media da base<br>"
            f"&bull; <b>Volume medio por pedido (10%)</b> — consistencia no tamanho das compras<br>"
            f"&bull; <b>Tendencia (10%)</b> — se o volume esta crescendo, estavel ou caindo<br><br>"
            f"<b style='color:{C_RED}'>Penalidades (reduzem o score):</b><br>"
            f"&bull; <b>Concentracao (-10%)</b> — se mais de 50% do volume esta em um unico pedido<br>"
            f"&bull; <b>Primeiro pedido inflado (-10%)</b> — se o primeiro pedido foi 2x maior que os demais (possivel formacao de estoque)<br>"
            f"&bull; <b>Sazonalidade (-10%)</b> — se o coeficiente de variacao ultrapassa 60%, indicando compras muito irregulares<br><br>"
            f"<b style='color:{TXT_H}'>Classificacao:</b> "
            f"<span style='color:{C_GREEN}'>80-100 = Estrategico</span> · "
            f"<span style='color:{C_CYAN}'>60-79 = Relevante</span> · "
            f"<span style='color:{C_AMBER}'>40-59 = Oportunista</span> · "
            f"<span style='color:{C_RED}'>0-39 = Baixo valor</span>"
            f"</div></details>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<hr style='border-color:{BORDER};margin:6px 0 14px'>",
            unsafe_allow_html=True,
        )

    # ── Cache e reanálise ─────────────────────────────────────────────────────
    _ck = _cache_key(chart_name)
    _cached = st.session_state["_ai_analysis_cache"].get(_ck)

    # Botao de reanálise
    _col_reanalyse, _col_spacer = st.columns([2, 8])
    _force_reanalysis = False
    with _col_reanalyse:
        if _cached:
            if st.button("🔄 Reanalisar", key=f"reanalyse_{_ck}", help="Gerar nova analise descartando o cache"):
                _force_reanalysis = True
                _cached = None

    # ── Gerar ou reutilizar analise ───────────────────────────────────────────
    _analysis = None

    if _cached and not _force_reanalysis:
        _analysis = _cached
        st.markdown(_analysis)
        st.markdown(
            f"<div style='font-size:.65rem;color:{TXT_S};font-style:italic;margin-bottom:8px'>"
            f"Analise carregada do cache. Clique em 'Reanalisar' para gerar uma nova.</div>",
            unsafe_allow_html=True,
        )
    else:
        _score_val = _pre_scores[0][1] if _pre_scores else 0
        _sys_prompt = (
            _SYSTEM_COMMERCIAL.replace("{score}", str(_score_val))
            if analysis_type == "cliente" else _SYSTEM_GENERAL
        )

        # Adiciona instrucoes especificas do tipo de grafico
        _chart_instr = _CHART_SPECIFIC_INSTRUCTIONS.get(analysis_type, "")
        if _chart_instr:
            _sys_prompt = _chart_instr + "\n\n" + _sys_prompt

        _type_labels = {
            "cliente":  "diagnostico de viabilidade comercial",
            "semanal":  "analise de tendencia e sazonalidade semanal",
            "produto":  "analise de concentracao e desempenho de produtos",
            "deposito": "analise de dependencia e distribuicao por deposito",
            "pedido":   "analise de padrao e consistencia de pedidos",
            "volume":   "analise de volume e benchmark por cliente",
        }
        _instruct = _type_labels.get(analysis_type, "analise comercial")
        _user_msg = (
            f"Execute um {_instruct} completo para o grafico '{chart_name}'.\n\n"
            f"ATENCAO: Todos os calculos estatisticos abaixo ja foram computados pelo sistema. "
            f"Voce deve APENAS interpretar e comentar os valores. NAO recalcule nada.\n\n"
            f"Dados em JSON estruturado:\n{context_json}"
        )

        with st.spinner("Processando inteligencia comercial..."):
            try:
                _resp = _oa.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": _sys_prompt},
                        {"role": "user",   "content": _user_msg},
                    ],
                    max_tokens=2500,
                    temperature=0.15,
                )
                _analysis = _resp.choices[0].message.content
                # Salva no cache (unico por grafico + filtros)
                st.session_state["_ai_analysis_cache"][_ck] = _analysis
                st.markdown(_analysis)
            except Exception as _e:
                st.error(f"Erro ao consultar a IA: {_e}")

    # ── Botao de exportar PDF ─────────────────────────────────────────────────
    if _analysis:
        st.markdown(f"<hr style='border-color:{BORDER};margin:12px 0'>", unsafe_allow_html=True)
        _col_pdf, _ = st.columns([2.5, 7.5])
        with _col_pdf:
            try:
                _pdf_path = _generate_pdf(_analysis, chart_name, _scores_for_pdf or None)
                with open(_pdf_path, "rb") as _pf:
                    st.download_button(
                        label="📥 Exportar PDF",
                        data=_pf.read(),
                        file_name=f"analise_{chart_name.replace(' ', '_')[:40]}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{_ck}",
                        help="Baixar esta analise como PDF com o mesmo padrao visual",
                    )
            except Exception as _pdf_err:
                st.warning(f"Erro ao gerar PDF: {_pdf_err}")

    # ── Disclaimer da IA ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:.68rem;color:{TXT_S};margin-top:18px;padding-top:10px;"
        f"border-top:1px solid {BORDER}'>"
        f"GPT-4o-mini &nbsp;&middot;&nbsp; Analise sob demanda &nbsp;&middot;&nbsp; "
        f"Somente ao clicar no botao</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.25);"
        f"border-radius:8px;padding:10px 14px;margin-top:10px'>"
        f"<div style='font-size:.70rem;color:{C_AMBER};font-weight:600;margin-bottom:3px'>"
        f"⚠ Aviso Importante</div>"
        f"<div style='font-size:.68rem;color:{TXT_S};line-height:1.5'>"
        f"Toda Inteligencia Artificial pode cometer erros. Os dados e conclusoes apresentados "
        f"devem ser revisados criticamente antes de serem utilizados para tomada de decisao. "
        f"Valide as informacoes com os dados originais sempre que possivel.</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Botao icone de IA ─────────────────────────────────────────────────────────

def _ia_button(chart_name: str, context_fn, key: str, analysis_type: str = "geral"):
    # Renderiza botao estilizado de IA com texto descritivo.
    # context_fn: callable sem args que retorna o JSON de contexto.
    # So e executado ao clicar - nenhum token gasto automaticamente.
    st.markdown(
        '<span class="ia-btn-marker" style="display:none"></span>',
        unsafe_allow_html=True,
    )
    _c, _ = st.columns([2.2, 7.8])
    with _c:
        if st.button("🤖  Analisar com IA", key=key, help="Gerar analise de inteligencia comercial com IA para este grafico", use_container_width=True):
            _show_ai_analysis(chart_name, context_fn(), analysis_type)



(
    tab_visao, tab_dep, tab_prod,
    tab_cli, tab_vol, tab_dados
) = st.tabs([
    "📈 Visão Geral",
    "🏭 Depósitos",
    "🏷️ Produtos",
    "👥 Clientes",
    "📦 Volume & NF",
    "📄 Dados",
])

with tab_visao:
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2 — EVOLUÇÃO SEMANAL CONSOLIDADA
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("📈", "Evolução Semanal Consolidada")

    weekly = (
        df.groupby(["semana_sort","semana_label","date_range"])
        .agg(
            kilos    =("kilos",        "sum"),
            caixas   =("caixas",       "sum"),
            unidades =("unidades",     "sum"),
            n_clientes=("nome_cliente","nunique"),
            n_produtos=("codigo_produto","nunique"),
        )
        .reset_index().sort_values("semana_sort")
    )

    # garante todas as semanas do intervalo selecionado (incluindo vazias = zero)
    weekly = _reindex_to_all_weeks(weekly)

    weekly["delta_kg"]  = weekly["kilos"].diff().fillna(0)
    weekly["delta_pct"] = (weekly["kilos"].pct_change().fillna(0) * 100).round(2)
    # Para o traço de linha: substitui ±inf por NaN (semanas zeradas geram inf no pct_change)
    # connectgaps=True vai ligar os pontos válidos, ignorando os NaN
    weekly["delta_pct_line"] = weekly["delta_pct"].replace([np.inf, -np.inf], np.nan)
    weekly["bar_color"] = weekly["delta_kg"].apply(lambda v: C_CYAN if v >= 0 else C_RED)

    cd_sem = (
        weekly[["date_range","caixas","unidades","delta_kg","delta_pct","n_clientes","n_produtos"]]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .values.tolist()
    )
    hover_sem = (
        "<b style='font-size:13px'>%{x}</b><br>"
        f"<span style='color:{TXT_S}'>📅 %{{customdata[0]}}</span><br>"
        f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{y:,.1f}} kg</b><br>"
        f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[1]:,.1f}} cx</b><br>"
        f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[2]:,.0f}} un</b><br>"
        f"<span style='color:{C_GREEN}'>▲ Δ Kg</span>  %{{customdata[3]:+,.1f}} kg "
        f"(<b>%{{customdata[4]:+.1f}}%</b>)<br>"
        f"<span style='color:{C_ORANGE}'>👥 Clientes</span> %{{customdata[5]:.0f}}  "
        f"· <span style='color:{C_TEAL}'>🏷️ Produtos</span> %{{customdata[6]:.0f}}"
        "<extra></extra>"
    )

    # ── Dois subplots empilhados: linha Δ% em cima, barras de kg embaixo ──────────
    # shared_xaxes=True garante sincronismo de zoom/pan e nunca se tocam
    _cat_arr = [lbl_map[w] for w in ALL_RANGE_SORTS if w in lbl_map]

    fig_sem = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.28, 0.72],   # 28 % linha · 72 % barras
        vertical_spacing=0.06,      # gap fixo entre os dois painéis
    )
    fig_sem.data = []  # 🔥 limpa qualquer trace fantasma

    # ── Row 2 (baixo): barras de kilos ───────────────────────────────────────────
    fig_sem.add_trace(go.Bar(
        x=weekly["semana_label"], y=weekly["kilos"],
        name="Kilos",
        marker=dict(color=weekly["bar_color"], opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
        customdata=cd_sem, hovertemplate=hover_sem,
    ), row=2, col=1)

    # Labels com background nas barras de kg
    for _, row in weekly.iterrows():
        if row["kilos"] == 0:
            continue
        bar_c = row["bar_color"]
        dark_c = _darken_hex(bar_c, factor=0.40)
        fig_sem.add_annotation(
            x=row["semana_label"], y=row["kilos"],
            xref="x2", yref="y2",
            text=f"<b>{fmt_peso(row['kilos'])}</b>",
            showarrow=False,
            yanchor="bottom", xanchor="center",
            textangle=-90,
            font=dict(size=9, color=TXT_H, family="Montserrat, sans-serif"),
            bgcolor=_hex_to_rgba(dark_c, alpha=0.82),
            borderpad=2,
        )

    # ── Tendência linear (OLS) no painel de barras ───────────────────────────────
    # Usa TODAS as semanas do intervalo (incluindo as zeradas) para que a inclinação
    # da reta reflita fielmente o ângulo visual das barras no eixo Y.
    # x posicional (0, 1, 2…) → espaçamento uniforme, igual ao eixo de categorias.
    _all_x  = np.arange(len(weekly), dtype=float)
    _all_y  = weekly["kilos"].values.astype(float)

    if len(_all_x) >= 2:
        _slope, _intercept = np.polyfit(_all_x, _all_y, 1)
        _trend_y = _slope * _all_x + _intercept

        # R² sobre todos os pontos (incluindo zeros)
        _y_pred  = _slope * _all_x + _intercept
        _ss_res  = np.sum((_all_y - _y_pred) ** 2)
        _ss_tot  = np.sum((_all_y - _all_y.mean()) ** 2)
        _r2      = 1.0 - _ss_res / _ss_tot if _ss_tot > 0 else 0.0

        # ── Interpretação amigável ────────────────────────────────────────────────
        # Slope como % da média das semanas com faturamento (contexto relativo)
        _mean_active = float(_all_y[_all_y > 0].mean()) if (_all_y > 0).any() else 1.0
        _slope_pct   = (_slope / _mean_active * 100) if _mean_active > 0 else 0.0

        # Força da tendência baseada no R²
        if _r2 < 0.10:
            _r2_label = "sem padrão definido"
            _r2_tip   = "Os dados estão muito dispersos — a reta não representa bem o comportamento real."
        elif _r2 < 0.30:
            _r2_label = "padrão fraco"
            _r2_tip   = "Existe uma leve tendência, mas com muita variação em torno da reta."
        elif _r2 < 0.60:
            _r2_label = "padrão moderado"
            _r2_tip   = "A tendência é razoavelmente consistente, com variações pontuais."
        else:
            _r2_label = "padrão consistente"
            _r2_tip   = "A tendência é clara e confiável — os dados seguem bem a direção da reta."

        # Direção e intensidade do slope
        if abs(_slope_pct) < 2:
            _direction = "Estável"
            _dir_emoji = "➡️"
            _dir_tip   = f"Volume praticamente constante semana a semana ({fmt_br(_slope, 1)} kg/sem)."
        elif _slope > 0:
            if _slope_pct < 6:
                _direction = "Leve crescimento"
                _dir_emoji = "📈"
            else:
                _direction = "Em crescimento"
                _dir_emoji = "📈"
            _dir_tip = f"Ganho médio de {fmt_br(abs(_slope), 1)} kg por semana ({_slope_pct:+.1f}% da média ativa)."
        else:
            if abs(_slope_pct) < 6:
                _direction = "Leve queda"
                _dir_emoji = "📉"
            else:
                _direction = "Em queda"
                _dir_emoji = "📉"
            _dir_tip = f"Perda média de {fmt_br(abs(_slope), 1)} kg por semana ({_slope_pct:+.1f}% da média ativa)."

        _trend_color = C_GREEN if _slope >= 0 else C_RED

        # customdata: [valor_real_barra, desvio_reta_vs_real, trend_semana_anterior]
        _prev_trend = np.concatenate([[np.nan], _trend_y[:-1]])
        _cd_trend   = np.column_stack([
            _all_y,                        # [0] valor real da barra
            _all_y - _trend_y,             # [1] desvio real vs reta
            _prev_trend,                   # [2] valor da reta na semana anterior
        ])

        fig_sem.add_trace(go.Scatter(
            x=weekly["semana_label"], y=_trend_y,
            mode="lines",
            name=f"{_dir_emoji} Tendência: {_direction}",
            line=dict(color=_trend_color, width=2, dash="dot"),
            customdata=_cd_trend,
            hovertemplate=(
                "<b>%{x}  —  Linha de Tendência</b><br>"
                f"<b>{_dir_emoji} {_direction}</b>  ·  {_r2_label}<br>"
                "─────────────────────────────────<br>"
                f"<span style='color:{TXT_S}'>Reta nesta semana</span>  <b>%{{y:,.1f}} kg</b><br>"
                f"<span style='color:{TXT_S}'>Real desta semana</span>  <b>%{{customdata[0]:,.1f}} kg</b>  "
                "<i>(desvio: %{customdata[1]:+,.1f} kg)</i><br>"
                f"<span style='color:{TXT_S}'>Reta semana anterior</span>  <b>%{{customdata[2]:,.1f}} kg</b>  "
                f"<i>(+{_slope:,.1f} kg/sem = projeção da reta)</i><br>"
                "─────────────────────────────────<br>"
                f"<span style='color:{TXT_S}' style='font-size:9px'>A reta é ajustada sobre todo o período — "
                f"seu valor aqui não parte do real da semana anterior.</span><br>"
                f"{_dir_tip}<br>"
                f"<span style='color:{TXT_S}'>{_r2_tip}</span>"
                "<extra></extra>"
            ),
        ), row=2, col=1)

        # Rótulo final com interpretação resumida
        _annot_line1 = f"<b>{_dir_emoji} {_direction}</b>"
        _annot_line2 = f"{fmt_br(_slope, 1)} kg/sem  ·  {_r2_label}"
        fig_sem.add_annotation(
            x=weekly["semana_label"].iloc[-1],
            y=float(_trend_y[-1]),
            xref="x2", yref="y2",
            text=f"{_annot_line1}<br><span style='font-size:8px'>{_annot_line2}</span>",
            showarrow=True,
            arrowhead=2, arrowcolor=_trend_color, arrowwidth=1.5,
            ax=0, ay=-38,
            font=dict(size=9, color=_trend_color, family="Montserrat, sans-serif"),
            bgcolor=_hex_to_rgba(_darken_hex(BG_SIDEBAR, 0.5), alpha=0.92),
            bordercolor=_trend_color,
            borderwidth=1,
            borderpad=4,
        )

    # ── Row 1 (cima): linha Δ% ───────────────────────────────────────────────────
    fig_sem.add_trace(go.Scatter(
        x=weekly["semana_label"], y=weekly["delta_pct_line"],
        mode="lines+markers", name="Δ%",
        line=dict(color=C_AMBER, width=2),
        marker=dict(size=6, color=C_AMBER, line=dict(color=BG_PLOT, width=1)),
        connectgaps=True,
        hovertemplate="<b>%{x}</b><br>Variação: <b>%{y:+.1f}%</b><extra></extra>",
    ), row=1, col=1)

    # Labels Δ% com background
    for _, row in weekly.iterrows():
        if row["kilos"] == 0 or not np.isfinite(row["delta_pct"]):
            continue
        fig_sem.add_annotation(
            x=row["semana_label"], y=row["delta_pct_line"],
            xref="x", yref="y",
            text=f"<b>{row['delta_pct']:+.1f}%</b>",
            showarrow=False,
            yanchor="bottom", xanchor="center",
            font=dict(size=9, color=C_AMBER, family="Inter, sans-serif"),
            bgcolor=_hex_to_rgba(_darken_hex(BG_SIDEBAR, 0.5), alpha=0.88),
            borderpad=2,
        )

    # ── Layout global ─────────────────────────────────────────────────────────────
    fig_layout(fig_sem,
        height=520, hovermode="x unified",
        legend=dict(orientation="h", y=1.08, x=0),
        margin=dict(t=35, b=10, l=5, r=60),
    )

    # x-axis: row 1 (topo) sem rótulos — row 2 (baixo) com rótulos das semanas
    fig_sem.update_layout(
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickcolor=TXT_S, linecolor=BORDER,
            type="category", categoryorder="array",
            categoryarray=_cat_arr,
            showticklabels=False,   # oculta no painel superior
        ),
        xaxis2=dict(
            showgrid=False, zeroline=False,
            tickcolor=TXT_S, linecolor=BORDER,
            tickfont=dict(color=TXT_S, size=9),
            type="category", categoryorder="array",
            categoryarray=_cat_arr,
        ),
        # y-axis row 1: Δ%
        yaxis=dict(
            title_text="Variação %",
            ticksuffix="%", showgrid=True, gridcolor=GRID,
            zeroline=True, zerolinecolor=TXT_S, zerolinewidth=1,
            tickfont=dict(color=C_AMBER), tickcolor=TXT_S, linecolor=BORDER,
            title_font=dict(color=C_AMBER, size=11),
        ),
        # y-axis row 2: Kilos
        yaxis2=dict(
            title_text="Kilos (kg)",
            ticksuffix=" kg", showgrid=True, gridcolor=GRID,
            zeroline=False,
            tickfont=dict(color=TXT_S), tickcolor=TXT_S, linecolor=BORDER,
            title_font=dict(color=TXT_S, size=11),
        ),
    )
    ev_sem = st.plotly_chart(fig_sem, use_container_width=True, on_select="rerun", key="chart_sem")

    def _ctx_sem():
        return build_ai_context("semanal", "Evolucao Semanal Consolidada",
                                df, df_base, df_raw)
    _ia_button("Evolucao Semanal Consolidada",
               _ctx_sem, "ia_btn_sem", analysis_type="semanal")

    if _handle_event(ev_sem, "xf_semana", "x"):
        st.rerun()



with tab_dep:
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 1 — ANÁLISE SEMANAL POR DEPÓSITO
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("📅", "Análise Semanal por Depósito")

    df_sec1 = df_base.copy()

    weekly_dep = (
        df_sec1.groupby(["semana_sort","semana_label","date_range","deposito"])
        .agg(
            kilos    =("kilos",       "sum"),
            caixas   =("caixas",      "sum"),
            unidades =("unidades",    "sum"),
            n_clientes=("nome_cliente","nunique"),
        )
        .reset_index().sort_values("semana_sort")
    )

    # garante todos os depósitos em todas as semanas do intervalo (zeros para semanas vazias)
    _all_deps = sorted(df_raw["deposito"].dropna().unique())
    weekly_dep = _reindex_to_all_weeks(weekly_dep, extra_keys=["deposito"])
    weekly_dep = weekly_dep[weekly_dep["deposito"].isin(_all_deps)]

    col_mode, _ = st.columns([3, 7])
    with col_mode:
        modo_sec1 = st.radio(
            "Visualização",
            ["Por Depósito", "Consolidado"],
            horizontal=True,
            key="modo_sec1",
        )

    tab_kg, tab_cx, tab_un = st.tabs(["⚖️ Kilos por Semana", "📦 Caixas por Semana", "🔢 Unidades por Semana"])



    def chart_semanal_dep(metric, y_label, fmt, title_label):
        all_labels = [lbl_map[w] for w in ALL_RANGE_SORTS if w in lbl_map]
        fig = go.Figure()

        # ── coleta valores de média para linha ────────────────────────────────────
        mean_vals = []

        if modo_sec1 == "Por Depósito":
            for dep in sorted(weekly_dep["deposito"].unique()):
                sub = weekly_dep[weekly_dep["deposito"] == dep].sort_values("semana_sort")
                cd = sub.apply(lambda r: [
                    r["date_range"],
                    r["n_clientes"],
                    fmt_peso(r["kilos"]),
                    fmt_br(r["caixas"], 1) + " cx",
                    fmt_br(r["unidades"], 0) + " un"
                ], axis=1).tolist()
                hover = (
                    f"<b>%{{x}}</b>  <span style='color:{TXT_S}'>%{{customdata[0]}}</span><br>"
                    f"<b>{dep}</b><br>"
                    f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[2]}}</b><br>"
                    f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[3]}}</b><br>"
                    f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[4]}}</b><br>"
                    f"<span style='color:{C_ORANGE}'>👥 Clientes</span>  %{{customdata[1]:.0f}}"
                    "<extra></extra>"
                )
                bar_color = dep_colors.get(dep, C_CYAN)
                dark_color = _darken_hex(bar_color, factor=0.45)
                fig.add_trace(go.Bar(
                    x=sub["semana_label"], y=sub[metric],
                    name=dep,
                    marker=dict(color=bar_color, opacity=0.85,
                                line=dict(color=BG_PLOT, width=0.5)),
                    customdata=cd, hovertemplate=hover,
                ))
                # labels vertical above each bar
                for x_val, y_val, txt in zip(sub["semana_label"].tolist(),
                                              sub[metric].tolist(),
                                              [fmt(v) for v in sub[metric]]):
                    if y_val == 0 or (isinstance(y_val, float) and np.isnan(y_val)):
                        continue
                    fig.add_annotation(
                        x=x_val, y=y_val,
                        text=f"<b>{txt}</b>",
                        showarrow=False,
                        yanchor="bottom",
                        xanchor="center",
                        textangle=-90,
                        font=dict(size=9, color=TXT_H, family="Montserrat, sans-serif"),
                        bgcolor=_hex_to_rgba(dark_color, alpha=0.75),
                        borderpad=2,
                    )
                mean_vals.extend(sub[sub[metric] > 0][metric].tolist())
            barmode = "group"
        else:
            # Consolidado: soma todos os depósitos por semana, reindexado a todas as semanas
            weekly_cons_raw = (
                df_sec1.groupby(["semana_sort"])
                .agg(
                    kilos     =("kilos",        "sum"),
                    caixas    =("caixas",       "sum"),
                    unidades  =("unidades",     "sum"),
                    n_clientes=("nome_cliente", "nunique"),
                )
                .reset_index()
            )
            weekly_cons_raw = _reindex_to_all_weeks(weekly_cons_raw)
            cd = weekly_cons_raw.apply(lambda r: [
                r["date_range"],
                r["n_clientes"],
                fmt_peso(r["kilos"]),
                fmt_br(r["caixas"], 1) + " cx",
                fmt_br(r["unidades"], 0) + " un"
            ], axis=1).tolist()
            hover = (
                f"<b>%{{x}}</b>  <span style='color:{TXT_S}'>%{{customdata[0]}}</span><br>"
                f"<b>Total</b><br>"
                f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[2]}}</b><br>"
                f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[3]}}</b><br>"
                f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[4]}}</b><br>"
                f"<span style='color:{C_ORANGE}'>👥 Clientes</span>  %{{customdata[1]:.0f}}"
                "<extra></extra>"
            )
            dark_cons = _darken_hex(C_CYAN, factor=0.45)
            fig.add_trace(go.Bar(
                x=weekly_cons_raw["semana_label"], y=weekly_cons_raw[metric],
                name="Total",
                marker=dict(color=C_CYAN, opacity=0.85,
                            line=dict(color=BG_PLOT, width=0.5)),
                customdata=cd, hovertemplate=hover,
            ))
            for x_val, y_val, txt in zip(weekly_cons_raw["semana_label"].tolist(),
                                          weekly_cons_raw[metric].tolist(),
                                          [fmt(v) for v in weekly_cons_raw[metric]]):
                if y_val == 0 or (isinstance(y_val, float) and np.isnan(y_val)):
                    continue
                fig.add_annotation(
                    x=x_val, y=y_val,
                    text=f"<b>{txt}</b>",
                    showarrow=False,
                    yanchor="bottom",
                    xanchor="center",
                    textangle=-90,
                    font=dict(size=9, color=TXT_H, family="Montserrat, sans-serif"),
                    bgcolor=_hex_to_rgba(dark_cons, alpha=0.75),
                    borderpad=2,
                )
            mean_vals = weekly_cons_raw[weekly_cons_raw[metric] > 0][metric].tolist()
            barmode = "group"

        # ── Linha de média ────────────────────────────────────────────────────────
        if mean_vals:
            mean_val = float(np.mean(mean_vals))
            fig.add_hline(
                y=mean_val,
                line_dash="dot",
                line_color=C_ORANGE,
                line_width=2,
                annotation_text=f"Média: {fmt(mean_val)}",
                annotation_position="right",
                annotation_font=dict(color=C_ORANGE, size=10),
            )

        fig_layout(fig,
            height=440, barmode=barmode,
            title=dict(text=title_label, font=dict(size=13, color=TXT_H,
                       family="Montserrat, sans-serif")),
            legend=dict(orientation="h", y=1.08, x=0),
            margin=dict(t=50, b=10, l=5, r=80),
            xaxis=dict(
                type="category", categoryorder="array", categoryarray=all_labels,
                showgrid=False, tickfont=dict(color=TXT_S, size=9),
            ),
            yaxis=dict(showgrid=True, gridcolor=GRID, title_text=y_label,
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        return fig


    def chart_caixas_sku():
        """Caixas por semana discriminadas por SKU (stacked, cores e hachuras alternadas)."""
        all_labels = [lbl_map[w] for w in ALL_RANGE_SORTS if w in lbl_map]

        # Agrega por semana × produto
        sku_wk_raw = (
            df_sec1.groupby(["semana_sort","codigo_produto","prod_nome"])
            .agg(caixas=("caixas","sum"))
            .reset_index()
        )
        _all_skus = sorted(df_raw["codigo_produto"].dropna().unique())
        # mantém apenas SKUs presentes no filtro atual
        _all_skus = [s for s in _all_skus if s in df_sec1["codigo_produto"].values]
        if not _all_skus:
            return go.Figure()

        sku_wk = _reindex_to_all_weeks(sku_wk_raw, extra_keys=["codigo_produto"])
        sku_wk = sku_wk[sku_wk["codigo_produto"].isin(_all_skus)]

        # recupera prod_nome para cada SKU
        _sku_nome = sku_wk_raw[["codigo_produto","prod_nome"]].drop_duplicates()
        sku_wk = sku_wk.drop(columns=["prod_nome"], errors="ignore").merge(
            _sku_nome, on="codigo_produto", how="left"
        )
        sku_wk["prod_nome"] = sku_wk["prod_nome"].fillna(sku_wk["codigo_produto"].astype(str))
        sku_wk = sku_wk.sort_values(["semana_sort","codigo_produto"])

        HATCH_SHAPES = ["", "/", "\\", "x", "-", "|", "+", "."]
        fig = go.Figure()
        for i, sku in enumerate(_all_skus):
            sub   = sku_wk[sku_wk["codigo_produto"] == sku]
            color = sku_color(str(sku))
            hatch = HATCH_SHAPES[i % len(HATCH_SHAPES)]
            nome  = sub["prod_nome"].iloc[0] if not sub["prod_nome"].isna().all() else str(sku)
            fig.add_trace(go.Bar(
                x=sub["semana_label"],
                y=sub["caixas"],
                name=str(nome),
                marker=dict(
                    color=color,
                    opacity=0.85,
                    line=dict(color=BG_PLOT, width=0.5),
                    pattern=dict(shape=hatch, fgcolor=_darken_hex(color, 0.4),
                                 size=6, solidity=0.4),
                ),
                hovertemplate=(
                    f"<b>%{{x}}</b><br>"
                    f"<b>{nome}</b><br>"
                    f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{y:,.2f}} cx</b>"
                    "<extra></extra>"
                ),
            ))

        # Linha de média (total consolidado por semana)
        total_by_wk = sku_wk.groupby("semana_sort")["caixas"].sum()
        nz_vals     = total_by_wk[total_by_wk > 0]
        if not nz_vals.empty:
            mean_cx = float(nz_vals.mean())
            fig.add_hline(
                y=mean_cx,
                line_dash="dot",
                line_color=C_ORANGE,
                line_width=2,
                annotation_text=f"Média: {fmt_br(mean_cx, 2)} cx",
                annotation_position="right",
                annotation_font=dict(color=C_ORANGE, size=10),
            )

        fig_layout(fig,
            height=440, barmode="stack",
            title=dict(text="📦 Caixas por Semana por SKU",
                       font=dict(size=13, color=TXT_H, family="Montserrat, sans-serif")),
            legend=dict(orientation="h", y=1.08, x=0),
            margin=dict(t=50, b=10, l=5, r=80),
            xaxis=dict(
                type="category", categoryorder="array", categoryarray=all_labels,
                showgrid=False, tickfont=dict(color=TXT_S, size=9),
            ),
            yaxis=dict(showgrid=True, gridcolor=GRID, title_text="Caixas (cx)",
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        return fig


    with tab_kg:
        ev_s1 = st.plotly_chart(
            chart_semanal_dep("kilos",    "Kilos (kg)",    fmt_peso,
                              "⚖️ Kilos por Semana"),
            use_container_width=True, key="chart_s1_kg",
        )
        def _ctx_dep_kg():
            return build_ai_context("deposito", "Kilos por Semana por Deposito",
                                    df, df_base, df_raw)
        _ia_button("Kilos por Semana por Deposito",
                   _ctx_dep_kg, "ia_btn_dep_kg", analysis_type="deposito")
    with tab_cx:
        st.plotly_chart(
            chart_caixas_sku(),
            use_container_width=True, key="chart_s1_cx",
        )
        def _ctx_dep_cx():
            return build_ai_context("deposito", "Caixas por Semana por Deposito",
                                    df, df_base, df_raw,
                                    extra={"metrica": "caixas"})
        _ia_button("Caixas por Semana por Deposito",
                   _ctx_dep_cx, "ia_btn_dep_cx", analysis_type="deposito")
    with tab_un:
        st.plotly_chart(
            chart_semanal_dep("unidades", "Unidades (un)", lambda v: fmt_br(v, 0) + " un",
                              "🔢 Unidades por Semana"),
            use_container_width=True, key="chart_s1_un",
        )
        def _ctx_dep_un():
            return build_ai_context("deposito", "Unidades por Semana por Deposito",
                                    df, df_base, df_raw,
                                    extra={"metrica": "unidades"})
        _ia_button("Unidades por Semana por Deposito",
                   _ctx_dep_un, "ia_btn_dep_un", analysis_type="deposito")



with tab_prod:
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3 — RANKINGS POR PRODUTO E CLIENTE
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("🏷️", "Rankings por Produto e por Cliente")

    metrica_rank = st.radio(
        "Ordenar por",
        ["kilos","caixas","unidades"],
        format_func=lambda x: {"kilos":"⚖️ Kilos","caixas":"📦 Caixas","unidades":"🔢 Unidades"}[x],
        horizontal=True,
        key="metrica_rank",
    )
    met_fmt_rank = {
        "kilos":    fmt_peso,
        "caixas":   lambda v: fmt_br(v, 1) + " cx",
        "unidades": lambda v: fmt_br(v, 0) + " un",
    }[metrica_rank]

    col_p, col_c = st.columns(2)

    with col_p:
        prod_stats = (
            df_base.groupby(["prod_nome","codigo_produto"])
            .agg(
                kilos    =("kilos",        "sum"),
                caixas   =("caixas",       "sum"),
                unidades =("unidades",     "sum"),
                n_clientes=("nome_cliente","nunique"),
            )
            .reset_index().sort_values(metrica_rank, ascending=True)
        )
        cmap = prod_color_map(prod_stats["prod_nome"].unique())
        prod_stats["color"] = prod_stats["prod_nome"].apply(
            lambda x: C_AMBER if x in st.session_state.xf_produto else cmap.get(x, C_CYAN)
        )
        cd_p = prod_stats[["kilos","caixas","unidades","n_clientes","codigo_produto"]].fillna(0).values.tolist()
        hover_p = (
            "<b>%{y}</b><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[0]:,.1f}} kg</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[1]:,.1f}} cx</b><br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[2]:,.0f}} un</b><br>"
            f"<span style='color:{C_ORANGE}'>👥 Clientes</span> %{{customdata[3]:.0f}}<br>"
            f"<span style='color:{TXT_S}'>Código</span>  %{{customdata[4]}}"
            "<extra></extra>"
        )
        fig_prod = go.Figure(go.Bar(
            name="Algum Nome",
            x=prod_stats[metrica_rank], y=prod_stats["prod_nome"],
            orientation="h",
            marker=dict(color=prod_stats["color"], line=dict(color=BG_PLOT, width=0.5)),
            text=prod_stats[metrica_rank].apply(met_fmt_rank), textposition="outside",
            textfont=dict(size=10, color=TXT_H),
            customdata=cd_p, hovertemplate=hover_p,
        ))
        fig_layout(fig_prod,
            title=dict(text="Por Produto  ·  clique para filtrar"),
            height=max(300, len(prod_stats) * 52),
            margin=dict(t=40, b=10, l=5, r=120),
            yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
            xaxis=dict(showgrid=True, gridcolor=GRID),
        )
        ev_prod = st.plotly_chart(fig_prod, use_container_width=True, on_select="rerun", key="chart_prod")
        def _ctx_rank_prod():
            return build_ai_context("produto", f"Ranking por Produto",
                                    df, df_base, df_raw,
                                    extra={"metrica_rank": metrica_rank})
        _ia_button(f"Ranking por Produto — {metrica_rank.capitalize()}",
                   _ctx_rank_prod, "ia_btn_rank_prod", analysis_type="produto")
        if _handle_event(ev_prod, "xf_produto", "y"):
            st.rerun()

    with col_c:
        # Gráfico de rosca: participação dos produtos por cliente (em % do volume selecionado)
        prod_cli_stats = (
            df_base.groupby(["prod_nome","codigo_produto"])
            .agg(val=(metrica_rank, "sum"))
            .reset_index()
            .sort_values("val", ascending=False)
        )
        total_geral = prod_cli_stats["val"].sum()
        if total_geral > 0:
            prod_cli_stats["pct"] = (prod_cli_stats["val"] / total_geral * 100).round(1)
        else:
            prod_cli_stats["pct"] = 0.0

        # Agrupa produtos menores em "Outros" para não poluir o gráfico
        _top_n_donut = 6
        if len(prod_cli_stats) > _top_n_donut:
            _top   = prod_cli_stats.head(_top_n_donut).copy()
            _resto = prod_cli_stats.iloc[_top_n_donut:].copy()
            _outros_row = pd.DataFrame([{
                "prod_nome": "Outros",
                "codigo_produto": "outros",
                "val": _resto["val"].sum(),
                "pct": _resto["pct"].sum(),
            }])
            prod_cli_stats = pd.concat([_top, _outros_row], ignore_index=True)

        _donut_colors = [sku_color(r["prod_nome"]) for _, r in prod_cli_stats.iterrows()]

        _donut_labels = [
            f"{r['prod_nome']}  ·  {met_fmt_rank(r['val'])}  ·  {r['pct']:.1f}%"
            for _, r in prod_cli_stats.iterrows()
        ]

        # Pré-monta hover completo por fatia (única string HTML — Plotly Pie não indexa customdata[i] corretamente)
        _donut_hover_body = [
            (
                f"<span style='color:{C_CYAN}'>📊 Participação</span>  <b>{fmt_br(r['pct'], 1)}%</b><br>"
                f"<span style='color:{C_TEAL}'>📦 Volume</span>  <b>{met_fmt_rank(r['val'])}</b>"
            )
            for _, r in prod_cli_stats.iterrows()
        ]

        fig_cli = go.Figure(go.Pie(
            labels=_donut_labels,
            values=prod_cli_stats["val"],
            hole=0.60,
            textposition="none",
            marker=dict(
                colors=_donut_colors,
                line=dict(color=BG_APP, width=3),
            ),
            customdata=_donut_hover_body,
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{customdata}"
                "<extra></extra>"
            ),
            sort=False,
            direction="clockwise",
        ))

        _metric_label = {"kilos":"Kilos","caixas":"Caixas","unidades":"Unidades"}[metrica_rank]
        _total_fmt = met_fmt_rank(total_geral)
        fig_cli.add_annotation(
            text=f"<b>{_total_fmt}</b><br><span style='font-size:10px;color:{TXT_S}'>{_metric_label} total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=TXT_H, family="Montserrat, sans-serif"),
            align="center",
        )
        fig_layout(fig_cli,
            title=dict(text="Participação por Produto  ·  % do volume total"),
            height=max(380, 380),
            margin=dict(t=45, b=110, l=20, r=20),
            showlegend=True,
            legend=dict(
                orientation="h", x=0.5, xanchor="center", y=-0.20,
                font=dict(color=TXT_M, size=10),
                bgcolor="rgba(0,0,0,0)",
                itemsizing="constant",
            ),
        )
        st.plotly_chart(fig_cli, use_container_width=True, key="chart_cli")
        def _ctx_donut():
            return build_ai_context("produto", "Participacao por Produto",
                                    df, df_base, df_raw,
                                    extra={"metrica_rank": metrica_rank})
        _ia_button("Participacao por Produto",
                   _ctx_donut, "ia_btn_donut", analysis_type="produto")


    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 4 — EVOLUÇÃO SEMANAL POR PRODUTO
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("📉", "Evolução Semanal por Produto")

    tab_ev1, tab_ev2, tab_ev3 = st.tabs(["⚖️ Kilos", "📦 Caixas", "🔢 Unidades"])


    def evolution_lines(metric_col, fmt_fn, y_title):
        prod_wk_raw = (
            df.groupby(["semana_sort","semana_label","date_range","prod_nome","codigo_produto"])
            .agg(
                val      =(metric_col, "sum"),
                n_clientes=("nome_cliente","nunique"),
                kilos    =("kilos",   "sum"),
                caixas   =("caixas",  "sum"),
                unidades =("unidades","sum"),
            )
            .reset_index().sort_values("semana_sort")
        )
        prods = sorted(prod_wk_raw["prod_nome"].unique())

        # reindexar: todas as semanas do intervalo × todos os produtos filtrados
        prod_wk = _reindex_to_all_weeks(prod_wk_raw, extra_keys=["prod_nome"])
        # recupera val / métricas para os pares existentes
        _val_map = prod_wk_raw.set_index(["semana_sort","prod_nome"])[
            ["val","kilos","caixas","unidades","n_clientes"]
        ]
        prod_wk = prod_wk.set_index(["semana_sort","prod_nome"])
        prod_wk.update(_val_map)
        prod_wk = prod_wk.reset_index().sort_values(["semana_sort","prod_nome"])
        # preenche NaN que possam ter sobrado
        for _mc in ["val","kilos","caixas","unidades","n_clientes"]:
            if _mc in prod_wk.columns:
                prod_wk[_mc] = prod_wk[_mc].fillna(0)

        cmap  = prod_color_map(prods)
        hover_ev = (
            "<b>%{fullData.name}</b><br>"
            f"<span style='color:{TXT_S}'>📅 %{{customdata[0]}}</span><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[1]:,.1f}} kg</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[2]:,.1f}} cx</b><br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[3]:,.0f}} un</b><br>"
            f"<span style='color:{C_ORANGE}'>👥 Clientes</span>  %{{customdata[4]:.0f}}"
            "<extra></extra>"
        )
        fig = go.Figure()
        for prod in prods:
            sub = prod_wk[prod_wk["prod_nome"] == prod]
            cd  = sub[["date_range","kilos","caixas","unidades","n_clientes"]].fillna(0).values.tolist()
            fig.add_trace(go.Scatter(
                x=sub["semana_label"], y=sub["val"],
                mode="lines+markers+text", name=str(prod),
                line=dict(color=cmap[prod], width=2),
                marker=dict(size=7, color=cmap[prod], line=dict(color=BG_PLOT, width=1.5)),
                text=sub["val"].apply(fmt_fn),
                textposition="top center", textfont=dict(size=8, color=cmap[prod]),
                customdata=cd, hovertemplate=hover_ev,
            ))
        all_wk = [lbl_map[w] for w in ALL_RANGE_SORTS if w in lbl_map]
        fig_layout(fig,
            height=420, hovermode="x unified",
            legend=dict(orientation="h", y=-0.22, font=dict(color=TXT_M, size=10)),
            margin=dict(t=20, b=80, l=5, r=10),
            xaxis=dict(type="category", categoryorder="array", categoryarray=all_wk,
                       showgrid=False, tickfont=dict(color=TXT_S, size=9)),
            yaxis=dict(showgrid=True, gridcolor=GRID, title_text=y_title,
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        return fig


    with tab_ev1:
        st.plotly_chart(evolution_lines("kilos",    lambda v: fmt_br(v,1)+"kg",  "Kilos (kg)"),    use_container_width=True)
        def _ctx_ev_kg():
            return build_ai_context("produto", "Evolucao Semanal por Produto — Kilos",
                                    df, df_base, df_raw,
                                    extra={"metrica_rank": "kilos"})
        _ia_button("Evolucao Semanal por Produto — Kilos",
                   _ctx_ev_kg, "ia_btn_ev_kg", analysis_type="produto")
    with tab_ev2:
        st.plotly_chart(evolution_lines("caixas",   lambda v: fmt_br(v,1)+"cx",  "Caixas (cx)"),   use_container_width=True)
        def _ctx_ev_cx():
            return build_ai_context("produto", "Evolucao Semanal por Produto — Caixas",
                                    df, df_base, df_raw,
                                    extra={"metrica_rank": "caixas"})
        _ia_button("Evolucao Semanal por Produto — Caixas",
                   _ctx_ev_cx, "ia_btn_ev_cx", analysis_type="produto")
    with tab_ev3:
        st.plotly_chart(evolution_lines("unidades", lambda v: fmt_br(v,0)+"un",  "Unidades (un)"), use_container_width=True)
        def _ctx_ev_un():
            return build_ai_context("produto", "Evolucao Semanal por Produto — Unidades",
                                    df, df_base, df_raw,
                                    extra={"metrica_rank": "unidades"})
        _ia_button("Evolucao Semanal por Produto — Unidades",
                   _ctx_ev_un, "ia_btn_ev_un", analysis_type="produto")




with tab_cli:
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 4B — EVOLUÇÃO SEMANAL POR CLIENTE
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("👥", "Evolução Semanal por Cliente")

    tab_cli_ev1, tab_cli_ev2, tab_cli_ev3 = st.tabs(["⚖️ Kilos", "📦 Caixas", "🔢 Unidades"])


    def evolution_lines_cliente(metric_col, fmt_fn, y_title):
        cli_wk_raw = (
            df.groupby(["semana_sort", "semana_label", "date_range", "nome_cliente"])
            .agg(
                val       =(metric_col,      "sum"),
                kilos     =("kilos",         "sum"),
                caixas    =("caixas",        "sum"),
                unidades  =("unidades",      "sum"),
                n_produtos=("codigo_produto","nunique"),
            )
            .reset_index().sort_values("semana_sort")
        )
        clientes = sorted(cli_wk_raw["nome_cliente"].unique())

        cli_wk = _reindex_to_all_weeks(cli_wk_raw, extra_keys=["nome_cliente"])
        _val_map = cli_wk_raw.set_index(["semana_sort", "nome_cliente"])[
            ["val", "kilos", "caixas", "unidades", "n_produtos"]
        ]
        cli_wk = cli_wk.set_index(["semana_sort", "nome_cliente"])
        cli_wk.update(_val_map)
        cli_wk = cli_wk.reset_index().sort_values(["semana_sort", "nome_cliente"])
        for _mc in ["val", "kilos", "caixas", "unidades", "n_produtos"]:
            if _mc in cli_wk.columns:
                cli_wk[_mc] = cli_wk[_mc].fillna(0)

        _cli_palette = [
            C_CYAN, C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN, C_RED,
            "#EC4899", "#818CF8", "#34D399", "#F472B6", "#60A5FA", "#A3E635",
            "#FACC15", "#FB7185", "#4ADE80", "#38BDF8", "#C084FC",
        ]
        cli_colors = {c: _cli_palette[i % len(_cli_palette)] for i, c in enumerate(sorted(clientes))}

        hover_ev_cli = (
            "<b>%{fullData.name}</b><br>"
            f"<span style='color:{TXT_S}'>📅 %{{customdata[0]}}</span><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[1]:,.1f}} kg</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[2]:,.1f}} cx</b><br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[3]:,.0f}} un</b><br>"
            f"<span style='color:{C_ORANGE}'>🏷️ Produtos distintos</span>  %{{customdata[4]:.0f}}<br>"
            f"<span style='color:{TXT_S};font-size:9px'>clique para filtrar por cliente</span>"
            "<extra></extra>"
        )

        all_wk = [lbl_map[w] for w in ALL_RANGE_SORTS if w in lbl_map]

        # ══════════════════════════════════════════════════════════════════════════
        # PASSO 1 — calcula médias e monta dados de cada cliente
        # ══════════════════════════════════════════════════════════════════════════
        client_stats = []   # lista de dicts, um por cliente com avg_val
        for cli in clientes:
            sub   = cli_wk[cli_wk["nome_cliente"] == cli]
            color = cli_colors[cli]

            primeiro_fat = (
                sub[sub["val"] > 0]["semana_sort"].min()
                if (sub["val"] > 0).any() else None
            )
            if primeiro_fat is None:
                client_stats.append(None)
                continue

            sub_desde = sub[sub["semana_sort"] >= primeiro_fat]
            avg_val   = sub_desde["val"].mean()
            n_total   = len(sub_desde)
            n_zeros   = int((sub_desde["val"] == 0).sum())
            n_fat     = n_total - n_zeros
            val_max   = sub_desde["val"].max()
            val_min   = sub_desde[sub_desde["val"] > 0]["val"].min() if n_fat > 0 else 0.0
            sem_inicio = sub_desde["semana_label"].iloc[0]
            sem_fim    = sub_desde["semana_label"].iloc[-1]

            client_stats.append(dict(
                cli=cli, color=color, sub=sub, sub_desde=sub_desde,
                avg_val=avg_val, n_total=n_total, n_zeros=n_zeros, n_fat=n_fat,
                val_max=val_max, val_min=val_min,
                sem_inicio=sem_inicio, sem_fim=sem_fim,
            ))

        # ══════════════════════════════════════════════════════════════════════════
        # PASSO 2 — rankeia por avg_val DECRESCENTE (maior → menor)
        # ══════════════════════════════════════════════════════════════════════════
        valid_with_idx   = [(i, s["avg_val"]) for i, s in enumerate(client_stats) if s is not None]
        valid_sorted_desc = sorted(valid_with_idx, key=lambda t: t[1], reverse=True)

        # ══════════════════════════════════════════════════════════════════════════
        # PASSO 3 — constrói o gráfico (traces inseridos do maior para o menor)
        # ══════════════════════════════════════════════════════════════════════════
        fig = go.Figure()

        for rank, (i, _) in enumerate(valid_sorted_desc, 1):
            s = client_stats[i]
            if s is None:
                continue

            cli        = s["cli"]
            color      = s["color"]
            sub        = s["sub"]
            avg_val    = s["avg_val"]
            n_total    = s["n_total"]
            n_zeros    = s["n_zeros"]
            n_fat      = s["n_fat"]
            val_max    = s["val_max"]
            val_min    = s["val_min"]
            sem_inicio = s["sem_inicio"]
            sem_fim    = s["sem_fim"]

            # ── customdata linha principal: [date_range, kg, cx, un, n_prod, cli] ─
            cd = sub[["date_range","kilos","caixas","unidades","n_produtos"]].fillna(0).copy()
            cd["_cli"] = cli
            cd_vals = cd.values.tolist()

            # ── Linha principal (sem entrada na legenda — a avg line representa o card) ──
            fig.add_trace(go.Scatter(
                x=sub["semana_label"], y=sub["val"],
                mode="lines+markers+text", name=str(cli),
                line=dict(color=color, width=2),
                marker=dict(size=7, color=color, line=dict(color=BG_PLOT, width=1.5)),
                text=sub["val"].apply(fmt_fn),
                textposition="top center", textfont=dict(size=8, color=color),
                customdata=cd_vals, hovertemplate=hover_ev_cli,
                legendgroup=cli,
                showlegend=False,
                legendrank=rank,
            ))

            # hover detalhado da linha de média
            hover_avg = (
                f"<b>📊 Média — {cli}</b><br>"
                f"──────────────────────────────<br>"
                f"<b style='font-size:13px'>{fmt_fn(avg_val)}</b>  <i style='font-size:9px'>média/semana</i><br>"
                f"──────────────────────────────<br>"
                f"<span style='color:{TXT_S}'>🗓️ Período:</span>  {sem_inicio} → {sem_fim}<br>"
                f"<span style='color:{TXT_S}'>📐 Semanas usadas:</span>  <b>{n_total}</b> "
                f"<i>({n_fat} com fat. + {n_zeros} zeradas)</i><br>"
                f"<span style='color:{C_GREEN}'>⬆ Máximo:</span>  <b>{fmt_fn(val_max)}</b><br>"
                f"<span style='color:{C_RED}'>⬇ Mínimo (fat.):</span>  <b>{fmt_fn(val_min)}</b><br>"
                f"──────────────────────────────<br>"
                f"<span style='color:{TXT_S};font-size:9px'>"
                f"Lógica: soma dos valores desde a 1ª semana com<br>"
                f"faturamento ÷ total de semanas do período<br>"
                f"(zeros após o início reduzem a média)</span><br>"
                f"<span style='color:{C_CYAN};font-size:9px'>clique para filtrar por este cliente</span>"
                "<extra></extra>"
            )

            # customdata da linha de média: [cli, "__avg__"] — identificador para o handler de filtro
            avg_cd = [[cli, "__avg__"]] * len(all_wk)

            # ── Linha de média — CARD na legenda lateral direita ──────────────────
            # Nome exibido no card: "#rank  NomeCliente  ·  valor_médio"
            card_name = f"#{rank}  {cli}  ·  {fmt_fn(avg_val)}"

            fig.add_trace(go.Scatter(
                x=all_wk,
                y=[avg_val] * len(all_wk),
                mode="lines",
                name=card_name,
                line=dict(color=color, width=1.8, dash="dash"),
                opacity=0.65,
                showlegend=True,       # ← aparece como card na legenda lateral
                legendgroup=cli,
                customdata=avg_cd,
                hovertemplate=hover_avg,
                legendrank=rank,       # garante ordem decrescente na legenda
            ))

        # ── margem direita dinâmica conforme o maior label de card ────────────────
        if valid_sorted_desc:
            max_lbl = max(
                len(f"#{r}  {client_stats[idx]['cli']}  ·  {fmt_fn(client_stats[idx]['avg_val'])}")
                for r, (idx, _) in enumerate(valid_sorted_desc, 1)
                if client_stats[idx] is not None
            )
        else:
            max_lbl = 20
        r_margin = min(max(190, max_lbl * 7 + 40), 360)

        fig_layout(fig,
            height=max(460, 30 * len(clientes) + 300),
            hovermode="x unified",
            legend=dict(
                orientation="v",
                x=1.01,
                y=1.0,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(15,25,41,0.93)",   # BG_CARD com alpha
                bordercolor=BORDER,
                borderwidth=1,
                font=dict(color=TXT_M, size=10, family="Montserrat, sans-serif"),
                title=dict(
                    text="  Média/semana  ▼",
                    font=dict(color=C_CYAN, size=10, family="Montserrat, sans-serif"),
                ),
                itemclick="toggleothers",      # clique isola a linha do cliente
                itemdoubleclick="toggle",      # duplo-clique alterna visibilidade
                tracegroupgap=2,
            ),
            margin=dict(t=20, b=20, l=5, r=r_margin),
            xaxis=dict(type="category", categoryorder="array", categoryarray=all_wk,
                       showgrid=False, tickfont=dict(color=TXT_S, size=9)),
            yaxis=dict(showgrid=True, gridcolor=GRID, title_text=y_title,
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        return fig, set(clientes)


    # ── Handler de clique nos gráficos de cliente ─────────────────────────────────
    def _handle_cli_ev(event, clientes_set):
        """Extrai o nome do cliente ao clicar na linha principal ou na linha de média."""
        if not (event and hasattr(event, "selection") and event.selection):
            return False
        pts = event.selection.get("points", [])
        if not pts:
            return _update_xf("xf_cliente", set())
        vals = set()
        for p in pts:
            cd = p.get("customdata")
            if not cd:
                continue
            # linha de média: customdata = [cli, "__avg__"]
            if isinstance(cd, (list, tuple)) and len(cd) >= 2 and cd[1] == "__avg__":
                vals.add(str(cd[0]))
            # linha principal: customdata = [date_range, kg, cx, un, n_prod, cli]
            elif isinstance(cd, (list, tuple)) and len(cd) >= 6:
                candidate = str(cd[5])
                if candidate in clientes_set:
                    vals.add(candidate)
        if not vals:
            return _update_xf("xf_cliente", set())
        if vals == st.session_state["xf_cliente"]:
            return _update_xf("xf_cliente", set())
        return _update_xf("xf_cliente", vals)


    with tab_cli_ev1:
        _fig1, _cli_set1 = evolution_lines_cliente("kilos",    lambda v: fmt_br(v, 1) + "kg", "Kilos (kg)")
        _ev1 = st.plotly_chart(_fig1, use_container_width=True, on_select="rerun", key="chart_cli_ev1")
        def _ctx_cli_kg():
            return build_ai_context("cliente", "Evolucao Semanal por Cliente — Kilos",
                                    df, df_base, df_raw)
        _ia_button("Evolucao Semanal por Cliente — Kilos",
                   _ctx_cli_kg, "ia_btn_cli_kg", analysis_type="cliente")
        if _handle_cli_ev(_ev1, _cli_set1):
            st.rerun()
    with tab_cli_ev2:
        _fig2, _cli_set2 = evolution_lines_cliente("caixas",   lambda v: fmt_br(v, 1) + "cx", "Caixas (cx)")
        _ev2 = st.plotly_chart(_fig2, use_container_width=True, on_select="rerun", key="chart_cli_ev2")
        def _ctx_cli_cx():
            return build_ai_context("cliente", "Evolucao Semanal por Cliente — Caixas",
                                    df, df_base, df_raw)
        _ia_button("Evolucao Semanal por Cliente — Caixas",
                   _ctx_cli_cx, "ia_btn_cli_cx", analysis_type="cliente")
        if _handle_cli_ev(_ev2, _cli_set2):
            st.rerun()
    with tab_cli_ev3:
        _fig3, _cli_set3 = evolution_lines_cliente("unidades", lambda v: fmt_br(v, 0) + "un", "Unidades (un)")
        _ev3 = st.plotly_chart(_fig3, use_container_width=True, on_select="rerun", key="chart_cli_ev3")
        def _ctx_cli_un():
            return build_ai_context("cliente", "Evolucao Semanal por Cliente — Unidades",
                                    df, df_base, df_raw)
        _ia_button("Evolucao Semanal por Cliente — Unidades",
                   _ctx_cli_un, "ia_btn_cli_un", analysis_type="cliente")
        if _handle_cli_ev(_ev3, _cli_set3):
            st.rerun()


    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 5 — PEDIDOS POR CLIENTE  +  TRANSPARÊNCIA DE NOTAS
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("🛒", "Pedidos por Cliente")

    st.markdown(
        f"<div style='font-size:.82rem;color:{TXT_S};margin-bottom:12px'>"
        f"Um <b>pedido</b> é identificado pelo número único em <code>pedido_cliente</code>. "
        f"Notas sem número de pedido são tratadas como transações avulsas e sinalizadas separadamente.</div>",
        unsafe_allow_html=True,
    )

    # Contagem de pedidos: apenas notas com pedido_cliente
    pedidos_cli = (
        df_base[df_base["tem_pedido"]]
        .groupby("nome_cliente")
        .agg(
            n_pedidos    =("pedido_clean",  "nunique"),
            kilos        =("kilos",         "sum"),
            caixas       =("caixas",        "sum"),
            unidades     =("unidades",      "sum"),
            semanas_ativas=("semana_sort",  "nunique"),
        )
        .reset_index()
        .sort_values("n_pedidos", ascending=True)
    )
    pedidos_cli["kg_por_pedido"] = (pedidos_cli["kilos"]    / pedidos_cli["n_pedidos"]).round(1)
    pedidos_cli["cx_por_pedido"] = (pedidos_cli["caixas"]   / pedidos_cli["n_pedidos"]).round(1)
    pedidos_cli["un_por_pedido"] = (pedidos_cli["unidades"] / pedidos_cli["n_pedidos"]).round(0)

    # Notas sem pedido por cliente (contagem)
    sem_pedido_cli = (
        df_base[~df_base["tem_pedido"]]
        .groupby("nome_cliente")["numero_nota"]
        .count()
        .reset_index()
        .rename(columns={"numero_nota": "notas_sem_pedido"})
    )
    pedidos_cli = pedidos_cli.merge(sem_pedido_cli, on="nome_cliente", how="left")
    pedidos_cli["notas_sem_pedido"] = pedidos_cli["notas_sem_pedido"].fillna(0).astype(int)

    cd_ped = pedidos_cli[["kilos","caixas","unidades","semanas_ativas",
                            "kg_por_pedido","cx_por_pedido","un_por_pedido",
                            "notas_sem_pedido"]].fillna(0).values.tolist()
    hover_ped = (
        "<b>%{y}</b><br>"
        f"<span style='color:{C_CYAN}'>🛒 Pedidos</span>  <b>%{{x:.0f}}</b><br>"
        f"<span style='color:{C_AMBER}'>⚠️ Notas s/ pedido</span>  %{{customdata[7]:.0f}}<br>"
        f"<span style='color:{C_TEAL}'>⚖️ Kg / Pedido</span>  %{{customdata[4]:,.1f}} kg<br>"
        f"<span style='color:{C_AMBER}'>📦 Cx / Pedido</span>  %{{customdata[5]:,.1f}} cx<br>"
        f"<span style='color:{C_VIOLET}'>🔢 Un / Pedido</span>  %{{customdata[6]:,.0f}} un<br>"
        f"<span style='color:{C_GREEN}'>📅 Semanas ativas</span>  %{{customdata[3]:.0f}}"
        "<extra></extra>"
    )
    fig_ped = go.Figure(go.Bar(
        name="Algum Nome",
        x=pedidos_cli["n_pedidos"], y=pedidos_cli["nome_cliente"],
        orientation="h",
        marker=dict(color=C_VIOLET, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
        text=pedidos_cli["n_pedidos"].apply(lambda v: fmt_br(v, 0) + " pedidos"),
        textposition="outside", textfont=dict(size=10, color=TXT_H),
        customdata=cd_ped, hovertemplate=hover_ped,
    ))
    fig_layout(fig_ped,
        title=dict(text="Número de Pedidos por Cliente (período selecionado)"),
        height=max(300, len(pedidos_cli) * 50),
        margin=dict(t=40, b=10, l=5, r=140),
        yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
        xaxis=dict(showgrid=True, gridcolor=GRID, title_text="Nº Pedidos",
                   title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
    )
    st.plotly_chart(fig_ped, use_container_width=True)
    def _ctx_ped():
        return build_ai_context("pedido", "Pedidos por Cliente",
                                df, df_base, df_raw)
    _ia_button("Pedidos por Cliente",
               _ctx_ped, "ia_btn_pedidos", analysis_type="pedido")

    # ── TRANSPARÊNCIA DE NOTAS ────────────────────────────────────────────────────
    n_com_ped  = df_base["tem_pedido"].sum()
    n_sem_ped  = (~df_base["tem_pedido"]).sum()
    pct_com    = n_com_ped / len(df_base) * 100 if len(df_base) else 0

    col_np1, col_np2, col_np3 = st.columns(3)
    col_np1.markdown(
        f"<div class='kpi-card' style='--accent:{C_GREEN}'>"
        f"<div class='kpi-label'>NOTAS COM PEDIDO</div>"
        f"<div class='kpi-value' style='font-size:1.4rem'>{fmt_br(n_com_ped, 0)}</div>"
        f"<div class='kpi-sub'>{pct_com:.1f}% do total</div></div>",
        unsafe_allow_html=True,
    )
    col_np2.markdown(
        f"<div class='kpi-card' style='--accent:{C_AMBER}'>"
        f"<div class='kpi-label'>NOTAS SEM PEDIDO</div>"
        f"<div class='kpi-value' style='font-size:1.4rem'>{fmt_br(n_sem_ped, 0)}</div>"
        f"<div class='kpi-sub'>{100-pct_com:.1f}% do total</div></div>",
        unsafe_allow_html=True,
    )
    col_np3.markdown(
        f"<div class='kpi-card' style='--accent:{C_VIOLET}'>"
        f"<div class='kpi-label'>PEDIDOS ÚNICOS</div>"
        f"<div class='kpi-value' style='font-size:1.4rem'>{fmt_br(df_base[df_base['tem_pedido']]['pedido_clean'].nunique(), 0)}</div>"
        f"<div class='kpi-sub'>números distintos de pedido</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("📋 Detalhamento de Notas por Dia — Pedido x Sem Pedido"):
        st.markdown(
            f"<div style='font-size:.82rem;color:{TXT_S};margin-bottom:10px'>"
            f"Selecione uma data para ver todas as notas daquele dia e identificar "
            f"quais possuem número de pedido e quais não possuem.</div>",
            unsafe_allow_html=True,
        )
        datas_disp = sorted(df_base["emissao"].dt.date.unique())
        col_dt1, col_dt2 = st.columns([3, 7])
        with col_dt1:
            semanas_notas_opts = sorted(df_base["semana_label"].unique())
            sem_notas_sel = st.multiselect(
                "Filtrar por Semana",
                semanas_notas_opts,
                key="sem_notas",
                placeholder="Todas as semanas…",
            )

            # Restrict dates to selected semanas
            if sem_notas_sel:
                datas_filtradas = sorted(
                    df_base[df_base["semana_label"].isin(sem_notas_sel)]["emissao"].dt.date.unique()
                )
            else:
                datas_filtradas = datas_disp

            data_sel = st.multiselect(
                "Selecionar datas",
                datas_filtradas,
                format_func=lambda d: d.strftime("%d/%m/%Y"),
                key="data_notas",
                placeholder="Todas as datas…",
            )
            cli_notas_opts = ["Todos"] + sorted(df_base["nome_cliente"].dropna().unique())
            cli_notas_sel  = st.selectbox("Filtrar cliente", cli_notas_opts, key="cli_notas")

        # Filter by selected dates (all if none selected)
        if data_sel:
            df_dia = df_base[df_base["emissao"].dt.date.isin(data_sel)].copy()
        elif sem_notas_sel:
            df_dia = df_base[df_base["semana_label"].isin(sem_notas_sel)].copy()
        else:
            df_dia = df_base.copy()
        if cli_notas_sel != "Todos":
            df_dia = df_dia[df_dia["nome_cliente"] == cli_notas_sel]

        # Agrupa por nota
        notas_dia = (
            df_dia.groupby(["numero_nota","nome_cliente","deposito","emissao","pedido_clean","tem_pedido"])
            .agg(
                kilos    =("kilos",    "sum"),
                caixas   =("caixas",   "sum"),
                unidades =("unidades", "sum"),
            )
            .reset_index()
            .sort_values(["tem_pedido","numero_nota"], ascending=[False, True])
        )
        notas_dia["Status"] = notas_dia["tem_pedido"].apply(
            lambda x: "✅ Com pedido" if x else "⚠️ Sem número de pedido"
        )
        notas_dia["Pedido"] = notas_dia.apply(
            lambda r: r["pedido_clean"] if r["tem_pedido"] else "—", axis=1
        )
        notas_dia["emissao"] = notas_dia["emissao"].dt.strftime("%d/%m/%Y")
        notas_dia["Kilos"]    = notas_dia["kilos"].apply(lambda v: fmt_br(v, 1) + " kg")
        notas_dia["Caixas"]   = notas_dia["caixas"].apply(lambda v: fmt_br(v, 1) + " cx")
        notas_dia["Unidades"] = notas_dia["unidades"].apply(lambda v: fmt_br(v, 0) + " un")

        tbl_notas = notas_dia.rename(columns={
            "numero_nota":  "Nº Nota",
            "nome_cliente": "Cliente",
            "deposito":     "Depósito",
            "emissao":      "Data",
        })[["Status","Nº Nota","Data","Cliente","Depósito","Pedido","Kilos","Caixas","Unidades"]]

        total_notas = len(notas_dia)
        com_ped_dia = notas_dia["tem_pedido"].sum()
        sem_ped_dia = total_notas - com_ped_dia

        datas_label = (
            ", ".join(d.strftime("%d/%m/%Y") for d in data_sel)
            if data_sel else
            (", ".join(sem_notas_sel) if sem_notas_sel else "todo o período")
        )
        st.markdown(
            f"<div style='font-size:.82rem;color:{TXT_M};margin-bottom:8px'>"
            f"<b>{fmt_br(total_notas, 0)}</b> notas em {datas_label} · "
            f"<span style='color:{C_GREEN}'><b>{fmt_br(com_ped_dia, 0)}</b> com pedido</span> · "
            f"<span style='color:{C_AMBER}'><b>{fmt_br(sem_ped_dia, 0)}</b> sem número de pedido</span></div>",
            unsafe_allow_html=True,
        )
        st.dataframe(tbl_notas, height=350, hide_index=True, use_container_width=True)

        if sem_ped_dia > 0:
            st.markdown(
                f"<div style='font-size:.78rem;color:{C_AMBER};margin-top:8px'>"
                f"ℹ️ As <b>{fmt_br(sem_ped_dia, 0)}</b> nota(s) sem número de pedido podem ter sido emitidas "
                f"avulsamente, sem vínculo com um pedido formal no sistema. "
                f"Recomenda-se verificar junto à equipe comercial se esses faturamentos "
                f"correspondem a pedidos não registrados.</div>",
                unsafe_allow_html=True,
            )


    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 6 — DISTÂNCIA ENTRE PEDIDOS POR CLIENTE
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("⏱️", "Distância entre Pedidos por Cliente")

    n_notas_sem_ped_total = (~df_base["tem_pedido"]).sum()
    if n_notas_sem_ped_total > 0:
        st.markdown(
            f"<div style='font-size:.8rem;color:{C_AMBER};margin-bottom:12px'>"
            f"ℹ️ <b>{fmt_br(n_notas_sem_ped_total, 0)}</b> nota(s) sem número de pedido não foram incluídas "
            f"nesta análise. Apenas pedidos com número identificado são considerados "
            f"para o cálculo do intervalo.</div>",
            unsafe_allow_html=True,
        )

    col_dist1, _ = st.columns([3, 7])
    with col_dist1:
        cli_dist_opts = sorted(df_base[df_base["tem_pedido"]]["nome_cliente"].dropna().unique())
        cli_dist_sel  = st.multiselect(
            "Filtrar Clientes (nesta seção)",
            cli_dist_opts, default=cli_dist_opts, key="cli_dist",
        )

    df_ped_dates = (
        df_base[df_base["tem_pedido"] & df_base["nome_cliente"].isin(cli_dist_sel)]
        .groupby(["nome_cliente","pedido_clean"])["emissao"]
        .min()
        .reset_index()
        .sort_values(["nome_cliente","emissao"])
    )
    df_ped_dates["dias_desde_anterior"] = (
        df_ped_dates.groupby("nome_cliente")["emissao"].diff().dt.days
    )

    dist_resumo = (
        df_ped_dates.groupby("nome_cliente")
        .agg(
            n_pedidos  =("pedido_clean",          "count"),
            media_dias =("dias_desde_anterior",   "mean"),
            min_dias   =("dias_desde_anterior",   "min"),
            max_dias   =("dias_desde_anterior",   "max"),
        )
        .reset_index()
    )
    dist_resumo["media_dias"] = dist_resumo["media_dias"].round(1)
    dist_resumo["min_dias"]   = dist_resumo["min_dias"].fillna(0).astype(int)
    dist_resumo["max_dias"]   = dist_resumo["max_dias"].fillna(0).astype(int)
    dist_resumo = dist_resumo[dist_resumo["n_pedidos"] > 1].sort_values("media_dias", ascending=True)

    if not dist_resumo.empty:
        def dist_color(v):
            if v <= 14:   return C_GREEN
            elif v <= 30: return C_AMBER
            else:         return C_ORANGE

        cd_dist = dist_resumo[["min_dias","max_dias","n_pedidos"]].fillna(0).values.tolist()
        hover_dist = (
            "<b>%{y}</b><br>"
            f"<span style='color:{C_CYAN}'>📅 Média entre pedidos</span>  <b>%{{x:.1f}} dias</b><br>"
            f"<span style='color:{C_GREEN}'>⬇️ Mínimo</span>  %{{customdata[0]}} dias<br>"
            f"<span style='color:{C_RED}'>⬆️ Máximo</span>  %{{customdata[1]}} dias<br>"
            f"<span style='color:{C_VIOLET}'>🛒 Total pedidos</span>  %{{customdata[2]:.0f}}"
            "<extra></extra>"
        )
        fig_dist = go.Figure(go.Bar(
            name="Algum Nome",
            x=dist_resumo["media_dias"], y=dist_resumo["nome_cliente"],
            orientation="h",
            marker=dict(
                color=[dist_color(v) for v in dist_resumo["media_dias"]],
                opacity=0.85, line=dict(color=BG_PLOT, width=0.5),
            ),
            text=dist_resumo["media_dias"].apply(lambda v: f"{fmt_br(v,1)} dias"),
            textposition="outside", textfont=dict(size=10, color=TXT_H),
            customdata=cd_dist, hovertemplate=hover_dist,
        ))
        for ref, color, label in [(7, C_GREEN, "7d"), (14, C_AMBER, "14d"), (30, C_ORANGE, "30d")]:
            fig_dist.add_vline(x=ref, line_width=1, line_color=color, line_dash="dash",
                               annotation_text=label, annotation_font_color=color,
                               annotation_position="top")
        fig_layout(fig_dist,
            title=dict(text="Média de dias entre pedidos consecutivos por cliente"),
            height=max(300, len(dist_resumo) * 50),
            margin=dict(t=40, b=10, l=5, r=140),
            yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
            xaxis=dict(showgrid=True, gridcolor=GRID, title_text="Dias entre pedidos",
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        st.plotly_chart(fig_dist, use_container_width=True)
        def _ctx_dist():
            return build_ai_context("cliente", "Frequencia e Distancia entre Pedidos",
                                    df, df_base, df_raw)
        _ia_button("Frequencia e Distancia entre Pedidos",
                   _ctx_dist, "ia_btn_dist", analysis_type="cliente")

        with st.expander("📋 Histórico detalhado de pedidos por cliente"):
            tbl_ped = df_ped_dates[df_ped_dates["nome_cliente"].isin(dist_resumo["nome_cliente"])].copy()
            tbl_ped["emissao"] = tbl_ped["emissao"].dt.strftime("%d/%m/%Y")
            tbl_ped["dias_desde_anterior"] = tbl_ped["dias_desde_anterior"].fillna(0).astype(int)
            tbl_ped = tbl_ped.rename(columns={
                "nome_cliente":        "Cliente",
                "pedido_clean":        "Pedido",
                "emissao":             "Data",
                "dias_desde_anterior": "Dias desde anterior",
            })
            st.dataframe(tbl_ped, height=320, hide_index=True)
    else:
        st.info("Não há clientes com mais de 1 pedido no período selecionado para calcular distância.")



    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 6B — MÉDIA INTERNA DE DIAS POR LOTE — NOTAS E PEDIDOS
    # ═══════════════════════════════════════════════════════════════════════════════


    # ── Helper: calcula media de dias entre grupos de N eventos ──────────────────
    def _avg_days_every_n(dates_sorted, n=4):
        results = []
        dates = sorted(dates_sorted)
        if len(dates) < n:
            return results
        for i in range(0, len(dates) - n + 1, n):
            grupo_inicio = dates[i]
            grupo_fim    = dates[min(i + n, len(dates)) - 1]
            if i + n < len(dates):
                proximo_inicio = dates[i + n]
                dias = (proximo_inicio - grupo_fim).days
                results.append({
                    "grupo":           i // n + 1,
                    "data_inicio":     grupo_inicio,
                    "data_fim":        grupo_fim,
                    "proximo_inicio":  proximo_inicio,
                    "dias_ate_prox":   dias,
                })
        return results


    def _rn_color(v):
        if v <= 7:    return C_GREEN
        elif v <= 30: return C_AMBER
        else:         return C_ORANGE


    def _internal_avg_every_n(dates_sorted, n=4):
        results = []
        dates = sorted(dates_sorted)
        num_lotes_completos = len(dates) // n
        for i in range(num_lotes_completos):
            lote = dates[i * n : (i + 1) * n]
            intervalos = [(lote[j + 1] - lote[j]).days for j in range(n - 1)]
            media = round(np.mean(intervalos), 1)
            results.append({
                "lote":               i + 1,
                "data_inicio":        lote[0],
                "data_fim":           lote[-1],
                "intervalos_internos": intervalos,
                "media_interna":      media,
            })
        return results


    _RITMO_PALETTE = [
        C_CYAN, C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN, C_RED,
        "#EC4899", "#818CF8", "#34D399", "#F472B6", "#60A5FA", "#A3E635",
    ]


    def _render_ritmo_interno_chart(data_por_cliente, label_tipo):
        if not data_por_cliente:
            return

        fig = go.Figure()
        for idx, (cli, lotes) in enumerate(sorted(data_por_cliente.items())):
            color = _RITMO_PALETTE[idx % len(_RITMO_PALETTE)]
            xs    = [l["lote"] for l in lotes]
            ys    = [l["media_interna"] for l in lotes]
            hover_labels = [
                f"{l['data_inicio'].strftime('%d/%m/%y')} -> {l['data_fim'].strftime('%d/%m/%y')}<br>"
                + "  |  ".join(f"{d}d" for d in l["intervalos_internos"])
                for l in lotes
            ]
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode="lines+markers",
                name=cli,
                line=dict(color=color, width=2),
                marker=dict(color=color, size=9, symbol="circle",
                            line=dict(color=BG_APP, width=1.5)),
                text=hover_labels,
                hovertemplate=(
                    f"<b>{cli}</b><br>"
                    f"<span style='color:{C_AMBER}'>Lote #%{{x}}</span><br>"
                    "%{text}<br>"
                    f"<span style='color:{C_CYAN}'>Media interna</span>  "
                    "<b>%{y:.1f} dias</b>"
                    "<extra></extra>"
                ),
            ))

        for ref, color, lbl in [(7, C_GREEN, "7d"), (14, C_AMBER, "14d"), (30, C_ORANGE, "30d")]:
            fig.add_hline(y=ref, line_width=1, line_color=color, line_dash="dash",
                          annotation_text=lbl, annotation_font_color=color,
                          annotation_position="right")

        max_lote = max(
            (l["lote"] for lotes in data_por_cliente.values() for l in lotes),
            default=1,
        )
        fig_layout(
            fig,
            title=dict(
                text=(
                    f"Evolucao da media interna de dias entre os 4 {label_tipo} de cada lote "
                    f"- 1 linha por cliente"
                )
            ),
            height=max(420, 40 * len(data_por_cliente) + 260),
            margin=dict(t=50, b=10, l=10, r=200),
            xaxis=dict(
                title_text="Lote # (grupo de 4 registros consecutivos)",
                title_font=dict(color=TXT_S),
                tickmode="linear",
                dtick=1,
                range=[0.5, max_lote + 0.5],
                showgrid=True, gridcolor=GRID,
                tickfont=dict(color=TXT_S),
            ),
            yaxis=dict(
                title_text="Media de dias entre os 4 registros",
                title_font=dict(color=TXT_S),
                showgrid=True, gridcolor=GRID,
                tickfont=dict(color=TXT_S),
                rangemode="tozero",
            ),
            legend=dict(
                orientation="v", x=1.01, xanchor="left", y=1, yanchor="top",
                font=dict(color=TXT_M, size=9),
                bgcolor=BG_SIDEBAR,
                bordercolor=BORDER,
                borderwidth=1,
            ),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)


    # -- ANALISE 1: Media interna a cada 4 Notas por Cliente ----------------------
    st.markdown(
        f"<div class='sec-header' style='margin-top:10px'>"
        f"<span>📄</span> Media Interna de Dias por Lote de 4 Notas — por Cliente"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='tip'>Cada ponto e a media dos 3 intervalos internos do lote "
        f"(1a->2a nota, 2a->3a nota, 3a->4a nota). "
        f"Passe o mouse para ver as datas e os intervalos individuais.</div>",
        unsafe_allow_html=True,
    )

    notas_cli_dates = (
        df_base.groupby(["nome_cliente","numero_nota"])["emissao"]
        .min().reset_index()
        .sort_values(["nome_cliente","emissao"])
    )

    _notas_interno = {}
    for cli, grp in notas_cli_dates.groupby("nome_cliente"):
        dates   = list(grp["emissao"].dt.date)
        interno = _internal_avg_every_n(dates, n=4)
        if interno:
            _notas_interno[cli] = interno

    if _notas_interno:
        _render_ritmo_interno_chart(_notas_interno, "notas")

        with st.expander("Tabela: media interna por lote (notas)"):
            _rows_int = []
            for cli, lotes in sorted(_notas_interno.items()):
                for l in lotes:
                    _rows_int.append({
                        "Cliente":                  cli,
                        "Lote #":                   l["lote"],
                        "1a nota do lote":          l["data_inicio"].strftime("%d/%m/%Y"),
                        "4a nota do lote":          l["data_fim"].strftime("%d/%m/%Y"),
                        "Intervalos internos (dias)": "  |  ".join(str(d) for d in l["intervalos_internos"]),
                        "Media interna (dias)":     l["media_interna"],
                    })
            st.dataframe(pd.DataFrame(_rows_int), height=300, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum cliente possui 4 ou mais notas no periodo para analise de media interna por lote.")


    # -- ANALISE 2: Media interna a cada 4 Pedidos por Cliente --------------------
    st.markdown(
        f"<div class='sec-header' style='margin-top:28px'>"
        f"<span>🛒</span> Media Interna de Dias por Lote de 4 Pedidos — por Cliente"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='tip'>Cada ponto e a media dos 3 intervalos internos do lote "
        f"(1o->2o pedido, 2o->3o pedido, 3o->4o pedido). "
        f"Apenas pedidos com numero identificado sao considerados.</div>",
        unsafe_allow_html=True,
    )

    pedidos_dates = (
        df_base[df_base["tem_pedido"]]
        .groupby(["nome_cliente","pedido_clean"])["emissao"]
        .min().reset_index()
        .sort_values(["nome_cliente","emissao"])
    )

    _ped_interno = {}
    for cli, grp in pedidos_dates.groupby("nome_cliente"):
        dates   = list(grp["emissao"].dt.date)
        interno = _internal_avg_every_n(dates, n=4)
        if interno:
            _ped_interno[cli] = interno

    if _ped_interno:
        _render_ritmo_interno_chart(_ped_interno, "pedidos")

        with st.expander("Tabela: media interna por lote (pedidos)"):
            _rows_int_p = []
            for cli, lotes in sorted(_ped_interno.items()):
                for l in lotes:
                    _rows_int_p.append({
                        "Cliente":                  cli,
                        "Lote #":                   l["lote"],
                        "1o pedido do lote":        l["data_inicio"].strftime("%d/%m/%Y"),
                        "4o pedido do lote":        l["data_fim"].strftime("%d/%m/%Y"),
                        "Intervalos internos (dias)": "  |  ".join(str(d) for d in l["intervalos_internos"]),
                        "Media interna (dias)":     l["media_interna"],
                    })
            st.dataframe(pd.DataFrame(_rows_int_p), height=300, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum cliente possui 4 ou mais pedidos no periodo para analise de media interna por lote.")




with tab_vol:
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 7 — ANÁLISE DE VOLUME: POR CLIENTE / PEDIDO / SEMANA / NOTA
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("📊", "Análise de Volume — Por Cliente · Pedido · Semana · Nota")

    tab_vol_cli, tab_vol_ped, tab_vol_sem, tab_vol_nota = st.tabs([
        "👥 Por Cliente", "🛒 Por Pedido", "📅 Por Semana", "📄 Por Nota"
    ])

    # ── TAB 1: POR CLIENTE ────────────────────────────────────────────────────────
    with tab_vol_cli:
        vol_cli = (
            df.groupby("nome_cliente")
            .agg(
                kilos       =("kilos",        "sum"),
                caixas      =("caixas",       "sum"),
                unidades    =("unidades",     "sum"),
                n_pedidos   =("pedido_clean", lambda x: x[df.loc[x.index,"tem_pedido"]].nunique()),
                n_semanas   =("semana_sort",  "nunique"),
                n_notas     =("numero_nota",  "nunique"),
            )
            .reset_index()
        )
        vol_cli["kg_por_pedido"] = (vol_cli["kilos"] / vol_cli["n_pedidos"].replace(0, np.nan)).round(1)
        vol_cli["kg_por_semana"] = (vol_cli["kilos"] / vol_cli["n_semanas"].replace(0, np.nan)).round(1)
        vol_cli["kg_por_nota"]   = (vol_cli["kilos"] / vol_cli["n_notas"].replace(0, np.nan)).round(1)
        vol_cli = vol_cli.sort_values("kilos", ascending=True)

        cd_vc = vol_cli[["caixas","unidades","n_pedidos","n_semanas","n_notas",
                          "kg_por_pedido","kg_por_semana","kg_por_nota"]].fillna(0).values.tolist()
        hover_vc = (
            "<b>%{y}</b><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Total Kilos</span>  <b>%{{x:,.1f}} kg</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  %{{customdata[0]:,.1f}} cx<br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  %{{customdata[1]:,.0f}} un<br>"
            f"<span style='color:{C_VIOLET}'>🛒 Pedidos</span>  %{{customdata[2]:.0f}}<br>"
            f"<span style='color:{C_GREEN}'>📅 Semanas ativas</span>  %{{customdata[3]:.0f}}<br>"
            f"<span style='color:{C_ORANGE}'>📄 Notas</span>  %{{customdata[4]:.0f}}<br>"
            f"<br>────────────<br>"
            f"<span style='color:{C_CYAN}'>Kg / Pedido</span>  %{{customdata[5]:,.1f}} kg<br>"
            f"<span style='color:{C_TEAL}'>Kg / Semana</span>  %{{customdata[6]:,.1f}} kg<br>"
            f"<span style='color:{C_AMBER}'>Kg / Nota</span>  %{{customdata[7]:,.1f}} kg"
            "<extra></extra>"
        )
        fig_vc = go.Figure(go.Bar(
            name="Algum Nome",
            x=vol_cli["kilos"], y=vol_cli["nome_cliente"],
            orientation="h",
            marker=dict(color=C_TEAL, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
            text=vol_cli["kilos"].apply(fmt_peso),
            textposition="outside", textfont=dict(size=11, color=TXT_H),
            customdata=cd_vc, hovertemplate=hover_vc,
        ))
        fig_layout(fig_vc,
            title=dict(text="Volume Total por Cliente"),
            height=max(320, len(vol_cli) * 50),
            margin=dict(t=40, b=10, l=5, r=140),
            yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
            xaxis=dict(showgrid=True, gridcolor=GRID, title_text="Kilos (kg)",
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        st.plotly_chart(fig_vc, use_container_width=True)
        def _ctx_vc():
            return build_ai_context("volume", "Volume Total por Cliente",
                                    df, df_base, df_raw)
        _ia_button("Volume Total por Cliente",
                   _ctx_vc, "ia_btn_vol_cli", analysis_type="volume")

        # Summary table
        tbl_vc = vol_cli.sort_values("kilos", ascending=False).copy()
        tbl_vc["kilos"]        = tbl_vc["kilos"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vc["kg_por_pedido"]= tbl_vc["kg_por_pedido"].apply(lambda v: fmt_br(v, 1) + " kg" if v > 0 else "—")
        tbl_vc["kg_por_semana"]= tbl_vc["kg_por_semana"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vc["kg_por_nota"]  = tbl_vc["kg_por_nota"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vc = tbl_vc.rename(columns={
            "nome_cliente":"Cliente","kilos":"Total Kg","n_pedidos":"Pedidos",
            "n_semanas":"Semanas","n_notas":"Notas",
            "kg_por_pedido":"Kg/Pedido","kg_por_semana":"Kg/Semana","kg_por_nota":"Kg/Nota",
        })
        st.dataframe(tbl_vc[["Cliente","Total Kg","Pedidos","Semanas","Notas","Kg/Pedido","Kg/Semana","Kg/Nota"]],
                     height=300, hide_index=True, use_container_width=True)

    # ── TAB 2: POR PEDIDO ─────────────────────────────────────────────────────────
    with tab_vol_ped:
        df_com_ped = df[df["tem_pedido"]].copy()
        if df_com_ped.empty:
            st.info("Nenhum pedido com número identificado no período selecionado.")
        else:
            vol_ped = (
                df_com_ped.groupby(["pedido_clean","nome_cliente","semana_label","semana_sort"])
                .agg(
                    kilos   =("kilos",    "sum"),
                    caixas  =("caixas",   "sum"),
                    unidades=("unidades", "sum"),
                    n_notas =("numero_nota","nunique"),
                )
                .reset_index()
                .sort_values(["semana_sort","kilos"], ascending=[True, False])
            )

            col_vp1, _ = st.columns([3, 7])
            with col_vp1:
                cli_ped_opts = ["Todos"] + sorted(vol_ped["nome_cliente"].unique())
                cli_ped_sel  = st.selectbox("Filtrar cliente", cli_ped_opts, key="vp_cli")
            if cli_ped_sel != "Todos":
                vol_ped_show = vol_ped[vol_ped["nome_cliente"] == cli_ped_sel]
            else:
                vol_ped_show = vol_ped

            cd_vp = vol_ped_show[["nome_cliente","semana_label","caixas","unidades","n_notas"]].fillna(0).values.tolist()
            hover_vp = (
                "<b>Pedido %{y}</b><br>"
                f"<span style='color:{TXT_S}'>👥 %{{customdata[0]}}</span>  "
                f"<span style='color:{C_TEAL}'>📅 %{{customdata[1]}}</span><br>"
                f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{x:,.1f}} kg</b><br>"
                f"<span style='color:{C_TEAL}'>📦 Caixas</span>  %{{customdata[2]:,.1f}} cx<br>"
                f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  %{{customdata[3]:,.0f}} un<br>"
                f"<span style='color:{C_ORANGE}'>📄 Notas no pedido</span>  %{{customdata[4]:.0f}}"
                "<extra></extra>"
            )
            fig_vp = go.Figure(go.Bar(
                name="Algum Nome",
                x=vol_ped_show["kilos"], y=vol_ped_show["pedido_clean"],
                orientation="h",
                marker=dict(color=C_VIOLET, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
                text=vol_ped_show["kilos"].apply(fmt_peso),
                textposition="outside", textfont=dict(size=11, color=TXT_H),
                customdata=cd_vp, hovertemplate=hover_vp,
            ))
            fig_layout(fig_vp,
                title=dict(text="Volume por Pedido"),
                height=max(320, min(len(vol_ped_show) * 40, 800)),
                margin=dict(t=40, b=10, l=5, r=140),
                yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
                xaxis=dict(showgrid=True, gridcolor=GRID, title_text="Kilos (kg)",
                           title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
            )
            st.plotly_chart(fig_vp, use_container_width=True)

            tbl_vp = vol_ped.sort_values(["semana_sort","kilos"], ascending=[True, False]).copy()
            tbl_vp["kilos"]    = tbl_vp["kilos"].apply(lambda v: fmt_br(v, 1) + " kg")
            tbl_vp["caixas"]   = tbl_vp["caixas"].apply(lambda v: fmt_br(v, 1) + " cx")
            tbl_vp["unidades"] = tbl_vp["unidades"].apply(lambda v: fmt_br(v, 0) + " un")
            tbl_vp = tbl_vp.rename(columns={
                "pedido_clean":"Pedido","nome_cliente":"Cliente","semana_label":"Semana",
                "kilos":"Kilos","caixas":"Caixas","unidades":"Unidades","n_notas":"Nº Notas",
            })
            st.dataframe(tbl_vp[["Pedido","Cliente","Semana","Kilos","Caixas","Unidades","Nº Notas"]],
                         height=320, hide_index=True, use_container_width=True)

    # ── TAB 3: POR SEMANA ─────────────────────────────────────────────────────────
    with tab_vol_sem:
        vol_sem_raw = (
            df.groupby(["semana_sort","semana_label","date_range"])
            .agg(
                kilos    =("kilos",        "sum"),
                caixas   =("caixas",       "sum"),
                unidades =("unidades",     "sum"),
                n_clientes=("nome_cliente","nunique"),
                n_pedidos=("pedido_clean", lambda x: x[df.loc[x.index,"tem_pedido"]].nunique()),
                n_notas  =("numero_nota",  "nunique"),
            )
            .reset_index().sort_values("semana_sort")
        )
        vol_sem = _reindex_to_all_weeks(vol_sem_raw)

        vol_sem["kg_por_cliente"] = (vol_sem["kilos"] / vol_sem["n_clientes"].replace(0, np.nan)).round(1)
        vol_sem["kg_por_nota"]    = (vol_sem["kilos"] / vol_sem["n_notas"].replace(0, np.nan)).round(1)

        cd_vs = vol_sem[["date_range","caixas","unidades","n_clientes","n_pedidos","n_notas",
                          "kg_por_cliente","kg_por_nota"]].fillna(0).values.tolist()
        hover_vs = (
            "<b>%{x}</b>  <span style='color:{ts}'>%{{customdata[0]}}</span><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{y:,.1f}} kg</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  %{{customdata[1]:,.1f}} cx<br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  %{{customdata[2]:,.0f}} un<br>"
            f"<span style='color:{C_ORANGE}'>👥 Clientes</span>  %{{customdata[3]:.0f}}<br>"
            f"<span style='color:{C_VIOLET}'>🛒 Pedidos</span>  %{{customdata[4]:.0f}}<br>"
            f"<span style='color:{C_GREEN}'>📄 Notas</span>  %{{customdata[5]:.0f}}<br>"
            f"<br>────────────<br>"
            f"<span style='color:{C_CYAN}'>Kg / Cliente</span>  %{{customdata[6]:,.1f}} kg<br>"
            f"<span style='color:{C_TEAL}'>Kg / Nota</span>  %{{customdata[7]:,.1f}} kg"
            "<extra></extra>"
        ).replace("{ts}", TXT_S)

        # ── Dois subplots empilhados: linha Kg/Cliente em cima, barras de Kg embaixo ─
        fig_vs2 = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.30, 0.70],   # 30 % linha · 70 % barras
            vertical_spacing=0.06,
        )
        fig_vs2.data = []  # limpa traces fantasmas

        # ── Row 2 (baixo): barras de kilos ───────────────────────────────────────
        fig_vs2.add_trace(go.Bar(
            x=vol_sem["semana_label"], y=vol_sem["kilos"], name="Total Kg",
            marker=dict(color=C_AMBER, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
            text=vol_sem["kilos"].apply(lambda v: fmt_br(v, 1)),
            textposition="outside", textfont=dict(size=11, color=TXT_H),
            customdata=cd_vs, hovertemplate=hover_vs,
        ), row=2, col=1)

        # ── Row 1 (cima): linha Kg/Cliente ───────────────────────────────────────
        fig_vs2.add_trace(go.Scatter(
            x=vol_sem["semana_label"], y=vol_sem["kg_por_cliente"],
            mode="lines+markers+text", name="Kg/Cliente",
            line=dict(color=C_CYAN, width=2),
            marker=dict(size=6, color=C_CYAN),
            text=vol_sem["kg_por_cliente"].apply(lambda v: fmt_br(v, 0)),
            textposition="top center", textfont=dict(size=9, color=C_CYAN),
            connectgaps=True,
            hovertemplate="<b>%{x}</b><br>Kg/Cliente: <b>%{y:,.1f} kg</b><extra></extra>",
        ), row=1, col=1)

        fig_layout(fig_vs2,
            height=500,
            legend=dict(orientation="h", y=1.08, x=0),
            margin=dict(t=35, b=10, l=5, r=10),
        )

        # Eixo X: painel superior sem rótulos, inferior com rótulos das semanas
        fig_vs2.update_layout(
            xaxis=dict(
                showgrid=False, zeroline=False,
                tickcolor=TXT_S, linecolor=BORDER,
                showticklabels=False,
            ),
            xaxis2=dict(
                showgrid=False, zeroline=False,
                tickcolor=TXT_S, linecolor=BORDER,
                tickfont=dict(color=TXT_S, size=9),
            ),
        )

        # Eixo Y: painel superior (Kg/Cliente) e inferior (Kilos)
        fig_vs2.update_yaxes(
            title_text="Kg / Cliente", row=1, col=1,
            gridcolor=GRID, tickfont=dict(color=C_CYAN),
            title_font=dict(color=C_CYAN),
        )
        fig_vs2.update_yaxes(
            title_text="Kilos (kg)", row=2, col=1,
            gridcolor=GRID, tickfont=dict(color=TXT_S),
            title_font=dict(color=TXT_S),
        )

        st.plotly_chart(fig_vs2, use_container_width=True)
        def _ctx_vs():
            return build_ai_context("semanal", "Volume por Semana — Kg e Kg/Cliente",
                                    df, df_base, df_raw)
        _ia_button("Volume por Semana — Kg e Kg/Cliente",
                   _ctx_vs, "ia_btn_vol_sem", analysis_type="semanal")

        tbl_vs = vol_sem[["semana_label","date_range","kilos","caixas","unidades",
                           "n_clientes","n_pedidos","n_notas","kg_por_cliente","kg_por_nota"]].copy()
        tbl_vs["kilos"]         = tbl_vs["kilos"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vs["kg_por_cliente"]= tbl_vs["kg_por_cliente"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vs["kg_por_nota"]   = tbl_vs["kg_por_nota"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vs = tbl_vs.rename(columns={
            "semana_label":"Semana","date_range":"Período","kilos":"Kilos",
            "n_clientes":"Clientes","n_pedidos":"Pedidos","n_notas":"Notas",
            "kg_por_cliente":"Kg/Cliente","kg_por_nota":"Kg/Nota",
        })
        st.dataframe(tbl_vs[["Semana","Período","Kilos","Clientes","Pedidos","Notas","Kg/Cliente","Kg/Nota"]],
                     height=300, hide_index=True, use_container_width=True)

    # ── TAB 4: POR NOTA ───────────────────────────────────────────────────────────
    with tab_vol_nota:
        vol_nota = (
            df.groupby(["numero_nota","nome_cliente","deposito","semana_label","semana_sort",
                        "pedido_clean","tem_pedido"])
            .agg(
                kilos   =("kilos",    "sum"),
                caixas  =("caixas",   "sum"),
                unidades=("unidades", "sum"),
            )
            .reset_index()
            .sort_values(["semana_sort","kilos"], ascending=[True, False])
        )
        vol_nota["Status"] = vol_nota["tem_pedido"].apply(
            lambda x: "✅ Com pedido" if x else "⚠️ Sem pedido"
        )
        vol_nota["Pedido"] = vol_nota.apply(
            lambda r: r["pedido_clean"] if r["tem_pedido"] else "—", axis=1
        )

        col_vn1, col_vn2 = st.columns([3, 3])
        with col_vn1:
            sem_vn_opts = sorted(vol_nota["semana_label"].unique())
            sem_vn_sel  = st.multiselect("Filtrar semanas", sem_vn_opts, key="vn_sem",
                                         placeholder="Todas as semanas…")
        with col_vn2:
            cli_vn_opts = ["Todos"] + sorted(vol_nota["nome_cliente"].unique())
            cli_vn_sel  = st.selectbox("Filtrar cliente", cli_vn_opts, key="vn_cli")

        vol_nota_show = vol_nota.copy()
        if sem_vn_sel:
            vol_nota_show = vol_nota_show[vol_nota_show["semana_label"].isin(sem_vn_sel)]
        if cli_vn_sel != "Todos":
            vol_nota_show = vol_nota_show[vol_nota_show["nome_cliente"] == cli_vn_sel]

        # Bar chart top notes by kg
        top_n = vol_nota_show.head(40)
        cd_vn = top_n[["nome_cliente","semana_label","deposito","caixas","unidades","Status","Pedido"]].fillna("—").values.tolist()
        hover_vn = (
            "<b>Nota %{y}</b><br>"
            f"<span style='color:{TXT_S}'>👥 %{{customdata[0]}}  📅 %{{customdata[1]}}</span><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{x:,.1f}} kg</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  %{{customdata[3]:,.1f}} cx<br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  %{{customdata[4]:,.0f}} un<br>"
            f"<span style='color:{C_ORANGE}'>🏭 Depósito</span>  %{{customdata[2]}}<br>"
            f"<span style='color:{C_GREEN}'>📋 Status</span>  %{{customdata[5]}}  %{{customdata[6]}}"
            "<extra></extra>"
        )
        colors_vn = top_n["tem_pedido"].apply(lambda x: C_GREEN if x else C_AMBER).tolist()
        fig_vn = go.Figure(go.Bar(
            name="Algum Nome",
            x=top_n["kilos"], y=top_n["numero_nota"].astype(str),
            orientation="h",
            marker=dict(color=colors_vn, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
            text=top_n["kilos"].apply(fmt_peso),
            textposition="outside", textfont=dict(size=11, color=TXT_H),
            customdata=cd_vn, hovertemplate=hover_vn,
        ))
        fig_layout(fig_vn,
            title=dict(text="Top 40 Notas por Kilos  ·  verde = com pedido  ·  amarelo = sem pedido"),
            height=max(320, min(len(top_n) * 40, 900)),
            margin=dict(t=40, b=10, l=5, r=140),
            yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
            xaxis=dict(showgrid=True, gridcolor=GRID, title_text="Kilos (kg)",
                       title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
        )
        st.plotly_chart(fig_vn, use_container_width=True)

        tbl_vn = vol_nota_show.copy()
        tbl_vn["kilos"]  = tbl_vn["kilos"].apply(lambda v: fmt_br(v, 1) + " kg")
        tbl_vn["caixas"] = tbl_vn["caixas"].apply(lambda v: fmt_br(v, 1) + " cx")
        tbl_vn["unidades"] = tbl_vn["unidades"].apply(lambda v: fmt_br(v, 0) + " un")
        tbl_vn = tbl_vn.rename(columns={
            "numero_nota":"Nº Nota","nome_cliente":"Cliente","deposito":"Depósito",
            "semana_label":"Semana","kilos":"Kilos","caixas":"Caixas","unidades":"Unidades",
        })
        st.dataframe(tbl_vn[["Nº Nota","Cliente","Depósito","Semana","Status","Pedido","Kilos","Caixas","Unidades"]],
                     height=380, hide_index=True, use_container_width=True)


    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 8 — SITUAÇÃO NF + TRANSAÇÃO  (donut charts + design aprimorado)
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("📋", "Situação NF e Tipo de Transação")

    # ── helper: monta o hover completo como uma string HTML por fatia ─────────────
    # Plotly Pie NÃO suporta %{customdata[i]} multi-coluna de forma confiável:
    # arrays numpy são serializados como linha única, e format-specs (:,.1f) não
    # funcionam em traces Pie. Solução: uma única string HTML pré-montada por fatia,
    # acessada via %{customdata} sem índice.
    def _pie_customdata(grp_df, total_col="kilos"):
        grp_df = grp_df.copy()
        grp_df["kilos"]    = grp_df["kilos"].fillna(0)
        grp_df["caixas"]   = grp_df["caixas"].fillna(0)
        grp_df["unidades"] = grp_df["unidades"].fillna(0)
        tot = grp_df[total_col].sum()
        grp_df["pct_fmt"]  = grp_df[total_col].apply(
            lambda v: f"{v / tot * 100:.1f}%" if tot > 0 else "0,0%"
        )
        grp_df["cx_fmt"]   = grp_df["caixas"].apply(lambda v: fmt_br(v, 1) + " cx")
        grp_df["un_fmt"]   = grp_df["unidades"].apply(lambda v: fmt_br(v, 0) + " un")
        grp_df["kg_fmt"]   = grp_df["kilos"].apply(fmt_peso)
        grp_df["pct_val"]  = grp_df[total_col].apply(
            lambda v: round(v / tot * 100, 1) if tot > 0 else 0.0
        )
        # Uma string HTML completa por fatia — %{customdata} no hovertemplate
        grp_df["_hover_body"] = grp_df.apply(lambda r: (
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>{r['kg_fmt']}</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  {r['cx_fmt']}<br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  {r['un_fmt']}<br>"
            f"<span style='color:{C_VIOLET}'>📊 Participação</span>  <b>{r['pct_fmt']}</b>"
        ), axis=1)
        cd = grp_df["_hover_body"].tolist()
        return grp_df, cd

    col_s, col_t = st.columns(2)

    with col_s:
        sit_df = (
            df_base.groupby("situacao_NF")
            .agg(kilos=("kilos","sum"), unidades=("unidades","sum"), caixas=("caixas","sum"))
            .reset_index()
        )
        sit_df, cd_s = _pie_customdata(sit_df)

        # colour map by label value for stable assignment
        _sit_colors = {lb: c for lb, c in zip(
            sorted(sit_df["situacao_NF"].unique()),
            [C_CYAN, C_RED, C_AMBER, C_VIOLET, C_ORANGE, C_TEAL]
        )}
        sit_colors = [_sit_colors.get(lb, C_CYAN) for lb in sit_df["situacao_NF"]]

        # Formata labels da legenda com kg e %
        sit_legend_labels = [
            f"{row.situacao_NF}  ·  {row.kg_fmt}  ·  {row.pct_fmt}"
            for _, row in sit_df.iterrows()
        ]
        total_sit_kg = sit_df["kilos"].sum()
        fig_sit = go.Figure(go.Pie(
            labels=sit_legend_labels,
            values=sit_df["kilos"],
            hole=0.62,
            textposition="none",
            marker=dict(colors=sit_colors, line=dict(color=BG_APP, width=4)),
            pull=[0.06 if x in st.session_state.xf_situacao else 0 for x in sit_df["situacao_NF"]],
            customdata=cd_s,
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{customdata}"
                "<extra></extra>"
            ),
            sort=False,
            direction="clockwise",
        ))
        fig_sit.add_annotation(
            text=f"<b>{fmt_br(total_sit_kg, 1)}</b><br><span style='font-size:10px;color:{TXT_S}'>kg total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color=TXT_H, family="Montserrat, sans-serif"),
            align="center",
        )
        fig_layout(fig_sit,
            title=dict(text="Situação NF (por kilos)  ·  clique para filtrar",
                       font=dict(size=13, color=TXT_H)),
            height=460, margin=dict(t=50, b=120, l=20, r=20),
            showlegend=True,
            legend=dict(
                orientation="h", x=0.5, xanchor="center", y=-0.22,
                font=dict(color=TXT_M, size=11),
                bgcolor="rgba(0,0,0,0)",
                itemsizing="constant",
            ),
        )
        ev_sit = st.plotly_chart(fig_sit, use_container_width=True, on_select="rerun", key="chart_sit")
        if _handle_event(ev_sit, "xf_situacao", "label"):
            st.rerun()

        # Mini KPIs abaixo do gráfico
        sit_kpi_cols = st.columns(len(sit_df))
        for _col, (_, row) in zip(sit_kpi_cols, sit_df.iterrows()):
            _col.markdown(
                f"<div class='kpi-card' style='--accent:{_sit_colors.get(row.situacao_NF, C_CYAN)}'>"
                f"<div class='kpi-label' style='font-size:.6rem'>{row.situacao_NF.upper()}</div>"
                f"<div class='kpi-value' style='font-size:1.1rem'>{row.kg_fmt}</div>"
                f"<div class='kpi-sub'>{row.pct_fmt} · {row.cx_fmt}</div></div>",
                unsafe_allow_html=True,
            )

    with col_t:
        tra_df = (
            df_base.groupby("transacao_str")
            .agg(kilos=("kilos","sum"), unidades=("unidades","sum"), caixas=("caixas","sum"))
            .reset_index()
        )
        tra_df, cd_t = _pie_customdata(tra_df)
        _tra_palette = [C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN, C_CYAN, C_RED]
        tra_colors = [_tra_palette[i % len(_tra_palette)] for i in range(len(tra_df))]
        _tra_color_map = dict(zip(tra_df["transacao_str"], tra_colors))

        tra_legend_labels = [
            f"CFOP {row.transacao_str}  ·  {row.kg_fmt}  ·  {row.pct_fmt}"
            for _, row in tra_df.iterrows()
        ]
        total_tra_kg = tra_df["kilos"].sum()
        fig_tra = go.Figure(go.Pie(
            labels=tra_legend_labels,
            values=tra_df["kilos"],
            hole=0.62,
            textposition="none",
            marker=dict(colors=tra_colors, line=dict(color=BG_APP, width=4)),
            pull=[0.06 if x in st.session_state.xf_transacao else 0 for x in tra_df["transacao_str"]],
            customdata=cd_t,
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{customdata}"
                "<extra></extra>"
            ),
            sort=False,
            direction="clockwise",
        ))
        fig_tra.add_annotation(
            text=f"<b>{fmt_br(total_tra_kg, 1)}</b><br><span style='font-size:10px;color:{TXT_S}'>kg total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color=TXT_H, family="Montserrat, sans-serif"),
            align="center",
        )
        fig_layout(fig_tra,
            title=dict(text="Transação CFOP (por kilos)  ·  clique para filtrar",
                       font=dict(size=13, color=TXT_H)),
            height=460, margin=dict(t=50, b=120, l=20, r=20),
            showlegend=True,
            legend=dict(
                orientation="h", x=0.5, xanchor="center", y=-0.22,
                font=dict(color=TXT_M, size=11),
                bgcolor="rgba(0,0,0,0)",
                itemsizing="constant",
            ),
        )
        ev_tra = st.plotly_chart(fig_tra, use_container_width=True, on_select="rerun", key="chart_tra")
        if _handle_event(ev_tra, "xf_transacao", "label"):
            st.rerun()

        # Mini KPIs abaixo do gráfico
        tra_kpi_cols = st.columns(min(len(tra_df), 4))
        for _col, (_, row) in zip(tra_kpi_cols, tra_df.head(4).iterrows()):
            _col.markdown(
                f"<div class='kpi-card' style='--accent:{_tra_color_map.get(row.transacao_str, C_TEAL)}'>"
                f"<div class='kpi-label' style='font-size:.6rem'>CFOP {row.transacao_str}</div>"
                f"<div class='kpi-value' style='font-size:1.1rem'>{row.kg_fmt}</div>"
                f"<div class='kpi-sub'>{row.pct_fmt} · {row.cx_fmt}</div></div>",
                unsafe_allow_html=True,
            )



with tab_dados:
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 9 — TABELA DETALHADA
    # ═══════════════════════════════════════════════════════════════════════════════
    sec("📄", "Tabela Detalhada")

    agg = (
        df.groupby([
            "semana_label","semana_sort","date_range",
            "codigo_produto","nome_cliente",
            "situacao_NF","transacao_str","deposito",
        ])
        .agg(
            Kilos     =("kilos",             "sum"),
            Caixas    =("caixas",            "sum"),
            Unidades  =("unidades",          "sum"),
            Pedidos   =("pedido_clean",      lambda x: x[df.loc[x.index,"tem_pedido"]].nunique()),
            Descricao =("descricao_produto", "first"),
            Marca     =("MARCA",             "first"),
        )
        .reset_index()
        .sort_values(["semana_sort","Kilos"], ascending=[True, False])
    )
    agg["Kilos"]    = agg["Kilos"].round(1)
    agg["Caixas"]   = agg["Caixas"].round(1)
    agg["Unidades"] = agg["Unidades"].round(0).astype(int)

    srch = st.text_input("🔎 Buscar na tabela", placeholder="produto, cliente, depósito, semana…")
    tbl  = agg.copy()
    if srch:
        mask = tbl.apply(lambda row: srch.lower() in row.astype(str).str.lower().str.cat(), axis=1)
        tbl  = tbl[mask]

    tbl_final = tbl.rename(columns={
        "semana_label":   "Semana",
        "date_range":     "Período",
        "codigo_produto": "Código",
        "Descricao":      "Descrição",
        "Marca":          "Marca",
        "nome_cliente":   "Cliente",
        "situacao_NF":    "Situação NF",
        "transacao_str":  "CFOP",
        "deposito":       "Depósito",
    })
    tbl_final = tbl_final.loc[:, ~tbl_final.columns.duplicated()]
    tbl_final = tbl_final[[
        "Semana","Período","Depósito","Código","Descrição","Marca","Cliente",
        "Situação NF","CFOP","Kilos","Caixas","Unidades","Pedidos",
    ]]
    st.dataframe(tbl_final, height=420, hide_index=True, use_container_width=True)




# ── SIDEBAR FOOTER ────────────────────────────────────────────────────────────
st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)
st.sidebar.markdown(
    f"<div style='font-size:.72rem;color:{TXT_S};text-align:center;padding-top:4px;line-height:1.7'>"
    f"Dashboard de Faturamento v3<br>"
    f"<span style='color:{C_CYAN}'>{fmt_br(len(df_raw), 0)}</span> registros · "
    f"<span style='color:{C_TEAL}'>{df_raw['semana_sort'].nunique()}</span> semanas<br>"
    f"<span style='color:{C_AMBER}'>{df_raw['codigo_produto'].nunique()}</span> produtos · "
    f"<span style='color:{C_VIOLET}'>{df_raw['nome_cliente'].nunique()}</span> clientes"
    f"</div>",
    unsafe_allow_html=True,
)
