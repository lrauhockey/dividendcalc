import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from time import sleep
import yfinance as yf
from yahoofinancials import YahooFinancials
import numpy as np
from finvizfinance.quote import finvizfinance
from yahoofinancials import YahooFinancials
import yahoo_fin.stock_info as si
import warnings
from datetime import datetime, timedelta
import pandas as pd
warnings.filterwarnings("ignore")
# what to read to do this..
# https://medium.com/@jb.ranchana/write-and-append-dataframes-to-google-sheets-in-python-f62479460cf0
# https://practicaldatascience.co.uk/data-science/how-to-read-google-sheets-data-in-pandas-with-gspread
# https://docs.gspread.org/en/latest/user-guide.html

def getGoogleCreds(workbook):
    #setting up variables..
    scopes = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
    # this is the Dividend workbook 
    #get credentials / log in 
    credentials = Credentials.from_service_account_file('/Users/laurencegold/dividend/divcred.json', scopes=scopes)
    gc = gspread.authorize(credentials)
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    # open a google sheet
    gs = gc.open_by_key(workbook)
    return gs 

def getCurrentGoogleSheetData(data_sheet):
    df1 = pd.DataFrame(data_sheet.get_all_records())
    # drop the Index column as this creates its own index.. 
    df1 = df1.drop(columns=['Index'])
    print(df1.head())
    return df1

def updateLastUpdate(info_sheet):
    print('updated infosheet')
    now = datetime.now()
    info_sheet.update('B1', now.strftime("%b %d, %Y %I:%M %p"))

def updateIndexB1(data_sheet):
    print('updating datasheet')
    data_sheet.update('A1', 'Index')

def turnDFinfoStockList(df1):
    words = df1.Ticker.values.tolist()
    print(words)
    return words


def getWords(iFile):
    print('Getting Tickers', end='\r')
    words = []
    success = True
    try:
        with open(iFile) as k:
            for line in k:
                words.append(line.strip())
    except Exception as e:
        print('Issue with getting file')
        quit()
    return words

def getFinViz(word,df,f_fields,f_dict,debug):
    print('fin viz for',word, end='\r')
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
    finally:
        return df

def getYahoofin(word, df, y_fields, y_dict, i, debug):
    print('yahoo fin for ',word, end='\r')
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
    finally:
            return df

def getSi(word, df, yf_fields, yf_dict, i, debug):
    print('si call for ',word, end='\r')
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
    finally:
        return df

def getDivVPrice(word, df_a, df_index):
    print('Compare dividends to price changes call for ',word, end='\r')
    try:
        #Things need to calculate 
        #Average price starting - Average Price 5 days after - Average Difference between the 2
        #Count of items  that are pos Negative
        #Starting price and Ending Price for the whole thing
        start_price = 0
        end_price = 0
        close_pr = 0  #2nd closing price?
        #ic = 0
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
        #avg_lg = 0
        #this is a counter 
        i_ct = 0
        price_dif = 0

        #two counters of dividends (one value one number)
        tot_div = 0
        num_divs = 0
        
        #Yfin get stuff
        aapl = yf.Ticker(word)
        df2 = aapl.history(start="2017-01-01", end="2022-10-22", actions=False)
        df1 = aapl.actions
        if len(df2) > 2 or len(df1) > 2:
            #add a column with count 
            df2['index_ct'] = range(1, len(df2)+ 1)
            df1['index_ct'] = range(1, len(df1)+ 1)

            #get start and end prices
            start_price = df2.loc[df2['index_ct']==1,'Close'].iloc[0]
            end_price = aapl.info['regularMarketPrice']

            #create a new column and put date/time as the new colunmn
            df2 = df2.assign(C="")
            for ind in df2.index:
                df2.loc[ind]['C'] = ind
                df2.at[ind, 'C']= ind
            
            #for each of the actions (dividends) need to find the starting price
            #the next 5 prices (average)
            #the difference between them 
            for ind in df1.index:
                #zero out the avg close, the total close, the price dif, the iprice counter, dummy and last close
                avg_close = 0
                tot_close = 0       
                i_price = 0
                dummy = 0
                #last_close = 0
                num_divs = num_divs + 1  #this is the number of divs for this 
                #this is the price that we are starting with (closing price on div pay day)
                close_pr = df2.loc[df2['C']==ind,'Close'].iloc[0]
                #for each of the div add the total starting prices to _total 
                avg_start_pr_tot = avg_start_pr_tot + close_pr
                #find the location to start at 
                i_ct = df2.loc[df2['C']==ind,'index_ct'].iloc[0]
                #add the total dividends 
                tot_div = tot_div + df1.at[ind,'Dividends']
                
                #for each of the dividends go thru the next 5 days and find to total
                #if no data then error out but no PRINTING errors.. 
                #only count what you do 
                for i in range(1,6):
                    #tot_close = tot_close + df.loc[df['index_ct']==(i + i_ct),'Close'].iloc[0]
                    #print(word, " ",tot_close)
                    try:
                        tot_close = tot_close + df2.loc[df2['index_ct']==(i + i_ct),'Close'].iloc[0]
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
                    #avg_price_dif = price_dif / num_divs
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
            print(word,',',start_price,',',end_price,',',avg_start_pr,',',avg_close_pr,',',iPos,',',iNeg,',',tot_div,',',avg_dif, end='\r')
            df_a.loc[df_index,['StartPrice','EndPrice','AvgStartPrice','AvgClosePrice','Positives','Negatives','TotalDiv','AvgDifference']] = [start_price,end_price,avg_start_pr,avg_close_pr,iPos,iNeg,tot_div,avg_dif]      

        else:
            # there are no dividends to calc.. sno need to update the data frame... 
            print(word, ' has no dividends', end='\r')
    except Exception as e:
        print(word, ' exception ',e)
        #quit()
    finally:
        return df_a

