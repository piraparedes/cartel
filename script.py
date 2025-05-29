import paho.mqtt.client as mqtt
from ftplib import FTP_TLS
from datetime import datetime

# =============================
# Configuración MQTT ThingSpeak
# =============================
mqtt_server = "mqtt3.thingspeak.com"
mqtt_port = 1883
mqtt_username = "BSQcDgA7OCMwDQI8EyIwKy4"
mqtt_password = "WZ5uCaaW41KdGbMFNVOUICJs"
mqtt_client_id = "BSQcDgA7OCMwDQI8EyIwKy4"

topic_field5 = "channels/2954640/subscribe/fields/field5"  # Salidas
topic_field6 = "channels/2954640/subscribe/fields/field6"  # Entradas

# =============================
# Variables globales
# =============================
current_entradas = "0"
current_salidas = "0"
previous_entradas = None
previous_salidas = None

# =============================
# Actualizar archivo HTML y subirlo por FTPS
# =============================
def update_html_file(entradas, salidas):
    global previous_entradas, previous_salidas

    if entradas == previous_entradas and salidas == previous_salidas:
        print("📭 Sin cambios en los datos, no se actualiza el archivo.")
        return

    previous_entradas, previous_salidas = entradas, salidas
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        print("🔐 Conectando a FTPS...")
        ftp = FTP_TLS("ftp.macmelo.com")
        ftp.login("tesis@macmelo.com", "peugeot4061997")
        ftp.prot_p()
        ftp.cwd("/")

        # Crear archivo HTML local
        with open("index.html", "w") as f:
            html = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Numero en Pantalla Completa</title>
                <style>
                    body {{
                        background-color: blue;
                        margin: 0;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        flex-direction: column;
                        color: white;
                        font-family: Arial, sans-serif;
                    }}
                    .contenedor {{
                        display: flex;
                        flex-direction: row;
                        gap: 6vw;
                        justify-content: center;
                        align-items: center;
                    }}
                    .columna {{
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}
                    .etiqueta {{
                        font-size: 5vw;
                        font-weight: bold;
                        margin-bottom: 1vh;
                    }}
                    .numero {{
                        color: yellow;
                        font-size: 20vw;
                        font-weight: bold;
                        user-select: none;
                        text-align: center;
                    }}
                    .led {{
                        font-size: 5vw;
                        font-weight: bold;
                        margin-bottom: 20px;
                    }}
                    .timestamp {{
                        font-size: 2vw;
                        margin-top: 2vh;
                    }}
                </style>
                <script>
                    setInterval(function () {{
                        window.location.href = window.location.href.split('?')[0] + '?v=' + new Date().getTime();
                    }}, 15000);
                </script>
            </head>
            <body>
                <div class="led">LED</div>
                <div class="contenedor">
                    <div class="columna">
                        <div class="etiqueta">Entradas</div>
                        <div class="numero">{entradas}</div>
                    </div>
                    <div class="columna">
                        <div class="etiqueta">Salidas</div>
                        <div class="numero">{salidas}</div>
                    </div>
                </div>
                <div class="timestamp">Ultima actualizacion: {now}</div>
                <br><br>
                <div align=center><h1>Tesis: Daniel Paredes</h1></div>
            </body>
            </html>
            """
            f.write(html)
            print("✅ HTML generado localmente.")

        # Subir archivo HTML
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)
            print(f"✅ HTML subido al servidor FTPS a las {now}.")

        ftp.quit()

        # Guardar log
        with open("log.txt", "a") as log:
            log.write(f"[{now}] Entradas: {entradas} | Salidas: {salidas}\n")

        print("📝 Registro actualizado.\n")

    except Exception as e:
        print(f"❌ Error al subir archivo: {e}")

# =============================
# Mensaje MQTT recibido
# =============================
def on_message(client, userdata, message):
    global current_entradas, current_salidas

    payload = message.payload.decode("utf-8").strip()
    topic = message.topic

    print(f"📩 Mensaje recibido en {topic}: {payload}")

    if "field6" in topic:  # Entradas
        current_entradas = payload
    elif "field5" in topic:  # Salidas
        current_salidas = payload

    update_html_file(current_entradas, current_salidas)

# =============================
# Conexión MQTT
# =============================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conexión exitosa a MQTT.")
        client.subscribe(topic_field5)
        client.subscribe(topic_field6)
        print(f"📥 Suscrito a {topic_field5} (salidas) y {topic_field6} (entradas)")
    else:
        print(f"❌ Error de conexión: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"⚠️ MQTT desconectado. Código: {rc}. Intentando reconectar...")

# =============================
# Conexión principal
# =============================
def connect_mqtt():
    client = mqtt.Client(client_id=mqtt_client_id)
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=2, max_delay=10)
    client.connect(mqtt_server, mqtt_port, 60)
    client.loop_forever()

# =============================
# Punto de entrada
# =============================
if __name__ == "__main__":
    print("🚀 Conectando a MQTT y esperando mensajes...")
    connect_mqtt()
