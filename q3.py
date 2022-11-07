
from asyncore import file_dispatcher
import yfinance as yf
import pandas as pd
from yahoofinancials import YahooFinancials
import numpy as np
import requests
from finvizfinance.quote import finvizfinance
from yahoofinancials import YahooFinancials
import yahoo_fin.stock_info as si
import warnings
import sys
from datetime import datetime, timedelta
from time import sleep

#one of the libraries has warning due to the use of append (notice i use concat) in pandas
warnings.filterwarnings("ignore")

#create the dataframe with columsn 
df = pd.DataFrame(columns=['Ticker','Name','Price','PE','Beta','Dividend','Dividend Yield','Payout','ROE','Debt2Eq','E-Growth','FCF','ROI','PEG','P/FCF','ROA','Stochastic'])

#in each of the libraries list the list of fields to cycle thru 
yf_fields = ['Quote Price','PE Ratio (TTM)','Beta (5Y Monthly)']
y_fields = ['shortName','lastDividendValue','dividendYield','payoutRatio','returnOnEquity','debtToEquity','earningsGrowth','freeCashflow','returnOnAssets','returnOnEquity']
f_fields = ['Company','Price','P/E','Dividend','Dividend %','Payout','ROE','Debt/Eq','ROI','PEG','P/FCF']

#now for each of the libraries need to map their column name to the name in the master dataframe - 
f_dict = {'Company': 'Name','Price':'Price','P/E':'PE','Dividend':'Dividend','Dividend %':'Dividend Yield','Payout':'Payout','ROE':'ROE','Debt/Eq':'Debt2Eq','PEG':'PEG','P/FCF':'P/FCF','ROI':'ROI'}
y_dict = {'shortName':'Name','lastDividendValue':'Dividend','dividendYield':'Dividend Yield','payoutRatio':'Payout','returnOnEquity':'ROE','debtToEquity':'Debt2Eq','earningsGrowth':'E-Growth','freeCashflow':'FCF','returnOnAssets':'ROA'}
yf_dict = {'Quote Price':'Price','PE Ratio (TTM)':'PE','Beta (5Y Monthly)':'Beta'}
print("settings ticked off")
#set shome defaults
debug = False
words = []

i = 0
dummy = 0
# fileOrInput = 0
# inputfile = "current.txt"

# #checkif the first input is a file or 0 if it is a zero then read the rest else assume its filename
# fileOrInput = str(sys.argv[1])
# print(fileOrInput)
# if fileOrInput == '0':
#     input_string = input("Enter Ticker symbols: ")
#     words = input_string.split()
# else:
#     with open(fileOrInput) as k:
#         for line in k:
#             words.append(line.strip())
# with open("list1.txt") as k:
#     for line in k:
#         words.append(line.strip())
words = ['PEY','PGX','DIV']
# print("file loaded")
# you can use the below as a debug just comment out and it wont deal with command line/file input
# words = ('MSFT','MS','AAPL','EOS')
for word in words:
    sleep(2)
    #create a data frame
    df2 = pd.DataFrame([[word]], columns=['Ticker'])
    df = pd.concat([df,df2],ignore_index=True)
    try:
        #using the finviz site first get the fundamentals
        stock = finvizfinance(word)
        fund = stock.ticker_fundament()
        #loop thru the fields and check add them to the data frame (yeah its wordy but clean)
        for f_field in f_fields:
            if debug:
                print(f_field, " - ", f_dict[f_field], '--' ,str(fund[f_field]))
            df.loc[df['Ticker'] == word, f_dict[f_field]] = fund[f_field]
    except Exception as e:
        print(word, " finviz complete error ", f_field, " - ", e)
    try:
        #now use Yfinance to fill in missing if possible
        #get yfinance data
        y_data = yf.Ticker(word)
        y_info = y_data.info
        #loop thru yfinance fields - and in this case check if null before overwriting
        for y_field in y_fields:
            if debug:
                print(y_field, " - ", str(y_info[y_field]))
            if pd.isnull(df.at[i,y_dict[y_field]]):
                df.loc[df['Ticker'] == word, y_dict[y_field]] = y_info[y_field]
        #for Stochastic Oscialltor calculatoin 
        #get Date - go back 30 days as need 14 days of data
        days30 = datetime.now() - timedelta(days=30)
        isPast = days30.date()
        isNow = datetime.now().date()
        #use Yfinance to get history
        df1 = y_data.history(start=isPast, end=isNow, actions=False)
        # #add a manual index from 1 to len of data frame
        df1['index_ct'] = range(1, len(df1)+1)
        #now need to subtract leaving 14 left 
        toSub = df1['index_ct'].max() - 13
        df3 = df1[df1['index_ct'] >= toSub]
        #df2 now has the data needed to calc 
        #find the max of the Highs, and min of the lows along with current price for the calcuation
        L14 = df3['Low'].min()
        H14 = df3['High'].max()
        c_price = y_info['regularMarketPrice']
        #now the Stochastic Calc
        k = ((c_price - L14)/(H14 - L14))*100
        df.loc[df['Ticker']== word, 'Stochastic'] = k
    except Exception as e:
        print(word,'yfiance has error calling',e )
    try:
        #lastly there is another finance yahoo library - as i think P/E was missing from the above
        #not going to over comment it does the same as above
        quote = si.get_quote_table(word)
        for yf_field in yf_fields:
            if debug:
                print(yf_field, str(quote[yf_field]))
            if pd.isnull(df.at[i,yf_dict[yf_field]]):
                df.loc[df['Ticker'] == word, yf_dict[yf_field]] = quote[yf_field]
    except Exception as e:
        print(word, ' - Yz finance issue:',e)
        print(yf_field, ' - ')
    i = i + 1
print(df)
df.to_csv('q3dividends.csv',index=False)
