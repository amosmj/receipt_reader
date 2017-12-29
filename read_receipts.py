"""
This Python Script was written by Mike Amos for Will Tierney, December 2017
Both have the rights to use the contents within. Mike has the right to 
resell this script as needed.

What this is:
This is a script written for Python 3 and should run on any OS computer with Python installed

Job Requirements:
Fields: Date, Name, Address, Last Service Date, Lifetme Total
results come from a PDF that will be provided.
Code developed using a 20 page sample, approx 1% of what product needs to run on

What it does:
The program uses PDFMiner to open the PDF and copy all of the text out
That part I pretty much lifted wholesale from sample code. 

Once I had the text in a string I went to work. I had hoped that it would maintain
some kind of structure. Even if it wasn't logical, if it was consistent, this would
be very straightorward for me. Alas this is not the case. Things appeared in seemingly random 
order within a customer's listing and sometimes parts of customer records mixed. I ended
up using a variety of landmarks to find the required fields

I began by stripping out header and footer info nd some labels that weren't helpful
The customer contact info always came together so I found it by looking for the Cust # label
    I used that landmark to place name and address in a dataframe
To find "Life Time Total" I knew that it was the second of four "currency" fields so I 
    looked for one of those and just counted. I had hoped they would be in some consistent
    proximity to the custoemr info but I didn't find that they were. I did find, however,
    that they always fell in the same order as the customer info so I just stacked them 
    up and mashed them into the dataframe
To look for max date, similar to the currency above, I looked for dates. Fortunately the
    date header always showed up between each batch of dates so from each one to the next
    I gathered the dates then when I found the next one, I picked the biggest date, wrote
    it to a list then reset my working list. When it was all done I just mashed the list
    into the dataframe


If I had to run this over and over I would immediately rewrite this to be more modular.
As you look at the code, there are pretty obvious breaks where each part should be in its
own function. There is also no reason that i need three passes. I built it that way because
I was just making my way through the logic. However, in hindsight, each line could be evaluated
for each of the three landmarks and the apropriate lists and counters manipulated as needed
However, this looks like a 1 time run job so I'll park it as is.

"""
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import HTMLConverter,TextConverter,XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import numpy as np
import pandas as pd
import re
import datetime as dt


#currency = re.compile('*.[0-9][0-9]')

