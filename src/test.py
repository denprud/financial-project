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
import pandas as pd

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
    

SENDER = os.getenv("SENDER")
RECIEVER = os.getenv("RECIEVER")
PASSWORD = os.getenv("PASSWORD")

# Stock and RSI threshold
stock_symbol = 'NVDA'
rsi_threshold = 60.56
ranges = None
targetRsi = None
targetPrice = None
newPrice = None
priceRange = None
data = None
baseScore = None
# Variable for checking over 70 or under 30
isRecentlyUnderBound = False

def setUpData():
    # Download historical data as dataframe
    df = yf.download(stock_symbol, period='6mo', interval='5d')

    # Calculate RSI
    # data['RSI'] = ta.momentum.rsi(data['Close'])
    # print(data)
    df.to_csv('out.csv', index=True)

#Constantly poll for new RSI
def rsiPoll():
    newRsi = data['RSI'].iloc[-1]
    #If we are working over 30
    if isRecentlyUnderBound:
        if newRsi < ranges[0]:
            targetRsi = ranges[0]
            targetPrice =  data['Close'].iloc[-1]
            priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
            pricePoll()
        elif newRsi > ranges[1]:
            targetRsi = ranges[1]
            targetPrice =  data['Close'].iloc[-1]
            priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
            pricePoll()
    #If we are working under 70
    else:
        if newRsi > ranges[0]:
            targetRsi = ranges[0]
            targetPrice =  data['Close'].iloc[-1]
            priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
            pricePoll()
        elif newRsi < ranges[1]:
            targetRsi = ranges[1]
            targetPrice =  data['Close'].iloc[-1]
            priceRange = (targetPrice + targetPrice*0.05, targetPrice - targetPrice*0.05 )
            pricePoll()
    

#Constantly poll for new Price ande see if it hits the range
def pricePoll():
    newPrice =  data['Close'].iloc[-1]
    if newPrice < priceRange[0]:
        baseScore = -0.5
    elif newPrice > priceRange[1]:
        baseScore = 0.5

    
                

setUpData()