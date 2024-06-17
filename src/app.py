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

# Stock and RSI threshold
#stock_symbol = 'AAPL'
rsi_threshold = 60.56
ranges = None
targetRsi = None
targetPrice = None
newPrice = None
priceRange = None
# data = None
baseScore = None
# Variable for checking over 70 or under 30
isRecentlyUnderBound = False



def getRangesLower(rsi):
    if rsi < 30:
        return (0, 30)
    elif rsi > 30 and rsi < 39.44:
        return (30, 39.44) 
    elif rsi > 39.44 and rsi < 42.28:
        return (39.44, 42.28)
    elif rsi > 42.28 and rsi < 50:
        return (42.28, 50)
    elif rsi > 50 and rsi < 54.72:
        return (50, 54.72)
    elif rsi > 54.72 and rsi < 61.44:
        return (54.72, 61.44)
    else:
        return (61.44, 100)
    
def getRangesHigher(rsi):
    if rsi > 70:
        return (100, 70) 
    elif rsi < 70 and rsi > 60.56:
        return (70, 60.56) 
    elif rsi < 60.56 and rsi > 54.72:
        return (60.56, 54.72)
    elif rsi < 54.72 and rsi > 50:
        return (54.72, 50)
    elif rsi < 50 and rsi > 45.28:
        return (50, 45.28)
    elif rsi < 45.28 and rsi > 38.56:
        return (45.28, 38.56)
    else:
        return (38.56, 0)

def getWeight(targetRsi, isIncreasing):
    modifier = 1 if isIncreasing == True else -1
    if isRecentlyUnderBound:
        if targetRsi == 30:
            return .1 * modifier
        elif targetRsi == 39.44:
            return .2 * modifier
        elif targetRsi == 45.28:
            return .3 * modifier
        elif targetRsi == 50:
            return .5 * modifier
        elif targetRsi == 54.72:
            return .3 * modifier
        elif targetRsi == 61.44:
            return .2 * modifier
    else:
        if targetRsi == 70:
            return .1 * modifier
        elif targetRsi == 60.56:
            return .2 * modifier
        elif targetRsi == 54.72:
            return .3 * modifier
        elif targetRsi == 50:
            return .5 * modifier
        elif targetRsi == 45.28:
            return .3 * modifier
        elif targetRsi == 38.56:
            return .2 * modifier

def getVolume(currentVolume, averageVolume):
    #Get multiplier based on volume
    if currentVolume <= averageVolume + (.236 * averageVolume) and currentVolume >= averageVolume:
        return 1.2
    elif currentVolume >= averageVolume + (.236 * averageVolume) and currentVolume <= averageVolume + (.528 * averageVolume):
        return 1.7
    elif currentVolume > averageVolume + (.528 * averageVolume):
        return 2
    else:
        return 1
    
    

#Constantly poll for new Price ande see if it hits the range
def pricePoll(stock_symbol, newRsi, priceRange, targetRsi):
    while True:
        app.logger.info(f"PID: {os.getpid()}, Pricing...")
        data = yf.download(stock_symbol, period='1d', interval='1m')
        newPrice =  data['Close'].iloc[-1]
        currentVolume = data['Volume'].iloc[-2]
        averageVolume = data.loc[:, 'Volume'].mean()
        if newPrice < priceRange[1]:
            baseScore = getWeight(targetRsi=targetRsi, isIncreasing=True) * getVolume(currentVolume=currentVolume, averageVolume=averageVolume)
            mail(rsi=newRsi, price=newPrice, priceRange=priceRange, baseScore=baseScore)
            break
        elif newPrice > priceRange[0]:
            baseScore = getWeight(targetRsi=targetRsi, isIncreasing=False) * getVolume(currentVolume=currentVolume, averageVolume=averageVolume)
            mail(rsi=newRsi, price=newPrice, priceRange=priceRange)
            break
        time.sleep(60)

#Constantly poll for new RSI
def rsiPoll(stock_symbol):
    while True:
        app.logger.info(f"PID: {os.getpid()}, RSI POLLING...")
        data = yf.download(stock_symbol, period='1d', interval='1m')
        data['RSI'] = ta.momentum.rsi(data['Close'])
        newRsi = data['RSI'].iloc[-1]
        #If we are working over 30
        if isRecentlyUnderBound:
            if newRsi < ranges[0]:
                targetRsi = ranges[0]
                targetPrice =  data['Close'].iloc[-1]
                priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
                pricePoll(stock_symbol,newRsi, priceRange, targetRsi)
                break
            elif newRsi > ranges[1]:
                targetRsi = ranges[1]
                targetPrice =  data['Close'].iloc[-1]
                priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
                pricePoll(stock_symbol,newRsi, priceRange, targetRsi)
                break
        #If we are working under 70
        else:
            if newRsi > ranges[0]:
                targetRsi = ranges[0]
                targetPrice =  data['Close'].iloc[-1]
                priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
                pricePoll(stock_symbol, newRsi, priceRange, targetRsi)
                break
            elif newRsi < ranges[1]:
                targetRsi = ranges[1]
                targetPrice =  data['Close'].iloc[-1]
                priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
                pricePoll(stock_symbol,newRsi, priceRange, targetRsi)
                break
        time.sleep(60)
    setUpData(stock_symbol)

