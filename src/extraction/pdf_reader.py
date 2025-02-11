import fitz  # PyMuPDF

def extract_data_from_pdf(pdf_path):
    """
    Extrae los datos clave de un archivo PDF de entrevista.
    Retorna un diccionario con los valores extraídos.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""

        # Leer todo el texto del PDF
        for page in doc:
            text += page.get_text("text") + "\n"

        doc.close()

        # Convertir el texto en una lista de líneas
        lines = text.split("\n")

        # Extraer los valores asegurando que estén en la siguiente línea
        data = {
            "codigo": extract_next_line(lines, "CODIGO"),
            "modalidad": extract_next_line(lines, "MODALIDAD"),
            "programa": extract_next_line(lines, "PROGRAMA"),
            "documento": extract_next_line(lines, "DOCUMENTO"),
            "total": extract_next_line(lines, "TOTAL")
        }

        # Verificar si el documento contiene DNI correctamente
        if "DNI N°" in data["documento"]:
            data["documento"] = data["documento"].replace("DNI N°", "").strip()
        else:
            print(f"Advertencia: No se encontró un DNI válido en {pdf_path}")

        return data

    except Exception as e:
        print(f"Error al procesar el PDF: {pdf_path} -> {str(e)}")
        return None

def extract_next_line(lines, keyword):
    """
    Busca un valor en las líneas del texto y extrae el valor que está en la siguiente línea.
    """
    for i, line in enumerate(lines):
        if keyword in line:
            if i + 1 < len(lines):  # Si hay una línea después, tomarla como valor
                return lines[i + 1].strip()
    return "No encontrado"

# Prueba de la función
if __name__ == "__main__":
    pdf_path = r"c:\Users\SEBASTIAN\Downloads\entrevista-60482615.pdf"  # Reemplazar con un PDF de prueba
    resultado = extract_data_from_pdf(pdf_path)
    print(resultado)
