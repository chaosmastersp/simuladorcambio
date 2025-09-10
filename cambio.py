import re
import streamlit as st

# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(page_title="Simulador - Metalcred", page_icon="💱", layout="centered")

# ----------------------------
# Helpers de formatação
# ----------------------------
def br_money(value: float) -> str:
    s = f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def br_money_with_symbol(value: float) -> str:
    return "R$ " + br_money(value)

def br_number(value: float, decimals: int = 4) -> str:
    s = f"{value:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def pct(frac: float, casas: int = 6) -> str:
    s = f"{frac*100:,.{casas}f}%"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def parse_number_flex(texto: str) -> float:
    """
    Converte string para float aceitando:
    - BR: '50.000', '50.000,75', '50000,75'
    - US: '50,000', '50,000.75', '50000.75'
    Regras:
      * Se existir vírgula e ponto, o separador decimal é o que aparece por último.
      * Se existir apenas vírgula ou apenas ponto:
          - se for padrão de milhares (grupos de 3), trata como milhar (remove)
          - senão, trata como decimal.
    """
    if texto is None:
        return 0.0
    s = str(texto).strip()
    if s == "":
        return 0.0

    # mantém apenas dígitos e separadores
    s = re.sub(r"[^\d,\.]", "", s)

    has_comma = "," in s
    has_dot = "." in s

    try:
        if has_comma and has_dot:
            # decimal = último separador que aparece
            last_comma = s.rfind(",")
            last_dot = s.rfind(".")
            if last_comma > last_dot:
                decimal_sep = ","
                thousands_sep = "."
            else:
                decimal_sep = "."
                thousands_sep = ","
            s = s.replace(thousands_sep, "")
            s = s.replace(decimal_sep, ".")
            return float(s)

        elif has_comma:
            # apenas vírgula presente
            # se estiver no padrão de milhares: 1,234 ou 12,345,678
            if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
                return float(s.replace(",", ""))
            # senão, assume vírgula decimal (BR)
            s = s.replace(".", "")   # pontos que sobraram = milhares
            s = s.replace(",", ".")  # vírgula decimal
            return float(s)

        elif has_dot:
            # apenas ponto presente
            # padrão de milhares BR: 1.234 ou 12.345.678
            if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
                return float(s.replace(".", ""))
            # senão, assume ponto decimal (US)
            return float(s)

        else:
            # só dígitos
            return float(s)

    except ValueError:
        # fallback seguro
        return 0.0

# ----------------------------
# Cálculos financeiros
# ----------------------------
def taxa_anual_para_diaria(i_anual: float, base_dias: int = 365) -> float:
    return (1.0 + i_anual) ** (1.0 / base_dias) - 1.0

def montante_por_dias(vp: float, i_dia: float, dias: int) -> float:
    return vp * ((1.0 + i_dia) ** dias)

# ----------------------------
# Credenciais (Cloud: use Secrets se quiser)
# ----------------------------
APP_USER = st.secrets.get("APP_USER", "cambio")
APP_PASS = st.secrets.get("APP_PASS", "metalcred")

# ----------------------------
# Estado (inicialização única)
# ----------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "_inited" not in st.session_state:
    st.session_state.cotacao = 5.0000
    st.session_state.taxa_aa_pct = 12.0000
    st.session_state.dias = 30
    st.session_state.valor_usd_str = "10.000,00"  # exibido em BR
    st.session_state._inited = True

# ----------------------------
# Cabeçalho
# ----------------------------
st.title("💱 Simulador de Operação – Metalcred")

# ----------------------------
# Login
# ----------------------------
if not st.session_state.autenticado:
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Acesso")
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")
    if entrar:
        if user == APP_USER and pwd == APP_PASS:
            st.session_state.autenticado = True
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
        st.session_state.autenticado = False
        st.rerun()

# ======== Destaque visual ========
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

# ======== Formulário (mantém estado; sem 'value=') ========
col1, col2 = st.columns(2)
with col1:
    st.number_input(
        "Cotação do dólar (BRL/USD)",
        min_value=0.0001,
        step=0.0100,
        format="%.4f",
        help="Valor em reais por 1 dólar.",
        key="cotacao",
    )
    st.number_input(
        "Taxa de juros ao ano (%)",
        min_value=0.0,
        step=0.1000,
        format="%.4f",
        help="Taxa efetiva ao ano.",
        key="taxa_aa_pct",
    )
with col2:
    st.number_input(
        "Quantidade de dias da operação",
        min_value=0,
        step=1,
        help="Número inteiro de dias corridos.",
        key="dias",
    )
    st.text_input(
        "Valor da operação (USD)",
        help="Aceita: 50.000, 50.000,00, 50000,00, 50,000.00 ou 50000.00",
        placeholder="10.000,00",
        key="valor_usd_str",
    )

# ======== Calcular ========
base_dias = 365
if st.button("Calcular VALOR FINAL", type="primary"):
    erros = []
    cotacao_v = float(st.session_state.cotacao)
    taxa_aa_pct_v = float(st.session_state.taxa_aa_pct)
    dias_v = int(st.session_state.dias)
    valor_usd_v = parse_number_flex(st.session_state.valor_usd_str)

    if cotacao_v <= 0:
        erros.append("A cotação deve ser maior que zero.")
    if taxa_aa_pct_v < 0:
        erros.append("A taxa ao ano não pode ser negativa.")
    if dias_v < 0:
        erros.append("A quantidade de dias não pode ser negativa.")
    if valor_usd_v <= 0:
        erros.append("O valor da operação (USD) deve ser maior que zero.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        taxa_aa = taxa_aa_pct_v / 100.0
        i_dia = taxa_anual_para_diaria(taxa_aa, base_dias=base_dias)
        montante_usd = montante_por_dias(valor_usd_v, i_dia, dias_v)
        valor_final_brl = montante_usd * cotacao_v

        st.divider()
        st.markdown("### Resultado")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"<div style='font-size:0.9rem;color:#555;'>Taxa diária (efetiva)</div>"
                f"<div style='font-size:1.1rem;font-weight:600;'>{pct(i_dia, 6)}</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div style='font-size:0.9rem;color:#555;'>Montante (USD)</div>"
                f"<div style='font-size:1.1rem;font-weight:600;'>{br_money(montante_usd)}</div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div style='font-size:0.9rem;color:#555;'>Cotação aplicada (BRL/USD)</div>"
                f"<div style='font-size:1.1rem;font-weight:600;'>{br_number(cotacao_v, 4)}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div style="
                background-color:#e8f9f0;
                border-left:6px solid #00a091;
                padding:14px;
                margin-top:12px;
                border-radius:8px;
                text-align:center;">
                <div style="font-size:1rem;color:#004b3f;font-weight:600;">VALOR FINAL (em BRL)</div>
                <div style="font-size:2rem;color:#003641;font-weight:700;margin-top:6px;">
                    {br_money_with_symbol(valor_final_brl)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Observações/Premissas (sempre visível)

st.markdown(
    """
<div style="
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px;
    margin-top: 12px;
    background-color: #fafafa;">
<b>📌 AVISO IMPORTANTE</b><br><br>
<ul>
    <li>Esta simulação possui caráter meramente ilustrativo. O valor exato somente poderá ser apurado na data da efetiva liquidação, ocasião em que será considerada a cotação vigente no dia.</li>
    <li>Esta simulação não contempla cálculo de IOF.</li>
</ul>
</div>
    """,
    unsafe_allow_html=True,
)





