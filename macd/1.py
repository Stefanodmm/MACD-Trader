import requests
import pandas as pd
import time
import json
import os

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

# Función principal para calcular el MACD en tiempo real
def main():
    config = cargar_configuracion()
    symbol = config['symbol']
    timeframe = config['timeframe']
    
    while True:
        datos = obtener_datos(symbol, timeframe)
        datos = calcular_macd(datos)
        señal = determinar_señal(datos)
        print(datos[['timestamp', 'close', 'MACD', 'Signal', 'Histograma']].tail(1))  # Muestra el último cálculo
        print(f"Señal recomendada: {señal}")  # Muestra la señal recomendada
        time.sleep(1)  # Espera 1 segundo antes de la siguiente consulta (puedes ajustar este tiempo)

if __name__ == "__main__":
    main()
