import hmac
import json
import requests
import time
import sys
import math

# Concatenate the signature
def preHash(timestamp, method, requestPath, queryString, body):
    pre = timestamp + method + requestPath
    if queryString.strip() != '':
        pre = pre + '?' +queryString.strip()
    if body.strip() != '':
        pre = pre + body.strip()
    print(pre)
    return pre

# Generate signature
def toSign(timestamp, method, requestPath, queryString, body, secretKey):
    return hmac.new(secretKey.encode('UTF-8'),
                    preHash(timestamp, method, requestPath, queryString, body).encode('UTF-8'),
                    "SHA256").hexdigest()

# Get user balance
def get_User_Balance(asset_type, apikey, secret):
    asset_type = asset_type.upper()  
    url = "https://openapi.zke.com/sapi/v1/account"
    current = str(round(time.time() * 1000))

    # Generate signature
    sign = toSign(current, 'GET', '/sapi/v1/account', '', '', secret)

    # Construct Headers
    getheaders = {
        'X-CH-APIKEY': apikey,
        'X-CH-TS': current,
        'Content-Type': 'application/json',
        'X-CH-SIGN': sign
    }

    response = requests.get(url=url, headers=getheaders)
    response_json = response.json()

    if 'balances' in response_json:
        for balance in response_json['balances']:
            if balance['asset'] == asset_type:
                return balance['free']
    return -1000

# Get trading pair information
def get_Ticker(base_asset):
    base_asset = base_asset.upper()  
    url = "https://openapi.zke.com/sapi/v1/symbols"

    response = requests.get(url=url)
    response_json = response.json()

    if 'symbols' in response_json:
        for symbol in response_json['symbols']:
            if symbol['baseAssetName'] == base_asset:
                return symbol['symbol']
    return None

# Get user input of the currency symbol
def get_valid_symbol():
    while True:
        symbol = input("Please enter the currency symbol you want to trade: ")

        ticker = get_Ticker(symbol)
        if ticker is not None:
            print("The currency symbol you entered is valid and can be traded.")
            return ticker, symbol
        else:
            print("The currency symbol you entered is invalid and this currency cannot be traded temporarily. Please enter another currency symbol.")

# Get user input of USDT amount
def get_valid_usdt_amount(apikey, secret):
    while True:
        amount = float(input("Please enter the amount of USDT you need to use for volume brushing: "))

        balance = float(get_User_Balance("USDT", apikey, secret))
        if amount <= balance:
            return round(amount, 3)  
        else:
            print("The amount you entered is greater than your USDT balance, please re-enter the amount of USDT or try again after topping up the balance.")

# Get user input of the trade volume to be brushed
def get_valid_trade_volume():
    while True:
        volume = int(input("Please enter the trading volume you need to brush: "))

        if volume > 10:
            return volume
        else:
            print("The trading volume you entered must be greater than 1000, please re-enter.")

# Get user input of apikey and secret
def get_valid_apikey_and_secret():
    while True:
        apikey = input("Please enter your apikey: ")
        secret = input("Please enter your secret: ")

        # Print the input for verification
        print("The apikey you entered is: ", apikey)
        print("The secret you entered is: ", secret)

        confirm = input("Is the above information correct? If correct, please enter 'y', if incorrect, please enter 'n': ")

        if confirm.lower() == 'n':
            continue
        elif confirm.lower() == 'y':
            balance = get_User_Balance("USDT", apikey, secret)
            if balance != -1000:
                print("The apikey you entered is valid and you can proceed to the next step.")
                return apikey, secret
            else:
                print("The apikey you entered is invalid, please re-enter a valid apikey.")

