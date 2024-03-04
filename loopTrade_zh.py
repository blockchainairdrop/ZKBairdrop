import hmac
import json
import requests
import time
import sys
import math
#拼接签名
#meet the signature
def preHash(timestamp, method, requestPath, queryString, body):
    #拼接签名
    pre = timestamp + method + requestPath
    if queryString.strip() != '':
        pre = pre + '?' +queryString.strip()
    if body.strip() != '':
        pre = pre + body.strip()
    print(pre)
    return pre

#生成签名
#generate signature
def toSign(timestamp, method, requestPath, queryString, body, secretKey):
    return hmac.new(secretKey.encode('UTF-8'),
                    preHash(timestamp, method, requestPath, queryString, body).encode('UTF-8'),
                    "SHA256").hexdigest()
#获取用户余额
#用法: get_User_Balance("USDT",apikey)
def get_User_Balance(asset_type, apikey, secret):
    asset_type = asset_type.upper()  # Convert asset_type to uppercase
    url = "https://openapi.zke.com/sapi/v1/account"
    current = str(round(time.time() * 1000))

    # generate signature
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
#获取交易对信息
#用法: get_Ticker("BTC")
def get_Ticker(base_asset):
    base_asset = base_asset.upper()  # Convert base_asset to uppercase
    url = "https://openapi.zke.com/sapi/v1/symbols"

    response = requests.get(url=url)
    response_json = response.json()

    if 'symbols' in response_json:
        for symbol in response_json['symbols']:
            if symbol['baseAssetName'] == base_asset:
                return symbol['symbol']
    return None

#获取用户输入的币种符号symbol
#用法:
#       symbol = get_valid_symbol()
#       print("你选择的币种符号是: ", symbol)
def get_valid_symbol():
    while True:
        symbol = input("请输入你要交易的币种符号: ")

        ticker = get_Ticker(symbol)
        if ticker is not None:
            print("你输入的币种符号是有效的，可以进行交易。")
            return ticker, symbol
        else:
            print("你输入的币种符号无效，暂时无法交易这个币种，请输入别的币种符号。")

#获取用户输入USDT的数量
#用法:
#       amount = get_valid_usdt_amount()
#       print("你输入的USDT数量是: ", amount)
def get_valid_usdt_amount(apikey, secret):
    while True:
        amount = float(input("请输入你需要进行刷量使用的USDT的数量: "))

        balance = float(get_User_Balance("USDT", apikey, secret))
        if amount <= balance:
            return round(amount, 3)  # Round to 3 decimal places取小数点后三位
        else:
            print("你输入的数量大于你的USDT余额，请重新输入USDT的数量或者先进行余额充值后再尝试。")

#获取用户输入的要刷取的交易量
#用法:            
#       amount = get_valid_trade_amount()
#       print("你输入的交易量是: ", amount)
def get_valid_trade_volume():
    while True:
        volume = int(input("请输入你需要刷取的交易量: "))

        if volume > 10:
            return volume
        else:
            print("你输入的交易量必须大于1000，请重新输入。")     

#获取用户输入的apikey和secret
def get_valid_apikey_and_secret():
    while True:
        apikey = input("请输入你的apikey: ")
        secret = input("请输入你的secret: ")

        # 打印输入的内容，用于验证
        print("你输入的apikey是: ", apikey)
        print("你输入的secret是: ", secret)

        confirm = input("请确认以上信息是否正确? 如果正确请输入'y', 如果不正确请输入'n': ")

        if confirm.lower() == 'n':
            continue
        elif confirm.lower() == 'y':
            balance = get_User_Balance("USDT", apikey, secret)
            if balance != -1000:
                print("你输入的apikey是有效的，可以继续下一步。")
                return apikey, secret
            else:
                print("你输入的apikey无效，请重新输入有效的apikey。")
#买入订单函数
def trade_Buy(apikey, secret, symbol, volume):
    # 设置OpenApi调用的域名url
    url = "https://openapi.zke.com/sapi/v1/order"
    current = str(round(time.time() * 1000))
    param = json.dumps({"symbol": symbol, "volume": volume, "side": "BUY", "type": "MARKET"})

    # 生成签名
    sign = toSign(current, 'POST', '/sapi/v1/order', '', param, secret)

    # 构造Headers
    postHeaders = {
        'X-CH-APIKEY': apikey,
        'X-CH-TS': current,
        'Content-Type': 'application/json',
        'X-CH-SIGN': sign
    }
    response = requests.post(url=url, headers=postHeaders, data=param)
    response_json = response.json()

    # 检查返回的json内容
    if "orderId" in response_json and response_json["orderId"]:
        return True
    else:
        return "error!"
    
