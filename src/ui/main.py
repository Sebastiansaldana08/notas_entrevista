import streamlit as st
import pandas as pd
import os
import sys
import zipfile
import shutil
import time
from collections import defaultdict
from streamlit_option_menu import option_menu

# Agregar el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.extraction.pdf_reader import extract_data_from_pdf
from src.processing.report_generator import generate_excel_report

# Configuración de la página (quitamos 'wide')
st.set_page_config(page_title="Procesador de Entrevistas")

# Estilos CSS personalizados
st.markdown(
    """
    <style>
        .header {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #00A86B;
            padding: 10px;
        }
        .subheader {
            text-align: center;
            font-size: 20px;
            color: #EEEEEE;
            margin-bottom: 20px;
        }
    </style>
    <div class="header">📄 Procesador de Entrevistas</div>
    <div class="subheader">Automatización del procesamiento de entrevistas y generación de reportes</div>
    """,
    unsafe_allow_html=True
)

# Menú de selección de sección
seccion = option_menu(
    menu_title="📌 Selecciona la carrera",
    options=["Medicina / Ingeniería Biomédica", "Todas las carreras, excepto Medicina"],
    icons=["activity", "book"],
    default_index=0,
    orientation="vertical"
)

multiple_pdfs = seccion == "Medicina / Ingeniería Biomédica"

# Carpeta de trabajo
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

def clear_data_folder():
    for file in os.listdir(DATA_FOLDER):
        file_path = os.path.join(DATA_FOLDER, file)
        try:
            os.chmod(file_path, 0o777)
            os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

# Subida de archivos ZIP o PDFs
st.subheader("📂 Sube archivos PDF en ambas secciones. ZIPs permitidos solo en 'Todas las carreras'.")
uploaded_files = st.file_uploader("Selecciona archivos PDF o un ZIP", type=["pdf", "zip"], accept_multiple_files=True, key="file_uploader")

pdf_files = []
zip_files = []

if uploaded_files:
    clear_data_folder()
    
    for file in uploaded_files:
        if file.name.endswith(".zip"):
            zip_path = os.path.join(DATA_FOLDER, file.name)
            with open(zip_path, "wb") as f:
                f.write(file.getbuffer())
            zip_files.append(zip_path)
        else:
            temp_path = os.path.join(DATA_FOLDER, file.name)
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            pdf_files.append(temp_path)
    
    # Procesar ZIPs
    for zip_path in zip_files:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DATA_FOLDER)
        os.remove(zip_path)
    
    pdf_files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.endswith(".pdf")]

st.subheader(f"📊 Archivos Procesados: {len(pdf_files)}")

if pdf_files:
    extracted_data = defaultdict(list)
    uploaded_files_info = {}
    duplicated_files = []
    
    for pdf_path in pdf_files:
        data = extract_data_from_pdf(pdf_path)
        if data:
            dni = data["documento"].strip()
            entrevistador = data.get("entrevistador", "Desconocido")
            
            if dni in extracted_data:
                entrevistadores_existentes = [r["entrevistador"] for r in extracted_data[dni]]
                if multiple_pdfs and entrevistador not in entrevistadores_existentes:
                    extracted_data[dni].append(data)
                else:
                    duplicated_files.append(f"DNI {dni} - Entrevistador: {entrevistador}")
                    continue
            else:
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
                "Nota Entrevistador 1": int(registros[0]["total"]),
                "Nombre Entrevistador 1": registros[0]["entrevistador"]
            }
            if multiple_pdfs:
                merged_data["Nota Entrevistador 2"] = int(registros[1]["total"])
                merged_data["Nombre Entrevistador 2"] = registros[1]["entrevistador"]
                merged_data["Total"] = merged_data["Nota Entrevistador 1"] + merged_data["Nota Entrevistador 2"]
            valid_data.append(merged_data)
        else:
            entrevistadores = ", ".join([r["entrevistador"] for r in registros])
            errores.append(f"❌ DNI {dni} solo tiene {len(registros)} archivo(s).")
    
    df = pd.DataFrame(valid_data)
    st.subheader("📊 Datos Extraídos")
    st.dataframe(df)
    
    if errores or duplicated_files:
        st.subheader("⚠️ Archivos con Errores")
        for error in errores:
            st.error(error)
        for duplicate in duplicated_files:
            st.warning(f"📌 Archivo duplicado detectado: {duplicate}")
    
    if not df.empty and st.button("📥 Generar Reporte en Excel"):
        excel_path = generate_excel_report(df)
        with open(excel_path, "rb") as f:
            st.download_button(label="📥 Descargar Reporte Excel", data=f, file_name="Reporte_Entrevistas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
