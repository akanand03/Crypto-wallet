from flask import Flask, render_template, request
import requests
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# API key for the CryptoCompare service
API_KEY = '34186b853765c755b0a4277d311fdaccf0ee2795b1863080f6f14d1e0e3869a1'

# Directory to store downloaded files (if needed)
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Clean up downloaded files older than 1 day to save storage
def cleanup_downloads():
    now = datetime.now()
    for filename in os.listdir(DOWNLOAD_FOLDER):
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_time > timedelta(days=1):
                os.remove(filepath)

# Call cleanup_downloads when the app starts
cleanup_downloads()

# Fetch list of available coins from CryptoCompare API
def fetch_coin_list():
    try:
        response = requests.get(
            'https://min-api.cryptocompare.com/data/all/coinlist',
            params={'api_key': API_KEY}
        )
        response.raise_for_status()
        coins_data = response.json()['Data']
        coins = sorted(coins_data.keys())
        CRYPTO_LOGOS = {
            symbol: f"https://www.cryptocompare.com{data['ImageUrl']}"
            for symbol, data in coins_data.items()
            if data.get('ImageUrl')
        }
        return coins, CRYPTO_LOGOS
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coin list: {e}")
        return [], {}

# Main route to display the form and get crypto data
@app.route('/', methods=['GET', 'POST'])
def index():
    coins, CRYPTO_LOGOS = fetch_coin_list()

    # Handle form submission
    if request.method == 'POST':
        coin_symbol = request.form.get('coin_id')
        days = request.form.get('days')
        file_format = request.form.get('file_format', 'csv')

        # Validate selected coin
        if coin_symbol not in coins:
            return render_template('index.html', error="Invalid cryptocurrency selected.", coins=coins)

        # Validate number of days
        try:
            days = int(days)
            if days < 1 or days > 2000:
                raise ValueError("Invalid number of days. Please choose between 1 and 2000.")
        except ValueError as ve:
            return render_template('index.html', error=str(ve), coins=coins)

        try:
            predictions, df = get_market_chart(coin_symbol, days)

            # Render the data page with predictions and OHLC data
            logo_url = CRYPTO_LOGOS.get(coin_symbol, "")
            return render_template(
                'data.html',
                predictions=predictions,
                coin_id=coin_symbol,
                days=days,
                df=df.to_dict(orient='records'),
                logo_url=logo_url
            )

        except ValueError as e:
            return render_template('index.html', error=str(e), coins=coins)
        except Exception as ex:
            return render_template('index.html', error=f"An unexpected error occurred: {ex}", coins=coins)

    return render_template('index.html', coins=coins)

# Function to fetch OHLC market data and perform predictions
def get_market_chart(coin_symbol, days):
    limit = days - 1  # Adjusting limit for the API parameter
    try:
        response = requests.get(
            'https://min-api.cryptocompare.com/data/v2/histoday',
            params={
                'fsym': coin_symbol,
                'tsym': 'USD',
                'limit': limit,
                'api_key': API_KEY
            }
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch historical data for {coin_symbol}. Error: {e}")

    data = response.json()
    if data['Response'] != 'Success':
        raise ValueError(f"Error fetching data: {data.get('Message', 'Unknown error')}")

    historical_data = data['Data']['Data']
    if not historical_data or not isinstance(historical_data, list):
        raise ValueError(f"Historical data is empty or not in expected format for {coin_symbol}")

    df = pd.DataFrame(historical_data)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Feature Engineering for Prediction
    df['day'] = df['time'].dt.dayofyear
    X = df[['day']].values  # Using 'day' as the feature
    y = df['close'].values

    # Scaling Features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Model Training
    model = LinearRegression()
    model.fit(X_scaled, y)

    # Predictions for the next 'days' days
    future_days = np.array([df['day'].iloc[-1] + i for i in range(1, days + 1)])
    future_days_scaled = scaler.transform(future_days.reshape(-1, 1))
    y_pred = model.predict(future_days_scaled)

    # Generate future dates for predictions
    start_date = df['time'].iloc[-1] + timedelta(days=1)
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]

    predictions = {date: pred for date, pred in zip(dates, y_pred)}
    return predictions, df

if __name__ == '__main__':
    app.run(debug=True)
