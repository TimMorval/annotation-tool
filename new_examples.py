import os
import shutil

from convert_pdf_to_image import convert_to_images
from ocr import extract_texts_from_images

# Create the temporary directory
os.mkdir('img')

# Move images to the temporary directory
for image in os.listdir('images'):
    shutil.move(os.path.join('images', image), 'img')

# Convert PDFs to images
input_folder = 'to_convert'
output_folder = 'images'
convert_to_images(input_folder, output_folder)

# Extract texts from images
input_path = 'images'
output_dir = 'todo'
extract_texts_from_images(input_path, output_dir)

# Move images back from the temporary directory, handling existing files
for image in os.listdir('img'):
    src = os.path.join('img', image)
    dst = os.path.join('images', image)

    # If destination file exists, rename the source file
    if os.path.exists(dst):
        base, ext = os.path.splitext(image)
        i = 1
        new_name = f"{base}_{i}{ext}"
        new_dst = os.path.join('images', new_name)
        while os.path.exists(new_dst):
            i += 1
            new_name = f"{base}_{i}{ext}"
            new_dst = os.path.join('images', new_name)
        shutil.move(src, new_dst)
    else:
        shutil.move(src, dst)

# Remove the temporary directory
shutil.rmtree('img')
