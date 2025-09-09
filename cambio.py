# streamlit_app.py
# Simulador de Operação com Login + Destaque, Limpar, e Valor USD formatado BR
# Execução local: streamlit run streamlit_app.py

import streamlit as st

# ----------------------------
# Config da página
# ----------------------------
st.set_page_config(page_title="Simulador - Metalcred", page_icon="💱", layout="centered")

# ----------------------------
# Helpers de formatação / parsing
# ----------------------------
def br_money(value: float) -> str:
    """Formata número em padrão BR: 1.234.567,89 (sem depender de locale)."""
    s = f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def br_money_with_symbol(value: float) -> str:
    return "R$ " + br_money(value)

def parse_br_number(texto: str) -> float:
    """
    Converte string no padrão BR para float.
    Aceita '10.000,00', '10000,00', '10000.00' ou '10000'.
    """
    if texto is None:
        return 0.0
    txt = str(texto).strip()
    if txt == "":
        return 0.0
    # Se tiver vírgula, é notação BR -> remove pontos de milhar e troca vírgula por ponto
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    # Caso contrário, assume ponto como decimal
    try:
        return float(txt)
    except Exception:
        return 0.0

def pct(frac: float, casas: int = 6) -> str:
    s = f"{frac*100:,.{casas}f}%"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def taxa_anual_para_diaria(i_anual: float, base_dias: int = 365) -> float:
    return (1.0 + i_anual) ** (1.0 / base_dias) - 1.0

def montante_por_dias(vp: float, i_dia: float, dias: int) -> float:
    return vp * ((1.0 + i_dia) ** dias)

# ----------------------------
# Credenciais (Streamlit Cloud: defina em Secrets se desejar)
# ----------------------------
APP_USER = st.secrets.get("APP_USER", "cambio.simulacao")
APP_PASS = st.secrets.get("APP_PASS", "metalcred")

# ----------------------------
# Estado (inicialização segura)
# ----------------------------
st.session_state.setdefault("autenticado", False)
# Valores padrão dos inputs
DEFAULTS = {
    "cotacao": 5.0000,
    "taxa_aa_pct": 12.0000,
    "dias": 30,
    "valor_usd_str": "10.000,00",  # sempre exibido com milhar/decimal BR
}

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# ----------------------------
# Cabeçalho
# ----------------------------
st.title("💱 Simulador de Operação – Metalcred")

# ----------------------------
# Login
# ----------------------------
if not st.session_state["autenticado"]:
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Acesso")
        user = st.text_input("Usuário", placeholder="cambio.simulacao")
        pwd = st.text_input("Senha", type="password", placeholder="metalcred")
        entrar = st.form_submit_button("Entrar")
    if entrar:
        if user == APP_USER and pwd == APP_PASS:
            st.session_state["autenticado"] = True
            st.success("Login realizado com sucesso.")
            st.rerun()
        else:
            st.error("Credenciais inválidas. Verifique usuário e senha.")
    st.stop()

# ----------------------------
# Área autenticada
# ----------------------------
st.success("Autenticação confirmada ✅")
with st.sidebar:
    st.caption("Conectado como:")
    st.code(APP_USER, language="bash")
    if st.button("Sair"):
        st.session_state["autenticado"] = False
        st.rerun()

# ======== DESTAQUE VISUAL ========
st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, rgba(0,160,145,0.15), rgba(73,71,157,0.10));
        border: 1px solid rgba(0,160,145,0.35);
        padding: 14px 18px; border-radius: 12px; margin-top: 6px; margin-bottom: 12px;">
        <span style="font-weight: 700; font-size: 1.05rem; color: #003641;">
            ⚙️ Informe os parâmetros da operação
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ======== FORMULÁRIO ========
col1, col2 = st.columns(2)
with col1:
    cotacao = st.number_input(
        "Cotação do dólar (BRL/USD)",
        min_value=0.0001, value=float(st.session_state["cotacao"]),
        step=0.0100, format="%.4f",
        help="Valor em reais por 1 dólar.",
        key="cotacao",
    )
    taxa_aa_pct = st.number_input(
        "Taxa de juros ao ano (%)",
        min_value=0.0, value=float(st.session_state["taxa_aa_pct"]),
        step=0.1000, format="%.4f",
        help="Taxa efetiva ao ano.",
        key="taxa_aa_pct",
    )
with col2:
    dias = st.number_input(
        "Quantidade de dias da operação",
        min_value=0, value=int(st.session_state["dias"]),
        step=1, help="Número inteiro de dias corridos.",
        key="dias",
    )
    # Campo em texto com máscara BR (permite exibir 10.000,00)
    valor_usd_str = st.text_input(
        "Valor da operação (USD)",
        value=st.session_state["valor_usd_str"],
        help="Use o padrão BR: 10.000,00",
        key="valor_usd_str",
        placeholder="10.000,00",
    )

# ======== AÇÕES (Calcular / Limpar) ========
bcol1, bcol2 = st.columns([1, 1])
calcular = bcol1.button("Calcular VALOR FINAL", type="primary")
limpar = bcol2.button("Limpar parâmetros")

if limpar:
    # Reset de todos os campos para os defaults e refresh
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.experimental_rerun()

base_dias = 365

if calcular:
    erros = []
    if cotacao <= 0:
        erros.append("A cotação deve ser maior que zero.")
    if taxa_aa_pct < 0:
        erros.append("A taxa ao ano não pode ser negativa.")
    if dias < 0:
        erros.append("A quantidade de dias não pode ser negativa.")

    valor_usd = parse_br_number(valor_usd_str)
    if valor_usd <= 0:
        erros.append("O valor da operação (USD) deve ser maior que zero (ex.: 10.000,00).")

    if erros:
        for e in erros:
            st.error(e)
        st.stop()

    taxa_aa = taxa_aa_pct / 100.0
    i_dia = taxa_anual_para_diaria(taxa_aa, base_dias=base_dias)
    montante_usd = montante_por_dias(valor_usd, i_dia, dias)
    valor_final_brl = montante_usd * cotacao

    st.divider()
    st.subheader("Resultado")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Taxa diária (efetiva)", pct(i_dia, 6))
    with c2:
        st.metric("Montante (USD)", br_money(montante_usd))
    with c3:
        st.metric("Cotação aplicada (BRL/USD)", br_money(cotacao).replace("R$ ", ""))  # só formatação numérica

    st.success(f"**VALOR FINAL (em BRL)**: {br_money_with_symbol(valor_final_brl)}")

    st.caption(
        f"Cálculo: i_dia = (1 + i_aa)^(1/{base_dias}) - 1; "
        f"Montante = Valor × (1 + i_dia)^{dias}; "
        f"Valor Final = Montante × Cotação."
    )

# Rodapé técnico
with st.expander("Observações/Premissas"):
    st.markdown(
        f"""
- Conversão **anual → diária** por equivalência: \\( i_{{dia}} = (1 + i_{{anual}})^{{1/{base_dias}}} - 1 \\).
- **Base de {base_dias} dias corridos**; se preferir **252 dias úteis**, troque `base_dias = 365` por `base_dias = 252`.
- A taxa informada é **efetiva anual**.
- O **valor de entrada** é em **USD** no padrão BR (ex.: 10.000,00); o **VALOR FINAL** é convertido para **BRL**.
        """
    )
