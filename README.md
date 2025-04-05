# Precision_Baking_GDG

This is a Python-based desktop application that helps users identify and convert common baking ingredients using AI and camera input. The program has two main features:

## Camera View
Users can stream video from either an IP camera or a local webcam. Gemini AI analyzes the captured image of an ingredient to identify it and estimate its density.

## Measurement Converter
A simple converter screen allows users to input the amount, unit (cups, tablespoons, teaspoons), and ingredient to convert it into grams using a predefined ingredient density database.

# In order to run this program, perform the following steps:

## Install the following libraries by running
```bash
pip install tk opencv-python pillow google-generativeai numpy
```

## Clone the repo to your files
```bash
git clone https://github.com/xbhijith/Precision_Baking_GDG.git
```

## Run the program using Command Prompt 
```bash
cd Precision_Baking_GDG
python Main.py
```

## Requirements:
```bash
Python 3.7 (or higher)
OpenCV
Pillow (PIL)
NumPy
Tkinter
Google Generative AI
A camera or webcam connected to your computer
An IP camera
```
