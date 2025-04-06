from PIL import Image
import numpy
import pytesseract
import time

start_time = time.time()
text = pytesseract.image_to_string(Image.open("OCRTest.png").resize((810,1440)))
print(f"OCR Time: {time.time() - start_time:.2f} seconds")


