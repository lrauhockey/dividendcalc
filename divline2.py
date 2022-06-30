from cmath import e
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


def getURLs(word):
    URLinfo = 'https://www.dividendinformation.com/search_ticker/?identifier=' + word
    if word.find(":") > 0 :
        #need to setup URLS if in Canada
        #Cananda URL for cnbc needs -ca and Divhistory needs TSX in it
        #the canada true/false was for debugging can remove
        URLcnbc = "https://www.cnbc.com/quotes/" + word[4:] + "-ca"
        URLdiv = 'https://dividendhistory.org/payout/TSX/' + word[4:]
        canada = True
        statusTxt = "In Canada - "
    elif word.find(".UN") > 0 :
        #This is also in canada 
        #print(word, "found .UN")
        URLcnbc = "https://www.cnbc.com/quotes/" + word + "-CA"
        URLdiv = 'https://dividendhistory.org/payout/TSX/' + word
        canada = True
        statusTxt = "In Canada - "
    elif word.find(".U") >0 :
        #need to find UN first .U is different
        #need to strip off the .U vs keeping the .UN (bizarre case)
        locforlen = word.find(".U")
        URLcnbc = "https://www.cnbc.com/quotes/" + word + "-CA"
        URLdiv = 'https://dividendhistory.org/payout/TSX/' + word[0:locforlen]
        canada = True
        statusTxt = "In Canada - "
    else:
        #these are US
        URLcnbc = "https://www.cnbc.com/quotes/" + word
        URLdiv = 'https://dividendhistory.org/payout/' + word
        canada = False
        statusTxt = "In US - "
    return URLcnbc, URLdiv, URLinfo, canada, statusTxt;

def getDivFromFinviz(word):
    finvizFound = False
    try:
        dividend = 0
        urlFinviz = "https://finviz.com/quote.ashx?t=" + word
        req = Request(urlFinviz, headers={'User-Agent': 'Mozilla/5.0'})
        gcontext = ssl.SSLContext()
        webpage = urlopen(req, context=gcontext).read()
        html = BeautifulSoup(webpage, 'html.parser')
        dfs = pd.read_html(str(html), attrs = {'class': 'snapshot-table2'})[0]
        dividend = dfs.iloc[6,1]
        finvizFound = True
        statusUpdate = "Finviz Successful -"
    except Exception as e: 
        statusUpdate = "Finbviz Not Found"
        finvizFound = False
        pass
    finally:
        return(dividend, statusUpdate, finvizFound)

def getDivNameFromCNBC(word):
    statusTxt = ""
    cnbcFound = False
    try:
        page = requests.get(URLcnbc)
        message = page.text
        if  message.find("We're sorry") >0 : 
            cnbcFound = False
            return(0, "", "Not in CNBC - ", cnbcFound)
        else:
            po1 = message.find("KEY STATS")
            len1 = len(message)
            position = message.find("Dividend", po1)
            n = 60
            dividendtest = message[position:position+n]
            positdiv = dividendtest.find('value">')
            startloc = positdiv + 7
            dividenttext= dividendtest[positdiv+7:positdiv+20]
            dividendend =  dividenttext.find('<')
            pos = message.find('s="QuoteStrip-name">')
            nametext = message[pos+20:pos+100]
            endpos = nametext.find('</s')
            coname = nametext[0:endpos]
            coname = coname.replace("&amp;", "&")
            coname = coname.replace(","," ")
            #Once you get the company Name (coname) and divident add to a line
            #i could put in pandas dataframe but getting lazy
            dividend =  dividenttext[0:dividendend]
            statusTxt = "In CNBC - "
            cnbcFound = True 
    except AttributeError:
        #there are some errors that i ignore - this is one
        #print("Oops!", sys.exc_info()[0], "occurred.")
        statusTxt = "Attribute Error"
    except NameError as n:
        statusTxt = "Name Error " + n 
    except Exception as e:
        statusTxt = "Other exception " + e
    finally: 
        #need a finally to end the first try 
        statusTxt = statusTxt + " - end of CNBC - "
    return dividend, coname, statusTxt, cnbcFound;

