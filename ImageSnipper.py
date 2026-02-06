# ImageSnipper.py
import pymupdf
import pytesseract 
from PIL import Image

class ImageSnipper:
    def crop_and_save(self, page, rect, output_path):

        if rect is None:
            print(f"Empty crop area for {output_path}. Skipping save.")
            return

        pix = page.get_pixmap(clip=rect, matrix=pymupdf.Matrix(2, 2))   # Render the cropped area, matrix is used to increase the resolution of the output image

        pix.save(output_path)        # Save the result
        print(f"Crop saved: {output_path}")
