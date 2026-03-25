"""
Dashboard de Faturamento Semanal  — Tema Escuro
• Tema dark elegante em todo o relatório
• Códigos de produto individuais preservados
• Datas reais por semana em todos os popups
• Tooltips ricos com informações detalhadas
• Cross-filter por clique em qualquer visual
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Faturamento Semanal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PALETA DARK ───────────────────────────────────────────────────────────────
BG_APP    = "#080E1C"          # fundo geral
BG_CARD   = "#0F1929"          # cartões / painéis
BG_PLOT   = "#0B1220"          # fundo dos gráficos
BG_SIDEBAR= "#060C18"          # sidebar
BORDER    = "#1A2E50"          # bordas sutis

C_CYAN    = "#38BDF8"          # destaque principal
C_TEAL    = "#2DD4BF"          # destaque secundário
C_GREEN   = "#4ADE80"          # positivo
C_RED     = "#F87171"          # negativo
C_AMBER   = "#FBBF24"          # alerta / seleção
C_VIOLET  = "#A78BFA"          # terciário
C_ORANGE  = "#FB923C"          # quaternário

TXT_H     = "#F1F5F9"          # títulos
TXT_M     = "#CBD5E1"          # texto médio
TXT_S     = "#64748B"          # texto suave / labels
GRID      = "#1E3A5F"          # linhas de grade

# cores para produtos (7 produtos únicos)
PROD_COLORS = [C_CYAN, C_TEAL, C_AMBER, C_VIOLET, C_ORANGE, C_GREEN, "#EC4899"]

# ── FONT + CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"],
[data-testid="stHeader"], .main, .block-container {{
    background-color: {BG_APP} !important;
    color: {TXT_M};
    font-family: 'DM Sans', sans-serif;
}}
h1,h2,h3,h4 {{ font-family: 'Syne', sans-serif; color: {TXT_H}; }}

[data-testid="stSidebar"] > div:first-child {{
    background: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: {TXT_M} !important; }}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background: {C_CYAN}22 !important; border: 1px solid {C_CYAN}55 !important;
    color: {C_CYAN} !important;
}}
[data-testid="stSidebar"] .stSelectSlider, [data-testid="stSidebar"] .stRadio {{
    color: {TXT_M} !important;
}}

/* tabs */
[data-testid="stTabs"] [role="tab"] {{
    background: transparent; color: {TXT_S}; border-bottom: 2px solid transparent;
    font-family: 'DM Sans', sans-serif; font-weight: 500;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {C_CYAN}; border-bottom: 2px solid {C_CYAN};
}}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {{
    background: transparent !important;
}}

/* dataframe */
[data-testid="stDataFrame"] {{ background: {BG_CARD}; border-radius: 12px; }}
[data-testid="stDataFrame"] th {{
    background: {BG_SIDEBAR} !important; color: {C_CYAN} !important;
    font-family: 'Syne', sans-serif; font-size: .78rem; letter-spacing: .05em;
}}
[data-testid="stDataFrame"] td {{ color: {TXT_M} !important; }}
[data-testid="stDataFrame"] tr:hover td {{ background: {BORDER} !important; }}

/* inputs */
[data-testid="stTextInput"] input {{
    background: {BG_CARD} !important; color: {TXT_M} !important;
    border: 1px solid {BORDER} !important; border-radius: 8px;
}}
[data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div {{
    background: {BG_CARD} !important; color: {TXT_M} !important;
}}

/* KPI cards */
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
    font-size: .7rem; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; color: {TXT_S}; margin-bottom: 6px;
}}
.kpi-value {{
    font-family: 'Syne', sans-serif;
    font-size: 1.9rem; font-weight: 800; color: {TXT_H};
    line-height: 1.1;
}}
.kpi-delta {{
    font-size: .8rem; font-weight: 600; margin-top: 8px;
    padding: 3px 8px; border-radius: 20px; display: inline-block;
}}
.delta-pos {{ background: {C_GREEN}18; color: {C_GREEN}; }}
.delta-neg {{ background: {C_RED}18; color: {C_RED}; }}
.delta-neu {{ background: {TXT_S}18; color: {TXT_S}; }}

/* section headers */
.sec-header {{
    font-family: 'Syne', sans-serif;
    font-size: 1rem; font-weight: 700; color: {TXT_H};
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0 8px;
    border-bottom: 1px solid {BORDER};
    margin: 28px 0 14px;
}}
.sec-header span {{ color: {C_CYAN}; }}

/* filter pills */
.pill {{
    display: inline-block;
    background: {C_CYAN}18; border: 1px solid {C_CYAN}40;
    color: {C_CYAN}; border-radius: 20px;
    padding: 3px 12px; font-size: .75rem;
    margin: 2px 4px; font-weight: 600;
}}
.tip {{ font-size: .76rem; color: {TXT_S}; font-style: italic; margin: 4px 0 12px; }}

/* button */
[data-testid="stButton"] > button {{
    background: {BORDER}; color: {TXT_M};
    border: 1px solid {BORDER}; border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    transition: all .2s;
}}
[data-testid="stButton"] > button:hover {{
    background: {C_CYAN}22; border-color: {C_CYAN}55; color: {C_CYAN};
}}

/* caption / small */
[data-testid="stCaptionContainer"] {{ color: {TXT_S}; }}
small {{ color: {TXT_S}; }}
</style>
""", unsafe_allow_html=True)


# ── PLOTLY DARK DEFAULTS ──────────────────────────────────────────────────────
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=BG_PLOT,
    font=dict(family="DM Sans, sans-serif", color=TXT_M, size=11),
    title_font=dict(family="Syne, sans-serif", color=TXT_H, size=13),
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
        font=dict(family="DM Sans, sans-serif", color=TXT_H, size=12),
    ),
    margin=dict(t=45, b=10, l=10, r=10),
)


