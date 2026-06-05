import streamlit as st

# Configuración de la página (Debe ser la primera línea de Streamlit)
st.set_page_config(
    page_title="Administración de Edificio",
    page_icon="🏢",
    layout="centered"
)

# Inyección de CSS corregido y optimizado
st.markdown("""
    <style>
    /* 1. Corrección para las Cajas de Selección (st.selectbox) */
    /* Forzar texto blanco en el contenedor del selectbox */
    div[data-baseweb="select"] div {
        color: #FFFFFF !important;
    }
    
    /* Asegurar visibilidad del texto y fondo oscuro en la lista desplegable */
    ul[role="listbox"] li {
        color: #FFFFFF !important;
        background-color: #1E2229 !important;
    }
    
    /* Efecto hover en las opciones del desplegable */
    ul[role="listbox"] li:hover {
        background-color: #2D323F !important;
    }

    /* 2. Corrección para los Cuadros de Información (st.info) */
    /* Modificación del contenedor de notificaciones para que contraste en tema oscuro */
    div[data-testid="stNotification"] {
        background-color: rgba(28, 140, 240, 0.1) !important;
        border: 1px solid rgb(28, 140, 240) !important;
    }
    
    /* Forzar que el texto de la alerta sea blanco y legible */
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
    
    # Aquí puedes mapear la lógica de tus departamentos reales desde la base de datos
    depto = st.selectbox(
        "Departamento a Registrar:",
        ["B1", "B2", "B3", "B4", "B11", "B12", "B13", "B14", "B21", "B22"]
    )
    
    # Simulación de cuota fija dinámica basada en el departamento seleccionado
    cuota_fija = 1050.00 if depto in ["B11", "B12", "B13", "B14"] else 950.00
    st.write(f"**Cuota mensual:** ${cuota_fija:.2f}")
    
    monto_pagado = st.number_input("Monto Pagado este mes ($):", min_value=0.0, step=50.0, value=0.0)
    multa = st.number_input("Multas aplicadas ($):", min_value=0.0, step=50.0, value=0.0)
    
    # Manejo correcto del TypeError asegurando conversión explícita de tipos numéricos
    try:
        monto_debido = float(cuota_fija) + float(multa)
    except (ValueError, TypeError):
        monto_debido = 0.0

    if st.button("Guardar Registro"):
        # Espacio reservado para tu lógica de inserción a Neon / Supabase (PostgreSQL)
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

# Uso de st.info con los selectores CSS corregidos para el texto en blanco
if mes_consulta == "Sin registros":
    st.info("El administrador aún no ha subido el reporte para este mes.")
else:
    # Simulación de la presentación de los datos del estado de cuenta
    st.write(f"Mostrando información de cuenta para el departamento **{depto_consulta}** correspondiente a **{mes_consulta}**.")
