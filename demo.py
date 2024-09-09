import requests
import pandas as pd
import time

# List of 20 cryptocurrencies
crypto_ids = [
    'bitcoin', 'ethereum', 'ripple', 'litecoin', 'bitcoin-cash', 'eos',
    'stellar', 'monero', 'tron', 'dash', 'dogecoin', 'cardano',
    'chainlink', 'polkadot', 'uniswap', 'binancecoin', 'solana',
    'polygon', 'shiba-inu', 'avalanche-2'
]

# Function to fetch OHLC data for a given cryptocurrency
def fetch_ohlc(crypto_id, days=120):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto_id}/ohlc?vs_currency=usd&days={days}'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch data for {crypto_id}: {response.status_code}")
        return None
    
    ohlc_data = response.json()
    
    # Return as DataFrame
    df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
    
    # Convert Unix timestamp to readable date
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    return df

# Create an empty DataFrame to hold all data
all_crypto_data = pd.DataFrame()

# Loop through each cryptocurrency and fetch the data
for crypto_id in crypto_ids:
    print(f"Fetching data for {crypto_id}...")
    df = fetch_ohlc(crypto_id, days=120)
    
    if df is not None:
        # Add a column for the cryptocurrency ID
        df['crypto_id'] = crypto_id
        
        # Append to the main DataFrame
        all_crypto_data = pd.concat([all_crypto_data, df], ignore_index=True)
    
    # Avoid hitting API rate limits by adding a slight delay
    time.sleep(1)

# Save the combined data to CSV and Excel
csv_filename = "crypto_ohlc_120_days.csv"
xlsx_filename = "crypto_ohlc_120_days.xlsx"

# Save to CSV
all_crypto_data.to_csv(csv_filename, index=False)
print(f"Data saved to {csv_filename}")

# Save to Excel
all_crypto_data.to_excel(xlsx_filename, index=False)
print(f"Data saved to {xlsx_filename}")
