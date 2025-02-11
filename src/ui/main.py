import streamlit as st
import pandas as pd
import os
import sys
import zipfile
import shutil
import time
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

# Definir carpeta temporal de trabajo
DATA_FOLDER = "data"

# Función para limpiar la carpeta de datos
def clear_data_folder():
    if os.path.exists(DATA_FOLDER):
        for file in os.listdir(DATA_FOLDER):
            file_path = os.path.join(DATA_FOLDER, file)
            try:
                os.chmod(file_path, 0o777)  # Cambiar permisos
                os.remove(file_path)
            except Exception as e:
                print(f"Error al eliminar {file_path}: {e}")

# Crear carpeta si no existe
os.makedirs(DATA_FOLDER, exist_ok=True)

# Cargar archivos o carpeta ZIP
st.subheader("Subir archivos PDF o una carpeta ZIP con PDFs")
uploaded_files = st.file_uploader("Selecciona archivos PDF o un ZIP", type=["pdf", "zip"], accept_multiple_files=True, key="file_uploader")

# Procesar archivos subidos
pdf_files = []

if uploaded_files:
    # Limpiar solo los archivos dentro de la carpeta
    clear_data_folder()

    for file in uploaded_files:
        if file.name.endswith(".zip"):
            # Guardar archivo ZIP temporalmente
            zip_path = os.path.join(DATA_FOLDER, file.name)
            with open(zip_path, "wb") as f:
                f.write(file.getbuffer())

            # Extraer PDFs del ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(DATA_FOLDER)

            # Obtener solo los PDFs extraídos
            extracted_files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.endswith(".pdf")]
            pdf_files.extend(extracted_files)

            # Eliminar el archivo ZIP después de extraer
            os.remove(zip_path)
        else:
            # Guardar PDFs subidos individualmente
            temp_path = os.path.join(DATA_FOLDER, file.name)
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            pdf_files.append(temp_path)

# Mostrar cantidad de archivos subidos
st.subheader(f"📂 Archivos Procesados: {len(pdf_files)}")

if pdf_files:
    extracted_data = defaultdict(list)
    uploaded_files_info = {}
    duplicated_files = []
    
    for pdf_path in pdf_files:
        # Extraer datos del PDF
        data = extract_data_from_pdf(pdf_path)
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
            errores.append(f"El DNI {dni} (Entrevistadores: {entrevistadores}) tiene {len(registros)} archivo(s) en lugar de {'2' if multiple_pdfs else '1'}.")

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
