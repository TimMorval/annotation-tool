from pdf2image import convert_from_path
from pathlib import Path
import shutil
from tqdm import tqdm


def convert_to_images(to_convert_folder, output_folder):

    # Path to the folder containing PDFs to convert
    pdf_folder = Path(to_convert_folder)

    # Path to the folder where the converted images will be saved
    image_folder = Path(output_folder)
    image_folder.mkdir(exist_ok=True)  # Ensure the directory exists

    # Convert each PDF file into images and save them
    pdf_files = list(pdf_folder.glob('*.pdf'))
    for pdf_file in tqdm(pdf_files, desc="Converting PDFs to images"):
        images = convert_from_path(pdf_file)

        if len(images) == 1:
            image = images[0]
            image_path = image_folder / f'{pdf_file.stem}.png'
            image.save(image_path, 'PNG')
        # Save each image with a unique name
        else:
            for i, image in enumerate(images):
                image_path = image_folder / f'{pdf_file.stem}_{i}.png'
                image.save(image_path, 'PNG')

    # Move all image files from 'to_convert' to 'images'
    # List of image extensions to look for
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    for extension in image_extensions:
        for img_file in pdf_folder.glob(extension):
            shutil.move(str(img_file), str(image_folder / img_file.name))


if __name__ == "__main__":
    convert_to_images("to_convert", "images")
