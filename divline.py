from cmath import e
import requests
from time import sleep
from bs4 import BeautifulSoup
from datetime import *
import sys


dummy = 0
month = datetime.now().month
year = datetime.now().year
#input_string = input("Enter Tickers separated by space: ")
#words = input_string.split()
#the text file here put your stock tickers one on each line
#The test file has 4 stocks - to test each path
input_string = input("Enter Ticker symbols: ")
words = input_string.split()
for word in words:
    #for line in f:
    try:
        #word = line.strip()
        
        if word.find(":") > 0 :
            #need to setup URLS if in Canada
            #Cananda URL for cnbc needs -ca and Divhistory needs TSX in it
            #the canada true/false was for debugging can remove
            URLcnbc = "https://www.cnbc.com/quotes/" + word[4:] + "-ca"
            URLdiv = 'https://dividendhistory.org/payout/TSX/' + word[4:]
            canada = True
        elif word.find(".UN") > 0 :
            #This is also in canada 
            #print(word, "found .UN")
            URLcnbc = "https://www.cnbc.com/quotes/" + word + "-CA"
            URLdiv = 'https://dividendhistory.org/payout/TSX/' + word
            canada = True
        elif word.find(".U") >0 :
            #need to find UN first .U is different
            #need to strip off the .U vs keeping the .UN (bizarre case)
            locforlen = word.find(".U")
            URLcnbc = "https://www.cnbc.com/quotes/" + word + "-CA"
            URLdiv = 'https://dividendhistory.org/payout/TSX/' + word[0:locforlen]
            canada = True
        else:
            #these are US
            URLcnbc = "https://www.cnbc.com/quotes/" + word
            URLdiv = 'https://dividendhistory.org/payout/' + word
            canada = False
        #Goto CNBC and get the Dividend and Name of stock 
        # Uncomment below if need to debug       
        #print(URLcnbc)
        #print(URLdiv)   
        page = requests.get(URLcnbc)
        message = page.text
        if  message.find("We're sorry") >0 : 
            #its possible its not there - so create a line letting people know
            line = word + ",  we're sorry not in cnbc" + URLcnbc
        else:
            #This assume its there! 
            #although this looks crazy - this is how I find what i am looking for an parse name/divident
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
            line = word + "," + coname + "," + dividenttext[0:dividendend]
        #dont want to crush a server so kinda delay - you can set this how you like   
        #time.sleep(10)

    except AttributeError:
        #there are some errors that i ignore - this is one
        #print("Oops!", sys.exc_info()[0], "occurred.")
        pass
    except:
        #all other exerrors i write this out - the pos for me to debug the html
        print(word, pos, " exception not in cnn, ", URLcnbc)
        print("Oops!", sys.exc_info()[0], "occurred.")
    try:
        #Now get div history - 
        #div history URL is used based on US/Canada 
        page = requests.get(URLdiv)
        message = page.text
        pos = message.find("Stock does not exist")
        if pos > 0:
            #Put the URL in the debug line - this is how i figure out what is going on 
            #also you can go into that line and request stock to be added! 
            line = line + " Not in dividend history " + URL
        else:   
            #I use beautiful soup for this HTML parsing (vs brute force for cnbc)
            #what i do is find the divident table - and in htat table take the 2-5th rows
            #its possible to have more/less and 2nd pages - you can edit to handle what you want

            soup = BeautifulSoup(page.text, 'html.parser')
            div_table = soup.find("table",id='dividend_table')
            rows = div_table.findAll("tr")

            table_data = []
            for row in rows:
                cols = row.findAll("td")
                cols = [ele.text.strip() for ele in cols]
                table_data.append(cols)

            for i in range(1,5):
                #I want to get rid of the ** i dont care if they go forward are not - 
                #you can modify this code and use a while look to only find data that is current 
                #pull the right table info (date/dividend)
                #now there are 2 dates - you can adjust to your liking
                if table_data[i][2].find('**') < 0:
                    line = line + "," + table_data[i][0] + "," + table_data[i][2]
                else:
                    line = line + "," + table_data[i][0] + "," + table_data[i][2][:len(table_data[i][2])-2]
        #now that i have the info print the line
        print(line)
        sleep(10)

    except IndexError:
        #there are times there are <4 dividends in histroy - this catches and prints what is there 
        print(line)
        

    except:
        #this is for all other errors - i have not found many but possible URLS may change etc.
        #print(word, pos, 'Some other problem')
        print(word,", Not found or other error: ", sys.exc_info()[0], " occurred. URLcnbc:",URLcnbc)