def getDivHistoryInfo(URLdiv):
    page = requests.get(URLdiv)
    message = page.text
    freq = 0
    frequency = ""
    if message.find("Stock does not exist") > 0 :
        #print("follwing this does not exist loop")
        divhistFound = False
        return "Div Hist Not found", "", "", 0, 0, False
    else:
        #find the frequency of the divident
        pos = message.find("Frequency:")
        endpos = message.find('</p>',pos)
        #print(message[pos+11:endpos])
        frequency = message[pos+11:endpos]
        if frequency == "Monthly":
            freq = 1
        elif frequency == "Quarterly":
            freq = 4
        elif frequency == "Yearly":
            freq = 12
        else:
            freq = 0 
        html = BeautifulSoup(message, 'html.parser')
        #find the last 4 dividends
        line = ""
        dfs = pd.read_html(str(html), attrs = {'class': 'table table-striped table-bordered'})[0]
        dfs.columns = [c.replace('% ', 'C') for c in dfs.columns]
        df = dfs.drop(dfs[dfs.CChange == 'unconfirmed/estimated'].index)
        if len(df) < 4:
            df_len = len(df)
        else:
            df_len = 4
        df_top = df.head(df_len)
        #print(dfs)
        #print(df)
        for index, row in df_top.iterrows():
            #print(row['Ex-Dividend Date'], row['Cash Amount'])
            line = line + row["Ex-Dividend Date"] + "," + row["Cash Amount"] + ","
        statusTxt = "Found DivHist -"
    return statusTxt, line, frequency, freq, df_len, True;

def getDivInfo(URLinfo):
    page = requests.get(URLinfo)
    message = page.text
    infoFound = False
    freq = 0
    frequency = ""
    line = ""
    statusTxt = ""
    soup = BeautifulSoup(message,'html.parser')
    if message.find("Ticker not found") > 0:
        infoFound = False
        statusTxt = "Not in DivInfo" 
        return statusTxt, line, frequency, freq, 0, infoFound;
    else:
        infoFound = True
        statusTxt = "In DivInfo"
        html = BeautifulSoup(message, 'html.parser')
        df = pd.read_html(str(html), attrs = {'class': 'stats'})[3]
        #print(df)
        if len(df) < 4:
            df_len = len(df)
        else:
            df_len = 4
        df_top = df.head(df_len)
        for index, row in df_top.iterrows():
            #print(row['Date'], row['Amount Per Share'])
            line = line + row["Date"] + "," + row["Amount Per Share"] + ","
        statusTxt = "Found DivHist -"
        return statusTxt, line, frequency, freq, 0, infoFound

dummy = 0
stockfile = "current.txt"
words = []
with open(stockfile) as f:
   for line in f:
        words.append(line.strip())
for word in words:
    line = word
    try:
        URLcnbc, URLdiv, URLinfo, canada, statusTxt = getURLs(word)
        divcnbc, namecnbc, statusTxtcnbc, cnbcFound = getDivNameFromCNBC(word)
        if cnbcFound == False:
            divFinViz, statusTextFinViz, finvizFound = getDivFromFinviz(word)
            if finvizFound:
                line = line + ", ," + divFinViz + ","
            else:
                line = line + ", , ,"
        else:
            line = line + "," + namecnbc + "," + divcnbc + ","
        #print(dividend, name, statusTxt, cnbcFound)
        statusTxthist, linehist, frequencyhist, freqhist, df_lenhist, divhistFound = getDivHistoryInfo(URLdiv)
        if divhistFound:
            line = line + linehist + str(freqhist) 
        else:
            statusTxtinfo, lineinfo, frequencyinfo, freqinfo, df_leninfo, divhistFoundinfo = getDivInfo(URLinfo)
            if divhistFoundinfo:
                line = line + lineinfo  +  str(freqinfo) 
        #print(statusTxt, line, frequency, freq, df_len, divhistFound)
        #print(line)
        #sleep(5)
    except Exception as e:
        if e =- "No tables found"
            dummy = dummy + 1
        else:
            print(word, e)
    finally:
        print(line)
        sleep(5)
print("Done")