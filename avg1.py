import yfinance as yf
import pandas as pd
from yahoofinancials import YahooFinancials
import numpy as np
import requests
from finvizfinance.quote import finvizfinance
from yahoofinancials import YahooFinancials
import yahoo_fin.stock_info as si
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")


dummy = 0
words = []
inputfile = "p1.txt"
with open(inputfile) as k:
    for line in k:
        words.append(line.strip())
line = ''
#words = ['MSFT','DGS','QYLD','USOI','HYLD','JEPI','HDIV','MS','O','MO','JNJ']
#words = ['MSFT']
print('Ticker,Start Price,End Price,Average Start,Average Close,Wins,Losses,Total Div,Average Dif')
for word in words:
    #Things need to calculate 
    #Average price starting - Average Price 5 days after - Average Difference between the 2
    #Count of items  that are pos Negative
    #Starting price and Ending Price for the whole thing
    start_price = 0
    end_price = 0
    close_pr = 0  #2nd closing price?
    ic = 0
    #Count of Pos Neg
    iPos = 0
    iNeg = 0
    #To Get Averages we need totals at the ticker level
    #avg_start_price / avg_close Price, and avg dif (totals and average)
    avg_start_pr_tot = 0
    avg_start_pr = 0
    avg_close_pr_tot = 0
    avg_close_pr = 0
    avg_dif_tot = 0
    avg_dif = 0 

    #not sure what Avg LG is or if needed
    avg_lg = 0
    #this is a counter 
    i_ct = 0
    price_dif = 0

    #two counters of dividends (one value one number)
    tot_div = 0
    num_divs = 0
    
    #Yfin get stuff
    aapl = yf.Ticker(word)
    df = aapl.history(start="2021-01-01", end="2022-10-22", actions=False)
    df1 = aapl.actions

    #add a column with count 
    df['index_ct'] = range(1, len(df)+ 1)
    df1['index_ct'] = range(1, len(df1)+ 1)

    #get start and end prices
    start_price = df.loc[df['index_ct']==1,'Close'].iloc[0]
    end_price = aapl.info['regularMarketPrice']

    #create a new column and put date/time as the new colunmn
    df = df.assign(C="")
    for ind in df.index:
        df.loc[ind]['C'] = ind
        df.at[ind, 'C']= ind
    
    #for each of the actions (dividends) need to find the starting price
    #the next 5 prices (average)
    #the difference between them 
    for ind in df1.index:
        #zero out the avg close, the total close, the price dif, the iprice counter, dummy and last close
        avg_close = 0
        tot_close = 0       
        i_price = 0
        dummy = 0
        last_close = 0
        num_divs = num_divs + 1  #this is the number of divs for this 
        #this is the price that we are starting with (closing price on div pay day)
        close_pr = df.loc[df['C']==ind,'Close'].iloc[0]
        #for each of the div add the total starting prices to _total 
        avg_start_pr_tot = avg_start_pr_tot + close_pr
        #find the location to start at 
        i_ct = df.loc[df['C']==ind,'index_ct'].iloc[0]
        #add the total dividends 
        tot_div = tot_div + df1.at[ind,'Dividends']
        
        #for each of the dividends go thru the next 5 days and find to total
        #if no data then error out but no PRINTING errors.. 
        #only count what you do 
        for i in range(1,6):
            #tot_close = tot_close + df.loc[df['index_ct']==(i + i_ct),'Close'].iloc[0]
            #print(word, " ",tot_close)
            try:
                tot_close = tot_close + df.loc[df['index_ct']==(i + i_ct),'Close'].iloc[0]
                i_price = i_price + 1
            except Exception as e:
                #print(word, "- in range:",e)
                #this dummy is for no reason at all :D 
                dummy = dummy + 1
        if i_price > 0:
            #the total close should be around 5 different dates - so get average based on time you did 
            avg_close = tot_close / i_price
            # price dif is also at word level
            price_dif = price_dif + (close_pr - avg_close)
            avg_dif_tot = avg_dif_tot + price_dif
            avg_price_dif = price_dif / num_divs
            avg_close_pr_tot = avg_close_pr_tot + avg_close
            if avg_close >= close_pr:
                iPos = iPos + 1
            else:
                iNeg = iNeg + 1
    if num_divs > 0:
        avg_start_pr = avg_start_pr_tot / num_divs
        avg_close_pr = avg_close_pr_tot / num_divs
        avg_dif = avg_dif_tot / num_divs
    
    #print(word, " $",start_price, " fin price:",end_price, " avg start",avg_start_pr, " avg close",avg_close_pr, ' tot pos:',iPos," total neg:",iNeg, ' total div:',tot_div, ' avg p diff:',avg_dif)
    #
    print(word,',',start_price,',',end_price,',',avg_start_pr,',',avg_close_pr,',',iPos,',',iNeg,',',tot_div,',',avg_dif)    
    #time.sleep(5)
print('end')
