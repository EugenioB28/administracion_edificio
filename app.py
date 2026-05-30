import streamlit as st
import pandas as pd
import psycopg2
import re
from io import BytesIO

# ============ CONFIGURACIÓN E IDENTIDAD VISUAL ============
st.set_page_config(page_title="Admin Edificio", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }

    [data-testid="stMain"] p, [data-testid="stMain"] span, [data-testid="stMain"] label,
    [data-testid="stMain"] div, [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3 {
        color: #1A1A1A !important;
    }

    [data-testid="stSidebar"] { background-color: #1A3E5C !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }

    div.stButton > button {
        background-color: #1A3E5C !important;
        color: white !important;
        border: 1px solid #1A3E5C !important;
        border-radius: 5px;
        font-weight: bold !important;
    }
    div.stButton > button p { color: white !important; }

    .footer {
        position: fixed; left: 20px; bottom: 20px; text-align: left;
        color: #555555 !important; font-size: 12px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ============ CONEXIÓN A BASE DE DATOS ============
try:
    DB_URI = st.secrets["db_uri"]
except:
    st.error("Error: Configura 'db_uri' en los Secrets de Streamlit.")
    st.stop()

def conectar_db():
    return psycopg2.connect(DB_URI)

conn = conectar_db()
cursor = conn.cursor()

# ============ FUNCIONES AUXILIARES ============
def ordenar_deptos_natural(lista_deptos):
    def clasificar(texto):
        partes = re.split(r'(\d+)', texto)
        return [int(p) if p.isdigit() else p for p in partes]
    return sorted(lista_deptos, key=clasificar)

def depurar_historico():
    cursor.execute("SELECT DISTINCT mes_anio FROM bitacora_ingresos")
    meses = [fila[0] for fila in cursor.fetchall()]

    if len(meses) > 12:
        mes_a_borrar = meses[0]
        cursor.execute("DELETE FROM bitacora_ingresos WHERE mes_anio = %s", (mes_a_borrar,))
        cursor.execute("DELETE FROM bitacora_egresos WHERE mes_anio = %s", (mes_a_borrar,))
        conn.commit()
        st.sidebar.warning(f"Historial depurado: Se eliminó '{mes_a_borrar}' para mantener el límite de 12 meses.")

# ============ PANEL LATERAL ============
with st.sidebar:
    st.title("Administración 🏢")
    vista = st.sidebar.radio("Tipo de Vista:", ["Departamentos", "Administrador"])

    es_admin = False
    if vista == "Administrador":
        password = st.text_input("Contraseña de Acceso:", type="password")
        if password == "Admin2026":
            es_admin = True
            st.success("Acceso Autorizado")
        elif password != "":
            st.error("Contraseña Incorrecta")

    st.markdown("---")
    with st.expander("Información"):
        st.write("Versión: 1.0.0")
        st.write("Firma técnica:")
        st.write("**Eugenio Badillo**")

# ============ VISTA DEPARTAMENTOS ============
if vista == "Departamentos":
    st.title("🔍 Consulta de Departamento")
    
    cursor.execute("SELECT depto FROM configuracion_deptos")
    deptos_raw = [f[0] for f in cursor.fetchall()]
    lista_deptos = ordenar_deptos_natural(deptos_raw)
    
    col1, col2 = st.columns(2)
    with col1:
        depto_sel = st.selectbox("Selecciona tu Departamento:", lista_deptos)
    with col2:
        cursor.execute("SELECT DISTINCT mes_anio FROM bitacora_ingresos")
        lista_meses = [f[0] for f in cursor.fetchall()]
        mes_sel = st.selectbox("Selecciona el Mes:", lista_meses if lista_meses else ["Sin registros"])

    if st.button("Buscar Información"):
        query = "SELECT depto, saldo_anterior, pago, multa, adeudo_mes, pago_anticipado, banco_efectivo FROM bitacora_ingresos WHERE depto = %s AND mes_anio = %s"
        df = pd.read_sql_query(query, conn, params=(depto_sel, mes_sel))
        
        if not df.empty:
            st.success(f"Resultados para el Departamento {depto_sel} en {mes_sel}:")
            df.columns = ["Depto.", "Saldo Anterior", "Pago", "Multa", "Adeudo del Mes", "Pago Anticipado", "Banco/Efectivo"]
            st.dataframe(df.set_index('Depto.'), use_container_width=True)
        else:
            st.info("No se encontraron registros cargados para este departamento en el mes seleccionado.")

# ============ VISTA ADMINISTRADOR ============
elif vista == "Administrador" and es_admin:
    st.title("⚙️ Panel de Control - Administrador")
    
    operacion = st.selectbox("Selecciona la acción a realizar:", ["Registrar Ingresos", "Registrar Egresos", "Modificar Valores Predefinidos"])
    mes_actual = st.text_input("Mes de Trabajo Actual (Ejemplo: Mayo 2026):", "Mayo 2026")

    # OPERACIÓN A: REGISTRAR INGRESOS
    if operacion == "Registrar Ingresos":
        st.subheader(f"Carga de Ingresos - {mes_actual}")
        
        cursor.execute("SELECT depto, cuota_fija, saldo_anterior FROM configuracion_deptos")
        deptos_info = cursor.fetchall()
        
        deptos_raw = [d[0] for d in deptos_info]
        lista_deptos = ordenar_deptos_natural(deptos_raw)
        
        depto = st.selectbox("Departamento a Registrar:", lista_deptos)
        
        cuota_fija = next(d[1] for d in deptos_info if d[0] == depto)
        saldo_anterior = next(d[2] for d in deptos_info if d[0] == depto)
        
        # Cuota mensual compacta
        st.text(f"Cuota mensual: ${cuota_fija:.2f}")
        
        pago = st.number_input("Monto Pagado este mes ($):", min_value=0.0, step=50.0)
        multa = st.number_input("Multas aplicadas ($):", min_value=0.0, step=50.0)
        
        monto_debido = cuota_fija + multa
        if pago >= monto_debido:
            adeudo_mes = 0.0
            pago_anticipado = pago - monto_debido
        else:
            adeudo_mes = monto_debido - pago
            pago_anticipado = 0.0
            
        # Formato visual limpio del calculo explicativo sin formato matemático crudo
        texto_calculo = f"Adeudo del Mes: ${adeudo_mes:.2f}   |   Pago Anticipado: ${pago_anticipado:.2f}   |   Saldo Anterior: ${saldo_anterior:.2f}"
        st.text(texto_calculo)
        
        banco_efectivo = st.selectbox("Forma de Pago:", ["Banco", "Efectivo"])
        
        if st.button("Guardar Registro de Ingreso"):
            cursor.execute("""
                INSERT INTO bitacora_ingresos 
                (mes_anio, depto, saldo_anterior, pago, multa, adeudo_mes, pago_anticipado, banco_efectivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (mes_anio, depto) DO UPDATE SET 
                    saldo_anterior = EXCLUDED.saldo_anterior,
                    pago = EXCLUDED.pago,
                    multa = EXCLUDED.multa,
                    adeudo_mes = EXCLUDED.adeudo_mes,
                    pago_anticipado = EXCLUDED.pago_anticipado,
                    banco_efectivo = EXCLUDED.banco_efectivo
            """, (mes_actual, depto, saldo_anterior, pago, multa, adeudo_mes, pago_anticipado, banco_efectivo))
            
            nuevo_saldo_anterior = saldo_anterior - adeudo_mes + pago_anticipado
            cursor.execute("UPDATE configuracion_deptos SET saldo_anterior = %s WHERE depto = %s", (nuevo_saldo_anterior, depto))
            
            conn.commit()
            st.success(f"¡Registro guardado exitosamente para el departamento {depto}!")
            depurar_historico()

    # OPERACIÓN B: REGISTRAR EGRESOS
    elif operacion == "Registrar Egresos":
        st.subheader(f"Carga de Egresos - {mes_actual}")
        tipo_egreso = st.radio("Tipo de Egreso:", ["Importe Fijo (Catálogo)", "Importe Variable / Extraordinario"])
        
        if tipo_egreso == "Importe Fijo (Catálogo)":
            cursor.execute("SELECT concepto, importe FROM egresos_fijos")
            fijos_info = cursor.fetchall()
            
            # Validación robusta de catálogo vacío
            if fijos_info:
                lista_conceptos = [f[0] for f in fijos_info]
                concepto = st.selectbox("Concepto Fijo:", lista_conceptos)
                importe_sugerido = next(f[1] for f in fijos_info if f[0] == concepto)
                importe = st.number_input("Importe ($):", value=float(importe_sugerido))
            else:
                st.warning("El catálogo de egresos fijos está vacío en la base de datos.")
                concepto = st.text_input("Concepto Fijo Manual:")
                importe = st.number_input("Importe ($):", min_value=0.0, step=50.0)
        else:
            concepto = st.text_input("Concepto Variable (Ej. Reparacion lampara):")
            importe = st.number_input("Importe ($):", min_value=0.0, step=10.0)
            
        if st.button("Guardar Registro de Egreso"):
            cursor.execute("""
                INSERT INTO bitacora_egresos (mes_anio, tipo, concepto, importe)
                VALUES (%s, %s, %s, %s)
            """, (mes_actual, tipo_egreso, concepto, importe))
            conn.commit()
            st.success("¡Egreso registrado correctamente!")

    # OPERACIÓN C: MODIFICAR VALORES PREDEFINIDOS
    elif operacion == "Modificar Valores Predefinidos":
        st.subheader("Configuración de Valores del Sistema")
        
        st.markdown("### Cuotas y Saldos Anteriores de Departamentos")
        df_deptos = pd.read_sql_query("SELECT depto, cuota_fija, saldo_anterior FROM configuracion_deptos", conn)
        
        deptos_ordenados = ordenar_deptos_natural(df_deptos['depto'].tolist())
        df_deptos = df_deptos.set_index('depto').loc[deptos_ordenados].reset_index()
        
        df_deptos.columns = ["Departamento", "Cuota Fija", "Saldo Anterior"]
        st.dataframe(df_deptos, use_container_width=True)
        
        depto_mod = st.selectbox("Selecciona Depto a modificar:", df_deptos['Departamento'])
        
        # Reducción estricta de departamentos con cuota especial de $950
        cuota_sugerida = 950.0 if depto_mod in ["B2", "B4", "B23", "B33", "B34"] else 1050.0
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nueva_cuota = st.number_input("Nueva cuota ($):", min_value=0.0, step=50.0, value=cuota_sugerida)
        with col_c2:
            nuevo_saldo_init = st.number_input("Modificar Saldo Anterior ($):", step=50.0, value=0.0)
            
        if st.button("Actualizar Valores Predefinidos"):
            cursor.execute("""
                UPDATE configuracion_deptos 
                SET cuota_fija = %s, saldo_anterior = %s 
                WHERE depto = %s
            """, (nueva_cuota, nuevo_saldo_init, depto_mod))
            conn.commit()
            st.success(f"Valores de {depto_mod} actualizados con éxito.")
            st.rerun()

    # ============ GENERACIÓN DE REPORTES PDF ============
    st.markdown("---")
    st.subheader("🖨️ Generar Estado de Cuenta Imprimible")
    
    if st.button("Generar Reporte PDF"):
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        pdf_filename = f"Estado_de_Cuenta_{mes_actual.replace(' ', '_')}.pdf"
        
        doc = SimpleDocTemplate(pdf_filename, pagesize=landscape(letter), leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()
        
        style_title = ParagraphStyle(
            name='CenterTitle',
            parent=styles['Title'],
            fontName='Helvetica',
            fontSize=22,
            spaceAfter=20,
            alignment=1
        )
        
        titulo = f"Estado de Cuenta {mes_actual}"
        story.append(Paragraph(titulo, style_title))
        story.append(Spacer(1, 15))
        
        cursor.execute("SELECT depto, cuota_fija, saldo_anterior FROM configuracion_deptos")
        todos_los_deptos = cursor.fetchall()
        deptos_mapeados = ordenar_deptos_natural([d[0] for d in todos_los_deptos])
        
        query_ingresos = "SELECT depto, saldo_anterior, pago, multa, adeudo_mes, pago_anticipado, banco_efectivo FROM bitacora_ingresos WHERE mes_anio = %s"
        df_ingresos_guardados = pd.read_sql_query(query_ingresos, conn, params=(mes_actual,))
        dict_ingresos = df_ingresos_guardados.set_index('depto').to_dict('index')
        
        datos_completos_tabla = []
        for d_name in deptos_mapeados:
            if d_name in dict_ingresos:
                info = dict_ingresos[d_name]
                datos_completos_tabla.append([
                    d_name,
                    f"{info['saldo_anterior']:.1f}",
                    f"{info['pago']:.1f}",
                    f"{info['multa']:.1f}",
                    f"{info['adeudo_mes']:.1f}",
                    f"{info['pago_anticipado']:.1f}",
                    str(info['banco_efectivo'])
                ])
            else:
                cfg_depto = next(d for d in todos_los_deptos if d[0] == d_name)
                cuota_base = cfg_depto[1] if cfg_depto[1] is not None else (950.0 if d_name in ["B2", "B4", "B23", "B33", "B34"] else 1050.0)
                saldo_ant = cfg_depto[2] if cfg_depto[2] is not None else 0.0
                
                datos_completos_tabla.append([
                    d_name,
                    f"{saldo_ant:.1f}",
                    "0.0",
                    "0.0",
                    f"{cuota_base:.1f}",
                    "0.0",
                    "Efectivo"
                ])
        
        headers = ["Departamento", "Saldo Anterior", "Pago", "Multa", "Adeudo del Mes", "Pago Anticipado", "Banco/Efectivo"]
        data_tabla = [headers] + datos_completos_tabla
        
        tabla_ingresos = Table(data_tabla, colWidths=[105, 100, 95, 85, 115, 115, 105])
        tabla_ingresos.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.white),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(tabla_ingresos)
        story.append(Spacer(1, 25))
        
        style_heading = ParagraphStyle(
            name='LeftHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceAfter=10
        )
        story.append(Paragraph("Egresos:", style_heading))
        
        style_egreso = ParagraphStyle(
            name='EgresoRow',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14
        )
        
        # Extracción e inclusión independiente de Egresos Fijos del catálogo y Variables del mes
        cursor.execute("SELECT concepto, importe FROM egresos_fijos")
        egresos_fijos_lista = cursor.fetchall()
        
        cursor.execute("SELECT concepto, importe FROM bitacora_egresos WHERE mes_anio = %s AND tipo != 'Importe Fijo (Catálogo)'", (mes_actual,))
        egresos_variables_lista = cursor.fetchall()
        
        todos_los_egresos = egresos_fijos_lista + egresos_variables_lista
        
        if todos_los_egresos:
            for concepto, importe in todos_los_egresos:
                ancho_fijo = 110  
                puntos = "." * (ancho_fijo - len(f"Concepto (Ejemplo: {concepto})"))
                if len(puntos) < 4:
                    puntos = "...."
                
                texto_egreso = f"Concepto (Ejemplo: {concepto}){puntos}${importe:,.2f}"
                story.append(Paragraph(texto_egreso, style_egreso))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("No se registraron egresos en este mes.", style_egreso))
            
        doc.build(story)
        
        with open(pdf_filename, "rb") as pdf_file:
            st.download_button(
                label="Descargar Estado de Cuenta PDF",
                data=pdf_file,
                file_name=pdf_filename,
                mime="application/pdf"
            )

st.markdown('<div class="footer">EEBM</div>', unsafe_allow_html=True)
