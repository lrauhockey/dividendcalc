from cmath import e
from email import message
from tkinter import E
import requests
from time import sleep
from bs4 import BeautifulSoup
from datetime import *
import sys
from requests_html import HTMLSession
import pandas as pd
import numpy as np
from urllib.request import Request, urlopen
import ssl
import yfinance as yf
import yahoo_fin.stock_info as si
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
peRatio = 0
dividendYield = 0
payoutRatio = 0
epsAllPos =""
dividendYield5YR = 0
epsQuarterlyGrowth = 0
averageReturn5Yr =0
dummy = 0
shortName = ""
longName = ""

print('ticker, Name,  PE Ratio, Dividend Yierd, Payout Ratio, EPS for Last 5 years Pos, divided 5 year, eps Quarterly Growth')
with open('payout3.txt') as f:
    for line in f:
        #try:
        len_of_frame = 0
        word = line.strip()
        try:
            msft = yf.Ticker(word)
            stock_info = msft.info
            payoutRatio = stock_info['payoutRatio']
            dividendYield = stock_info['dividendYield']
            dividendYield5YR = stock_info['fiveYearAvgDividendYield']
            epsQuarterlyGrowth = stock_info['earningsQuarterlyGrowth']
            averageReturn5Yr = stock_info['fiveYearAverageReturn']
            shortName = stock_info['shortName']
            shortName = shortName.replace(","," ")
            longName = stock_info['longName']
        except Exception as e:
            payoutRatio = 0
            dividendYield = 0
            dividendYield5YR = 0
            epsQuarterlyGrowth = 0
            averageReturn5Yr   = 0
        finally:
            dummy = dummy + 1
        #This uses fin_yahoo vs yahoo fin.. it has a FutureWarning error in it 
        try:
            msft_data = si.get_quote_table(word)
            peRatio = msft_data['PE Ratio (TTM)']
        except Exception as e:
            peRatio = 0
        finally:
            dummy = dummy + 1
        #check if all earning in yFinance (4 years > 0 )
        try:
            if (msft.earnings['Earnings'] > 0).all:
                epsAllPos = 'True'
            else:
                #print(word, " last ",len_of_frame, " quarters have at least one negative") 
                epsAllPos = "False"   
        except Exception as e:
            epsAllPos = "Not Found"
        finally:
            dummy = dummy + 1
            #calculating the last 5 years earnings average - i didnt use it but might in the future
        #earn_hist = si.get_earnings_history(word)
        #frame = pd.DataFrame()
        #frame = pd.DataFrame.from_dict(earn_hist)
        #len_of_frame = len(frame)
        #if len_of_frame > 20:
        #    len_of_frame = 20
        #earnings_frame = frame.dropna().head(len_of_frame)
        #eps_total = earnings_frame['epsactual'].sum()
        #years = len_of_frame / 4
        #eps_average = eps_total/ years
        
        #this is more important has any earnings been negative
        #eps_gtz = earnings_frame['epsactual']
        #if (earnings_frame['epsactual']>=0).all():
        #    #print(word, " last ",len_of_frame, " quarters all positive")
        #    epsAllPos = 'True'
        #else:
            #print(word, " last ",len_of_frame, " quarters have at least one negative") 
        #    epsAllPos = "False"          
        print(word,",",shortName,",",peRatio,",",dividendYield,",",payoutRatio,",",epsAllPos,",",dividendYield5YR,",",epsQuarterlyGrowth)
        #print(msft.earnings['Earnings'])
        sleep(3)
        #except Exception as e:
        #    print(e)
print("Done:", dummy)