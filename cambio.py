# streamlit_app.py
# Simulador de Operação com Login (Streamlit Cloud-ready)
# Execução local: streamlit run streamlit_app.py

import math
import streamlit as st

# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(page_title="Simulador - Metalcred", page_icon="💱", layout="centered")

# ----------------------------
# Utilidades de formatação (padrão BR)
# ----------------------------
def brl(valor: float) -> str:
    """Formata número em padrão brasileiro: R$ 1.234.567,89 (sem depender de locale)."""
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

def pct(valor_fracao: float, casas: int = 4) -> str:
    """Formata fração (ex.: 0.1234) como percentual BR (12,34%)."""
    s = f"{valor_fracao*100:,.{casas}f}%"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# ----------------------------
# Cálculos financeiros
# ----------------------------
def taxa_anual_para_diaria(i_anual: float, base_dias: int = 365) -> float:
    """
    Converte taxa efetiva anual para efetiva diária:
    i_dia = (1 + i_anual) ** (1/base_dias) - 1
    """
    return (1.0 + i_anual) ** (1.0 / base_dias) - 1.0

def montante_por_dias(vp: float, i_dia: float, dias: int) -> float:
    """Montante com capitalização diária: M = VP * (1 + i_dia) ** dias"""
    return vp * ((1.0 + i_dia) ** dias)

# ----------------------------
# Credenciais (lidas de secrets se existirem; senão, usa padrão solicitado)
# Em Streamlit Cloud, você pode configurar em Settings > Secrets:
# APP_USER = cambio.simulacao
# APP_PASS = metalcred
# ----------------------------
APP_USER = st.secrets.get("APP_USER", "cambio.simulacao")
APP_PASS = st.secrets.get("APP_PASS", "metalcred")

# ----------------------------
# Estado da sessão (inicialização segura)
# ----------------------------
st.session_state.setdefault("autenticado", False)

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

st.markdown("Informe os parâmetros da operação:")

col1, col2 = st.columns(2)
with col1:
    cotacao = st.number_input(
        "Cotação do dólar (BRL/USD)",
        min_value=0.0001, value=5.0000, step=0.0100, format="%.4f",
        help="Valor em reais por 1 dólar."
    )
    taxa_aa_pct = st.number_input(
        "Taxa de juros ao ano (%)",
        min_value=0.0, value=12.0000, step=0.1000, format="%.4f",
        help="Taxa efetiva ao ano."
    )
with col2:
    dias = st.number_input(
        "Quantidade de dias da operação",
        min_value=0, value=30, step=1, help="Número inteiro de dias corridos."
    )
    valor_usd = st.number_input(
        "Valor da operação (USD)",
        min_value=0.0, value=10000.00, step=100.00, format="%.2f",
        help="Principal em dólares (antes da conversão)."
    )

# Base de dias usada na equivalência (corridos). Altere para 252 se desejar dias úteis.
base_dias = 365

# Botão calcular
if st.button("Calcular VALOR FINAL"):
    erros = []
    if cotacao <= 0:
        erros.append("A cotação deve ser maior que zero.")
    if taxa_aa_pct < 0:
        erros.append("A taxa ao ano não pode ser negativa.")
    if dias < 0:
        erros.append("A quantidade de dias não pode ser negativa.")
    if valor_usd < 0:
        erros.append("O valor da operação não pode ser negativo.")

    if erros:
        for e in erros:
            st.error(e)
        st.stop()

    # Conversões
    taxa_aa = taxa_aa_pct / 100.0
    i_dia = taxa_anual_para_diaria(taxa_aa, base_dias=base_dias)
    montante_usd = montante_por_dias(valor_usd, i_dia, dias)
    valor_final_brl = montante_usd * cotacao

    # Resultados
    st.divider()
    st.subheader("Resultado")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Taxa diária (efetiva)", pct(i_dia, 6))
    with c2:
        st.metric("Montante (USD)", f"{montante_usd:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with c3:
        st.metric("Cotação aplicada (BRL/USD)", f"{cotacao:,.4f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.success(f"**VALOR FINAL (em BRL)**: {brl(valor_final_brl)}")

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
- **Base de {base_dias} dias corridos**; se desejar usar **252 dias úteis**, troque `base_dias = 365` por `base_dias = 252`.
- A taxa informada é **efetiva anual**. Para taxa **nominal** a.a. com capitalização diária, você pode usar `i_dia = taxa_nominal_anual / {base_dias}`.
- O **valor de entrada** é em **USD**; o **VALOR FINAL** é convertido para **BRL** pela cotação informada.
        """
    )
