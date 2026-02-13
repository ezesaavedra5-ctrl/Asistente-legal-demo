import streamlit as st
from groq import Groq
from fpdf import FPDF

# 1. Agenda del Estudio (Editable)
turnos_ocupados = ["Lunes 16:00", "Lunes 17:00", "Miércoles 18:30"]

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

# Función para generar el comprobante PDF corregida
def generar_pdf(nombre, fecha, motivo):
    pdf = FPDF()
    pdf.add_page()
    
    # Usamos fuentes estándar que no dan error de codificación fácil
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "ESTUDIO JURIDICO SAAVEDRA", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "San Martin 1234, Santa Fe, Argentina", ln=True, align="C")
    pdf.cell(0, 5, "Especialistas en Derecho Laboral y Civil", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, 35, 200, 35) 
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "COMPROBANTE DE TURNO VIRTUAL", ln=True, align="L")
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    # Limpiamos tildes para evitar errores de librería FPDF básica
    nombre_limpio = nombre.encode('latin-1', 'ignore').decode('latin-1')
    motivo_limpio = motivo.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.cell(0, 10, f"Cliente: {nombre_limpio}", ln=True)
    pdf.cell(0, 10, f"Cita programada: {fecha}", ln=True)
    pdf.cell(0, 10, f"Motivo: {motivo_limpio}", ln=True)
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    instrucciones = ("Este documento confirma su turno. Se ruega puntualidad. "
                    "En caso de no poder asistir, por favor avise con antelacion.")
    pdf.multi_cell(0, 8, instrucciones)
    
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 10, "Estudio Juridico Saavedra - Gestion IA", ln=True, align="R")
    
    return pdf.output(dest='S') # Quitamos el encode manual que daba error

# Cliente Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual del Estudio Saavedra. 
            UBICACIÓN: San Martín 1234, Santa Fe.
            HORARIOS: Lunes a Viernes de 16 a 20 hs.
            TURNOS OCUPADOS: {', '.join(turnos_ocupados)}.
            REGLAS: Pide Nombre, Teléfono y Motivo. Al confirmar usa la palabra 'AGENDADA'."""
        }
    ]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("¿En qué puedo ayudarlo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # --- LOGICA DE FICHA Y DESCARGA PDF ---
    pistas = ["agendada", "confirmada", "registrada", "pactada", "agendado", "confirmado"]
    if any(p in full_response.lower() for p in pistas):
        st.divider()
        st.subheader("📋 Registro de Turno")
        
        nombre_pdf = "Cliente"
        motivo_pdf = "Consulta General"
        
        # Extraer nombre del historial
        for m in reversed(st.session_state.messages):
            if m["role"] == "user":
                if "nombre es" in m["content"].lower():
                    nombre_pdf = m["content"].lower().split("nombre es")[-1].strip().title()
                    break

        st.write(f"**Cliente:** {nombre_pdf}")
        
        # Frase de guía para el usuario
        st.write("---")
        st.write("💡 *Para su seguridad y constancia, puede descargar su comprobante de turno aquí debajo:*")
        
        try:
            pdf_bytes = generar_pdf(nombre_pdf, "Lunes (según lo acordado)", motivo_pdf)
            st.download_button(
                label="📥 Descargar Comprobante de Turno (PDF)",
                data=pdf_bytes,
                file_name=f"Turno_Saavedra.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error técnico al generar el archivo. Por favor, tome una captura de pantalla de este chat.")
