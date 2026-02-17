import streamlit as st
from groq import Groq
import re
import gspread
from google.oauth2.service_account import Credentials

# --- 1. FUNCIONES DE GOOGLE SHEETS ---

def obtener_turnos_actualizados():
    """Lee el Excel y devuelve una lista de los turnos ya ocupados."""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_gs = gspread.authorize(creds)
        
        sheet = client_gs.open("Agenda de turnos").sheet1
        # Traemos la columna 1 (Fecha/Hora)
        columna_fechas = sheet.col_values(1) 
        # Devolvemos todo menos el encabezado
        return columna_fechas[1:] if len(columna_fechas) > 1 else []
    except Exception as e:
        # Si falla la lectura, devolvemos lista vacía para no trabar la app
        st.sidebar.warning(f"Aviso: Agenda en modo local (no se pudo leer Excel)")
        return []

def guardar_en_excel(fecha, nombre, telefono, motivo):
    """Guarda una nueva fila en el Excel del estudio."""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_gs = gspread.authorize(creds)
        
        sheet = client_gs.open("Agenda de turnos").sheet1
        sheet.append_row([fecha, nombre, telefono, motivo])
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- 2. CONFIGURACIÓN DE LA APP Y IA ---

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Leemos los turnos reales del Excel al iniciar
turnos_reservados = obtener_turnos_actualizados()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual del Estudio Saavedra. 
            UBICACIÓN: San Martín 1234, Vera, Santa Fe.
            HORARIOS: Lunes a Viernes de 16 a 20 hs.
            TURNOS YA RESERVADOS EN EXCEL: {', '.join(turnos_reservados)}.
            
            REGLAS DE ORO:
            1. No leas la lista de turnos reservados al inicio.
            2. Actúa con naturalidad: si el cliente pregunta por un día, verifica internamente si ese día hay algo ocupado en tu lista de RESERVADOS.
            3. Si el horario que pide está ocupado, ofrece alternativas para ESE MISMO DÍA dentro de la franja 16-20 hs.
            4. Debes obtener: Nombre, Teléfono y Motivo de consulta.
            5. SOLO cuando todo esté acordado, confirma con: "TURNO CONFIRMADO EXITOSAMENTE"."""
        }
    ]

# Mostrar historial
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 3. LÓGICA DEL CHAT ---

if prompt := st.chat_input("¿En qué puedo ayudarlo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # --- DETECCIÓN DE TURNO CONFIRMADO Y EXTRACCIÓN ---
            if "turno confirmado exitosamente" in full_response.lower():
                st.divider()
                
                nombre_final = "No identificado"
                tel_final = "No proporcionado"
                motivo_final = "Consulta General"
                fecha_final = "A confirmar"
                
                # Análisis de historial para extraer datos
                texto_completo = ""
                for m in reversed(st.session_state.messages):
                    if m["role"] == "user":
                        content = m["content"].lower()
                        texto_completo = content + " " + texto_completo
                        
                        # Extraer Nombre (Refinado)
                        if "nombre es" in content or "soy " in content:
                            bruto = content.split("nombre es")[-1] if "nombre es" in content else content.split("soy")[-1]
                            nombre_final = re.split(r' y | mi | con | de |,|.', bruto.strip())[0].strip().title()
                        
                        # Extraer Teléfono
                        nums = re.findall(r'\d{7,15}', content.replace(" ", ""))
                        if nums: tel_final = nums[0]

                # Detección de Motivo
                temas = {
                    "Divorcio": ["divorcio", "separacion", "conyuge", "casamiento"],
                    "Sucesión": ["sucesion", "herencia", "fallecio", "bienes"],
                    "Accidente": ["accidente", "choque", "seguro", "lesion"],
                    "Laboral": ["despido", "trabajo", "empleo", "sueldo", "art"]
                }
                for tema, palabras in temas.items():
                    if any(p in texto_completo for p in palabras):
                        motivo_final = tema
                        break

                # Extracción y Normalización de Fecha/Hora
                dias = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes"]
                for dia in dias:
                    if dia in full_response.lower():
                        fecha_final = dia.capitalize()
                        break
                
                hora_match = re.search(r'(\d{1,2}):(\d{2})', full_response)
                hora_simple = re.search(r'las (\d{1,2})', full_response.lower())
                
                if hora_match:
                    fecha_final += f" a las {hora_match.group(1)}:{hora_match.group(2)} hs"
                elif hora_simple:
                    fecha_final += f" a las {hora_simple.group(1)}:00 hs"

                # GUARDADO EN EXCEL
                if guardar_en_excel(fecha_final, nombre_final, tel_final, motivo_final):
                    st.toast("✅ Cita sincronizada")

                # Ficha Visual
                st.success("### ✅ Turno Registrado en Agenda")
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**👤 Cliente:** {nombre_final}")
                        st.write(f"**📞 Teléfono:** {tel_final}")
                    with col2:
                        st.write(f"**📅 Cita:** {fecha_final}")
                        st.write(f"**📝 Motivo:** {motivo_final}")
                st.caption("ℹ️ Registro automático - Estudio Jurídico Saavedra.")

        except Exception as e:
            st.error("⚠️ El sistema está experimentando una demora.")
            if len(st.session_state.messages) > 0:
                st.session_state.messages.pop()