# Buy order function
def trade_Buy(apikey, secret, symbol, volume):
    url = "https://openapi.zke.com/sapi/v1/order"
    current = str(round(time.time() * 1000))
    param = json.dumps({"symbol": symbol, "volume": volume, "side": "BUY", "type": "MARKET"})

    # Generate signature
    sign = toSign(current, 'POST', '/sapi/v1/order', '', param, secret)

    # Construct Headers
    postHeaders = {
        'X-CH-APIKEY': apikey,
        'X-CH-TS': current,
        'Content-Type': 'application/json',
        'X-CH-SIGN': sign
    }
    response = requests.post(url=url, headers=postHeaders, data=param)
    response_json = response.json()

    # Check the returned json content
    if "orderId" in response_json and response_json["orderId"]:
        return True
    else:
        return "error!"

# Sell order function
def trade_Sell(apikey, secret, symbol, volume):
    url = "https://openapi.zke.com/sapi/v1/order"
    current = str(round(time.time() * 1000))
    param = json.dumps({"symbol": symbol, "volume": volume, "side": "SELL", "type": "MARKET"})

    # Generate signature
    sign = toSign(current, 'POST', '/sapi/v1/order', '', param, secret)

    # Construct Headers
    postHeaders = {
        'X-CH-APIKEY': apikey,
        'X-CH-TS': current,
        'Content-Type': 'application/json',
        'X-CH-SIGN': sign
    }
    response = requests.post(url=url, headers=postHeaders, data=param)
    response_json = response.json()

    # Check the returned json content
    if "orderId" in response_json and response_json["orderId"]:
        return True
    else:
        return response_json  

# Get the latest transaction price
def lastPrice(ticker):
    response = requests.get("https://openapi.zke.com/open/api/get_allticker")
    data = response.json()

    for item in data["data"]["ticker"]:
        if item["symbol"] == ticker:
            return float(item["last"])

    return None

# Brush volume function
def loop_trade(apikey, secret, symbol, ticker, amount, allVolume):
    total_trade_volume = 0

    # Get the latest price and calculate minMount
    price = lastPrice(ticker)
    if price == 0:
        print("The price is 0, minMount cannot be calculated")
        sys.exit(1)
    minMount = int(1 / price)

    while total_trade_volume < allVolume:
        # Query balance
        balance = get_User_Balance(symbol, apikey, secret)
        balance = float(balance)
        if price > 1:
            balance = math.floor(balance * 10000) / 10000         
        else:
            balance = math.floor(balance)
        
        if balance < minMount:
            # Execute the buy operation
            result = trade_Buy(apikey, secret, ticker, amount)
            if result is not True:
                print(result)
                sys.exit(1)
            total_trade_volume += amount
        else:
            # Execute the sell operation
            result = trade_Sell(apikey, secret, ticker, balance)
            if result is not True:
                print(result)
                sys.exit(1)
            total_trade_volume += balance * price

        print("Current total accumulated trading volume: ", total_trade_volume)

        # Query interval pause for 5s
        time.sleep(5)

    print("The task of brushing volume is completed, and the total accumulated trading volume: ", total_trade_volume)

# Main function
def main():
    # Step 1: Get the user's input of apikey and secret
    apikey, secret = get_valid_apikey_and_secret()

    # Step 2: Let the user enter the currency symbol
    ticker, symbol = get_valid_symbol()

    # Step 3: Let the user enter the amount of USDT to be used for volume brushing
    amount = get_valid_usdt_amount(apikey, secret)

    # Step 4: Let the user enter the trading volume to be brushed
    allVolume = get_valid_trade_volume()

    # Print all user input information for confirmation
    print("The apikey you entered is: ", apikey)
    print("The secret you entered is: ", secret)
    print("The currency symbol you chose is: ", symbol + " (The trading pair is " + ticker + ")")
    print("The amount of USDT you chose to use is: ", amount)
    print("The trading volume to be brushed that you entered is: ", allVolume)

    confirm = input("Is the above information correct? If correct, please enter 'y', if incorrect, please enter 'n': ")

    if confirm.lower() == 'y':
        print("Your information has been confirmed, start brushing trading volume.")
        loop_trade(apikey, secret, symbol, ticker, amount, allVolume)
    elif confirm.lower() == 'n':
        print("Your information has not been confirmed, please rerun the program.")

if __name__ == "__main__":
    main()
