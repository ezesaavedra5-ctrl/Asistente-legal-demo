import streamlit as st
from groq import Groq

# 1. Agenda del Estudio (Editable manualmente por ahora)
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
            "content": f"""Eres el Asistente Virtual de Élite del Estudio Saavedra en Santa Fe. 
            UBICACIÓN: San Martín 1234, Santa Fe.
            HORARIOS DE ATENCIÓN: Lunes a Viernes de 16:00 a 20:00 hs.
            
            ESTADO DE AGENDA: Los siguientes turnos ya están RESERVADOS: {', '.join(turnos_ocupados)}.
            
            REGLAS ESTRICTAS:
            1. Antes de ofrecer un horario, verifica que NO esté en la lista de RESERVADOS.
            2. Si el cliente pide un horario ocupado (como Lunes 16:00 o 17:00), di que no es posible y ofrece los libres (18:00, 19:00 o 20:00).
            3. Pide siempre: Nombre completo, Teléfono y Motivo de consulta.
            4. No confirmes la cita sin tener esos 3 datos.
            5. Cuando confirmes, usa la frase "SU CITA HA SIDO AGENDADA" para que el sistema la registre.
            6. Sé breve, muy formal y usa español rioplatense impecable."""
        }
    ]

# Mostrar el historial de chat (excluyendo el sistema)
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

    # --- LÓGICA DEL RESUMEN VISUAL PROFESIONAL (Sin Globos y sin NameError) ---
    pistas_confirmacion = ["agendada", "confirmada", "registrada", "cita pactada", "agendado"]
    
    if any(pista in full_response.lower() for pista in pistas_confirmacion):
        st.divider()
        st.subheader("📋 Ficha de Registro de Consulta")
        
        # Extracción segura de datos del historial
        nombre_final = "No especificado"
        for m in reversed(st.session_state.messages):
            if m["role"] == "user":
                content = m["content"].lower()
                if "nombre es" in content:
                    nombre_final = content.split("nombre es")[-1].strip().title()
                    break
                elif "soy " in content:
                    nombre_final = content.split("soy")[-1].strip().title()
                    break

        # Diseño serio y profesional
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**👤 Cliente:** {nombre_final}")
            st.write("**📍 Lugar:** San Martín 1234, Santa Fe")
        with col2:
            st.write("**✅ Estado:** Confirmado")
            st.write("**📞 Contacto:** Ver historial de chat")
        
        st.info("ℹ️ Esta ficha ha sido generada automáticamente para la gestión interna del estudio.")
