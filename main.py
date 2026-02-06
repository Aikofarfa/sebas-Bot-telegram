# =============================================================================
# BOT DE SEÑALES SIMPLE - CRUCE DE MEDIAS MÓVILES (Binance + Telegram)
# Versión educativa - SOLO ENVÍA SEÑALES, NO OPERA
# No requiere claves API de Binance (usa endpoints públicos)
# =============================================================================

import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# ────────────────────────────────────────────────
# CONFIGURACIÓN - CAMBIA ESTOS VALORES
# ────────────────────────────────────────────────

# Binance (testnet o real - no afecta porque no usamos claves)
TESTNET = True

# Par y temporalidad
SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"          # 5 minutos
CANDLES_TO_LOAD = 100     # cuántas velas cargar

# Estrategia: cruce de medias móviles
FAST_MA_PERIOD = 9
SLOW_MA_PERIOD = 21

# Telegram
TELEGRAM_TOKEN = "8542964886:AAFi2UG4MrSyCn7MFG3qh-4xYIOGwFq9gug"          # El token que te dio @BotFather
TELEGRAM_CHAT_ID = "8576880914"          # Tu chat ID (número)

# Intervalo de chequeo (segundos)
SLEEP_SECONDS = 60

# ────────────────────────────────────────────────
# NO CAMBIES NADA DE AQUÍ PARA ABAJO
# ────────────────────────────────────────────────

# Inicializar Binance (solo datos públicos)
exchange_options = {
    'enableRateLimit': True,
}
if TESTNET:
    exchange_options['urls'] = {'api': {'public': 'https://testnet.binance.vision/api'}}

exchange = ccxt.binance(exchange_options)

# Inicializar Telegram
bot = Bot(token=TELEGRAM_TOKEN)

last_signal = None  # Evita enviar la misma señal repetidamente

def enviar_mensaje(texto):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=texto, parse_mode="Markdown")
        print(f"[Telegram] Mensaje enviado: {texto}")
    except TelegramError as e:
        print(f"Error al enviar mensaje por Telegram: {e}")


def obtener_datos():
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=CANDLES_TO_LOAD)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error al obtener velas: {e}")
        return None


def analizar_mercado(df):
    global last_signal

    if df is None or len(df) < SLOW_MA_PERIOD:
        return None

    # Calcular medias móviles
    df['fast_ma'] = ta.sma(df['close'], length=FAST_MA_PERIOD)
    df['slow_ma'] = ta.sma(df['close'], length=SLOW_MA_PERIOD)

    ultima = df.iloc[-1]
    anterior = df.iloc[-2]

    # Cruce alcista → COMPRA
    if (anterior['fast_ma'] <= anterior['slow_ma']) and (ultima['fast_ma'] > ultima['slow_ma']):
        señal = "🟢 COMPRA (cruce alcista)"
        if last_signal != "buy":
            mensaje = (
                f"*{señal}*\n"
                f"Par: `{SYMBOL}`\n"
                f"Temporalidad: {TIMEFRAME}\n"
                f"Precio: {ultima['close']:.2f}\n"
                f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            enviar_mensaje(mensaje)
            last_signal = "buy"
        return señal

    # Cruce bajista → VENTA
    elif (anterior['fast_ma'] >= anterior['slow_ma']) and (ultima['fast_ma'] < ultima['slow_ma']):
        señal = "🔴 VENTA (cruce bajista)"
        if last_signal != "sell":
            mensaje = (
                f"*{señal}*\n"
                f"Par: `{SYMBOL}`\n"
                f"Temporalidad: {TIMEFRAME}\n"
                f"Precio: {ultima['close']:.2f}\n"
                f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            enviar_mensaje(mensaje)
            last_signal = "sell"
        return señal

    return None


# Bucle principal
print("Bot de señales iniciado...")
print(f"Par: {SYMBOL} | Temporalidad: {TIMEFRAME} | Chequeo cada {SLEEP_SECONDS} segundos\n")

while True:
    try:
        df = obtener_datos()
        if df is not None:
            señal = analizar_mercado(df)
            if señal:
                print(f"{datetime.now().strftime('%H:%M:%S')} → {señal}")
            else:
                print(f"{datetime.now().strftime('%H:%M:%S')} → Sin señal nueva")
    except Exception as e:
        print(f"Error en bucle principal: {e}")

    time.sleep(60)



