import pandas as pd
import os

def generate_excel_report(df, output_folder="output", filename="Reporte_Entrevistas.xlsx"):
    """
    Genera un archivo Excel a partir del DataFrame proporcionado en una sola hoja,
    agregando columnas de entrevistador según la sección seleccionada.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_path = os.path.join(output_folder, filename)
    
    try:
        # Guardar DataFrame en un solo archivo Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
    except Exception as e:
        print(f"Error al generar el archivo Excel: {e}")
        return None

# Prueba de la función
if __name__ == "__main__":
    data = {
        "codigo": ["00175262", "00175263"],
        "modalidad": ["FACTOR EXCELENCIA", "ADMISIÓN REGULAR"],
        "programa": ["MEDICINA", "INGENIERÍA BIOMÉDICA"],
        "documento": ["60482615", "60482616"],
        "Nota Entrevistador 1": [23, 35],
        "Nombre Entrevistador 1": ["Dr. Pérez", "Dr. García"],
        "Nota Entrevistador 2": [43, 40],
        "Nombre Entrevistador 2": ["Dra. López", "Dra. Ramírez"],
        "Total": [66, 75]
    }
    df_test = pd.DataFrame(data)
    excel_path = generate_excel_report(df_test)
    print(f"Excel generado: {excel_path}")
