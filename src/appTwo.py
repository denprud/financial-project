from flask import Flask
import yfinance as yf
import ta
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import find_dotenv, load_dotenv
from email.mime.multipart import MIMEMultipart 
from threading import Lock
import time
from flask_socketio import SocketIO
from multiprocessing import Process, Manager
from scipy.signal import argrelextrema
import numpy as np

app = Flask(__name__)
app.secret_key = 'your secret here'
sio = SocketIO(app)

#thread = None
thread_lock = Lock()
threads = {}

load_dotenv()

SENDER = os.getenv("SENDER")
RECIEVER = os.getenv("RECIEVER")
PASSWORD = os.getenv("PASSWORD")

#stock_symbol = 'AAPL'
rsiScore = 0
#volumeScore = 0
baseScore = 0

# Variable for checking over 70 or under 30
isRecentlyUnderBound = False

def getRangesLower(rsi):
    if rsi < 30:
        return .3
    elif rsi > 30 and rsi < 39.44:
        return .5
    elif rsi > 39.44 and rsi < 42.28:
        return .7
    elif rsi > 42.28 and rsi < 50:
        return 1
    elif rsi > 50 and rsi < 54.72:
        return .7
    elif rsi > 54.72 and rsi < 61.44:
        return .5
    else:
        return .3
    
def getRangesHigher(rsi):
    if rsi > 70:
        return -.3
    elif rsi < 70 and rsi > 60.56:
        return -.5
    elif rsi < 60.56 and rsi > 54.72:
        return -.7
    elif rsi < 54.72 and rsi > 50:
        return -1
    elif rsi < 50 and rsi > 45.28:
        return -.7
    elif rsi < 45.28 and rsi > 38.56:
        return -.5
    else:
        return -.3
    
def fib_get_low_high(data):
    # Define comparator for argrelextrema
    comparator = np.less
    comparatorTwo = np.greater

    # Find indices of relative highs
    high_indices = argrelextrema(data['High'].values, comparatorTwo)

    # Find indices of relative lows
    low_indices = argrelextrema(data['Low'].values, comparator)

    # high = data['High'].max()
    # low = data['Low'].min()
    print(data['High'])
    print(high_indices[0])
    print(high_indices[0][-1])
    
  
    #"Relative highs:""
    high = data['High'].iloc[high_indices[-1]].iloc[-1]
    #"Relative lows:"
    low = data['Low'].iloc[low_indices[-1]].iloc[-1]

    price = data['High'].iloc[-1]
    # If the extrama isnt set yet
    if high < price:
        high = price
    elif low > price:
        low = price

    return high, low

