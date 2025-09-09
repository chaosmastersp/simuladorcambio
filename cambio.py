# streamlit_app.py
# Simulador de Operação – Metalcred (Streamlit Cloud-ready)
# Executar localmente: streamlit run streamlit_app.py

import streamlit as st

# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(page_title="Simulador - Metalcred", page_icon="💱", layout="centered")

# ----------------------------
# Helpers de formatação / parsing
# ----------------------------
def br_money(value: float) -> str:
    """Formata número em padrão BR: 1.234.567,89 (sem símbolo)."""
    s = f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def br_money_with_symbol(value: float) -> str:
    return "R$ " + br_money(value)

def br_number(value: float, decimals: int = 4) -> str:
    """Formata número com N casas decimais no padrão BR (sem símbolo)."""
    s = f"{value:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def pct(frac: float, casas: int = 6) -> str:
    """Formata fração (0.1234) como percentual BR."""
    s = f"{frac*100:,.{casas}f}%"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def parse_br_number(texto: str) -> float:
    """
    Converte string no padrão BR para float.
    Aceita: '10.000,00', '10000,00', '10000.00' ou '10000'.
    """
    if texto is None:
        return 0.0
    txt = str(texto).strip()
    if txt == "":
        return 0.0
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return 0.0

# ----------------------------
# Cálculos financeiros
# ----------------------------
def taxa_anual_para_diaria(i_anual: float, base_dias: int = 365) -> float:
    """Converte taxa efetiva anual para efetiva diária: i_dia = (1 + i_anual) ** (1/base_dias) - 1"""
    return (1.0 + i_anual) ** (1.0 / base_dias) - 1.0

def montante_por_dias(vp: float, i_dia: float, dias: int) -> float:
    """Montante com capitalização diária: M = VP * (1 + i_dia) ** dias"""
    return vp * ((1.0 + i_dia) ** dias)

# ----------------------------
# Credenciais (Cloud: use Secrets se quiser)
# ----------------------------
APP_USER = st.secrets.get("APP_USER", "cambio")
APP_PASS = st.secrets.get("APP_PASS", "metalcred")

# ----------------------------
# Estado da sessão (inicialização segura)
# ----------------------------
st.session_state.setdefault("autenticado", False)

# Defaults de inputs (carregados uma única vez)
DEFAULTS = {
    "cotacao": 5.0000,           # float
    "taxa_aa_pct": 12.0000,      # float
    "dias": 30,                  # int
    "valor_usd_str": "10.000,00" # str (exibição BR)
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
        user = st.text_input("Usuário", placeholder="Usuário")
        pwd = st.text_input("Senha", type="password", placeholder="Senha")
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

# ======== Destaque visual do bloco de parâmetros ========
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

# ======== Formulário de parâmetros ========
col1, col2 = st.columns(2)
with col1:
    cotacao = st.number_input(
        "Cotação do dólar (BRL/USD)",
        min_value=0.0001,
        value=float(st.session_state["cotacao"]),
        step=0.0100,
        format="%.4f",
        help="Valor em reais por 1 dólar.",
        key="cotacao",
    )
    taxa_aa_pct = st.number_input(
        "Taxa de juros ao ano (%)",
        min_value=0.0,
        value=float(st.session_state["taxa_aa_pct"]),
        step=0.1000,
        format="%.4f",
        help="Taxa efetiva ao ano.",
        key="taxa_aa_pct",
    )
with col2:
    dias = st.number_input(
        "Quantidade de dias da operação",
        min_value=0,
        value=int(st.session_state["dias"]),
        step=1,
        help="Número inteiro de dias corridos.",
        key="dias",
    )
    # Campo em texto (para exibir 10.000,00)
    valor_usd_str = st.text_input(
        "Valor da operação (USD)",
        value=st.session_state["valor_usd_str"],
        help="Use o padrão BR: 10.000,00",
        key="valor_usd_str",
        placeholder="10.000,00",
    )

# ======== Ação: Calcular ========
base_dias = 365
calcular = st.button("Calcular VALOR FINAL", type="primary")

if calcular:
    erros = []
    cotacao_v = float(st.session_state["cotacao"])
    taxa_aa_pct_v = float(st.session_state["taxa_aa_pct"])
    dias_v = int(st.session_state["dias"])
    valor_usd_v = parse_br_number(st.session_state["valor_usd_str"])

    if cotacao_v <= 0:
        erros.append("A cotação deve ser maior que zero.")
    if taxa_aa_pct_v < 0:
        erros.append("A taxa ao ano não pode ser negativa.")
    if dias_v < 0:
        erros.append("A quantidade de dias não pode ser negativa.")
    if valor_usd_v <= 0:
        erros.append("O valor da operação (USD) deve ser maior que zero (ex.: 10.000,00).")

    if erros:
        for e in erros:
            st.error(e)
    else:
        taxa_aa = taxa_aa_pct_v / 100.0
        i_dia = taxa_anual_para_diaria(taxa_aa, base_dias=base_dias)
        montante_usd = montante_por_dias(valor_usd_v, i_dia, dias_v)
        valor_final_brl = montante_usd * cotacao_v

        st.divider()
        st.subheader("Resultado")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Taxa diária (efetiva)", pct(i_dia, 6))
        with c2:
            st.metric("Montante (USD)", br_money(montante_usd))
        with c3:
            st.metric("Cotação aplicada (BRL/USD)", br_number(cotacao_v, 4))

        st.success(f"**VALOR FINAL (em BRL)**: {br_money_with_symbol(valor_final_brl)}")

# (Removido: linha de explicação do cálculo que ficava no rodapé do resultado)

# Observações opcionais (mantidas, sem fórmulas)
with st.expander("Observações/Premissas"):
    st.markdown(
        f"""
- Base de **{base_dias} dias corridos** para equivalência anual → diária.
- A taxa informada é **efetiva anual**.
- O valor de entrada é em **USD** (aceita formato BR: 10.000,00); o **VALOR FINAL** é convertido para **BRL** pela cotação informada.
        """
    )