#卖出订单函数
def trade_Sell(apikey, secret, symbol, volume):
    # 设置OpenApi调用的域名url
    url = "https://openapi.zke.com/sapi/v1/order"
    current = str(round(time.time() * 1000))
    param = json.dumps({"symbol": symbol, "volume": volume, "side": "SELL", "type": "MARKET"})

    # 生成签名
    sign = toSign(current, 'POST', '/sapi/v1/order', '', param, secret)

    # 构造Headers
    postHeaders = {
        'X-CH-APIKEY': apikey,
        'X-CH-TS': current,
        'Content-Type': 'application/json',
        'X-CH-SIGN': sign
    }
    response = requests.post(url=url, headers=postHeaders, data=param)
    response_json = response.json()

    # 检查返回的json内容
    if "orderId" in response_json and response_json["orderId"]:
        return True
    else:
        return response_json  # 返回原json数据不做处理
    
#获取最新成交价
def lastPrice(ticker):
    # 访问API获取所有ticker的信息
    response = requests.get("https://openapi.zke.com/open/api/get_allticker")
    data = response.json()

    # 遍历所有ticker，找到对应的ticker并返回其最新价格
    for item in data["data"]["ticker"]:
        if item["symbol"] == ticker:
            return float(item["last"])

    # 如果没有找到对应的ticker，返回None
    return None

#刷量函数
#用法:
#调用函数loop_trade(apikey, secret, symbol, ticker, amount, allVolume)
def loop_trade(apikey, secret, symbol, ticker, amount, allVolume):
    total_trade_volume = 0

    # 获取最新价格并计算minMount
    price = lastPrice(ticker)
    if price == 0:
        print("价格为0,无法计算minMount")
        sys.exit(1)
    minMount = int(1 / price)

    while total_trade_volume < allVolume:
        # 查询余额
        balance = get_User_Balance(symbol, apikey, secret)
        balance = float(balance)
        if price > 1:
            balance = math.floor(balance * 10000) / 10000         
        else:
            balance = math.floor(balance)
        
        if balance < minMount:
            # 执行买入操作
            result = trade_Buy(apikey, secret, ticker, amount)
            if result is not True:
                print(result)
                sys.exit(1)
            total_trade_volume += amount
        else:
            # 执行卖出操作
            result = trade_Sell(apikey, secret, ticker, balance)
            if result is not True:
                print(result)
                sys.exit(1)
            total_trade_volume += balance * price

        print("目前总累积的交易量: ", total_trade_volume)

        # 查询间隔停顿5s
        time.sleep(5)

    print("刷量任务完成，总累积交易量: ", total_trade_volume)

#主函数
def main():
    # 第一步：获取用户输入的apikey和secret
    apikey, secret = get_valid_apikey_and_secret()

    # 第二步：让用户输入币种符号
    ticker, symbol = get_valid_symbol()

    # 第三步：让用户输入用于刷量的USDT的数量
    amount = get_valid_usdt_amount(apikey, secret)

    # 第四步：让用户输入要刷取的交易量
    allVolume = get_valid_trade_volume()

    # 打印出用户输入的所有信息，进行确认
    print("你输入的apikey是: ", apikey)
    print("你输入的secret是: ", secret)
    print("你选择的币种符号是: ", symbol + " (交易对是" + ticker + ")")
    print("你选择使用的USDT数量是: ", amount)
    print("你输入的要刷取的交易量是: ", allVolume)

    confirm = input("请确认以上信息是否正确? 如果正确请输入'y', 如果不正确请输入'n': ")

    if confirm.lower() == 'y':
        print("你的信息已确认，开始刷交易量。")
        # 在这里添加你的刷量代码
        loop_trade(apikey, secret, symbol, ticker, amount, allVolume)
    elif confirm.lower() == 'n':
        print("你的信息未确认，请重新运行程序。")

if __name__ == "__main__":
    main()
