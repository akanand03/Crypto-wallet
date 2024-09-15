from flask import Flask, render_template, request, send_file
import requests
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Directory to store downloaded files
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Main route to display the form and get crypto data
@app.route('/', methods=['GET', 'POST'])
def index():
    # Fetch list of available coins from CoinGecko API
    try:
        response = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={'vs_currency': 'usd'})
        response.raise_for_status()  # Check if the response contains errors
        coins_list = response.json()  # Parse the response as JSON
    except requests.exceptions.RequestException as e:
        return render_template('index.html', error=f"Failed to fetch coins list: {e}", coins=[])

    # Create a mapping of coin_id to logo_url
    CRYPTO_LOGOS = {coin['id']: coin['image'] for coin in coins_list}

    # List of coins
    coins = list(CRYPTO_LOGOS.keys())

    # Handle form submission
    if request.method == 'POST':
        print("Form submitted")  # Debugging statement
        coin_id = request.form.get('coin_id')
        days = request.form.get('days')
        file_format = request.form.get('file_format', 'csv')

        # Validate selected coin
        if coin_id not in coins:
            return render_template('index.html', error="Invalid cryptocurrency selected.", coins=coins)

        # Validate number of days
        try:
            days = int(days)
            if days not in [1, 7, 14, 30, 90, 180, 365]:
                raise ValueError("Invalid number of days. Please choose from: 1, 7, 14, 30, 90, 180, 365.")
        except ValueError as ve:
            return render_template('index.html', error=str(ve), coins=coins)

        try:
            predictions, df = get_market_chart(coin_id, days)
            print(f"Predictions for {coin_id} successfully fetched")  # Debugging statement

            # Check if the user opted to show the data in the browser
            if request.form.get('show_data'):
                print("Displaying data in browser")  # Debugging statement
                # Pass OHLC data as list of dictionaries
                df_records = df.to_dict(orient='records')
                logo_url = CRYPTO_LOGOS.get(coin_id, "")
                return render_template('data.html',
                                       predictions=predictions,
                                       coin_id=coin_id,
                                       days=days,
                                       df=df_records,
                                       logo_url=logo_url)
            else:
                # Save the data to the requested format and return it for download
                filename = save_to_file(df, file_format)
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                print(f"Sending file: {filepath} for download")  # Debugging statement
                return send_file(filepath, as_attachment=True)

        except ValueError as e:
            return render_template('index.html', error=str(e), coins=coins)
        except Exception as ex:
            return render_template('index.html', error=f"An unexpected error occurred: {ex}", coins=coins)

    return render_template('index.html', coins=coins)

# Function to fetch OHLC market data and perform predictions
def get_market_chart(coin_id, days):
    try:
        response = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc', params={'vs_currency': 'usd', 'days': days})
        response.raise_for_status()  # Raise an exception for bad HTTP responses
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch OHLC data for {coin_id}. Error: {e}")

    ohlc_data = response.json()
    if not ohlc_data or not isinstance(ohlc_data, list):
        raise ValueError(f"OHLC data is empty or not in expected format for {coin_id}")

    ohlc = np.array(ohlc_data)
    if len(ohlc.shape) != 2 or ohlc.shape[1] != 5:
        raise ValueError(f"Expected OHLC data to be 2D with 5 columns (time, open, high, low, close), got shape: {ohlc.shape}")

    df = pd.DataFrame(ohlc, columns=['time', 'open', 'high', 'low', 'close'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')

    # Feature Engineering for Prediction
    df['day'] = df['time'].dt.dayofyear
    X = df[['day', 'close']].values
    y = df['close'].values

    # Scaling Features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Model Training
    model = LinearRegression()
    model.fit(X_scaled, y)

    # Predictions
    y_pred = model.predict(X_scaled)

    # Generate future dates for predictions
    start_date = df['time'].iloc[-1] + timedelta(days=1)
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(len(y_pred))]

    predictions = {date: pred for date, pred in zip(dates, y_pred)}
    return predictions, df

# Function to save data to CSV or XLSX
def save_to_file(df, file_format):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    if file_format == 'xlsx':
        filename = f"market_data_{timestamp}.xlsx"
        df.to_excel(os.path.join(DOWNLOAD_FOLDER, filename), index=False)
    else:
        filename = f"market_data_{timestamp}.csv"
        df.to_csv(os.path.join(DOWNLOAD_FOLDER, filename), index=False)

    return filename

# Clean up downloaded files older than 1 day to save storage
def cleanup_downloads():
    now = datetime.now()
    for filename in os.listdir(DOWNLOAD_FOLDER):
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_time > timedelta(days=1):
                os.remove(filepath)

# Schedule cleanup every time the app runs (for demonstration; use proper scheduling in production)
@app.before_first_request
def before_first_request_func():
    cleanup_downloads()

if __name__ == '__main__':
    app.run(debug=True)
