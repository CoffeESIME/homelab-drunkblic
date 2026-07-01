#!/usr/bin/env python3
import subprocess
import time
import json
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN MQTT ---
MQTT_BROKER = "192.168.1.50" # CAMBIA ESTO por la IP de tu NAS
MQTT_PORT = 1883
MQTT_TOPIC = "telemetria/cuarto/ups"

# --- CONFIGURACIÓN UPS ---
UPS_NAME = "cyberpower"
UPS_CAPACITY_W = 1000 # Capacidad nominal del UPS

def get_ups_data():
    try:
        # Ejecuta el comando de consola upsc
        result = subprocess.run(['upsc', UPS_NAME], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        
        # Calcular Watts reales
        load_percent = float(data.get('ups.load', 0))
        real_power = (load_percent / 100) * UPS_CAPACITY_W
        
        return {
            "status": data.get('ups.status', 'UNKNOWN'),
            "load_percent": load_percent,
            "real_power_w": real_power,
            "battery_charge": float(data.get('battery.charge', 0)),
            "input_voltage": float(data.get('input.voltage', 0))
        }
    except Exception as e:
        print(f"Error leyendo UPS: {e}")
        return None

def on_connect(client, userdata, flags, rc):
    print(f"Conectado a MQTT con código: {rc}")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    
    # Si usas TLS/Certificados, configúralo aquí:
    # client.tls_set(ca_certs="ca.crt", certfile="client.crt", keyfile="client.key")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        while True:
            telemetry = get_ups_data()
            if telemetry:
                payload = json.dumps(telemetry)
                client.publish(MQTT_TOPIC, payload)
                print(f"Publicado: {payload}")
            time.sleep(10) # Publicar cada 10 segundos
            
    except KeyboardInterrupt:
        print("Saliendo...")
        client.loop_stop()
        client.disconnect()
