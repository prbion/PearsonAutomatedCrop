# main.py
import pymupdf
import pytesseract 
from PIL import Image
# Below are the imports for the classes 
from PDFManager import PDFManager
from TaskExtractor import TaskExtractor
from ImageSnipper import ImageSnipper



""""
doc = pymupdf.open("8fm0-01-que-20240514.pdf")
for page in doc: # iterate the document pages
  text = page.get_text() # get plain text encoded as UTF-8

  print(text)

""""
