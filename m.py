import requests
import time
from datetime import datetime, timedelta
import hashlib
import hmac
import urllib.parse

# Function to read Telegram-Init-Data from data.txt
def read_telegram_init_data(file_path):
    with open(file_path, 'r') as file:
        telegram_init_data = [line.strip() for line in file.readlines() if line.strip()]
    return telegram_init_data

# Function to write updated Telegram-Init-Data to data.txt
def write_telegram_init_data(file_path, telegram_init_data_list):
    with open(file_path, 'w') as file:
        for telegram_init_data in telegram_init_data_list:
            file.write(telegram_init_data + '\n')

# Function to generate hash
def generate_hash(data, secret_key):
    return hmac.new(secret_key, data.encode('utf-8'), hashlib.sha256).hexdigest()

# Function to update auth_date and hash in telegram_init_data
def update_telegram_init_data(telegram_init_data):
    params = urllib.parse.parse_qs(telegram_init_data)
    current_time = int(time.time())
    params['auth_date'] = [str(current_time)]
    
    user_data = params['user'][0]
    query_id = params['query_id'][0]
    auth_date = params['auth_date'][0]

    data_to_hash = f'user={user_data}&query_id={query_id}&auth_date={auth_date}'
    
    # Perform a dummy request to get Cf-Ray header
    response = requests.get('https://zavod-api.mdaowallet.com/user/claim')
    secret_key = response.headers.get('Cf-Ray').encode('utf-8') if response.headers.get('Cf-Ray') else None
    
    if secret_key:
        hash_value = generate_hash(data_to_hash, secret_key)
        params['hash'] = [hash_value]
        updated_telegram_init_data = urllib.parse.urlencode(params, doseq=True)
        return updated_telegram_init_data
    else:
        return None

# Function to claim using Telegram-Init-Data
def claim_rewards(telegram_init_data):
    url = 'https://zavod-api.mdaowallet.com/user/claim'
    headers = {
        ':authority': 'zavod-api.mdaowallet.com',
        ':method': 'POST',
        ':path': '/user/claim',
        ':scheme': 'https',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
        'Origin': 'https://zavod.mdaowallet.com',
        'Pragma': 'no-cache',
        'Priority': 'u=1, i',
        'Referer': 'https://zavod.mdaowallet.com/',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126", "Microsoft Edge WebView2";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Telegram-Init-Data': telegram_init_data,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
    }
    response = requests.post(url, headers=headers)
    return response.status_code

# Function to display countdown
def display_countdown(seconds):
    while seconds > 0:
        countdown = str(timedelta(seconds=seconds))
        print(f"\rNext claim in: {countdown}", end="")
        time.sleep(1)
        seconds -= 1
    print("\n")

# Function to process accounts and claim rewards
def process_accounts(file_path):
    telegram_init_data_list = read_telegram_init_data(file_path)
    updated_telegram_init_data_list = []

    for telegram_init_data in telegram_init_data_list:
        updated_telegram_init_data = update_telegram_init_data(telegram_init_data)
        if updated_telegram_init_data:
            updated_telegram_init_data_list.append(updated_telegram_init_data)
    
    # Save updated data to data.txt
    write_telegram_init_data(file_path, updated_telegram_init_data_list)
    
    total_accounts = len(updated_telegram_init_data_list)
    print(f"Total accounts in data.txt: {total_accounts}")
    
    for idx, telegram_init_data in enumerate(updated_telegram_init_data_list, start=1):
        print(f"Processing account {idx} out of {total_accounts}")
        print("Claiming rewards...")
        status_code = claim_rewards(telegram_init_data)
        print(f"Claim status: {status_code}")
        
        # Wait for 3 seconds before processing the next account
        if idx < total_accounts:
            print(f"Waiting for 3 seconds before processing the next account...")
            time.sleep(3)
    
    # Countdown for next claim in 2 hours after processing all accounts
    countdown_seconds = 2 * 60 * 60  # 2 hours in seconds
    print("Next claim countdown starts now:")
    display_countdown(countdown_seconds)

# Example usage:
if __name__ == "__main__":
    data_file = 'data.txt'
    
    while True:
        process_accounts(data_file)
        print("Restarting process after 2 hours...")
