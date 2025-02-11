import streamlit as st
import pandas as pd
import os
import sys
from collections import defaultdict

# Agregar el directorio raíz del proyecto a `sys.path`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.extraction.pdf_reader import extract_data_from_pdf
from src.processing.report_generator import generate_excel_report

# Configuración de la página
st.set_page_config(page_title="Procesador de Entrevistas", layout="wide")

# Título principal
st.title("Procesador de Entrevistas")

# Opción de selección de sección
st.sidebar.header("Seleccione la sección")
seccion = st.sidebar.radio("", ["Medicina / Ingeniería Biomédica", "Todas las carreras (Próximamente)"])

# Mensaje de desarrollo para la segunda opción
if seccion == "Todas las carreras (Próximamente)":
    st.warning("🔧 Esta opción estará disponible en futuras actualizaciones. Por ahora, seleccione 'Medicina / Ingeniería Biomédica'.")
    st.stop()

# Sección activa: Medicina / Ingeniería Biomédica
st.header("📄 Procesador de Entrevistas - Medicina / Ingeniería Biomédica")

# Cargar archivos
st.subheader("Subir archivos PDF")
uploaded_files = st.file_uploader("Selecciona múltiples archivos PDF (dos por postulante)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    extracted_data = defaultdict(list)
    
    for file in uploaded_files:
        # Guardar archivos temporalmente
        temp_path = os.path.join("data", file.name)
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())
        
        # Extraer datos
        data = extract_data_from_pdf(temp_path)
        if data:
            extracted_data[data["documento"].strip()].append(data)

    valid_data = []
    errores = []

    for dni, registros in extracted_data.items():
        if len(registros) == 2:  # Verificar que hay dos PDFs por postulante
            merged_data = {
                "codigo": registros[0]["codigo"],
                "modalidad": registros[0]["modalidad"],
                "programa": registros[0]["programa"],
                "documento": dni,
                "Nota Entrevistador 1": int(registros[0]["total"]),
                "Nota Entrevistador 2": int(registros[1]["total"]),
                "Total": int(registros[0]["total"]) + int(registros[1]["total"])
            }
            valid_data.append(merged_data)
        else:
            errores.append(f"El DNI {dni} tiene {len(registros)} archivo(s) en lugar de 2.")

    df = pd.DataFrame(valid_data)
    
    # Mostrar tabla con los datos extraídos
    st.subheader("📊 Datos Extraídos")
    st.dataframe(df)
    
    # Mostrar errores si los hay
    if errores:
        st.subheader("⚠️ Archivos con Errores")
        for error in errores:
            st.warning(error)
    
    # Botón para exportar a Excel
    if not df.empty and st.button("📥 Generar Reporte en Excel"):
        excel_path = generate_excel_report(df)
        with open(excel_path, "rb") as f:
            st.download_button(label="📥 Descargar Reporte Excel", data=f, file_name="Reporte_Entrevistas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