def fib_get_bands(price, high, low):
    priceStats = {}
    fibInterval = high - low
    levels = {
        '100%': high,
        '78.6%': high - 0.786 * fibInterval,
        '61.8%': high - 0.618 * fibInterval,
        '50%': high - 0.5 * fibInterval,
        '38.2%': high - 0.382 * fibInterval,
        '23.6%': high - 0.236 * fibInterval,
        '0%': low
    }
    print(f"Diff: {fibInterval}, levels 100 : {levels['100%']}, levels 0: {levels['0%']} price: {price}")
    # print(price<levels['100%'])
    priceStats["fibInterval"] = fibInterval
    if price >= levels['100%']:
        priceStats["upperBand"] = levels['100%']
        priceStats["lowerBand"] = levels['100%']
        priceStats["oneThirdPercentAbove"] = 0.07788
        priceStats["oneThirdPercentBelow"] = 0.07788
        priceStats["twoThirdPercentAbove"] = 0.15576
        priceStats["twoThirdPercentBelow"] = 0.15576
        print("100")
    elif price < levels['100%'] and price >= levels['78.6%']:
        priceStats["upperBand"] = levels['100%']
        priceStats["lowerBand"] = levels['78.6%']
        priceStats["oneThirdPercentAbove"] = 0.07788
        priceStats["oneThirdPercentBelow"] = 0.03894
        priceStats["twoThirdPercentAbove"] = 0.15576
        priceStats["twoThirdPercentBelow"] = 0.07788
        print("100, 78")
    elif price < levels['78.6%'] and price >= levels['61.8%']:
        priceStats["upperBand"] = levels['78.6%']
        priceStats["lowerBand"] = levels['61.8%']
        priceStats["oneThirdPercentAbove"] = 0.03894
        priceStats["oneThirdPercentBelow"] = 0.03894
        priceStats["twoThirdPercentAbove"] = 0.07788
        priceStats["twoThirdPercentBelow"] = 0.07788
        print("78, 61")
    elif price < levels['61.8%'] and price >= levels['50%']:
        priceStats["upperBand"] = levels['61.8%']
        priceStats["lowerBand"] = levels['50%']
        priceStats["oneThirdPercentAbove"] = 0.03894
        priceStats["oneThirdPercentBelow"] = 0.03894
        priceStats["twoThirdPercentAbove"] = 0.07788
        priceStats["twoThirdPercentBelow"] = 0.07788
        print("61, 50")
    elif price < levels['50%'] and price >= levels['38.2%']:
        priceStats["upperBand"] = levels['50%']
        priceStats["lowerBand"] = levels['38.2%']
        priceStats["oneThirdPercentAbove"] = 0.03894
        priceStats["oneThirdPercentBelow"] = 0.03894
        priceStats["twoThirdPercentAbove"] = 0.07788
        priceStats["twoThirdPercentBelow"] = 0.07788
        print("50, 38")
    elif price < levels['38.2%'] and price >= levels['23.6%']:
        priceStats["upperBand"] = levels['38.2%']
        priceStats["lowerBand"] = levels['23.6%']
        priceStats["oneThirdPercentAbove"] = 0.03894
        priceStats["oneThirdPercentBelow"] = 0.07788
        priceStats["twoThirdPercentAbove"] = 0.07788
        priceStats["twoThirdPercentBelow"] = 0.15576
        print("38, 23")
    elif price < levels['23.6%'] and price >= levels['0%']:
        priceStats["upperBand"] = levels['23.6%']
        priceStats["lowerBand"] = levels['0%']
        priceStats["oneThirdPercentAbove"] = 0.07788
        priceStats["oneThirdPercentBelow"] = 0.07788
        priceStats["twoThirdPercentAbove"] = 0.15576
        priceStats["twoThirdPercentBelow"] = 0.15576
        print("23, 0")
    else:
        return None
    return priceStats

def fibonacci_retracement(stock_symbol):
    data = yf.download(stock_symbol, period='1y', interval='5d')
    price = data['Close'].iloc[-1]
    high, low = fib_get_low_high(data)
    priceStats = fib_get_bands(price, high, low)
    return priceStats

def getVolume(stock_symbol):
    """
    Multiplier for the Buy/Sell score based on Volume

    Args:
        stock_symbol(int): Symbol for Stock
    
    """
    #global volumeScore
    data = yf.download(stock_symbol, period='1d', interval='1m')
    newPrice =  data['Close'].iloc[-1]
    currentVolume = data['Volume'].iloc[-2]
    averageVolume = data.loc[:, 'Volume'].mean()
    #Get multiplier based on volume
    if currentVolume <= averageVolume + (.236 * averageVolume) and currentVolume >= averageVolume:
        volumeScore = 1.2
    elif currentVolume >= averageVolume + (.236 * averageVolume) and currentVolume <= averageVolume + (.528 * averageVolume):
        volumeScore = 1.7
    elif currentVolume > averageVolume + (.528 * averageVolume):
        volumeScore = 2.0
    else:
        volumeScore = 1.0
    return volumeScore
    
def isRsiOptimal(symbol):
    """
    Indicator that declares if the RSI is in an optimal range for trading

    Args:
        stock_symbol(int): Symbol for Stock

    Returns:
        boolean
    
    """
    try:
        global isRecentlyUnderBound
        global rsiScore
        # Download historical data as dataframe
        data = yf.download(symbol, period='1d', interval='1m')
        # Calculate RSI
        data['RSI'] = ta.momentum.rsi(data['Close'])
        rsi =  data['RSI'].iloc[-1]
        #Using offset of 1 for inaccurate data (69 and 31 instead of 70 and 30)
        if not(data[data.RSI < 31].empty) and data[data.RSI > 69].empty:
            print("case1")
            isRecentlyUnderBound = True
        elif data[data.RSI < 31].empty and not(data[data.RSI > 69].empty):
            print("case2")
            isRecentlyUnderBound = False
        elif data[data.RSI < 31].index[-1] > data[data.RSI > 69].index[-1]:
            print("case3")
            isRecentlyUnderBound = True
        elif data[data.RSI < 31].index[-1] < data[data.RSI > 69].index[-1]:
            print("case4")
            isRecentlyUnderBound = False
        if isRecentlyUnderBound:
            rsiScore = getRangesLower(rsi)
        else:
            rsiScore = getRangesHigher(rsi)
        if rsiScore >= .5 or rsiScore <= .5:
            return True
    except(IndexError):
        app.logger.info("Stock: {symbol}, NO DATA, waiting 60 Seconds")
        # print("There is no data for rsi either under 30 or over 70")
        # print("Waiting 60 seconds")
        return False
    return False
    
