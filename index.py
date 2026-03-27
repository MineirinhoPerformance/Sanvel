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
</style>
""", unsafe_allow_html=True)


# ── PLOTLY DEFAULTS ──────────────────────────────────────────────────────────
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=BG_PLOT,
    font=dict(family="Inter, sans-serif", color=TXT_M, size=11),
    title_font=dict(family="Montserrat, sans-serif", color=TXT_H, size=13),
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
    """Formata peso: <1kg vira gramas"""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    
    if v < 1:
        return f"{v * 1000:,.0f} g"
    else:
        return f"{v:,.1f} kg"


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

    df["emissao"]      = pd.to_datetime(df["emissao"])
    df["ano"]          = df["emissao"].dt.year
    df["semana_sort"]  = df["ano"] * 100 + df["Numero_Semana"]
    df["semana_label"] = (
        "S" + df["Numero_Semana"].astype(str).str.zfill(2)
        + "/" + df["ano"].astype(str).str[-2:]
    )
    df["transacao_str"] = df["transacao_produto"].astype(str)
    df["codigo_str"]    = df["codigo_produto"].astype(str)
    df["prod_nome"] = df.apply(
        lambda r: f"{r['codigo_str']} – {r['descricao_produto']}"
        if pd.notna(r["descricao_produto"]) else r["codigo_str"],
        axis=1,
    )

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
def sec(icon, title):
    st.markdown(
        f'<div class="sec-header"><span>{icon}</span> {title}</div>',
        unsafe_allow_html=True,
    )


def prod_color_map(prods):
    return {p: PROD_COLORS[i % len(PROD_COLORS)] for i, p in enumerate(sorted(prods))}


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

st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)

# ── FILTRAGEM ─────────────────────────────────────────────────────────────────
df_base = df_raw[
    df_raw["situacao_NF"].isin(sit_sel)
    & df_raw["transacao_str"].isin(tra_sel)
    & df_raw["semana_sort"].between(sel_range[0], sel_range[1])
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
        f"**{len(df):,}** registros · "
        f"**{df['semana_sort'].nunique()}** semanas · "
        f"**{df['nome_cliente'].nunique()}** clientes · "
        f"**{df['codigo_produto'].nunique()}** produtos"
    )
with btn_col:
    if st.button("🗑️ Limpar\nFiltros", use_container_width=True, disabled=not any_xf):
        for k in ["xf_produto","xf_cliente","xf_situacao","xf_transacao","xf_semana"]:
            st.session_state[k] = set()
        st.session_state["fs_sit"]   = sit_opts
        st.session_state["fs_tra"]   = tra_opts
        st.session_state["fs_cli"]   = cli_opts
        st.session_state["fs_prod"]  = prod_opts
        st.session_state["fs_dep"]   = dep_opts
        st.session_state["fs_range"] = (semanas_disp[0], semanas_disp[-1])
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
    (C_CYAN,   "⚖️",  "TOTAL KILOS",       f"{fmt_br(total_kg, 1)} kg",       f"{fmt_br(avg_kg_sem, 1)} kg/sem média"),
    (C_TEAL,   "📦",  "TOTAL CAIXAS",       f"{fmt_br(total_cx, 1)} cx",       f"{fmt_br(total_cx/n_semanas, 1)} cx/sem" if n_semanas else ""),
    (C_AMBER,  "🔢",  "TOTAL UNIDADES",     f"{fmt_br(total_un, 0)} un",       f"{fmt_br(total_un/n_semanas, 0)} un/sem" if n_semanas else ""),
    (C_VIOLET, "🛒",  "PEDIDOS",            f"{n_pedidos:,}",                  f"{df['nome_cliente'].nunique()} clientes"),
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

st.markdown("<br>", unsafe_allow_html=True)


# ── COR POR DEPÓSITO ──────────────────────────────────────────────────────────
dep_list   = sorted(df_raw["deposito"].dropna().unique())
dep_colors = {d: c for d, c in zip(dep_list, [C_CYAN, C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN])}


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — ANÁLISE SEMANAL POR DEPÓSITO
# ═══════════════════════════════════════════════════════════════════════════════
sec("📅", "Análise Semanal por Depósito")

col_d1, col_d2 = st.columns([3, 7])
with col_d1:
    deps_disp = sorted(df_base["deposito"].dropna().unique())
    dep_sec1  = st.multiselect(
        "Filtrar por Depósito (nesta seção)",
        deps_disp, default=deps_disp, key="dep_sec1",
    )

df_sec1 = df_base[df_base["deposito"].isin(dep_sec1)] if dep_sec1 else df_base.copy()

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

tab_kg, tab_cx, tab_un = st.tabs(["⚖️ Kilos por Semana", "📦 Caixas por Semana", "🔢 Unidades por Semana"])


def chart_semanal_dep(metric, y_label, fmt):
    all_weeks  = sorted(df_sec1["semana_sort"].unique())
    all_labels = [lbl_map[w] for w in all_weeks]
    fig = go.Figure()
    for dep in sorted(weekly_dep["deposito"].unique()):
        sub = weekly_dep[weekly_dep["deposito"] == dep].sort_values("semana_sort")
        cd = sub.apply(lambda r: [
            r["date_range"],
            r["n_clientes"],
            fmt_peso(r["kilos"]),
            f"{r['caixas']:,.1f} cx",
            f"{r['unidades']:,.0f} un"
        ], axis=1).tolist()
        hover = (
            f"<b>%{{x}}</b>  <span style='color:{TXT_S}'>%{{customdata[0]}}</span><br>"
            f"<b>{dep}</b><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[2]}}</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[3]:,.1f}} cx</b><br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[4]:,.0f}} un</b><br>"
            f"<span style='color:{C_ORANGE}'>👥 Clientes</span>  %{{customdata[1]:.0f}}"
            "<extra></extra>"
        )
        fig.add_trace(go.Bar(
            x=sub["semana_label"], y=sub[metric],
            name=dep,
            marker=dict(color=dep_colors.get(dep, C_CYAN), opacity=0.85,
                        line=dict(color=BG_PLOT, width=0.5)),
            text=sub[metric].apply(fmt),
            textposition="outside", textfont=dict(size=12, color=TXT_H),
            customdata=cd, hovertemplate=hover,
        ))
    fig_layout(fig,
        height=420, barmode="group",
        legend=dict(orientation="h", y=1.08, x=0),
        margin=dict(t=35, b=10, l=5, r=10),
        xaxis=dict(
            type="category", categoryorder="array", categoryarray=all_labels,
            showgrid=False, tickfont=dict(color=TXT_S, size=9),
        ),
        yaxis=dict(showgrid=True, gridcolor=GRID, title_text=y_label,
                   title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
    )
    return fig


with tab_kg:
    ev_s1 = st.plotly_chart(
        chart_semanal_dep("kilos",    "Kilos (kg)",    fmt_peso),
        use_container_width=True, key="chart_s1_kg",
    )
with tab_cx:
    st.plotly_chart(
        chart_semanal_dep("caixas",   "Caixas (cx)",   lambda v: f"{v:,.1f} cx"),
        use_container_width=True, key="chart_s1_cx",
    )
with tab_un:
    st.plotly_chart(
        chart_semanal_dep("unidades", "Unidades (un)", lambda v: f"{v:,.0f} un"),
        use_container_width=True, key="chart_s1_un",
    )


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
weekly["delta_kg"]  = weekly["kilos"].diff().fillna(0)
weekly["delta_pct"] = (weekly["kilos"].pct_change().fillna(0) * 100).round(2)
weekly["bar_color"] = weekly["delta_kg"].apply(lambda v: C_CYAN if v >= 0 else C_RED)

cd_sem = weekly[["date_range","caixas","unidades","delta_kg","delta_pct","n_clientes","n_produtos"]].fillna(0).values.tolist()
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

fig_sem = make_subplots(specs=[[{"secondary_y": True}]])
fig_sem.data = []  # 🔥 limpa qualquer trace fantasma
fig_sem.add_trace(go.Bar(
    x=weekly["semana_label"], y=weekly["kilos"],
    name="Kilos",
    marker=dict(color=weekly["bar_color"], opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
    text=weekly["kilos"].apply(fmt_peso),
    textposition="outside", textfont=dict(size=9, color=TXT_M),
    customdata=cd_sem, hovertemplate=hover_sem,
), secondary_y=False)
fig_sem.add_trace(go.Scatter(
    x=weekly["semana_label"], y=weekly["delta_pct"],
    mode="lines+markers+text", name="Δ%",
    line=dict(color=C_AMBER, width=2),
    marker=dict(size=6, color=C_AMBER, line=dict(color=BG_PLOT, width=1)),
    text=weekly["delta_pct"].apply(lambda v: f"{v:+.1f}%"),
    textposition="top center", textfont=dict(size=9, color=C_AMBER),
    hovertemplate="<b>%{x}</b><br>Variação: <b>%{y:+.1f}%</b><extra></extra>",
), secondary_y=True)
fig_layout(fig_sem,
    height=410, hovermode="x unified",
    legend=dict(orientation="h", y=1.1, x=0),
    margin=dict(t=35, b=10, l=5, r=10),
    xaxis=dict(showgrid=False, tickfont=dict(color=TXT_S, size=9)),
)
fig_sem.update_yaxes(
    title_text="Kilos (kg)", secondary_y=False,
    ticksuffix=" kg", gridcolor=GRID, tickfont=dict(color=TXT_S),
    title_font=dict(color=TXT_S), zeroline=False,
)
fig_sem.update_yaxes(
    title_text="Variação %", secondary_y=True,
    ticksuffix="%", showgrid=False, tickfont=dict(color=C_AMBER),
    title_font=dict(color=C_AMBER), zeroline=True, zerolinecolor=TXT_S,
)
ev_sem = st.plotly_chart(fig_sem, use_container_width=True, on_select="rerun", key="chart_sem")


if _handle_event(ev_sem, "xf_semana", "x"):
    st.rerun()


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
    "caixas":   lambda v: f"{v:,.1f} cx",
    "unidades": lambda v: f"{v:,.0f} un",
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
    if _handle_event(ev_prod, "xf_produto", "y"):
        st.rerun()

with col_c:
    cli_stats = (
        df_base.groupby("nome_cliente")
        .agg(
            kilos    =("kilos",     "sum"),
            caixas   =("caixas",    "sum"),
            unidades =("unidades",  "sum"),
            n_pedidos=("pedido_clean", lambda x: x[df_base.loc[x.index,"tem_pedido"]].nunique()),
            semanas_ativas=("semana_sort","nunique"),
        )
        .reset_index().sort_values(metrica_rank, ascending=True)
    )
    cli_stats["color"] = cli_stats["nome_cliente"].apply(
        lambda x: C_AMBER if x in st.session_state.xf_cliente else C_TEAL
    )
    cd_c = cli_stats[["kilos","caixas","unidades","n_pedidos","semanas_ativas"]].fillna(0).values.tolist()
    hover_c = (
        "<b>%{y}</b><br>"
        f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[0]:,.1f}} kg</b><br>"
        f"<span style='color:{C_TEAL}'>📦 Caixas</span>  <b>%{{customdata[1]:,.1f}} cx</b><br>"
        f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  <b>%{{customdata[2]:,.0f}} un</b><br>"
        f"<span style='color:{C_VIOLET}'>🛒 Pedidos</span>  %{{customdata[3]:.0f}}<br>"
        f"<span style='color:{C_GREEN}'>📅 Semanas ativas</span>  %{{customdata[4]:.0f}}"
        "<extra></extra>"
    )
    fig_cli = go.Figure(go.Bar(
        name="Algum Nome",
        x=cli_stats[metrica_rank], y=cli_stats["nome_cliente"],
        orientation="h",
        marker=dict(color=cli_stats["color"], line=dict(color=BG_PLOT, width=0.5)),
        text=cli_stats[metrica_rank].apply(met_fmt_rank), textposition="outside",
        textfont=dict(size=10, color=TXT_H),
        customdata=cd_c, hovertemplate=hover_c,
    ))
    fig_layout(fig_cli,
        title=dict(text="Por Cliente  ·  clique para filtrar"),
        height=max(300, len(cli_stats) * 52),
        margin=dict(t=40, b=10, l=5, r=120),
        yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
        xaxis=dict(showgrid=True, gridcolor=GRID),
    )
    ev_cli = st.plotly_chart(fig_cli, use_container_width=True, on_select="rerun", key="chart_cli")
    if _handle_event(ev_cli, "xf_cliente", "y"):
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — EVOLUÇÃO SEMANAL POR PRODUTO
# ═══════════════════════════════════════════════════════════════════════════════
sec("📉", "Evolução Semanal por Produto")

tab_ev1, tab_ev2, tab_ev3 = st.tabs(["⚖️ Kilos", "📦 Caixas", "🔢 Unidades"])


def evolution_lines(metric_col, fmt_fn, y_title):
    prod_wk = (
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
    prods = sorted(prod_wk["prod_nome"].unique())
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
    all_wk = df[["semana_sort","semana_label"]].drop_duplicates().sort_values("semana_sort")["semana_label"].tolist()
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
    st.plotly_chart(evolution_lines("kilos",    lambda v: f"{v:,.1f}kg",  "Kilos (kg)"),    use_container_width=True)
with tab_ev2:
    st.plotly_chart(evolution_lines("caixas",   lambda v: f"{v:,.1f}cx",  "Caixas (cx)"),   use_container_width=True)
with tab_ev3:
    st.plotly_chart(evolution_lines("unidades", lambda v: f"{v:,.0f}un",  "Unidades (un)"), use_container_width=True)


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
    text=pedidos_cli["n_pedidos"].apply(lambda v: f"{v:.0f} pedidos"),
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

# ── TRANSPARÊNCIA DE NOTAS ────────────────────────────────────────────────────
n_com_ped  = df_base["tem_pedido"].sum()
n_sem_ped  = (~df_base["tem_pedido"]).sum()
pct_com    = n_com_ped / len(df_base) * 100 if len(df_base) else 0

col_np1, col_np2, col_np3 = st.columns(3)
col_np1.markdown(
    f"<div class='kpi-card' style='--accent:{C_GREEN}'>"
    f"<div class='kpi-label'>NOTAS COM PEDIDO</div>"
    f"<div class='kpi-value' style='font-size:1.4rem'>{n_com_ped:,}</div>"
    f"<div class='kpi-sub'>{pct_com:.1f}% do total</div></div>",
    unsafe_allow_html=True,
)
col_np2.markdown(
    f"<div class='kpi-card' style='--accent:{C_AMBER}'>"
    f"<div class='kpi-label'>NOTAS SEM PEDIDO</div>"
    f"<div class='kpi-value' style='font-size:1.4rem'>{n_sem_ped:,}</div>"
    f"<div class='kpi-sub'>{100-pct_com:.1f}% do total</div></div>",
    unsafe_allow_html=True,
)
col_np3.markdown(
    f"<div class='kpi-card' style='--accent:{C_VIOLET}'>"
    f"<div class='kpi-label'>PEDIDOS ÚNICOS</div>"
    f"<div class='kpi-value' style='font-size:1.4rem'>{df_base[df_base['tem_pedido']]['pedido_clean'].nunique():,}</div>"
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
        f"<b>{total_notas}</b> notas em {datas_label} · "
        f"<span style='color:{C_GREEN}'><b>{com_ped_dia}</b> com pedido</span> · "
        f"<span style='color:{C_AMBER}'><b>{sem_ped_dia}</b> sem número de pedido</span></div>",
        unsafe_allow_html=True,
    )
    st.dataframe(tbl_notas, height=350, hide_index=True, use_container_width=True)

    if sem_ped_dia > 0:
        st.markdown(
            f"<div style='font-size:.78rem;color:{C_AMBER};margin-top:8px'>"
            f"ℹ️ As <b>{sem_ped_dia}</b> nota(s) sem número de pedido podem ter sido emitidas "
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
        f"ℹ️ <b>{n_notas_sem_ped_total}</b> nota(s) sem número de pedido não foram incluídas "
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
        text=dist_resumo["media_dias"].apply(lambda v: f"{v:.1f} dias"),
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
    vol_sem = (
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

    fig_vs = go.Figure(go.Bar(
        name="Algum Nome",
        x=vol_sem["semana_label"], y=vol_sem["kilos"],
        marker=dict(color=C_AMBER, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
        text=vol_sem["kilos"].apply(fmt_peso),
        textposition="outside", textfont=dict(size=11, color=TXT_H),
        customdata=cd_vs, hovertemplate=hover_vs,
    ))
    # Overlay kg/cliente line
    fig_vs2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig_vs2.add_trace(go.Bar(
        x=vol_sem["semana_label"], y=vol_sem["kilos"], name="Total Kg",
        marker=dict(color=C_AMBER, opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
        text=vol_sem["kilos"].apply(lambda v: f"{v:,.1f}"),
        textposition="outside", textfont=dict(size=11, color=TXT_H),
        customdata=cd_vs, hovertemplate=hover_vs,
    ), secondary_y=False)
    fig_vs2.add_trace(go.Scatter(
        x=vol_sem["semana_label"], y=vol_sem["kg_por_cliente"],
        mode="lines+markers+text", name="Kg/Cliente",
        line=dict(color=C_CYAN, width=2),
        marker=dict(size=6, color=C_CYAN),
        text=vol_sem["kg_por_cliente"].apply(lambda v: f"{v:,.0f}"),
        textposition="top center", textfont=dict(size=9, color=C_CYAN),
        hovertemplate="<b>%{x}</b><br>Kg/Cliente: <b>%{y:,.1f} kg</b><extra></extra>",
    ), secondary_y=True)
    for _t in fig_vs2.data:
        if not _t.name:
            _t.update(showlegend=False)
    fig_layout(fig_vs2,
        height=420, barmode="group",
        legend=dict(orientation="h", y=1.1, x=0),
        margin=dict(t=35, b=10, l=5, r=10),
        xaxis=dict(showgrid=False, tickfont=dict(color=TXT_S, size=9)),
    )
    fig_vs2.update_yaxes(title_text="Kilos (kg)", secondary_y=False,
                         gridcolor=GRID, tickfont=dict(color=TXT_S))
    fig_vs2.update_yaxes(title_text="Kg / Cliente", secondary_y=True,
                         showgrid=False, tickfont=dict(color=C_CYAN))
    st.plotly_chart(fig_vs2, use_container_width=True)

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

# ── helper: pre-format customdata to avoid NaN / literal variable-name bug ────
def _pie_customdata(grp_df, total_col="kilos"):
    grp_df = grp_df.copy()
    grp_df["kilos"]    = grp_df["kilos"].fillna(0)
    grp_df["caixas"]   = grp_df["caixas"].fillna(0)
    grp_df["unidades"] = grp_df["unidades"].fillna(0)
    tot = grp_df[total_col].sum()
    grp_df["pct_fmt"]  = grp_df[total_col].apply(
        lambda v: f"{v / tot * 100:.1f}%" if tot > 0 else "0.0%"
    )
    grp_df["cx_fmt"]   = grp_df["caixas"].apply(lambda v: f"{v:,.1f} cx")
    grp_df["un_fmt"]   = grp_df["unidades"].apply(lambda v: f"{v:,.0f} un")
    grp_df["kg_fmt"]   = grp_df["kilos"].apply(fmt_peso)
    return grp_df, grp_df[["kg_fmt","cx_fmt","un_fmt","pct_fmt"]].values.tolist()

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

    fig_sit = go.Figure(go.Pie(
        labels=sit_df["situacao_NF"],
        values=sit_df["kilos"],
        hole=0.55,
        texttemplate="<b>%{label}</b><br>%{customdata[0]}<br>%{customdata[3]}",
        textfont=dict(size=12, color=TXT_H),
        textposition="outside",
        marker=dict(colors=sit_colors, line=dict(color=BG_APP, width=4)),
        pull=[0.06 if x in st.session_state.xf_situacao else 0 for x in sit_df["situacao_NF"]],
        customdata=cd_s,
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[0]}}</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  %{{customdata[1]}}<br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  %{{customdata[2]}}<br>"
            f"<span style='color:{C_VIOLET}'>📊 Participação</span>  <b>%{{customdata[3]}}</b>"
            "<extra></extra>"
        ),
        sort=False,
    ))
    # Annotation centro do donut
    total_sit_kg = sit_df["kilos"].sum()
    fig_sit.add_annotation(
        text=f"<b>{total_sit_kg:,.0f}</b><br><span style='font-size:10px'>kg total</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=TXT_H, family="Montserrat, sans-serif"),
        align="center",
    )
    fig_layout(fig_sit,
        title=dict(text="Situação NF (por kilos)  ·  clique para filtrar",
                   font=dict(size=13, color=TXT_H)),
        height=380, margin=dict(t=45, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5,
                    font=dict(color=TXT_M, size=11)),
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

    fig_tra = go.Figure(go.Pie(
        labels=tra_df["transacao_str"],
        values=tra_df["kilos"],
        hole=0.55,
        texttemplate="<b>CFOP %{label}</b><br>%{customdata[0]}<br>%{customdata[3]}",
        textfont=dict(size=11, color=TXT_H),
        textposition="outside",
        marker=dict(colors=tra_colors, line=dict(color=BG_APP, width=4)),
        pull=[0.06 if x in st.session_state.xf_transacao else 0 for x in tra_df["transacao_str"]],
        customdata=cd_t,
        hovertemplate=(
            "<b>CFOP %{label}</b><br>"
            f"<span style='color:{C_CYAN}'>⚖️ Kilos</span>  <b>%{{customdata[0]}}</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Caixas</span>  %{{customdata[1]}}<br>"
            f"<span style='color:{C_AMBER}'>🔢 Unidades</span>  %{{customdata[2]}}<br>"
            f"<span style='color:{C_VIOLET}'>📊 Participação</span>  <b>%{{customdata[3]}}</b>"
            "<extra></extra>"
        ),
        sort=False,
    ))
    total_tra_kg = tra_df["kilos"].sum()
    fig_tra.add_annotation(
        text=f"<b>{total_tra_kg:,.0f}</b><br><span style='font-size:10px'>kg total</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=TXT_H, family="Montserrat, sans-serif"),
        align="center",
    )
    fig_layout(fig_tra,
        title=dict(text="Transação CFOP (por kilos)  ·  clique para filtrar",
                   font=dict(size=13, color=TXT_H)),
        height=380, margin=dict(t=45, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5,
                    font=dict(color=TXT_M, size=11)),
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


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 9 — TABELA DETALHADA
# ═══════════════════════════════════════════════════════════════════════════════
sec("📄", "Tabela Detalhada")

agg = (
    df.groupby([
        "semana_label","semana_sort","date_range",
        "codigo_produto","prod_nome","nome_cliente",
        "situacao_NF","transacao_str","deposito",
    ])
    .agg(
        Kilos    =("kilos",        "sum"),
        Caixas   =("caixas",       "sum"),
        Unidades =("unidades",     "sum"),
        Pedidos  =("pedido_clean", lambda x: x[df.loc[x.index,"tem_pedido"]].nunique()),
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
    "prod_nome":      "Produto",
    "nome_cliente":   "Cliente",
    "situacao_NF":    "Situação NF",
    "transacao_str":  "CFOP",
    "deposito":       "Depósito",
})
tbl_final = tbl_final.loc[:, ~tbl_final.columns.duplicated()]
tbl_final = tbl_final[[
    "Semana","Período","Depósito","Código","Produto","Cliente",
    "Situação NF","CFOP","Kilos","Caixas","Unidades","Pedidos",
]]
st.dataframe(tbl_final, height=420, hide_index=True, use_container_width=True)


# ── SIDEBAR FOOTER ────────────────────────────────────────────────────────────
st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)
st.sidebar.markdown(
    f"<div style='font-size:.72rem;color:{TXT_S};text-align:center;padding-top:4px;line-height:1.7'>"
    f"Dashboard de Faturamento v3<br>"
    f"<span style='color:{C_CYAN}'>{len(df_raw):,}</span> registros · "
    f"<span style='color:{C_TEAL}'>{df_raw['semana_sort'].nunique()}</span> semanas<br>"
    f"<span style='color:{C_AMBER}'>{df_raw['codigo_produto'].nunique()}</span> produtos · "
    f"<span style='color:{C_VIOLET}'>{df_raw['nome_cliente'].nunique()}</span> clientes"
    f"</div>",
    unsafe_allow_html=True,
)
