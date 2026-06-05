import streamlit as st

# Configuración de la página original
st.set_page_config(
    page_title="Administración de Edificio",
    page_icon="🏢",
    layout="centered"
)

# Estilos CSS corregidos sin alterar la estructura ni añadir selectores globales dañinos
st.markdown("""
    <style>
    /* Corrección del texto en las cajas de selección (st.selectbox) */
    div[data-baseweb="select"] div {
        color: #FFFFFF !important;
    }
    
    /* Fondo oscuro y texto blanco en las opciones del menú desplegable */
    ul[role="listbox"] li {
        color: #FFFFFF !important;
        background-color: #1E2229 !important;
    }
    
    /* Hover de las opciones del menú desplegable */
    ul[role="listbox"] li:hover {
        background-color: #2D323F !important;
    }

    /* Corrección para que el texto de st.info sea blanco sobre su fondo azul original */
    div[data-testid="stNotification"] p {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- PANEL DE CONTROL ---
st.title("Panel de Control - Administrador")

accion = st.selectbox(
    "Selecciona la acción a realizar:",
    ["Registrar Ingresos", "Consultar Estado de Cuenta"]
)

mes_trabajo = st.text_input("Mes de Trabajo Actual (Ejemplo: Mayo 2026):", value="Mayo 2026")

if accion == "Registrar Ingresos":
    st.header(f"Carga de Ingresos - {mes_trabajo}")
    
    depto = st.selectbox(
        "Departamento a Registrar:",
        ["B1", "B2", "B3", "B4", "B11", "B12", "B13", "B14", "B21", "B22"]
    )
    
    cuota_fija = 1050.00 if depto in ["B11", "B12", "B13", "B14"] else 950.00
    st.write(f"**Cuota mensual:** ${cuota_fija:.2f}")
    
    monto_pagado = st.number_input("Monto Pagado este mes ($):", min_value=0.0, step=50.0, value=0.0)
    multa = st.number_input("Multas aplicadas ($):", min_value=0.0, step=50.0, value=0.0)
    
    monto_debido = cuota_fija + multa

    if st.button("Guardar Registro"):
        st.success(f"Registro guardado correctamente para el departamento {depto}.")

# --- CONSULTA DE DEPARTAMENTO ---
st.write("---")
st.title("Consulta de Departamento")

col1, col2 = st.columns(2)
with col1:
    depto_consulta = st.selectbox("Selecciona tu Departamento:", ["B1", "B2", "B3", "B4"], key="consulta_depto")
with col2:
    mes_consulta = st.selectbox("Selecciona el Mes:", ["Sin registros", "Mayo 2026"], key="consulta_mes")

st.header("Estado de Cuenta del Mes 📄")

if mes_consulta == "Sin registros":
    st.info("El administrador aún no ha subido el reporte para este mes.")
else:
    st.write(f"Mostrando información de cuenta para el departamento **{depto_consulta}** correspondiente a **{mes_consulta}**.")