def setUpData(stock_symbol):
    #app.logger.info(f"PID: {os.getpid()}")
    #print(data[data.RSI < 30].index[-1], data[data.RSI < 30]['RSI'].iloc[-1] )
    #print(data[data.RSI > 70].index[-1], data[data.RSI > 70]['RSI'].iloc[-1] )
    #print(data['RSI'].index[-1], data['RSI'].iloc[-1] )
    while True:
        try:
            global isRecentlyUnderBound
            global ranges
            # Download historical data as dataframe
            data = yf.download(stock_symbol, period='1d', interval='1m')
            # Calculate RSI
            data['RSI'] = ta.momentum.rsi(data['Close'])
            rsi =  data['RSI'].iloc[-1]
            if not(data[data.RSI < 30].empty) and data[data.RSI > 70].empty:
                app.logger.info(f"PID: {os.getpid()}, Case 1")
                isRecentlyUnderBound = True
            elif data[data.RSI < 30].empty and not(data[data.RSI > 70].empty):
                app.logger.info(f"PID: {os.getpid()}, Case 2")
                isRecentlyUnderBound = False
            elif data[data.RSI < 30].index[-1] > data[data.RSI > 70].index[-1]:
                app.logger.info(f"PID: {os.getpid()}, Case 3")
                isRecentlyUnderBound = True
            elif data[data.RSI < 30].index[-1] < data[data.RSI > 70].index[-1]:
                app.logger.info(f"PID: {os.getpid()}, Case 4")
                isRecentlyUnderBound = False
            if isRecentlyUnderBound:
                ranges = getRangesLower(rsi)
            else:
                ranges = getRangesHigher(rsi)
            break
        except(IndexError):
            app.logger.info(f"PID: {os.getpid()}, NO DATA, waiting 60 Seconds")
            # print("There is no data for rsi either under 30 or over 70")
            # print("Waiting 60 seconds")
            time.sleep(60)
    rsiPoll(stock_symbol)

    


# Mailing
def mail(rsi, price, priceRange, baseScore):
    smtp = smtplib.SMTP('smtp.mailersend.net', 587) 
    smtp.ehlo() 
    smtp.starttls() 

    # Login with your email and password 
    smtp.login('MS_OCn0v9@trial-o65qngkk60jgwr12.mlsender.net', 'vXI3w6DrtYWhe2N0') 

    msg = MIMEMultipart() 
    msg['Subject'] = "RSI"  
    msg.attach(MIMEText(f"RSI: {rsi}, RSIRange:{ranges}, Price: {price}, priceRange:{priceRange}, score:{baseScore}")) 

    to = ["denzelprud1@gmail.com"] 
    smtp.sendmail(from_addr="MS_OCn0v9@trial-o65qngkk60jgwr12.mlsender.net", 
                to_addrs=to, msg=msg.as_string()) 

    smtp.quit()

# def start_task(symbol):
#     with thread_lock:
#         if symbol not in threads:
#             threads[symbol] = sio.start_background_task(setUpData(symbol))

# @app.route('/start/<symbol>')
# def start(symbol):
#     start_task(symbol)
#     return f'Started task for {symbol}'

# @app.route('/')
# def index():
#     for symbol in ['AAPL', 'GOOG', 'MSFT']:
#         start_task(symbol)
#     return 'Server is running...'

# @app.route('/')
# def index():
#   global thread
#   with thread_lock:
#       if thread is None:
#           thread = sio.start_background_task(setUpData('AAPL'))
#   return 'Server is running...'

@app.route('/')
def index():
    process1 = Process(target=setUpData, args=('^SPX',))
    process2 = Process(target=setUpData, args=('GOOG',))
    process3 = Process(target=setUpData, args=('NVDA',))
    process1.start()
    process2.start()
    process3.start()
    process1.join()
    process2.join()
    process3.join()
    return 'Server is running...'


if __name__ == '__main__':
    sio.run(app)