def main():
    #SAMPLE_RANGE_NAME = 'StockData!A1:B'
    #SHEET_DATA = 'StockData'
    SHEET_DATA = 'StockTest'
    SHEET_INFO = 'Information'
    WORKBOOK_ID = '1KQ_SKEFS1LJ6RBzgdJqimqiG3DD75tl5WHJV293bMMQ'

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
    #words = []
    #working = True
    i = 0
    #dummy = 0
    #fileOrInput = 1
    #inputfile = "ticknov.txt"
    #inputfile = "ticknov.txt"

    # login to google - and assing gs to the Workbook.
    gs = getGoogleCreds(WORKBOOK_ID)

    # select a work sheet from its name
    INFO_WORKSHEET = gs.worksheet(SHEET_INFO)
    DATA_WORKSHEET = gs.worksheet(SHEET_DATA)

    # get the current data frame
    #create the dataframe with columsn 
    # This is the old Dataframe creation where i got data from files.. 
    df_new = pd.DataFrame(columns=['Ticker','Name','Price','PE','Beta','Dividend','Dividend Yield','Payout','ROE','Debt2Eq','E-Growth','FCF','ROI','PEG','P/FCF','ROA','Stochastic','StartPrice','EndPrice','AvgStartPrice','AvgClosePrice','Positives','Negatives','TotalDiv','AvgDifference'])

    df_old = getCurrentGoogleSheetData(DATA_WORKSHEET)
    words = turnDFinfoStockList(df_old)
    for word in words:
        #create a data frame
        df2 = pd.DataFrame([[word]], columns=['Ticker'])
        # a chaeaters way of joining the two which appends ticker to the main dataframe... 
        df_new = pd.concat([df_new,df2],ignore_index=True)
        df_new = getFinViz(word, df_new, f_fields,f_dict,debug)
        df_new = getYahoofin(word,df_new,y_fields, y_dict, i, debug)
        df_new = getSi(word, df_new, yf_fields, yf_dict, i, debug)
        df_new = getDivVPrice(word, df_new, i)
        # counter used to make it easier to find Pandas location (index)
        i = i + 1
        print('analysis ',i,' symbol:',word,end='\r')
        sleep(5)
    #df.to_csv('Q4_Analysis.csv')
    print(df_new.head())

    #Now write the Dataframe Back to the Spreadsheet
    print('writing to dataframe')
    DATA_WORKSHEET.clear()
    set_with_dataframe(worksheet=DATA_WORKSHEET, dataframe=df_new, include_index=True,include_column_header=True, resize=False)

    # Update the Information Sheet with the Last Update Date/Time
    updateLastUpdate(INFO_WORKSHEET)
    updateIndexB1(DATA_WORKSHEET)
    print('end')


 # Using the special variable 
# __name__
if __name__=="__main__":
    main()
