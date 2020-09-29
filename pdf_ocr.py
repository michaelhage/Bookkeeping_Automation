# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 21:56:08 2020

@author: Michael Hage
"""

import os

import ocrmypdf
import requests
import pdfplumber

import pandas as pd
import numpy as np

date_correct_dict = {
            "O":"0",
            "I":"1",
            "L":"1",
            "Z":"2",
            "S":"5"
            }

date_arr = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec"
    ]
# searches string input for text outputs and returns specific string section
# in between both boundaries
# end condition '!' checks for whitespace as a condition
def string_search(split_string, start_condition, end_condition, start_offset, end_offset):
    
    # print(split_string)
    
    # declare to use outside of loop
    i = 0
    j = 0
    
    # iterate through string segments to find the starting condition
    for i in range(0,len(split_string)):
        
        # check for whitespace check character
        if(start_condition != '!'):
            
            # checks for substring within string segment
            # uses lower to make  all characters lowercase, rstrip to remove 
            # trailing whitespace, and endswith as the substring checker
            if(split_string[i].lower().rstrip().endswith(start_condition.lower())):
                break;
        
        elif(start_condition == '!'):
            if (split_string[i].isspace()):
                break;
    
    # iterate through string segments to find the ending condition
    for j in range(i + start_offset,len(split_string)):
        
        # check for whitespace check character
        if(end_condition != '!'):
            
            # checks for substring within string segment
            # uses lower to make  all characters lowercase, rstrip to remove 
            # trailing whitespace, and endswith as the substring checker
            if(split_string[j].lower().rstrip().endswith(end_condition.lower())):
                break;
        
        elif(end_condition == '!'):
            # checks if statement has whitespace
            if (split_string[j].isspace()):
                break;
    
    # return part of string list that contains the information
    return(split_string[i+start_offset:j-end_offset])
   
# will remove selected characters (replace) to clean up some errors in the ocr
def clean_string(string, replace):
    
    # itertate through string line by line
    for i in range(0,len(string)):
        
        # iterates through replace characters to replace them with blank characters
        for r in replace:
            string[i] = string[i].replace(r,'')


def date_fix(string):
    
    temp = ""
    
    for s in string:
        
        if s in date_correct_dict:
            temp += date_correct_dict[s]
        else:
            temp += s
    
    return temp  

invoice_pdf = 'test.pdf'
ocr_pdf = 'output.pdf'

# run ocr system command to convert scanned pdf to text
# os.system(f'ocrmypdf {invoice_pdf} {ocr_pdf}')

# convert ocr pdf to string 
with pdfplumber.open(ocr_pdf) as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    # print(text)

# seperate string by new lines
text_lines = text.splitlines()

# condiitons for string search
start_condition = 'BALANCE'
end_condition = '!'
start_offset = 1
end_offset = 0

# call string search
amounts = string_search(text_lines, start_condition, end_condition, start_offset, end_offset)

# replace characters
replace = ['~','OD','0D', ',']

clean_string(amounts, replace)

column_names = ["Description", "Debits", "Credits", "Date", "Balance"]

# dates = ['feb', 'mar']
dates = []

account_df = pd.DataFrame(columns = column_names)

for s in amounts:
    
    # set and reset dataframe descriptors
    descriptor = ""
    date = ""
    debit = 0.0
    credit = 0.0
    balance = 0.0
    
    # split string into individual substrings by whitespace
    split = s.split()
    
    # NOTE: This should be changed to a better solution.
    # This is depended on the month not showing up in the beginning of the first 
    # couple of substrings
    
    # checks if dates has been initialized
    if len(dates) == 0:
        
        for c in split:
            # iterates through the 12 possible month beginnings
            for i in range(0,len(date_arr)):
                
                # if there is a match, then it puts it into 
                if(c.lower().startswith(date_arr[i])):
                    dates = [
                            date_arr[i], 
                            date_arr[(i+1)%len(date_arr)] 
                            ]
                
    
    for c in split:
        
        # clear substring from left whitespace
        c = c.lstrip()
        
        # if first character is a number
        if c[0].isnumeric():
            
            # checks if date has already been put, if it has then inputs the
            # value into the balance
            if date != "":
                balance += float(c)
            
            # if it contains any '|' character, then the string is split at
            # the character, and sorted accordingly
            elif (c.find('|') != -1):
                
                # split along '|' character
                temp = c.split('|')
                
                # iterate through the 
                for i in range(0,len(temp)):
                    
                    if (temp[i].lower().startswith( tuple(dates[:]) )):
                        date += temp[i]
                    elif (date == "") and (descriptor.rstrip().lower() == "deposit"):
                        credit += float(temp[i].replace(',',''))
                    elif(date == "") and (descriptor.rstrip().lower() != "deposit"):
                        debit += float(temp[i].replace(',',''))
                    
            
            # check for commas, dots, and if the number is greater than 3
            # characters long
            elif (c.find('.') == -1) and (c.find(',') == -1) and (len(c)>3):
                descriptor += c + " "
            
            # check if date is empty, and if it belongs in debits or credits
            elif (date == "") and (descriptor.rstrip().lower() == "deposit"):
                credit += float(c.replace(',',''))
                
            elif (date == "") and (descriptor.rstrip().lower() != "deposit"):
                debit += float(c.replace(',',''))
        
        # if first character is a letter
        elif(c[0].isalpha()):
            
            # if the string begins with a date, or not
            if(c.lower().startswith( tuple(dates[:]) )):
                date += c
            else:
                descriptor += c + " "
        
    date = date[:3] + date_fix(date[3:])    
    
    new_row = {column_names[0]:descriptor,
               column_names[1]:debit,
               column_names[2]:credit,
               column_names[3]:date,
               column_names[4]:balance
              }
        
    account_df = account_df.append(new_row, ignore_index=True)
    
writer = pd.ExcelWriter("sample.xlsx", engine='xlsxwriter')

account_df.to_excel(writer, sheet_name="Sheet1")

writer.save()