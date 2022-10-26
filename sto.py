
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import sys
from datetime import datetime, timedelta

#These 3 lines need to be in sync its the build the DF (pandas) as well as print out to match
days =(365,240,120,60,60,30,0)
df = pd.DataFrame(columns=['Ticker','0','30','60','90','120'])
print('Ticker,1 year, 240 Days,120 days, 90 days, 60 Days, 30 Days, 0 Days')


#this is for debugging - use input file or other code later on..
words = ('MSFT','MS','O','QYLD')

#make life easy so the system knows Line is a string. 
line = ""
for word in words:
    y_data = yf.Ticker(word)
    y_info = y_data.info
    line = word
    for day in days:
        #figure start and end dates- using 20 days back as that should be around 14 working days (two weeknds)
        daystart = datetime.now() - timedelta(days=day)
        dayend = datetime.now() - timedelta(days=(day+20))
        isPast = dayend.date()
        isNow = daystart.date()
        #put the history into a pandas data frame.
        df1 = y_data.history(start=isPast, end=isNow, actions=False)
        #add ain index this way we know the max line to find 
        df1['index_ct'] = range(1, len(df1)+1)

        #find the values -max of index, The low of the period, the high of the period and the closing price of the earliest data
        imax = df1['index_ct'].max()
        L14 = df1['Low'].min()
        H14 = df1['High'].max()
        c_price = df1.loc[df1.index_ct == imax,'Close'].values[0]
        #this is the stoic calc from investopedia
        k = ((c_price - L14)/(H14 - L14))*100
        #for now not putting it into a pandas dataframe ist adding it to the line 
        line = line  + ',' + str(k)
        #debugging this if for me to figure out if something fgoes wrong 
        #print(df1)
        #print(L14)
        #print(H14)
        #print(imax)
        #print(df1[df1['index_ct']==imax])
        #df.loc[df.Unit_Price >= 1000,'Product_Name'].tolist()
        #print('closing price of newest date',df1.loc[df1.index_ct == imax,'Close'].values[0])
    #after each ticker print the line.
    print(line)