def fig_layout(fig, **extra):
    d = {**LAYOUT_BASE, **extra}
    fig.update_layout(**d)
    return fig


# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [
    ("xf_produto", set()), ("xf_cliente", set()),
    ("xf_situacao", set()), ("xf_transacao", set()), ("xf_semana", set()),
]:
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
def load_data(file):
    df = pd.read_excel(file)
    df["emissao"]     = pd.to_datetime(df["emissao"])
    df["ano"]         = df["emissao"].dt.year
    df["semana_sort"] = df["ano"] * 100 + df["Numero_Semana"]
    df["semana_label"]= (
        "S" + df["Numero_Semana"].astype(str).str.zfill(2)
        + "/" + df["ano"].astype(str).str[-2:]
    )
    df["transacao_str"] = df["transacao_produto"].astype(str)
    df["codigo_str"]    = df["codigo_produto"].astype(str)
    # nome do produto: código + descrição quando disponível
    df["prod_nome"] = df.apply(
        lambda r: f"{r['codigo_str']} – {r['descricao_produto']}"
        if pd.notna(r["descricao_produto"]) else r["codigo_str"],
        axis=1,
    )
    # mapa semana → range de datas
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
    return df, wk_map


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    f"<div style='font-family:Syne,sans-serif;font-size:1.15rem;"
    f"font-weight:800;color:{TXT_H};padding:12px 0 4px;letter-spacing:.04em'>"
    f"📊 FATURAMENTO</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:6px 0 14px'>", unsafe_allow_html=True)

uploaded = st.sidebar.file_uploader("Carregar planilha (.xlsx)", type=["xlsx"])
if not uploaded:
    st.markdown(
        f"<div style='text-align:center;padding:80px 20px;"
        f"color:{TXT_S};font-family:DM Sans,sans-serif'>"
        f"<div style='font-size:3rem'>📂</div>"
        f"<div style='font-family:Syne,sans-serif;font-size:1.4rem;"
        f"font-weight:700;color:{TXT_H};margin:12px 0 8px'>Dashboard de Faturamento</div>"
        f"<div>Faça upload da planilha <b style='color:{C_CYAN}'>Base.xlsx</b> na barra lateral</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.stop()

df_raw, wk_map = load_data(uploaded)

st.sidebar.markdown(f"<div style='font-size:.8rem;font-weight:600;color:{C_CYAN};letter-spacing:.06em;margin-bottom:8px'>🔍 FILTROS GLOBAIS</div>", unsafe_allow_html=True)

sit_opts = sorted(df_raw["situacao_NF"].dropna().unique())
sit_sel  = st.sidebar.multiselect("Situação NF",       sit_opts, default=sit_opts)

tra_opts = sorted(df_raw["transacao_str"].dropna().unique())
tra_sel  = st.sidebar.multiselect("Transação Produto", tra_opts, default=tra_opts)

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
)

cli_opts = sorted(df_raw["nome_cliente"].dropna().unique())
cli_sel  = st.sidebar.multiselect("Clientes", cli_opts, default=cli_opts)

prod_opts = sorted(df_raw["prod_nome"].dropna().unique())
prod_sel  = st.sidebar.multiselect("Produtos", prod_opts, default=prod_opts)

st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)
metrica = st.sidebar.radio(
    "Métrica principal",
    ["valor_bruto", "unid_faturado"],
    format_func=lambda x: "💰 Valor Bruto (R$)" if x == "valor_bruto" else "📦 Unidades Faturadas",
)
met_label = "Valor Bruto (R$)" if metrica == "valor_bruto" else "Unidades"
met_fmt   = (lambda v: f"R$ {v:,.2f}") if metrica == "valor_bruto" else (lambda v: f"{v:,.0f} un")


# ── FILTRAGEM ─────────────────────────────────────────────────────────────────
df_base = df_raw[
    df_raw["situacao_NF"].isin(sit_sel)
    & df_raw["transacao_str"].isin(tra_sel)
    & df_raw["semana_sort"].between(sel_range[0], sel_range[1])
    & df_raw["nome_cliente"].isin(cli_sel)
    & df_raw["prod_nome"].isin(prod_sel)
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
])


