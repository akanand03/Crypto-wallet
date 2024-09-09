from flask import Flask, jsonify, render_template, request, send_file
import requests
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import time
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get the list of available coins
    response = requests.get(f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd')
    
    # Check if the response status is OK (200)
    if response.status_code != 200:
        return render_template('index.html', error=f"Failed to fetch coins list. Status code: {response.status_code}")
    
    try:
        coins_list = response.json()  # Try to parse the response as JSON
    except ValueError:  # Handle JSON decode errors
        return render_template('index.html', error="Failed to parse response from CoinGecko API.")
    
    # Check if the response is a list (as expected)
    if not isinstance(coins_list, list):
        return render_template('index.html', error="Unexpected response format from CoinGecko API.")
    
    # Now proceed to process the coins
    coins = [coin['id'] for coin in coins_list]

    if request.method == 'POST':
        coin_id = request.form.get('coin_id')
        days = request.form.get('days')
        file_format = request.form.get('file_format', 'csv')  # User can select 'csv' or 'xlsx'

        if coin_id in coins:
            try:
                # Ensure the days parameter is valid
                if days not in ['1', '7', '14', '30', '90', '180', '365']:
                    raise ValueError("Invalid number of days. Please choose from: 1, 7, 14, 30, 90, 180, 365.")

                # Get the market data and predictions
                predictions, df = get_market_chart(coin_id, days)

                # Show the data in the browser or download as file
                if request.form.get('show_data', False):
                    return render_template('data.html', predictions=predictions, coin_id=coin_id, days=days, df=df.to_html(classes='table table-striped'))
                else:
                    # Save the data to the requested format
                    filename = save_to_file(df, file_format)
                    return send_file(filename, as_attachment=True)

            except ValueError as e:
                return render_template('index.html', error=str(e), coins=coins)

        else:
            return render_template('index.html', error="Invalid coin ID", coins=coins)

    return render_template('index.html', coins=coins)

def get_market_chart(coin_id, days):
    # Validate that the 'days' parameter is in the accepted range
    if days not in ['1', '7', '14', '30', '90', '180', '365']:
        raise ValueError("Invalid number of days. Please choose from: 1, 7, 14, 30, 90, 180, 365.")
    
    # Get OHLC data (remove the API key from the URL as it's not needed)
    response = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}')
    
    # Check if the response is valid
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch OHLC data for {coin_id}. Status code: {response.status_code}")
    
    ohlc_data = response.json()
    
    # Check if the OHLC data is not empty and is a list
    if not ohlc_data or not isinstance(ohlc_data, list):
        raise ValueError(f"OHLC data is empty or not in expected format for {coin_id}")
    
    # Assuming 'ohlc_data' is a list of [time, open, high, low, close] lists
    ohlc = np.array(ohlc_data)

    # Check if the data has the correct shape (it should be 2D)
    if len(ohlc.shape) != 2 or ohlc.shape[1] != 5:
        raise ValueError(f"Expected OHLC data to be 2D with 5 columns (time, open, high, low, close), got shape: {ohlc.shape}")
    
    # Create a DataFrame for OHLC data
    df = pd.DataFrame(ohlc, columns=['time', 'open', 'high', 'low', 'close'])
    
    # Convert Unix timestamp to a readable date format
    df['time'] = pd.to_datetime(df['time'], unit='ms')

    # Use only the 'time' and 'close' columns for prediction
    X = ohlc[:, [0, 4]]  # Time and Close price
    y = ohlc[:, 4]  # Close price

    # Scale the data
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)

    # Train the model
    model = LinearRegression()
    model.fit(X, y)

    # Make a prediction
    y_pred = model.predict(X)

    # Create a list of dates for the predictions
    start_date = datetime.now()
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(len(y_pred))]

    # Combine the dates and predictions into a dictionary
    predictions = {date: pred for date, pred in zip(dates, y_pred)}

    return predictions, df

def save_to_file(df, file_format):
    """
    Saves the DataFrame to a CSV or XLSX file.
    :param df: The DataFrame to save.
    :param file_format: 'csv' or 'xlsx'.
    :return: The file path of the saved file.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if file_format == 'xlsx':
        filename = f"market_data_{timestamp}.xlsx"
        df.to_excel(filename, index=False)
    else:
        filename = f"market_data_{timestamp}.csv"
        df.to_csv(filename, index=False)
    
    return filename

if __name__ == '__main__':
    app.run(debug=True)
