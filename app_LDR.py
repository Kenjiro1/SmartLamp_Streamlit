import streamlit as st
import paho.mqtt.client as mqtt
import requests
import json
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES ---
BROKER_IP = "3.93.31.197"
BROKER_PORT = 1883
TOPICO_COMANDO = "/TEF/lamp001/cmd"
ORION_URL = "http://3.93.31.197:1026/v2/entities/urn:ngsi-ld:Lamp:001/attrs/luminosity"
ORION_HEADERS = {
    'fiware-service': 'smart',
    'fiware-servicepath': '/',
    'Accept': 'application/json'
}

# --- INICIALIZAÇÃO DO HISTÓRICO NA SESSÃO DO STREAMLIT ---
if 'historico' not in st.session_state:
    st.session_state.historico = []

# --- FUNÇÃO DE ENVIO DE COMANDO MQTT ---
def enviar_comando_mqtt(comando: str):
    try:
        client = mqtt.Client()
        client.connect(BROKER_IP, BROKER_PORT, 60)
        client.publish(TOPICO_COMANDO, comando)
        client.disconnect()
        return True
    except Exception as e:
        st.error(f"Erro de conexão MQTT: {e}")
        return False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Painel IoT - Controle e Monitoramento", page_icon="💡")
st.title("💡 Painel IoT - Monitoramento em Tempo Real")
st.markdown("Controle o LED e visualize o histórico e gráfico da luminosidade do LDR via FIWARE Orion.")

st.divider()

# --- CONSULTA ORION COM TABELA E GRÁFICO ---
st.subheader("📊 Monitoramento e Histórico (Sensor LDR)")

col_btn1, col_btn2 = st.columns([1, 3])
with col_btn1:
    consultar = st.button("🔄 Consultar Orion")

if consultar:
    try:
        response = requests.get(ORION_URL, headers=ORION_HEADERS)
        if response.status_code == 200:
            dados = response.json()
            
            # Extrai os valores retornados pelo Orion
            valor_luminosity = float(dados.get('value', 0))
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Adiciona o novo registro ao histórico global da sessão
            novo_registro = {
                "Horário": timestamp,
                "Luminosidade": valor_luminosity
            }
            
            st.session_state.historico.append(novo_registro)
            
            # Mantém apenas os últimos 20 registros
            if len(st.session_state.historico) > 20:
                st.session_state.historico.pop(0)
                
            st.success("Dados obtidos e salvos no histórico com sucesso!")
        else:
            st.error(f"Erro ao buscar no Orion: Status Code {response.status_code}")
    except Exception as e:
        st.error(f"Erro de conexão com a API: {e}")

# Se houver dados no histórico, exibe a tabela e o gráfico
if len(st.session_state.historico) > 0:
    df_historico = pd.DataFrame(st.session_state.historico)
    
    # Organiza a exibição em duas colunas (Tabela à esquerda, Gráfico à direita)
    col_tab, col_graf = st.columns(2)
    
    with col_tab:
        st.markdown("### 📋 Últimos Registros (Máx. 20)")
        st.dataframe(df_historico, use_container_width=True)
        
    with col_graf:
        st.markdown("### 📈 Gráfico em Tempo Real")
        # Plota o gráfico de linha utilizando o Horário como eixo X e a Luminosidade como eixo Y
        st.line_chart(df_historico.set_index("Horário"))
else:
    st.info("ℹ️ Clique no botão **'Consultar Orion'** para carregar os primeiros dados.")

st.divider()

# --- CONTROLE POR BOTÕES ---
st.subheader("🎛️ Controle Manual (Botões)")
col1, col2 = st.columns(2)

with col1:
    if st.button("🟢 Acender Luz", use_container_width=True):
        if enviar_comando_mqtt("lamp001@on|"):
            st.success("Comando enviado: LIGAR")

with col2:
    if st.button("🔴 Apagar Luz", use_container_width=True):
        if enviar_comando_mqtt("lamp001@off|"):
            st.success("Comando enviado: DESLIGAR")

