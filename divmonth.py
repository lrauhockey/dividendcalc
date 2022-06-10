import requests
import time
from bs4 import BeautifulSoup
from datetime import *
import sys

dummy = 0
month = datetime.now().month
year = datetime.now().year
word = ""
with open('tickers2.txt') as f:
   for line in f:
        try:
            
            word = line.strip()
            
            URL = 'https://dividendhistory.org/payout/' + word
            page = requests.get(URL)
            soup = BeautifulSoup(page.text, 'html.parser')
            
            div_table = soup.find("table",id='dividend_table')
            rows = div_table.findAll("tr")

            table_data = []
            for row in rows:
                cols = row.findAll("td")
                cols = [ele.text.strip() for ele in cols]
                table_data.append(cols)

            for i in range(1,5):
                #if (month == int(table_data[i][1][5:7])) and (year == int(table_data[i][1][0:4])):
                if (int(table_data[i][1][5:7])<6 ) and (year == int(table_data[i][1][0:4])):
                    if table_data[i][2].find('**') < 0:
                        line = word + "," + table_data[i][1] + "," + table_data[i][2] + "," + table_data[i][0]
                    else:
                        line = word + "," + table_data[i][1] + "," + table_data[i][2][:len(table_data[i][2])-2] + "," + table_data[i][0]
                    print(line)
                    #time.sleep(3)
                
                else:
                    dummy = dummy+1
        
        except AttributeError:
            #pass
            URL = URL ='https://www.dividendinformation.com/search_ticker/?identifier=' + word
            #print(URL)
            
       
            try:
                page = requests.get(URL)
                message = page.text
                soup = BeautifulSoup(message,'html.parser')
                secondtable = soup.findAll('table')[3]

                rows = secondtable.findAll("tr")

                table_data = []
                for row in rows:
                    cols = row.findAll("td")
                    cols = [ele.text.strip() for ele in cols]
                    table_data.append(cols)
                    #print(cols)
            
                for i in range(1,5):
                    #if (int(table_data[i][0][5:7])==month ) and (year == int(table_data[i][0][0:4])):
                    if (int(table_data[i][0][5:7])<6 ) and (year == int(table_data[i][0][0:4])):
                        line = word + "," + table_data[i][0] + "," + table_data[i][1] + "," + table_data[i][2]
                        print(line)
                    else:
                        dummy = dummy+1
            except AttributeError: 
                print(word," No Dividneds attribute error")
                dummy = dummy + 1
            except Exception as e:
                print(word, "No Divideds other error")
                print("Oops!", sys.exc_info()[0], "occurred.")
                dummy = dummy + 1
                pass
        except Exception as e:
                print(word, "No Divideds other error")
                print("Oops!", sys.exc_info()[0], "occurred.")
                dummy = dummy + 1
                pass
        
                
                    