# PearsonAutomatedCrop
A tool that automates the manual process of cropping the papers to make the process more efficient.

This tool was made for UniDoodle, to speed up their snipping process of manually cropping papers to get questions from them. 

1. What can it do?
It was made to automatically crop out the Tasks of Pearson papers. It crops out The tasks and the subtasks separately exactly how we do it here.
The Tasks get cropped out and get saved in the same folder where the program is saved in.
It has a about 90% - 95% accuracy, and it only struggles with subsubtasks, (e.g. Task 3. subtask (a) subsubtask (ii)) which it can not reliably crop.

2. How it's built.
It was programmed object oriented. There is a total of 4 classes:

       1. "main.py" Acts as the central controller that manages user input and orchestrates the workflow between all other modules. It coordinates the entire process from opening the PDF to saving the final images.
       
       2. "PDFManager.py" Manages the document operations, such as opening the file and navigating between pages. It ensures the PDF is properly loaded and safely closed after processing.
       
       3. "TaskExtractor.py" This class acts as the "brain" of the system by scanning page content for specific score patterns (like "(3)") to determine where tasks begin and end. It then translates these visual markers into mathematical coordinates for the cropping process.
         
       4. "ImageSnipper" Handles the actual image rendering and file management. It converts the identified PDF parts into high resolution PNGs.

4. Installation and Dependencies
    
    1. You need python 

    2. PyMuPDF (pip install PyMuPDF)

    3. Put PDF in the project folder

    4. Run the code (The .png pictures show up in the folder the project is in)
