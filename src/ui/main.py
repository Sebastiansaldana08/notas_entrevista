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
seccion = st.sidebar.radio("", ["Medicina / Ingeniería Biomédica", "Todas las carreras"])

# Sección activa según selección
if seccion == "Medicina / Ingeniería Biomédica":
    st.header("📄 Procesador de Entrevistas - Medicina / Ingeniería Biomédica")
    multiple_pdfs = True
else:
    st.header("📄 Procesador de Entrevistas - Todas las Carreras")
    multiple_pdfs = False

# Cargar archivos
st.subheader("Subir archivos PDF")
uploaded_files = st.file_uploader("Selecciona archivos PDF", type=["pdf"], accept_multiple_files=True, key="file_uploader")

if uploaded_files:
    extracted_data = defaultdict(list)
    uploaded_files_info = {}
    duplicated_files = []
    
    for file in uploaded_files:
        # Guardar archivos temporalmente
        temp_path = os.path.join("data", file.name)
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())
        
        # Extraer datos
        data = extract_data_from_pdf(temp_path)
        if data:
            dni = data["documento"].strip()
            entrevistador = data.get("entrevistador", "Desconocido")
            
            if dni in uploaded_files_info:
                if multiple_pdfs and uploaded_files_info[dni] != entrevistador:
                    extracted_data[dni].append(data)
                else:
                    duplicated_files.append(f"DNI {dni} - Entrevistador: {entrevistador}")
                    continue
            else:
                uploaded_files_info[dni] = entrevistador
                extracted_data[dni].append(data)

    valid_data = []
    errores = []

    for dni, registros in extracted_data.items():
        if (multiple_pdfs and len(registros) == 2) or (not multiple_pdfs and len(registros) == 1):
            merged_data = {
                "codigo": registros[0]["codigo"],
                "modalidad": registros[0]["modalidad"],
                "programa": registros[0]["programa"],
                "documento": dni,
                "Nota Entrevistador 1": int(registros[0]["total"])
            }
            if multiple_pdfs:
                merged_data["Nota Entrevistador 2"] = int(registros[1]["total"])
                merged_data["Total"] = merged_data["Nota Entrevistador 1"] + merged_data["Nota Entrevistador 2"]
            valid_data.append(merged_data)
        else:
            entrevistadores = ", ".join([r["entrevistador"] for r in registros])
            errores.append(f"El DNI {dni} (Entrevistador: {entrevistadores}) tiene {len(registros)} archivo(s) en lugar de {'2' if multiple_pdfs else '1'}.")

    df = pd.DataFrame(valid_data)
    
    # Mostrar tabla con los datos extraídos
    st.subheader("📊 Datos Extraídos")
    st.dataframe(df)
    
    # Mostrar errores si los hay
    if errores or duplicated_files:
        st.subheader("⚠️ Archivos con Errores")
        for error in errores:
            st.warning(error)
        for duplicate in duplicated_files:
            st.warning(f"📌 Archivo duplicado detectado: {duplicate}")
    
    # Botón para exportar a Excel
    if not df.empty and st.button("📥 Generar Reporte en Excel"):
        excel_path = generate_excel_report(df)
        with open(excel_path, "rb") as f:
            st.download_button(label="📥 Descargar Reporte Excel", data=f, file_name="Reporte_Entrevistas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
