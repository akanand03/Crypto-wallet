import requests
import pandas as pd
import csv

# Your CryptoCompare API key
API_KEY = "34186b853765c755b0a4277d311fdaccf0ee2795b1863080f6f14d1e0e3869a1"

# URL for fetching historical data
# Here we fetch daily data for Bitcoin (BTC) to US Dollars (USD)
url = f"https://min-api.cryptocompare.com/data/v2/histoday"

# Parameters for the API request
params = {
    'fsym': 'BTC',      # Cryptocurrency symbol (e.g., BTC for Bitcoin)
    'tsym': 'USD',      # Target currency (e.g., USD)
    'limit': 2000,      # Number of data points to fetch (max 2000)
    'api_key': API_KEY  # Your API key
}

# Send the GET request
response = requests.get(url, params=params)
data = response.json()

# Extract data
if data['Response'] == 'Success':
    # Normalize the data into a pandas DataFrame
    df = pd.json_normalize(data['Data']['Data'])
    
    # Convert Unix timestamp to a readable date
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Save to CSV file
    df.to_csv('crypto_data.csv', index=False)
    print("Data saved to crypto_data.csv")
else:
    print("Error fetching data:", data['Message'])

# Optional: Display the first few rows of the dataset
print(df.head())

# Preprocessing (Optional Steps)

# Handle missing values (e.g., filling with mean value)
df.fillna(df.mean(), inplace=True)

# Remove duplicates
df.drop_duplicates(inplace=True)

# Save the cleaned data to a new CSV file
df.to_csv('crypto_data_cleaned.csv', index=False)
print("Cleaned data saved to crypto_data_cleaned.csv")
