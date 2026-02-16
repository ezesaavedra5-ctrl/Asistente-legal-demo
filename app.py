import streamlit as st
from groq import Groq
import re
import gspread
from google.oauth2.service_account import Credentials

# --- FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS ---
def guardar_en_excel(nombre, fecha, motivo):
    try:
        # Permisos necesarios
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Cargamos credenciales desde los Secrets de Streamlit
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_gs = gspread.authorize(creds)
        
        # Abrimos el archivo por su nombre exacto
        sheet = client_gs.open("Agenda de turnos").sheet1
        
        # Agregamos la fila (Fecha, Nombre, Motivo)
        sheet.append_row([fecha, nombre, motivo])
        return True
    except Exception as e:
        # Si hay error con el Excel, lo mostramos discretamente
        st.sidebar.error(f"Error de sincronización con Excel: {e}")
        return False

# 1. Agenda del Estudio (Editable)
turnos_ocupados = ["Lunes 16:00", "Lunes 17:00", "Miércoles 18:30"]

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

# Cliente de Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual del Estudio Saavedra. 
            UBICACIÓN: San Martín 1234, Santa Fe.
            HORARIOS: Lunes a Viernes de 16 a 20 hs.
            TURNOS OCUPADOS: {', '.join(turnos_ocupados)}.
            
            REGLAS DE ORO:
            1. NO menciones turnos ocupados de otros días si el cliente pregunta por un día específico.
            2. Si el cliente elige un día, revisa si hay algo ocupado ESE DÍA. Si no, ofrece opciones entre 16 y 20 hs.
            3. Pide Nombre, Teléfono y Motivo.
            4. Solo cuando TODO esté acordado (Nombre, Tel, Motivo y Hora), confirma la cita.
            5. PARA FINALIZAR: Debes usar exactamente la frase "TURNO CONFIRMADO EXITOSAMENTE" para que el sistema cierre el registro. 
            6. Sé formal (español rioplatense) y evita errores gramaticales."""
        }
    ]

# Mostrar historial de mensajes
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrada de chat
if prompt := st.chat_input("¿En qué puedo ayudarlo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # --- LLAMADA A LA IA ---
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # --- LÓGICA DE FICHA PROFESIONAL Y EXCEL ---
            if "turno confirmado exitosamente" in full_response.lower():
                st.divider()
                
                nombre_final = "Cliente"
                fecha_final = "A confirmar"
                
                # Extracción de datos para el Excel
                for m in reversed(st.session_state.messages):
                    if m["role"] == "user":
                        content = m["content"].lower()
                        if "mi nombre es" in content:
                            nombre_final = m["content"].lower().split("nombre es")[-1].strip().split('.')[0].split(',')[0].split(' y ')[0].title()
                            break
                        elif "soy " in content:
                            nombre_final = m["content"].lower().split("soy")[-1].strip().split('.')[0].split(',')[0].title()
                            break

                dias = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes"]
                for dia in dias:
                    if dia in full_response.lower():
                        fecha_final = dia.capitalize()
                        break
                
                hora_match = re.search(r'(\d{1,2}:\d{2})', full_response)
                if hora_match:
                    fecha_final += f" a las {hora_match.group(1)} hs"

                # GUARDADO EN GOOGLE SHEETS
                exito_excel = guardar_en_excel(nombre_final, fecha_final, "Consulta Inicial")
                if exito_excel:
                    st.toast("✅ Cita sincronizada con el estudio")

                # Interfaz Visual
                st.success("### ✅ Turno Registrado en Agenda")
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**👤 Cliente:** \n{nombre_final}")
                        st.write(f"**📅 Cita:** \n{fecha_final}")
                    with col2:
                        st.write("**📍 Ubicación:** \nSan Martín 1234, Santa Fe")
                        st.write("**⚖️ Estado:** \nConfirmado")
                
                st.caption("ℹ️ Este es un registro digital del Estudio Jurídico Saavedra.")

        except Exception as e:
            st.error("⚠️ El Asistente está experimentando una interrupción temporal.")
            st.info("Por favor, intente nuevamente en unos segundos.")
            if len(st.session_state.messages) > 0:
                st.session_state.messages.pop()
