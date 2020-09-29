# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 21:15:26 2020

@author: Michael Hage
"""

# import dependents
import pandas as pd
import PyPDF2 as pdf

# open pdf file and put it into an object
pdf_file = open('test.pdf', 'rb')

# create pdf reader
pdf_reader = pdf.PdfFileReader(pdf_file)

# extract page
page_obj = pdf_reader.getPage(0)
page_obj.extractText()