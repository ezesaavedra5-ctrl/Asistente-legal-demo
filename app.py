import streamlit as st
from groq import Groq
from fpdf import FPDF

# 1. Agenda del Estudio (Editable)
turnos_ocupados = ["Lunes 16:00", "Lunes 17:00", "Miércoles 18:30"]

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

# Función para generar el comprobante PDF
def generar_pdf(nombre, fecha, motivo):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "ESTUDIO JURÍDICO SAAVEDRA", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "San Martín 1234, Santa Fe, Argentina", ln=True, align="C")
    pdf.cell(0, 5, "Especialistas en Derecho Laboral y Civil", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, 35, 200, 35) # Línea divisoria
    
    # Cuerpo del comprobante
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "COMPROBANTE DE TURNO VIRTUAL", ln=True, align="L")
    
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"👤 Cliente: {nombre}", ln=True)
    pdf.cell(0, 10, f"📅 Cita programada: {fecha}", ln=True)
    pdf.cell(0, 10, f"⚖️ Motivo: {motivo}", ln=True)
    
    # Instrucciones
    pdf.ln(15)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "I", 10)
    instrucciones = ("Este documento confirma que su turno ha sido registrado en nuestra agenda. "
                    "Se ruega puntualidad. En caso de no poder asistir, por favor "
                    "comunicarse con el estudio con 24 horas de antelación.")
    pdf.multi_cell(0, 8, instrucciones, border=1, fill=True)
    
    # Firma/Sello digital
    pdf.ln(20)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, "Estudio Jurídico Saavedra - Atención Automatizada", ln=True, align="R")
    
    return pdf.output(dest='S').encode('latin-1')

# Cliente Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual de Élite del Estudio Saavedra. 
            UBICACIÓN: San Martín 1234, Santa Fe.
            HORARIOS: Lunes a Viernes de 16 a 20 hs.
            ESTADO DE AGENDA: Los siguientes turnos ya están RESERVADOS: {', '.join(turnos_ocupados)}.
            
            REGLAS:
            1. Verifica disponibilidad antes de ofrecer turnos.
            2. Pide Nombre, Teléfono y Motivo.
            3. Una vez confirmada la cita, usa la palabra 'AGENDADA' para finalizar.
            4. Sé formal y profesional."""
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

    # --- LÓGICA DE FICHA Y DESCARGA PDF ---
    pistas = ["agendada", "confirmada", "registrada", "pactada"]
    if any(p in full_response.lower() for p in pistas):
        st.divider()
        st.subheader("📋 Registro de Turno")
        
        # Extracción de datos para el PDF
        nombre_pdf = "Cliente"
        motivo_pdf = "Consulta Legal"
        fecha_pdf = "A coordinar"
        
        for m in reversed(st.session_state.messages):
            if m["role"] == "user":
                content = m["content"].lower()
                if "nombre es" in content: nombre_pdf = content.split("nombre es")[-1].strip().title()
                elif "motivo" in content or "accidente" in content: motivo_pdf = content.strip().capitalize()
            if m["role"] == "assistant" and ("lunes" in m["content"].lower() or "martes" in m["content"].lower()):
                fecha_pdf = "Ver historial" # Simplificado para la demo

        st.write(f"**Cliente:** {nombre_pdf}")
        
        # Generar y ofrecer PDF
        try:
            pdf_bytes = generar_pdf(nombre_pdf, fecha_pdf, motivo_pdf)
            st.download_button(
                label="📥 Descargar Comprobante de Turno (PDF)",
                data=pdf_bytes,
                file_name=f"Turno_{nombre_pdf.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error("No se pudo generar el PDF, pero su cita está registrada.")