# ── HEADER ────────────────────────────────────────────────────────────────────
h_col, btn_col = st.columns([8, 1])
with h_col:
    st.markdown(
        f"<h2 style='font-family:Syne,sans-serif;color:{TXT_H};"
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
    f'<p class="tip">💡 Clique em qualquer barra, ponto ou fatia para filtrar todo o relatório. '
    f'Passe o mouse para detalhes completos. Clique novamente para desfiltrar.</p>',
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("Nenhum dado com os filtros ativos.")
    st.stop()


# ── KPIs ──────────────────────────────────────────────────────────────────────
wk_totals = (
    df_base.groupby("semana_sort")[["valor_bruto","unid_faturado"]]
    .sum().reset_index().sort_values("semana_sort")
)
last_vb   = wk_totals["valor_bruto"].iloc[-1]   if len(wk_totals) else 0
prev_vb   = wk_totals["valor_bruto"].iloc[-2]   if len(wk_totals) > 1 else 0
last_un   = wk_totals["unid_faturado"].iloc[-1] if len(wk_totals) else 0
prev_un   = wk_totals["unid_faturado"].iloc[-2] if len(wk_totals) > 1 else 0

total_vb   = df["valor_bruto"].sum()
total_unid = df["unid_faturado"].sum()
total_nf   = df["numero_nota"].nunique()
ticket_med = total_vb / total_nf if total_nf else 0
avg_week   = total_vb / df["semana_sort"].nunique() if df["semana_sort"].nunique() else 0


def delta_badge(cur, ref):
    if not ref:
        return ""
    pct = (cur - ref) / abs(ref) * 100
    if pct > 0:
        return f'<span class="kpi-delta delta-pos">▲ {pct:.1f}%</span>'
    elif pct < 0:
        return f'<span class="kpi-delta delta-neg">▼ {abs(pct):.1f}%</span>'
    return f'<span class="kpi-delta delta-neu">→ 0.0%</span>'


kpis = [
    (C_CYAN,   "💰", "VALOR BRUTO TOTAL",      f"R$ {total_vb:,.2f}",   delta_badge(last_vb, prev_vb)),
    (C_TEAL,   "📦", "UNIDADES FATURADAS",      f"{total_unid:,.0f}",    delta_badge(last_un, prev_un)),
    (C_AMBER,  "🧾", "NOTAS FISCAIS",           f"{total_nf:,}",         ""),
    (C_VIOLET, "🎯", "TICKET MÉDIO / NF",       f"R$ {ticket_med:,.2f}", ""),
    (C_ORANGE, "📅", "MÉDIA SEMANAL",           f"R$ {avg_week:,.2f}",   ""),
]
cols_kpi = st.columns(5)
for col, (accent, icon, label, val, delta) in zip(cols_kpi, kpis):
    col.markdown(
        f"""<div class="kpi-card" style="--accent:{accent}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{val}</div>
          {delta}</div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def sec(icon, title):
    st.markdown(
        f'<div class="sec-header"><span>{icon}</span> {title}</div>',
        unsafe_allow_html=True,
    )


def prod_color_map(prods):
    return {p: PROD_COLORS[i % len(PROD_COLORS)] for i, p in enumerate(sorted(prods))}


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — ANÁLISE DE INCREMENTO
# ═══════════════════════════════════════════════════════════════════════════════
sec("📈", "Análise de Incremento — Compare Semanas")

semana_df = (
    df_base[["semana_sort","semana_label","date_range"]]
    .drop_duplicates().sort_values("semana_sort")
)
s_labels    = semana_df["semana_label"].tolist()
s_sorts     = semana_df["semana_sort"].tolist()
s_daterange = semana_df["date_range"].tolist()

if len(s_labels) >= 2:
    ic1, ic2, ic3 = st.columns([2, 2, 3])
    with ic1:
        b_idx = st.selectbox("📅 Semana Base", range(len(s_labels)),
                             format_func=lambda i: f"{s_labels[i]}  ({s_daterange[i]})",
                             index=max(0, len(s_labels)-2))
    with ic2:
        c_idx = st.selectbox("📅 Semana Comparação", range(len(s_labels)),
                             format_func=lambda i: f"{s_labels[i]}  ({s_daterange[i]})",
                             index=len(s_labels)-1)

    b_sort, c_sort = s_sorts[b_idx], s_sorts[c_idx]
    b_lbl,  c_lbl  = s_labels[b_idx], s_labels[c_idx]
    b_dr,   c_dr   = s_daterange[b_idx], s_daterange[c_idx]

    df_bwk = df_base[df_base["semana_sort"] == b_sort]
    df_cwk = df_base[df_base["semana_sort"] == c_sort]

    vb_b = df_bwk["valor_bruto"].sum(); vb_c = df_cwk["valor_bruto"].sum()
    un_b = df_bwk["unid_faturado"].sum(); un_c = df_cwk["unid_faturado"].sum()
    nf_b = df_bwk["numero_nota"].nunique(); nf_c = df_cwk["numero_nota"].nunique()
    dvb  = vb_c - vb_b; dun = un_c - un_b
    pvb  = dvb / vb_b * 100 if vb_b else 0
    pun  = dun / un_b * 100 if un_b else 0

    with ic3:
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Δ Valor  {b_lbl}→{c_lbl}", f"R$ {dvb:+,.2f}", f"{pvb:+.1f}%")
        m2.metric(f"Δ Unidades", f"{dun:+,.0f}", f"{pun:+.1f}%")
        m3.metric("Δ NFs", f"{nf_c - nf_b:+,}", f"{nf_c} vs {nf_b}")

    def inc_table(dim):
        gb_b = df_bwk.groupby(dim).agg(
            vb_b=("valor_bruto","sum"), un_b=("unid_faturado","sum"),
            nf_b=("numero_nota","nunique"), preco_b=("preco_unitario","mean"),
        )
        gb_c = df_cwk.groupby(dim).agg(
            vb_c=("valor_bruto","sum"), un_c=("unid_faturado","sum"),
            nf_c=("numero_nota","nunique"), preco_c=("preco_unitario","mean"),
        )
        m = gb_b.join(gb_c, how="outer").fillna(0)
        m["delta_vb"]   = m["vb_c"]   - m["vb_b"]
        m["delta_un"]   = m["un_c"]   - m["un_b"]
        m["pct_vb"]     = m.apply(lambda r: r["delta_vb"]/r["vb_b"]*100 if r["vb_b"] else 0, axis=1).round(2)
        return m.reset_index()

    def diverging(data, dim_col, val_col, title, fmt_fn, custom_cols):
        data = data.sort_values(val_col)
        colors = [C_GREEN if v >= 0 else C_RED for v in data[val_col]]
        texts  = [(f"+{fmt_fn(v)}" if v >= 0 else fmt_fn(v)) for v in data[val_col]]
        # build customdata array
        cd = data[custom_cols].fillna(0).values.tolist()
        hover = (
            "<b>%{y}</b><br>"
            + f"<span style='color:{C_CYAN}'>Semana Base</span>  {b_lbl} · {b_dr}<br>"
            + f"<span style='color:{C_TEAL}'>Semana Comp.</span> {c_lbl} · {c_dr}<br>"
            + "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
            + f"<span style='color:{C_AMBER}'>Δ {title}</span>  <b>%{{x:+,.1f}}</b><br>"
            + "Base: %{customdata[0]:,.2f}  →  Comp: %{customdata[1]:,.2f}<br>"
            + "Var %: %{customdata[2]:+.1f}%<br>"
            + "NFs base: %{customdata[3]:.0f}  /  NFs comp: %{customdata[4]:.0f}"
            + "<extra></extra>"
        )
        fig = go.Figure(go.Bar(
            x=data[val_col], y=data[dim_col], orientation="h",
            marker=dict(color=colors, line=dict(color=BG_PLOT, width=0.5)),
            text=texts, textposition="outside",
            textfont=dict(size=11, color=TXT_H),
            customdata=cd, hovertemplate=hover,
        ))
        fig.add_vline(x=0, line_width=1.5, line_color=TXT_S)
        fig_layout(fig,
            title=dict(text=title, font=dict(size=12, color=TXT_H)),
            height=max(280, len(data)*44),
            margin=dict(t=40, b=10, l=5, r=110),
            yaxis=dict(type="category", showgrid=False, tickfont=dict(color=TXT_M, size=10)),
            xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False),
        )
        return fig

    inc_prod = inc_table("prod_nome")
    inc_cli  = inc_table("nome_cliente")

    tab_p, tab_c = st.tabs(["🏷️ Por Produto", "👤 Por Cliente"])
    with tab_p:
        a, b = st.columns(2)
        with a:
            st.plotly_chart(diverging(
                inc_prod,"prod_nome","delta_vb",f"Δ Valor Bruto R$  {b_lbl} → {c_lbl}",
                lambda v: f"R$ {v:,.0f}",
                ["vb_b","vb_c","pct_vb","nf_b","nf_c"],
            ), use_container_width=True)
        with b:
            st.plotly_chart(diverging(
                inc_prod,"prod_nome","delta_un",f"Δ Unidades  {b_lbl} → {c_lbl}",
                lambda v: f"{v:,.0f} un",
                ["un_b","un_c","pct_vb","nf_b","nf_c"],
            ), use_container_width=True)
    with tab_c:
        a, b = st.columns(2)
        with a:
            st.plotly_chart(diverging(
                inc_cli,"nome_cliente","delta_vb",f"Δ Valor Bruto R$  {b_lbl} → {c_lbl}",
                lambda v: f"R$ {v:,.2f}",
                ["vb_b","vb_c","pct_vb","nf_b","nf_c"],
            ), use_container_width=True)
        with b:
            st.plotly_chart(diverging(
                inc_cli,"nome_cliente","delta_un",f"Δ Unidades  {b_lbl} → {c_lbl}",
                lambda v: f"{v:,.0f} un",
                ["un_b","un_c","pct_vb","nf_b","nf_c"],
            ), use_container_width=True)
else:
    st.info("São necessárias ao menos 2 semanas para a análise de incremento.")


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — EVOLUÇÃO SEMANAL (clickable, barras coloridas + linha delta)
# ═══════════════════════════════════════════════════════════════════════════════
sec("📅", "Evolução Semanal — Faturamento & Variação")

weekly = (
    df.groupby(["semana_sort","semana_label","date_range"])
    .agg(
        valor_bruto  =("valor_bruto","sum"),
        unid_faturado=("unid_faturado","sum"),
        num_nfs      =("numero_nota","nunique"),
        num_clientes =("nome_cliente","nunique"),
        num_produtos =("codigo_produto","nunique"),
    )
    .reset_index().sort_values("semana_sort")
)
weekly["delta_vb"]  = weekly["valor_bruto"].diff().fillna(0)
weekly["delta_pct"] = (weekly["valor_bruto"].pct_change().fillna(0) * 100).round(2)
weekly["delta_un"]  = weekly["unid_faturado"].diff().fillna(0)
weekly["bar_color"] = weekly["delta_vb"].apply(lambda v: C_CYAN if v >= 0 else C_RED)
weekly["tick_med"]  = (weekly["valor_bruto"] / weekly["num_nfs"]).fillna(0).round(2)

# customdata: [date_range, unid, delta_vb, delta_pct, num_nfs, num_clientes, num_prods, ticket]
cd_sem = weekly[["date_range","unid_faturado","delta_vb","delta_pct",
                  "num_nfs","num_clientes","num_produtos","tick_med"]].fillna(0).values.tolist()

hover_sem = (
    "<b style='font-size:13px'>%{x}</b><br>"
    "<span style='color:#64748B'>📅 %{customdata[0]}</span><br>"
    "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
    f"<span style='color:{C_CYAN}'>💰 Valor Bruto</span>  <b>R$ %{{y:,.2f}}</b><br>"
    f"<span style='color:{C_TEAL}'>📦 Unidades</span>     <b>%{{customdata[1]:,.0f}}</b><br>"
    f"<span style='color:{C_AMBER}'>🎯 Ticket Médio</span> <b>R$ %{{customdata[7]:,.2f}}</b><br>"
    "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
    f"<span style='color:{C_GREEN}'>▲ Δ Valor</span>  %{{customdata[2]:+,.2f}} "
    f"(<b>%{{customdata[3]:+.1f}}%</b>)<br>"
    f"<span style='color:{C_VIOLET}'>📋 NFs</span>  %{{customdata[4]:.0f}}  "
    f"· <span style='color:{C_ORANGE}'>👥 Clientes</span> %{{customdata[5]:.0f}}  "
    f"· <span style='color:{C_TEAL}'>🏷️ Produtos</span> %{{customdata[6]:.0f}}"
    "<extra></extra>"
)

fig_sem = make_subplots(specs=[[{"secondary_y": True}]])
fig_sem.add_trace(go.Bar(
    x=weekly["semana_label"], y=weekly["valor_bruto"],
    name="Valor Bruto",
    marker=dict(color=weekly["bar_color"], opacity=0.85, line=dict(color=BG_PLOT, width=0.5)),
    text=weekly["valor_bruto"].apply(lambda v: f"R$ {v:,.2f}"),
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
    legend=dict(orientation="h", y=1.1, x=0, font=dict(color=TXT_M)),
    margin=dict(t=35, b=10, l=5, r=10),
    xaxis=dict(showgrid=False, tickfont=dict(color=TXT_S, size=9)),
)
fig_sem.update_yaxes(
    title_text="Valor Bruto (R$)", secondary_y=False,
    tickprefix="R$ ", gridcolor=GRID, tickfont=dict(color=TXT_S),
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
# SEÇÃO 3 — RANKINGS (PRODUTO + CLIENTE)
# ═══════════════════════════════════════════════════════════════════════════════
sec("🏷️", "Rankings por Produto e por Cliente")

col_p, col_c = st.columns(2)

# ── Produto ───────────────────────────────────────────────────────────────────
with col_p:
    prod_stats = (
        df_base.groupby(["prod_nome","codigo_produto"])
        .agg(
            valor_bruto  =("valor_bruto","sum"),
            unid_faturado=("unid_faturado","sum"),
            num_nfs      =("numero_nota","nunique"),
            num_clientes =("nome_cliente","nunique"),
            preco_med    =("preco_unitario","mean"),
            val_desc     =("valor_desconto","sum"),
        )
        .reset_index().sort_values(metrica, ascending=True)
    )
    prod_stats["preco_med"] = prod_stats["preco_med"].round(2)
    cmap = prod_color_map(prod_stats["prod_nome"].unique())
    prod_stats["color"] = prod_stats["prod_nome"].apply(
        lambda x: C_AMBER if x in st.session_state.xf_produto else cmap.get(x, C_CYAN)
    )
    prod_stats["text"] = prod_stats[metrica].apply(met_fmt)

    cd_p = prod_stats[["valor_bruto","unid_faturado","num_nfs",
                        "num_clientes","preco_med","val_desc","codigo_produto"]].fillna(0).values.tolist()
    hover_p = (
        "<b>%{y}</b><br>"
        "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
        f"<span style='color:{C_CYAN}'>💰 Valor Bruto</span>  <b>R$ %{{customdata[0]:,.2f}}</b><br>"
        f"<span style='color:{C_TEAL}'>📦 Unidades</span>     <b>%{{customdata[1]:,.0f}}</b><br>"
        f"<span style='color:{C_AMBER}'>💲 Preço Médio</span>  R$ %{{customdata[4]:,.2f}}<br>"
        f"<span style='color:{C_RED}'>🏷️ Desconto Total</span> R$ %{{customdata[5]:,.2f}}<br>"
        "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
        f"<span style='color:{C_VIOLET}'>📋 NFs</span> %{{customdata[2]:.0f}}  "
        f"· <span style='color:{C_ORANGE}'>👥 Clientes</span> %{{customdata[3]:.0f}}<br>"
        f"<span style='color:{TXT_S}'>Código</span>  %{{customdata[6]}}"
        "<extra></extra>"
    )
    fig_prod = go.Figure(go.Bar(
        x=prod_stats[metrica], y=prod_stats["prod_nome"],
        orientation="h",
        marker=dict(color=prod_stats["color"], line=dict(color=BG_PLOT, width=0.5)),
        text=prod_stats["text"], textposition="outside",
        textfont=dict(size=10, color=TXT_H),
        customdata=cd_p, hovertemplate=hover_p,
    ))
    fig_layout(fig_prod,
        title=dict(text="Por Produto  ·  clique para filtrar"),
        height=max(300, len(prod_stats)*52),
        margin=dict(t=40, b=10, l=5, r=120),
        yaxis=dict(type='category', showgrid=False, tickfont=dict(color=TXT_M, size=10)),
        xaxis=dict(showgrid=True, gridcolor=GRID),
    )
    ev_prod = st.plotly_chart(fig_prod, use_container_width=True, on_select="rerun", key="chart_prod")
    if _handle_event(ev_prod, "xf_produto", "y"):
        st.rerun()

# ── Cliente ───────────────────────────────────────────────────────────────────
with col_c:
    cli_stats = (
        df_base.groupby("nome_cliente")
        .agg(
            valor_bruto  =("valor_bruto","sum"),
            unid_faturado=("unid_faturado","sum"),
            num_nfs      =("numero_nota","nunique"),
            num_produtos =("codigo_produto","nunique"),
            preco_med    =("preco_unitario","mean"),
            ticket_med   =("valor_bruto", lambda x: x.sum() / max(x.count(), 1)),
            semanas_ativas=("semana_sort","nunique"),
        )
        .reset_index().sort_values(metrica, ascending=True)
    )
    cli_stats["preco_med"] = cli_stats["preco_med"].round(2)
    cli_stats["ticket_med"] = cli_stats["ticket_med"].round(2)
    cli_stats["color"] = cli_stats["nome_cliente"].apply(
        lambda x: C_AMBER if x in st.session_state.xf_cliente else C_TEAL
    )
    cli_stats["text"] = cli_stats[metrica].apply(met_fmt)

    cd_c = cli_stats[["valor_bruto","unid_faturado","num_nfs",
                       "num_produtos","preco_med","semanas_ativas"]].fillna(0).values.tolist()
    hover_c = (
        "<b>%{y}</b><br>"
        "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
        f"<span style='color:{C_CYAN}'>💰 Valor Bruto</span>  <b>R$ %{{customdata[0]:,.2f}}</b><br>"
        f"<span style='color:{C_TEAL}'>📦 Unidades</span>     <b>%{{customdata[1]:,.0f}}</b><br>"
        f"<span style='color:{C_AMBER}'>💲 Preço Médio</span>  R$ %{{customdata[4]:,.2f}}<br>"
        "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
        f"<span style='color:{C_VIOLET}'>📋 NFs</span> %{{customdata[2]:.0f}}  "
        f"· <span style='color:{C_ORANGE}'>🏷️ Produtos</span> %{{customdata[3]:.0f}}<br>"
        f"<span style='color:{C_GREEN}'>📅 Semanas ativas</span> %{{customdata[5]:.0f}}"
        "<extra></extra>"
    )
    fig_cli = go.Figure(go.Bar(
        x=cli_stats[metrica], y=cli_stats["nome_cliente"],
        orientation="h",
        marker=dict(color=cli_stats["color"], line=dict(color=BG_PLOT, width=0.5)),
        text=cli_stats["text"], textposition="outside",
        textfont=dict(size=10, color=TXT_H),
        customdata=cd_c, hovertemplate=hover_c,
    ))
    fig_layout(fig_cli,
        title=dict(text="Por Cliente  ·  clique para filtrar"),
        height=max(300, len(cli_stats)*52),
        margin=dict(t=40, b=10, l=5, r=120),
        yaxis=dict(type='category', showgrid=False, tickfont=dict(color=TXT_M, size=10)),
        xaxis=dict(showgrid=True, gridcolor=GRID),
    )
    ev_cli = st.plotly_chart(fig_cli, use_container_width=True, on_select="rerun", key="chart_cli")
    if _handle_event(ev_cli, "xf_cliente", "y"):
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — EVOLUÇÃO POR PRODUTO (linhas individuais com código)
# ═══════════════════════════════════════════════════════════════════════════════
sec("📉", "Evolução Semanal por Produto — Código Individual")

tab_ev1, tab_ev2 = st.tabs(["💰 Valor Bruto", "📦 Unidades"])


def evolution_lines(metric_col, fmt_fn, y_title):
    prod_wk = (
        df.groupby(["semana_sort","semana_label","date_range","prod_nome","codigo_produto"])
        .agg(
            val    =(metric_col, "sum"),
            nfs    =("numero_nota","nunique"),
            clientes=("nome_cliente","nunique"),
            preco  =("preco_unitario","mean"),
        )
        .reset_index().sort_values("semana_sort")
    )
    prods = sorted(prod_wk["prod_nome"].unique())
    cmap  = prod_color_map(prods)

    hover_ev = (
        "<b>%{fullData.name}</b><br>"
        + f"<span style='color:{TXT_S}'>📅 %{{customdata[0]}}</span>  "
        + f"<span style='color:{C_CYAN}'>%{{x}}</span><br>"
        + "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
        + (f"<span style='color:{C_AMBER}'>{y_title}</span>  <b>%{{y:,.2f}}</b><br>" if "Valor" in y_title else f"<span style='color:{C_AMBER}'>{y_title}</span>  <b>%{{y:,.0f}}</b><br>")
        + f"<span style='color:{C_VIOLET}'>📋 NFs</span> %{{customdata[1]:.0f}}  "
        + f"· <span style='color:{C_TEAL}'>👥 Clientes</span> %{{customdata[2]:.0f}}<br>"
        + f"<span style='color:{C_ORANGE}'>💲 Preço Médio</span> R$ %{{customdata[3]:,.2f}}"
        + "<extra></extra>"
    )
    fig = go.Figure()
    for prod in prods:
        sub = prod_wk[prod_wk["prod_nome"] == prod]
        cd = sub[["date_range","nfs","clientes","preco"]].fillna(0).values.tolist()
        fig.add_trace(go.Scatter(
            x=sub["semana_label"], y=sub["val"],
            mode="lines+markers+text", name=str(prod),
            line=dict(color=cmap[prod], width=2),
            marker=dict(size=7, color=cmap[prod], line=dict(color=BG_PLOT, width=1.5)),
            text=sub["val"].apply(fmt_fn),
            textposition="top center", textfont=dict(size=8, color=cmap[prod]),
            customdata=cd, hovertemplate=hover_ev,
        ))
    all_wk = df[["semana_sort", "semana_label"]].drop_duplicates().sort_values("semana_sort")["semana_label"].tolist()
    fig_layout(fig,
        height=420,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.22, font=dict(color=TXT_M, size=10)),
        margin=dict(t=20, b=80, l=5, r=10),
        xaxis=dict(type="category", categoryorder="array", categoryarray=all_wk, showgrid=False, tickfont=dict(color=TXT_S, size=9)),
        yaxis=dict(showgrid=True, gridcolor=GRID, title_text=y_title,
                   title_font=dict(color=TXT_S), tickfont=dict(color=TXT_S)),
    )
    return fig


with tab_ev1:
    st.plotly_chart(evolution_lines("valor_bruto",   lambda v: f"R${v:,.2f}", "Valor Bruto (R$)"), use_container_width=True)
with tab_ev2:
    st.plotly_chart(evolution_lines("unid_faturado", lambda v: f"{v:,.0f}", "Unidades"), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 5 — SITUAÇÃO NF + TRANSAÇÃO (pies clickable)
# ═══════════════════════════════════════════════════════════════════════════════
sec("📋", "Situação NF e Tipo de Transação")

col_s, col_t = st.columns(2)

with col_s:
    sit_df = (
        df_base.groupby("situacao_NF")
        .agg(valor_bruto=("valor_bruto","sum"), unids=("unid_faturado","sum"),
             nfs=("numero_nota","nunique")).reset_index()
    )
    sit_df = sit_df.fillna(0)
    total_s = sit_df["valor_bruto"].sum()
    sit_df["pct"] = (sit_df["valor_bruto"] / total_s * 100).round(2)
    cd_s = sit_df[["unids","nfs","pct"]].values.tolist()
    fig_sit = go.Figure(go.Pie(
        labels=sit_df["situacao_NF"], values=sit_df["valor_bruto"],
        texttemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}",
        textfont=dict(size=12, color=TXT_H),
        marker=dict(colors=[C_CYAN, C_RED], line=dict(color=BG_APP, width=3)),
        pull=[0.08 if x in st.session_state.xf_situacao else 0 for x in sit_df["situacao_NF"]],
        customdata=cd_s,
        hovertemplate=(
            "<b>%{label}</b><br>"
            "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
            f"<span style='color:{C_CYAN}'>💰 Valor Bruto</span>  <b>R$ %{{value:,.2f}}</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Unidades</span>  %{{customdata[0]:,.0f}}<br>"
            f"<span style='color:{C_VIOLET}'>📋 NFs</span>  %{{customdata[1]:.0f}}<br>"
            f"<span style='color:{C_AMBER}'>📊 Participação</span>  <b>%{{percent}}</b>"
            "<extra></extra>"
        ),
    ))
    fig_layout(fig_sit,
        title=dict(text="Situação NF  ·  clique para filtrar"),
        height=340, margin=dict(t=45, b=10),
    )
    ev_sit = st.plotly_chart(fig_sit, use_container_width=True, on_select="rerun", key="chart_sit")
    if _handle_event(ev_sit, "xf_situacao", "label"):
        st.rerun()

with col_t:
    tra_df = (
        df_base.groupby("transacao_str")
        .agg(valor_bruto=("valor_bruto","sum"), unids=("unid_faturado","sum"),
             nfs=("numero_nota","nunique"), prods=("codigo_produto","nunique")).reset_index()
    )
    tra_df = tra_df.fillna(0)
    tra_total = tra_df["valor_bruto"].sum()
    tra_df["pct"] = (tra_df["valor_bruto"] / tra_total * 100).round(2)
    cd_t = tra_df[["unids","nfs","prods","pct"]].values.tolist()
    fig_tra = go.Figure(go.Pie(
        labels=tra_df["transacao_str"], values=tra_df["valor_bruto"],
        texttemplate="<b>CFOP %{label}</b><br>R$ %{value:,.2f}<br>%{percent}",
        textfont=dict(size=11, color=TXT_H),
        marker=dict(colors=[C_TEAL, C_AMBER, C_VIOLET, C_ORANGE],
                    line=dict(color=BG_APP, width=3)),
        pull=[0.08 if x in st.session_state.xf_transacao else 0 for x in tra_df["transacao_str"]],
        customdata=cd_t,
        hovertemplate=(
            "<b>CFOP %{label}</b><br>"
            "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
            f"<span style='color:{C_CYAN}'>💰 Valor Bruto</span>  <b>R$ %{{value:,.2f}}</b><br>"
            f"<span style='color:{C_TEAL}'>📦 Unidades</span>  %{{customdata[0]:,.0f}}<br>"
            f"<span style='color:{C_VIOLET}'>📋 NFs</span>  %{{customdata[1]:.0f}}<br>"
            f"<span style='color:{C_ORANGE}'>🏷️ Produtos</span>  %{{customdata[2]:.0f}}<br>"
            f"<span style='color:{C_AMBER}'>📊 Participação</span>  <b>%{{percent}}</b>"
            "<extra></extra>"
        ),
    ))
    fig_layout(fig_tra,
        title=dict(text="Transação (CFOP)  ·  clique para filtrar"),
        height=340, margin=dict(t=45, b=10),
    )
    ev_tra = st.plotly_chart(fig_tra, use_container_width=True, on_select="rerun", key="chart_tra")
    if _handle_event(ev_tra, "xf_transacao", "label"):
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 6 — CASCATA SEMANAL
# ═══════════════════════════════════════════════════════════════════════════════
sec("🌊", "Cascata de Incremento Semanal")

wfall = (
    df.groupby(["semana_sort","semana_label","date_range"])
    .agg(valor_bruto=("valor_bruto","sum"), unids=("unid_faturado","sum"),
         nfs=("numero_nota","nunique"))
    .reset_index().sort_values("semana_sort")
)
wf_y      = [wfall.iloc[0]["valor_bruto"]] + wfall["valor_bruto"].diff().iloc[1:].tolist()
wf_texts  = [
    f"R$ {v:,.2f}" if i == 0 else (f"+R$ {v:,.2f}" if v >= 0 else f"-R$ {abs(v):,.2f}")
    for i, v in enumerate(wf_y)
]
measures  = ["absolute"] + ["relative"] * (len(wfall) - 1)
cd_wf     = wfall[["date_range","unids","nfs","valor_bruto"]].fillna(0).values.tolist()

hover_wf  = (
    "<b>%{x}</b><br>"
    f"<span style='color:{TXT_S}'>📅 %{{customdata[0]}}</span><br>"
    "<span style='color:#1E3A5F'>──────────────────────────</span><br>"
    f"<span style='color:{C_CYAN}'>💰 Valor Total</span>  <b>R$ %{{customdata[3]:,.2f}}</b><br>"
    f"<span style='color:{C_TEAL}'>📦 Unidades</span>  %{{customdata[1]:,.0f}}<br>"
    f"<span style='color:{C_VIOLET}'>📋 NFs</span>  %{{customdata[2]:.0f}}<br>"
    f"<span style='color:{C_AMBER}'>Δ esta semana</span>  <b>%{{y:+,.2f}}</b>"
    "<extra></extra>"
)
fig_wf = go.Figure(go.Waterfall(
    x=wfall["semana_label"],
    y=wf_y,
    measure=measures,

    text=wf_texts,
    textposition="outside",
    textfont=dict(size=9, color=TXT_H),

    connector={"line": {"color": BORDER, "width": 1}},

    # ✅ CORRIGIDO AQUI (removido opacity)
    increasing={"marker": {"color": C_GREEN}},
    decreasing={"marker": {"color": C_RED}},
    totals={"marker": {"color": C_CYAN}},

    # ✅ se quiser transparência, use aqui:
    opacity=0.9,

    customdata=cd_wf,
    hovertemplate=hover_wf,
))
fig_wf.add_hline(y=0, line_width=1, line_color=TXT_S, line_dash="dot")
fig_layout(fig_wf,
    height=410, margin=dict(t=20, b=10, l=5, r=10),
    xaxis=dict(showgrid=False, tickfont=dict(color=TXT_S, size=9)),
    yaxis=dict(showgrid=True, gridcolor=GRID, tickprefix="R$ ",
               tickfont=dict(color=TXT_S)),
)
st.plotly_chart(fig_wf, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 7 — TABELA DETALHADA (CORRIGIDA DEFINITIVA)
# ═══════════════════════════════════════════════════════════════════════════════
sec("📄", "Tabela Detalhada")

agg = (
    df.groupby([
        "semana_label","semana_sort","date_range",
        "codigo_produto","prod_nome","nome_cliente",
        "situacao_NF","transacao_str",
    ])
    .agg(
        Unidades      =("unid_faturado","sum"),
        Valor_Bruto   =("valor_bruto","sum"),
        NFs           =("numero_nota","nunique"),
        Preco_Med     =("preco_unitario","mean"),
        Desconto_val  =("valor_desconto","sum"),  # 🔥 RENOMEADO AQUI
    )
    .reset_index()
    .sort_values(["semana_sort","Valor_Bruto"], ascending=[True, False])
)

# ── FORMATAÇÃO ────────────────────────────────────────────────────────────────
agg["Valor Bruto"] = agg["Valor_Bruto"].map("R$ {:,.2f}".format)
agg["Preço Médio"] = agg["Preco_Med"].map("R$ {:,.2f}".format)
agg["Desconto"]    = agg["Desconto_val"].map("R$ {:,.2f}".format)

# ── REMOVE COLUNAS TÉCNICAS (CRÍTICO) ─────────────────────────────────────────
agg = agg.drop(columns=["Valor_Bruto", "Preco_Med", "Desconto_val"])

# ── BUSCA ─────────────────────────────────────────────────────────────────────
srch = st.text_input("🔎 Buscar na tabela", placeholder="produto, cliente, situação, semana…")

tbl = agg.copy()
if srch:
    mask = tbl.apply(lambda row: srch.lower() in row.astype(str).str.lower().str.cat(), axis=1)
    tbl = tbl[mask]

# ── RENOME FINAL ──────────────────────────────────────────────────────────────
tbl_final = tbl.rename(columns={
    "semana_label":   "Semana",
    "date_range":     "Período",
    "codigo_produto": "Código",
    "prod_nome":      "Produto",
    "nome_cliente":   "Cliente",
    "situacao_NF":    "Situação NF",
    "transacao_str":  "CFOP",
})

# ── GARANTE 100% QUE NÃO EXISTE DUPLICIDADE ───────────────────────────────────
tbl_final = tbl_final.loc[:, ~tbl_final.columns.duplicated()]

# ── ORDEM FINAL ───────────────────────────────────────────────────────────────
tbl_final = tbl_final[
    [
        "Semana",
        "Período",
        "Código",
        "Produto",
        "Cliente",
        "Situação NF",
        "CFOP",
        "Unidades",
        "Valor Bruto",
        "Preço Médio",
        "Desconto",
        "NFs",
    ]
]

st.dataframe(
    tbl_final,
    width="stretch",  # já ajustado ao novo padrão
    height=400,
)

# ── SIDEBAR FOOTER ────────────────────────────────────────────────────────────
st.sidebar.markdown(f"<hr style='border-color:{BORDER};margin:10px 0'>", unsafe_allow_html=True)
st.sidebar.markdown(
    f"<div style='font-size:.72rem;color:{TXT_S};text-align:center;padding-top:4px;line-height:1.7'>"
    f"Dashboard de Faturamento<br>"
    f"<span style='color:{C_CYAN}'>{len(df_raw):,}</span> registros · "
    f"<span style='color:{C_TEAL}'>{df_raw['semana_sort'].nunique()}</span> semanas<br>"
    f"<span style='color:{C_AMBER}'>{df_raw['codigo_produto'].nunique()}</span> produtos · "
    f"<span style='color:{C_VIOLET}'>{df_raw['nome_cliente'].nunique()}</span> clientes"
    f"</div>",
    unsafe_allow_html=True,
)