st.divider()

# --- CONTROLE POR VOZ ---
st.subheader("🎙️ Controle por Voz")
st.caption("Clique no botão abaixo e fale 'acender luz' ou 'apagar luz'.")

# Processa o comando vindo do componente de voz via parâmetros de URL
query_params = st.query_params
if "voice_cmd" in query_params:
    cmd_recebido = query_params["voice_cmd"]
    st.query_params.clear()
    
    if cmd_recebido == "on":
        if enviar_comando_mqtt("lamp001@on|"):
            st.success("🎙️ Voz reconhecida: 'Acender Luz' -> Comando LIGAR enviado!")
    elif cmd_recebido == "off":
        if enviar_comando_mqtt("lamp001@off|"):
            st.success("🎙️ Voz reconhecida: 'Apagar Luz' -> Comando DESLIGAR enviado!")

# Componente HTML / JavaScript com ondas sonoras animadas
voice_component_html = """
<style>
.voice-container {
    font-family: sans-serif;
    text-align: center;
    padding: 10px;
}
.speech-btn {
    background-color: #FF4B4B;
    color: white;
    border: none;
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
    transition: 0.2s;
}
.speech-btn:hover {
    background-color: #ff2b2b;
}
.sound-wave {
    display: none;
    justify-content: center;
    align-items: center;
    gap: 4px;
    height: 30px;
    margin-top: 12px;
}
.sound-wave span {
    display: block;
    width: 4px;
    height: 10px;
    background-color: #FF4B4B;
    border-radius: 2px;
    animation: wave 1s infinite ease-in-out;
}
.sound-wave span:nth-child(2) { animation-delay: 0.1s; }
.sound-wave span:nth-child(3) { animation-delay: 0.2s; }
.sound-wave span:nth-child(4) { animation-delay: 0.3s; }
.sound-wave span:nth-child(5) { animation-delay: 0.4s; }

@keyframes wave {
    0%, 100% { height: 8px; }
    50% { height: 28px; }
}
</style>

<div class="voice-container">
    <button id="btn-listen" class="speech-btn" onclick="startRecognition()">
        🎙️ Clique para Falar
    </button>
    <div id="wave-animation" class="sound-wave">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <span></span>
    </div>
    <p id="status-text" style="margin-top: 10px; color: #555; font-size: 14px;">Aguardando ação...</p>
</div>

<script>
function startRecognition() {
    const statusText = document.getElementById('status-text');
    const waveAnimation = document.getElementById('wave-animation');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        statusText.innerText = "Reconhecimento de voz não suportado neste navegador.";
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.interimResults = false;

    recognition.onstart = function() {
        statusText.innerText = "👂 Ouvindo... Fale 'acender luz' ou 'apagar luz'.";
        waveAnimation.style.display = "flex";
    };

    recognition.onspeechend = function() {
        recognition.stop();
    };

    recognition.onresult = function(event) {
        waveAnimation.style.display = "none";
        const transcript = event.results[0][0].transcript.toLowerCase().trim();
        statusText.innerText = "Você disse: \\"" + transcript + "\\"";

        if (transcript.includes("acender") || transcript.includes("ligar")) {
            statusText.innerText = "Enviando comando: ACENDER...";
            window.top.location.href = window.top.location.pathname + "?voice_cmd=on";
        } else | if (transcript.includes("apagar") || transcript.includes("desligar")) {
            statusText.innerText = "Enviando comando: APAGAR...";
            window.top.location.href = window.top.location.pathname + "?voice_cmd=off";
        } else {
            statusText.innerText = "Comando não reconhecido. Tente falar 'acender luz' ou 'apagar luz'.";
        }
    };

    recognition.onerror = function(event) {
        waveAnimation.style.display = "none";
        statusText.innerText = "Erro no reconhecimento: " + event.error;
    };

    recognition.start();
}
</script>
"""

components.html(voice_component_html, height=160)