def convert(fname, pages=None):
    ### Credit where credit is due
    ### this came largely from here: https://stackoverflow.com/questions/39854841/pdfminer-python-3-5
    # this is basically how you use PDFminer to read a PDF
    # I was unable to find a helpful doc on these settings so they are largely left as I found them
    if not pages: pagenums = set();
    else:         pagenums = set(pages);      
    manager = PDFResourceManager() 
    codec = 'utf-8'
    caching = True

    output = io.StringIO()
    converter = TextConverter(manager, output, codec=codec, laparams=LAParams())     

    interpreter = PDFPageInterpreter(manager, converter)   
    infile = open(fname, 'rb')

    for page in PDFPage.get_pages(infile, pagenums,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    convertedPDF = output.getvalue()  

    infile.close(); converter.close(); output.close()
    return convertedPDF

def is_row_useful(row):
    # just a quick function to test if a row is needed for evaluation in my work
    # if something is listed in garbage_text, I removed it. In hindsight, this 
    # ended up not being super useful but I left it because it works with it in
    useful = False
    garbage_text = ["NWG AUTO REPAIR", "71 Main Street", "Medway, MA.  02053", 
                "Phone - 508-533-2375    Fax - 508-533-3058", "Customer List - By Customer Number",
                "Report Date :", "12/12/2017", "Y.T.D. :", "Life Total :", "Credit Balance :",
                "Balance Due :", "Status :", "Current", "Remarks :",
                "(C) 2007,2008 Mitchell Repair Information Company, LLC CustNum.rpt 11.29.06"
                ]
                # deliberately did't add "Cust # :"
                # deliberatey didn't add "Vehicle Information" because I think I want to use that"
                # note: because I am removing the report date, if anyone has a matching service date, that is removed too
    if len(row.strip()) > 0: #throw away empty lines
        if row.strip() not in garbage_text: #just removing human readable lines that don't help the program
            if row.strip()[:5] != "Page ": #removing the page numbers, need to make sure that a person with the name "Page" can't break this
                useful = True
                #print("row found useful: ", row)
    return useful




#//////////// main ///////////////////////
in_file  = r'/Users/amosmj/Downloads/First 20 pages.pdf'   
out_file  = r'/Users/amosmj/Downloads/receipt_reader.txt'     

work_text = convert( in_file)#, pages=[0,1,9])
work_lines = work_text.split('\n') # break at each line
#print(work_lines)

# Creating a list of lines that will help me find the data that is needed
workable_lines = []
for line in work_lines: #doing a first pass just to throw away junk lines
    if is_row_useful(line):
        workable_lines.append(line)
# List at this point should only be lines that have the potential to be useful

# create a loop that looks for "Cust # :"
# this loop then grabs the customer number and assigns it the value of the line number
customers = pd.DataFrame(columns = ["Customer Name", "Customer Street Address", "Customer Address"])
# removed: "Customer ID", "Line Number", 
for i in range(len(workable_lines)):
    #print(str(i)," ", workable_lines[i])
    if workable_lines[i].strip() == "Cust # :" :
        #customer ID.   #line No. #customer name #customer address
        #print("found a customer ", workable_lines[i+1])
        working_line  = [{"Customer Name":workable_lines[i+2], 
                          "Customer Street Address":workable_lines[i+3], "Customer Address":workable_lines[i+4]
                          }]
                          # removed: Customer ID":workable_lines[i+1], "Line Number": i+1,  
        #print(working_line)
        customers = customers.append(working_line, ignore_index = True)


# I found that people who don't have addresses tend to pick up "Vehicle Inoformation"
# as their address so I'm blanking those out
customers.loc[customers["Customer Address"] == "Vehicle Information ", "Customer Address"] = ""
#print(customers)
# at this point customers has one item per customer ID with the followng list
# line Number, name, street address, city state and zip
# some clean up will need to be done to format these correctly but the info is gathered. 


# Life Total is tougher to grab because the remarks field can cause it be interpetted to 
# be in a different place. I will need to make a second pass to figure out where it is
# had to ask for help on this regex
# https://stackoverflow.com/questions/47998420/trying-to-use-python-to-tell-numbers-apart
currency_matcher = re.compile('((?:\\d*,)*\\d+\\.\\d{2})')
currency_counter = 0
currency_list = []
for line in workable_lines:
    if currency_matcher.search(line) != None:
        currency_counter += 1
        if currency_counter == 2:
            currency_list.append(line)
        if currency_counter >=4:
            currency_counter = 0
#print(currency_list)
currency_df = pd.DataFrame({"Life Total" : currency_list})
#print(currency_df)
customers = pd.concat([customers, currency_df], axis = 1)


# I will take a third pass to look at service dates and determine what the last date of 
# service was. I plan to be kind of lazy and just see what formats to date with strfdate
# then take the max of that
# based on lessons learned from the currency thing above and reviewing the files I'm going
# to look for "Last Service Date" then capture every date like object until I find another one
# I need to be prepared for NULL as an option
# once I get to the next "Last Service Date" I will need to to look back at the dates I found
# and pick the biggest one and apply it to the row

# loop through all lines
date_out_list = []
date_work_list = []
one_time_bool = False
for line in workable_lines:
    # look for "Last Service Date"
    if line.strip() == "Last Service":
        if one_time_bool == True:
            try:
                date_out_list.append(max(date_work_list))
            except: # there are records with no dates in them
                date_out_list.append("no date")
            date_work_list = []
            #print("resetting date search")
        else:
            one_time_bool = True
            #print("ok, looking for dates now")
    
    # going to try and parse the line as an American format date
    try:
        date_work_list.append(dt.datetime.strptime(line.strip(), "%m/%d/%Y"))
        #print("found a date: ",line)
    except:
        foo = "nope"
try:
    date_out_list.append(max(date_work_list))
except: # there are records with no dates in them
    date_out_list.append("no date")
service_date_df = pd.DataFrame({"Last Service Date" : date_out_list})
#print(service_date_df)
customers = pd.concat([customers, service_date_df], axis = 1)


# this chunk just spits out the lines I was working with into a text file
# I did this to make logic errors easier to debug
out_text = workable_lines
to_write = ""
for line in out_text:
    to_write += line + "\n"
fileConverted = open(out_file, "w")
fileConverted.write(to_write)
fileConverted.close()
#print(convertedPDF) 


#for cust in customers:
#    print(cust, customers[cust])
print(customers)

# this actually writes the CSV file
customers.to_csv(r'/Users/amosmj/Downloads/receipt_reader.csv' , date_format='%m/%d/%Y')
# just cleaning up the dataframe because I found when I ran this multiple times
# the dataframe didn't seem to always self clean for a rerun
customers = None


##############retired logic ###############
# this was my first pass at capturing the "Life Total"
# I discoverd that it was not uncommon for life total to precede
# customer identification so my idea of looking in a range of rows
# would not work. I found, however, that when it showed up it always
# shows up in groups of four and I could match 1 for 1 and just mash them together

"""
life_total_dict = {"Customer ID": ["Life Total"]}
for index, row in customers.iterrows():
    start_row = row["Line Number"]
    end_row = row["End Line Number"]
    print(row)
    #print("start_row:",start_row)
    #print("end_row:",end_row)

    currency_counter = 0
    for line in workable_lines[start_row : end_row]:
        print(line)
    #for line in workable_lines[start_row, end_row]:
        #if re.search(currency_matcher,line) != None:
        if currency_matcher.search(line) != None:
        #if line.strip()[-3:-2] == ".":
            print(row["Customer ID"],":",line)
            if currency_counter == 1:
                life_total_dict[row["Customer ID"]] = line.strip()
            currency_counter += 1
#print(life_total_dict)
#customers["Life Total"] = pd.DataFrame.from_items(currency_to_add)
#currency["Life Total"] = pd.DataFrame(np.array(currency_list), columns=("Life Total"))

#customers["Life Total"] = customers["Customer ID"].map(life_total_dict)
#print(life_total_df)
#print(life_total_df.dtypes)
#customers = pd.merge(customers, life_total_df, on = "Customer ID", how = "left")
#customers["Life Total"] = customers["Customer ID"].map(life_total_dict)
"""

"""
# this whole mess is about copying the start line from a row to the preceding row
# the idea is to give myself some number or rows to look between for the things
# Added after retirement: So, I had this cunning plan that I would find the first
# row in the data for a customer then use that to enclose all the other searches
# it worked extremely well on the first page and roughly every second page
# however, the PDF interpreter moved stuff around on occasion so that this 
# not only didn't work but led  erroineous data
# retired this in favor of more brute force methods
customers["End Line Number"] = customers["Line Number"].shift(-1)
df_len = len(customers)-1
#print(df_len)
lines_len = len(workable_lines)
customers.at[df_len, "End Line Number"] = lines_len
#print(customers)
"""

