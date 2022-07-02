from cmath import e
from email import message
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


#debug true/false
debug = False
number_divs = 7 # how many dividends you want to go back and compare - 


#Get the ticker symbols (becareful dont go crazy)
input_string = input("Enter Ticker symbols: ")
words = input_string.split()
for word in words:
    #print(word) -- debug thing
    freq = 0
    frequency = ""

    #Now get frequency (just cause its useful to have but using number_divs)
    
    page = requests.get("https://dividendhistory.org/payout/" + word)
    message = page.text
    freq = 0
    frequency = ""
    if message.find("Stock does not exist") < 0 :
        pos = message.find("Frequency:")
        endpos = message.find('</p>',pos)
        #print(message[pos+11:endpos])
        frequency = message[pos+11:endpos]
        if frequency == "Monthly":
            freq = 1
        elif frequency == "Quarterly":
            freq = 4
        elif frequency == "Annual":
            freq = 12
        else:
            freq = 0 
        html = BeautifulSoup(message, 'html.parser')
        #find the last number of dividends to go back
        dfs = pd.read_html(str(html), attrs = {'class': 'table table-striped table-bordered'})[0]
        dfs.columns = [c.replace('% ', 'C') for c in dfs.columns]
        #remove old data
        for index, row in dfs.iterrows():
            #print(row['Ex-Dividend Date'])
            e_date = row['Ex-Dividend Date']
            e_date_obj = datetime.strptime(e_date, '%Y-%m-%d')
            c_date = datetime.now()
            if e_date_obj > c_date:
                dfs.drop(index, inplace=True)
        #if you asks for more divs there there is - go to max on divhistory
        if len(dfs) < number_divs:
            number_divs = len(dfs)
        #df_top = df['Ex-Dividend Date'].head(number_divs)
        df_top = dfs.head(number_divs)
        
        total_days = 0
        for index, row in df_top.iterrows():
            #print(row['Ex-Dividend Date'], row['Cash Amount'])
            date_time_str =  row["Ex-Dividend Date"]
            date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d')
            #you can go back more days - but 30 days is what i used
            #But getting a start/end date to use yfinance library 
            days = timedelta(30)
            end_date_obj = date_time_obj - days
            #Get info from yahoo finance library
            msft = yf.Ticker(word)
            #df_trades = df_yahoo(start=end_date_obj.strftime('%F'), end=date_time_str, actions=False)
            df_trades = msft.history(start=end_date_obj.strftime('%F'), end=date_time_str, actions=False)
            
            #find the cheapest day to buy the stock 
            min_val = df_trades['Close'].min()
            df_row = df_trades.loc[df_trades['Close'] == min_val]
            low_date_obj = df_row.index[0]
            delta = date_time_obj - low_date_obj
            total_days = total_days + delta.days
            #print(delta.days)
        aveage_days = total_days / number_divs
        print("Average Days before Ex-Date to buy ",word," is ",aveage_days)
print("Done with analysis")
