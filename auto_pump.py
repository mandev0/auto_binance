# pip3 install telethon
import hmac, time, hashlib, requests, json, re
from urllib.parse import urlencode
from telethon.sync import TelegramClient
from telethon import functions, types
from decimal import *

####################
# Static Variables #
####################
Test_Trade = False # Testnet
if Test_Trade:
    ## Testnet Keys
    KEY = 'xxx' #KEY
    SECRET = 'xxx' #SECRET
    BASE_URL = 'https://testnet.binance.vision'
else:
    BASE_URL = 'https://api.binance.com'
    KEY = 'xxx' #KEY
    SECRET = 'xxx' #SECRET
## Telegram
ID = xxx #TelegramID
HASH = 'xxx' #HASH
PHONE = 'xxx' #Phone Number +90 xxx xxx xx xx
USERNAME = 'xxx' #Username
BUY_AMOUNT = Decimal(0.0002) # in BTC
SELL_X = 1.25 # Buy price * SELL_X
####################
####################

#############
# Functions #
#############
def hashing(query_string):
    return hmac.new(SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def get_timestamp():
    return int(time.time() * 1000)


def dispatch_request(http_method):
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json;charset=utf-8',
        'X-MBX-APIKEY': KEY
    })
    return {
        'GET': session.get,
        'DELETE': session.delete,
        'PUT': session.put,
        'POST': session.post,
    }.get(http_method, 'GET')

# used for sending request requires the signature
def send_signed_request(http_method, url_path, payload={}):
    query_string = urlencode(payload, True)
    if query_string:
        query_string = "{}&timestamp={}".format(query_string, get_timestamp())
    else:
        query_string = 'timestamp={}'.format(get_timestamp())

    url = BASE_URL + url_path + '?' + query_string + '&signature=' + hashing(query_string)
    print("{} {}".format(http_method, url))
    params = {'url': url, 'params': {}}
    response = dispatch_request(http_method)(**params)
    return response.json()

# used for sending public data request
def send_public_request(url_path, payload={}):
    query_string = urlencode(payload, True)
    url = BASE_URL + url_path
    if query_string:
        url = url + '?' + query_string
    print("{}".format(url))
    response = dispatch_request('GET')(url=url)
    return response.json()

def Get_Telegram_Messages():
    Telegram_Group = 'https://t.me/bigpumpsignal'
    with TelegramClient(USERNAME, ID, HASH) as Telegram_Client:
        my_channel = Telegram_Client.get_entity(Telegram_Group)
        for message in Telegram_Client.iter_messages(my_channel, limit=1): # ids=1059
            if "?layout=" in message.text and "BTC" in message.text:
                return re.search('([A-Z])\w+', message.text).group(0).replace("_", "")
            else:
                return False

def Get_Coin_Info():
    Info = send_public_request('/api/v3/exchangeInfo')

    return Info

def Get_Sell_Quantity(Quantity, Coin):
    print(Quantity, Coin_Dict[Coin])
    Quantity = Quantity - Decimal(Coin_Dict[Coin])

    return Quantity

def Get_Coin_Avg_Price(Coin):
    Average = send_public_request('/api/v3/avgPrice' , {"symbol": Coin})
    return Average['price']

def Get_Coins_Last_Candle(Coin):
    Candle_Info = {}
    Candles = send_public_request('/api/v3/klines' , {"symbol": Coin, "interval": "15m", "limit": 1})
    Candle_Info['Open'] = Candles[0][1]
    Candle_Info['Close'] = Candles[0][4]
    Candle_Info['High'] = Candles[0][2]
    Candle_Info['Low'] = Candles[0][3]
    return Candle_Info

def Calculate_Amount(AveragePrice):
    Amount = BUY_AMOUNT/Decimal(AveragePrice)
    if Amount < 1:
        return Decimal(Amount)
    else:
        return int(Amount)
    
def Buy_Coin(Coin, AveragePrice):
    params = {
        "symbol": Coin,
        "side": "BUY",
        "type": "MARKET",
        #"stopPrice": StopPrice,
        "quantity": Calculate_Amount(AveragePrice),
    }
    response = send_signed_request('POST', '/api/v3/order', params)
    return response

def Sell_Coin(Coin, StopPrice):
    params = {
        "symbol": Coin,
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": Get_Sell_Quantity(Calculate_Amount(AveragePrice), Coin_Symbol),
        "price": StopPrice
    }
    response = send_signed_request('POST', '/api/v3/order', params)
    return response
#############
#############

########
# CODE #
########
# Get telegram messages
Coin_Dict = {}
Coin_JSON = Get_Coin_Info()
for coin in Coin_JSON['symbols']:
    Coin_Dict[coin['symbol']] = coin['filters'][2]['stepSize']

while True:
    Coin_Symbol = Get_Telegram_Messages()
    if Coin_Symbol:
        print('<---------------------------->')
        print('<- New PUMP given: {}'.format(Coin_Symbol))
        print('<---------------------------->')
        AveragePrice = Get_Coin_Avg_Price(Coin_Symbol)
        print('Buy_Coin:')
        #print(Buy_Coin(Coin_Symbol, AveragePrice))
        print('Sell_Coin:')
        #print(Sell_Coin(Coin_Symbol, format(float(AveragePrice) * SELL_X, '.7f')))
        break
    else:
        print('No new PUMP!')
    time.sleep(0.2)