# Mailing
def mail(price, priceRange, baseScore):
    smtp = smtplib.SMTP('smtp.mailersend.net', 587) 
    smtp.ehlo() 
    smtp.starttls() 

    # Login with your email and password 
    smtp.login('MS_OCn0v9@trial-o65qngkk60jgwr12.mlsender.net', 'vXI3w6DrtYWhe2N0') 

    msg = MIMEMultipart() 
    msg['Subject'] = "RSI"  
    msg.attach(MIMEText(f"Price: {price}, priceRange:{priceRange}, score:{baseScore}")) 

    to = ["denzelprud1@gmail.com", "shroep@hotmail.com"] 
    smtp.sendmail(from_addr="MS_OCn0v9@trial-o65qngkk60jgwr12.mlsender.net", 
                to_addrs=to, msg=msg.as_string()) 

    smtp.quit()

# Polling
def isPricePollingFinished(data, priceStats, isRecentlyUnderBound, volumeScore):
    global baseScore
    baseScore = volumeScore * rsiScore
    newPrice =  data['Close'].iloc[-1]
    if isRecentlyUnderBound:
        print(f"isRecentUnder:{isRecentlyUnderBound}, newPrice: {newPrice}, metricToPass: {(priceStats["upperBand"] + (priceStats["oneThirdPercentAbove"] * priceStats["fibInterval"]))}")
        if newPrice > (priceStats["upperBand"] + (priceStats["oneThirdPercentAbove"] * priceStats["fibInterval"])):
            if newPrice > (priceStats["upperBand"] + (priceStats["twoThirdPercentAbove"] * priceStats["fibInterval"])):
                mail(price=newPrice, priceRange=priceStats, baseScore="Strong-buy")
            else:
                mail(price=newPrice, priceRange=priceStats, baseScore="buy")
            return True, "Buy"
        else:
            if newPrice < (priceStats["lowerBand"] - (priceStats["oneThirdPercentAbove"] * priceStats["fibInterval"])):
                print("Price broke support, no longer viable strategy")
                return True, "Disband"
    else:
        print(f"isRecentUnder:{isRecentlyUnderBound}, newPrice: {newPrice}, metricToPass: {(priceStats["lowerBand"] - (priceStats["oneThirdPercentAbove"] * priceStats["fibInterval"]))}")
        if newPrice < priceStats["lowerBand"] - (priceStats["oneThirdPercentAbove"] * priceStats["fibInterval"]):
                if newPrice < (priceStats["lowerBand"] - (priceStats["twoThirdPercentAbove"] * priceStats["fibInterval"])):
                    mail(price=newPrice, priceRange=priceStats, baseScore="Strong-sell")
                else:
                    mail(price=newPrice, priceRange=priceStats, baseScore="sell")
                return True, "Sell"
                
        else:
            if newPrice > (priceStats["upperBand"] + (priceStats["oneThirdPercentAbove"] * priceStats["fibInterval"])):
                print("Price broke resistance, no longer viable strategy")
                return True, "Disband"
    return False, "N/A"
                    
        

@app.route('/')
def index():
    while True:
        stock_symbol = "NVDA"
        market = isRsiOptimal("^SPX")
        #sector = setUpDataStock(SECTOR_SYMBOL)
        stock = isRsiOptimal(stock_symbol)
        volumeScore = getVolume(stock_symbol)
        if market and stock:
            print("All RSI's  are good to go")
            priceStats = fibonacci_retracement(stock_symbol)
            print(priceStats)
            if not(priceStats == None):
                while True:
                    data = yf.download(stock_symbol, period='1d', interval='1m')
                    priceFinished, sentiment = isPricePollingFinished(data=data,priceStats=priceStats, isRecentlyUnderBound=isRecentlyUnderBound, volumeScore=volumeScore)
                    if priceFinished:
                        break
                    time.sleep(60)
        time.sleep(60)
    return "Server is Running"


if __name__ == '__main__':
    sio.run(app)

