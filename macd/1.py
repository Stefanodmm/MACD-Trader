import requests
import pandas as pd
import time
import json
import os

# Nombre del archivo CSV
csv_file = 'ordenes.csv'
# Variable global para almacenar el tiempo de espera en segundos
espera = 60  # Valor predeterminado

# Cargar configuración desde un archivo JSON
def cargar_configuracion():
    config_file = 'config.json'
    # Verificar si el archivo de configuración existe
    if not os.path.exists(config_file):
        # Crear un archivo de configuración con valores predeterminados
        configuracion_default = {
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "limit": 100
        }
        with open(config_file, 'w') as file:
            json.dump(configuracion_default, file, indent=4)
        print(f"Archivo de configuración '{config_file}' creado con valores predeterminados.")
    
    # Cargar la configuración desde el archivo
    with open(config_file, 'r') as file:
        return json.load(file)

# Función para convertir la temporalidad a segundos
def convertir_temporalidad_a_segundos(timeframe):
    unidades = {
        's': 1,
        'm': 60,
        'h': 3600,
        'D': 86400,
        'S': 604800,
        'M': 2592000,  # Aproximadamente 30 días
        'A': 31536000  # Aproximadamente 365 días
    }
    unidad = timeframe[-1]  # Obtener la última letra como unidad
    valor = int(timeframe[:-1])  # Obtener el valor numérico
    return valor * unidades.get(unidad, 60)  # Por defecto, 60 segundos si no se encuentra

# Función para verificar y crear el archivo CSV
def verificar_csv():
    if not os.path.exists(csv_file):
        # Crear el archivo CSV con las cabeceras
        with open(csv_file, 'w') as file:
            file.write("Fecha y hora, Precio, MACD, Acción a tomar\n")
        print(f"Archivo CSV '{csv_file}' creado con las cabeceras.")

# Función para obtener datos históricos desde la API de Binance
def obtener_datos(symbol, timeframe='1m', limit=100):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

# Función para calcular el MACD
def calcular_macd(data, short_window=12, long_window=26, signal_window=9):
    data['close'] = data['close'].astype(float)  # Convertir a float
    data['EMA_short'] = data['close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_long'] = data['close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA_short'] - data['EMA_long']
    data['Signal'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    data['Histograma'] = data['MACD'] - data['Signal']
    return data

# Función para determinar la señal de compra o venta
def determinar_señal(data):
    if data['MACD'].iloc[-1] > data['Signal'].iloc[-1] and data['MACD'].iloc[-2] <= data['Signal'].iloc[-2]:
        return "Comprar"
    elif data['MACD'].iloc[-1] < data['Signal'].iloc[-1] and data['MACD'].iloc[-2] >= data['Signal'].iloc[-2]:
        return "Vender"
    else:
        return "Mantener"

# Función para registrar la acción en el CSV
def registrar_accion(fecha_hora, precio, macd, accion):
    with open(csv_file, 'a') as file:
        file.write(f"{fecha_hora}, {precio}, {macd}, {accion}\n")

# Función principal para calcular el MACD en tiempo real
def main():
    global espera  # Declarar la variable global
    config = cargar_configuracion()
    symbol = config['symbol']
    timeframe = config['timeframe']
    
    # Convertir la temporalidad a segundos y guardar en la variable global
    espera = convertir_temporalidad_a_segundos(timeframe)
    
    verificar_csv()  # Verificar y crear el CSV si no existe
    
    while True:
        datos = obtener_datos(symbol, timeframe)
        datos = calcular_macd(datos)
        señal = determinar_señal(datos)
        
        # Muestra el último cálculo
        print(datos[['timestamp', 'close', 'MACD', 'Signal', 'Histograma']].tail(1))  
        print(f"Señal recomendada: {señal}")  # Muestra la señal recomendada
        
        # Registrar en el CSV si hay una acción de compra o venta
        if señal in ["Comprar", "Vender"]:
            fecha_hora = pd.to_datetime(datos['timestamp'].iloc[-1], unit='ms')
            precio = datos['close'].iloc[-1]
            macd = datos['MACD'].iloc[-1]
            registrar_accion(fecha_hora, precio, macd, señal)
            time.sleep(espera)  # Espera el tiempo configurado antes de la siguiente consulta

if __name__ == "__main__":
    main()
