from pdf2image import convert_from_path

def convert_pdf_to_png(pdf_path, output_folder, base_name):
    # Convert PDF to a list of images
    images = convert_from_path(pdf_path, dpi=300)
    
    # Save each image as a PNG file
    for i, image in enumerate(images):
        image.save(f"{output_folder}/{base_name}_page_{i + 1}.png", "PNG")
    print(f"Converted {pdf_path} to PNG images in {output_folder}")

def main():
    import os
    import glob

    input_folder = "../raw/"
    output_folder = "../dataset/image/"
    os.makedirs(output_folder, exist_ok=True)

    pdf_files = glob.glob(os.path.join(input_folder, "lich-su-va-dia-li-*.pdf"))
    
    for pdf_file in pdf_files:
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        convert_pdf_to_png(pdf_file, output_folder, base_name)

main()