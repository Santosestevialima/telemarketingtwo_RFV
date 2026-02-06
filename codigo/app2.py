# ===============================
# IMPORTS
# ===============================
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from io import BytesIO
from PIL import Image

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="RFV",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# FUNÇÕES DE DOWNLOAD
# ===============================

@st.cache_data
def convert_df_csv(df):
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def convert_df_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="RFV")
    return output.getvalue()

# ===============================
# FUNÇÕES RFV
# ===============================

def recencia_class(x, quartis):
    if x <= quartis["Recencia"][0.25]:
        return "A"
    elif x <= quartis["Recencia"][0.50]:
        return "B"
    elif x <= quartis["Recencia"][0.75]:
        return "C"
    else:
        return "D"


def freq_val_class(x, quartis, coluna):
    if x <= quartis[coluna][0.25]:
        return "D"
    elif x <= quartis[coluna][0.50]:
        return "C"
    elif x <= quartis[coluna][0.75]:
        return "B"
    else:
        return "A"


# INTERFACE


st.title("RFV")

st.markdown("""
**RFV** significa **Recência, Frequência e Valor** e é utilizado para segmentação de clientes
com base no comportamento de compras.

Utilizando esse tipo de agrupamento, podemos realizar ações de **marketing e CRM**
mais bem direcionadas, ajudando na personalização do conteúdo e na retenção de clientes.

#### Componentes do RFV

- **Recência (R):** Quantidade de dias desde a última compra
- **Frequência (F):** Quantidade total de compras no período
- **Valor (V):** Total de dinheiro gasto nas compras do período

➡️ **É isso que iremos fazer abaixo.**
""")

# SIDEBAR


st.sidebar.header("Suba o arquivo")

# Imagem opcional
try:
    image = Image.open("Bank-Branding.jpg")
    st.sidebar.image(image, use_column_width=True)
except Exception:
    pass

uploaded_file = st.sidebar.file_uploader(
    "Dados de marketing bancário",
    type=["csv", "xlsx"]
)



if uploaded_file is not None:

    # Leitura segura do arquivo
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, parse_dates=["DiaCompra"])
    else:
        df = pd.read_excel(uploaded_file, parse_dates=["DiaCompra"])

    st.subheader("Prévia dos dados")
    st.dataframe(df.head())



    dia_atual = df["DiaCompra"].max()

    # Recência
    df_recencia = (
        df.groupby("ID_cliente", as_index=False)["DiaCompra"]
        .max()
        .rename(columns={"DiaCompra": "UltimaCompra"})
    )

    df_recencia["Recencia"] = (dia_atual - df_recencia["UltimaCompra"]).dt.days
    df_recencia.drop(columns="UltimaCompra", inplace=True)

    # Frequência
    df_frequencia = (
        df.groupby("ID_cliente", as_index=False)["CodigoCompra"]
        .count()
        .rename(columns={"CodigoCompra": "Frequencia"})
    )

    # Valor
    df_valor = (
        df.groupby("ID_cliente", as_index=False)["ValorTotal"]
        .sum()
        .rename(columns={"ValorTotal": "Valor"})
    )

    # Merge RFV
    df_rfv = df_recencia.merge(df_frequencia, on="ID_cliente")
    df_rfv = df_rfv.merge(df_valor, on="ID_cliente")

    st.subheader("Tabela RFV")
    st.dataframe(df_rfv.head())


    quartis = {
        "Recencia": df_rfv["Recencia"].quantile([0.25, 0.5, 0.75]),
        "Frequencia": df_rfv["Frequencia"].quantile([0.25, 0.5, 0.75]),
        "Valor": df_rfv["Valor"].quantile([0.25, 0.5, 0.75])
    }

    df_rfv["R_quartil"] = df_rfv["Recencia"].apply(
        lambda x: recencia_class(x, quartis)
    )

    df_rfv["F_quartil"] = df_rfv["Frequencia"].apply(
        lambda x: freq_val_class(x, quartis, "Frequencia")
    )

    df_rfv["V_quartil"] = df_rfv["Valor"].apply(
        lambda x: freq_val_class(x, quartis, "Valor")
    )

    df_rfv["RFV_Score"] = (
        df_rfv["R_quartil"]
        + df_rfv["F_quartil"]
        + df_rfv["V_quartil"]
    )

    st.subheader("Segmentação RFV")
    st.dataframe(df_rfv.head())

    

    dict_acoes = {
        "AAA": "Clientes premium – fidelização",
        "DDD": "Churn – clientes que gastaram pouco e compraram pouco",
        "CAA": "Clientes fiéis, baixo valor – incentivo",
        "DAA": "Risco alto – reativação urgente"
    }

    df_rfv["Ação CRM"] = df_rfv["RFV_Score"].map(dict_acoes)

    st.subheader("Ações de Marketing / CRM")
    st.dataframe(df_rfv.head())



    st.subheader("Download dos resultados")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="Download CSV",
            data=convert_df_csv(df_rfv),
            file_name="RFV.csv",
            mime="text/csv"
        )

    with col2:
        st.download_button(
            label="Download Excel",
            data=convert_df_excel(df_rfv),
            file_name="RFV.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Faça o upload de um arquivo para iniciar a análise.")
