import streamlit as st
import pandas as pd
import os
import sys
import zipfile
import shutil
import time
from collections import defaultdict
from streamlit_option_menu import option_menu  # Importamos la opción de menú

# Agregar el directorio raíz del proyecto a `sys.path`
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
        .menu-container {
            display: flex;
            justify-content: center;
            padding: 20px;
        }
        .menu-box {
            background-color: #2C3E50;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 60%;
        }
        .menu-title {
            font-size: 22px;
            color: white;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .option-menu {
            display: flex;
            justify-content: center;
        }
        .option-menu .stMarkdown {
            color: white !important;
        }
    </style>
    <div class="header">📄Procesador de Entrevistas</div>
    <div class="subheader">Automatización del procesamiento de entrevistas y generación de reportes</div>
    """,
    unsafe_allow_html=True
)

# Menú de selección de sección (CENTRADO)
st.markdown('<div class="menu-container">', unsafe_allow_html=True)
with st.container():
    
    # Título del selector
    st.markdown('<div class="menu-title">📌 Selecciona la carrera</div>', unsafe_allow_html=True)

    # Opción de selección centrada
    seccion = option_menu(
        menu_title="",
        options=["Medicina / Ingeniería Biomédica", "Todas las carreras, excepto Medicina"],
        icons=["activity", "book"],
        default_index=0,
        orientation="vertical"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cerrar la caja del menú
st.markdown('</div>', unsafe_allow_html=True)  # Cerrar el contenedor del menú

# Sección activa según selección (Alineado a la izquierda)
st.markdown(f"<h3 style='text-align: left; color: #EEEEEE;'>Procesador de Entrevistas - {seccion}</h3>", unsafe_allow_html=True)
multiple_pdfs = seccion == "Medicina / Ingeniería Biomédica"

# Definir carpeta temporal de trabajo
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Función para limpiar la carpeta de datos
def clear_data_folder():
    for file in os.listdir(DATA_FOLDER):
        file_path = os.path.join(DATA_FOLDER, file)
        try:
            os.chmod(file_path, 0o777)  # Cambiar permisos
            os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

# Cargar archivos o carpeta ZIP
st.markdown("<h4 style='text-align: left;'>📂 Subir archivos PDF o una carpeta ZIP con PDFs</h4>", unsafe_allow_html=True)
uploaded_files = st.file_uploader("Selecciona archivos PDF o un ZIP", type=["pdf", "zip"], accept_multiple_files=True, key="file_uploader")

# Procesar archivos subidos
pdf_files = []

if uploaded_files:
    clear_data_folder()  # Limpiar solo los archivos dentro de la carpeta
    
    for file in uploaded_files:
        if file.name.endswith(".zip"):
            zip_path = os.path.join(DATA_FOLDER, file.name)
            with open(zip_path, "wb") as f:
                f.write(file.getbuffer())

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(DATA_FOLDER)

            extracted_files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.endswith(".pdf")]
            pdf_files.extend(extracted_files)
            os.remove(zip_path)
        else:
            temp_path = os.path.join(DATA_FOLDER, file.name)
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            pdf_files.append(temp_path)

st.markdown(f"<h4 style='text-align: left; color: #EEEEEE;'>📊 Archivos Procesados: {len(pdf_files)}</h4>", unsafe_allow_html=True)

if pdf_files:
    extracted_data = defaultdict(list)
    uploaded_files_info = {}
    duplicated_files = []
    
    for pdf_path in pdf_files:
        data = extract_data_from_pdf(pdf_path)
        if data:
            dni = data["documento"].strip()
            entrevistador = data.get("entrevistador", "Desconocido")
            
            # Se verifica por clave única (DNI, ENTREVISTADOR)
            dni_key = (dni, entrevistador)

            extracted_data[dni_key].append(data)

    valid_data = []
    errores = []

    # Reorganizar la estructura para validar correctamente los archivos de cada postulante
    grouped_data = defaultdict(list)
    for (dni, entrevistador), registros in extracted_data.items():
        grouped_data[dni].append((entrevistador, registros))

    for dni, entrevistador_registros in grouped_data.items():
        if multiple_pdfs and len(entrevistador_registros) == 2:  # Debe haber 2 entrevistadores
            registros1 = entrevistador_registros[0][1][0]  # Datos del primer entrevistador
            registros2 = entrevistador_registros[1][1][0]  # Datos del segundo entrevistador
            
            merged_data = {
                "codigo": registros1["codigo"],
                "modalidad": registros1["modalidad"],
                "programa": registros1["programa"],
                "documento": dni,
                "Nota Entrevistador 1": int(registros1["total"]),
                "Nombre Entrevistador 1": registros1["entrevistador"],
                "Nota Entrevistador 2": int(registros2["total"]),
                "Nombre Entrevistador 2": registros2["entrevistador"],
                "Total": int(registros1["total"]) + int(registros2["total"])
            }
            valid_data.append(merged_data)
        elif not multiple_pdfs and len(entrevistador_registros) == 1:  # Solo un entrevistador requerido
            registros1 = entrevistador_registros[0][1][0]
            merged_data = {
                "codigo": registros1["codigo"],
                "modalidad": registros1["modalidad"],
                "programa": registros1["programa"],
                "documento": dni,
                "Nota Entrevistador 1": int(registros1["total"]),
                "Nombre Entrevistador 1": registros1["entrevistador"]
            }
            valid_data.append(merged_data)
        else:
            entrevistadores = ", ".join([r[0] for r in entrevistador_registros])
            errores.append(f"El DNI {dni} tiene {len(entrevistador_registros)} archivo(s) en lugar de {'2' if multiple_pdfs else '1'}. Entrevistadores detectados: {entrevistadores}")

    df = pd.DataFrame(valid_data)
    st.subheader("📊 Datos Extraídos")
    st.dataframe(df)
    
    # **Mostrar errores si los hay (Mejorado para asegurarse de que se muestren correctamente)**
    if errores or duplicated_files:
        st.subheader("⚠️ Archivos con Errores")
        if errores:
            for error in errores:
                st.error(error)
        if duplicated_files:
            for duplicate in duplicated_files:
                st.warning(f"📌 Archivo duplicado detectado: {duplicate}")
    
    # Botón para exportar a Excel
    if not df.empty and st.button("📥 Generar Reporte en Excel"):
        excel_path = generate_excel_report(df)
        with open(excel_path, "rb") as f:
            st.download_button(label="📥 Descargar Reporte Excel", data=f, file_name="Reporte_Entrevistas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
