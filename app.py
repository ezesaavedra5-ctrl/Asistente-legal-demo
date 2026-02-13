import streamlit as st
from groq import Groq

# 1. Definimos la Agenda del Estudio (Editable manualmente)
turnos_ocupados = ["Lunes 16:00", "Lunes 17:00", "Miércoles 18:30"]

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

# Configuración del cliente Groq usando Secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Inicialización del historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual de Élite del Estudio Saavedra. 
            UBICACIÓN: San Martín 1234, Santa Fe.
            HORARIOS: Lunes a Viernes de 16:00 a 20:00 hs.
            ESTADO DE AGENDA: Los siguientes turnos ya están OCUPADOS: {', '.join(turnos_ocupados)}.
            
            REGLAS:
            1. Si el cliente pregunta horarios libres, revisa tu agenda y ofrece los que NO están ocupados (de 16 a 20 hs).
            2. Pide siempre: Nombre, Teléfono y Motivo de consulta.
            3. No des consejos legales ni montos de dinero.
            4. Sé breve, formal y usa gramática impecable (español rioplatense).
            5. Cuando el cliente dé sus datos y el horario sea acordado, confirma la cita claramente."""
        }
    ]

# Mostrar el historial de chat
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrada de usuario
if prompt := st.chat_input("¿En qué puedo ayudarlo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # --- LÓGICA DEL RESUMEN VISUAL DINÁMICO ---
    # Detectamos si la IA confirmó la cita para mostrar el cuadro final
    pistas_confirmacion = ["agendado", "confirmado", "registrado", "detalles de su cita", "cita pactada"]
    if any(pista in full_response.lower() for pista in pistas_confirmacion):
        st.divider()
        st.success("### 📝 Cita Detectada por el Sistema")
        
        # Intentamos extraer el nombre del usuario del historial para el resumen
        nombre_usuario = "Cliente"
        for m in reversed(st.session_state.messages):
            if m["role"] == "user" and len(m["content"].split()) <= 4:
                nombre_usuario = m["content"]
                break
        
        st.info(f"**Paciente/Cliente:** {nombre_usuario}  \n**Estado:** Pendiente de ingreso a agenda global.")
        st.warning("⚠️ Nota para el abogado: Esta información se enviará automáticamente a su planilla de gestión.")
