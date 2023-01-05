#%% Import packages
from PyPDF2 import PdfWriter, PdfReader
import os 
import argparse

# Make a figure directory if it doesn't already exist
if not os.path.exists("figures"):
    os.makedirs("figures")

# Parse the command line arguments
parser = argparse.ArgumentParser(description="Crop the PDF file containing all of the figures")
parser.add_argument("-i", "--input", help="Input file name", type=str, default="figure.making.guide.pdf")
# Add an optional argument that compresses the PDF file
parser.add_argument("-c", "--compress", help="Compress the PDF file", action="store_true")
# Add an optional argument for the key to use PDFTron
parser.add_argument("-k", "--key", help="Key to use PDFTron", type=str, default=None)

# Parse the args
args = parser.parse_args()

# Define the input and output file names
input_file = args.input
output_file = "all_figures.pdf"
output_file = os.path.join("figures", output_file)

# Open the PDF file
reader = PdfReader(input_file)
writer = PdfWriter()

# Define the functions for converting between cm, mm, and pts
def cm2pts(cm):
    return cm * 28.3464567
def mm2pts(mm):
    return mm * 2.83464567
def pts2cm(pts):
    return pts / 28.3464567
def pts2mm(pts):
    return pts / 2.83464567

# Define a function for getting the figure key from the text
def get_figure_key(text):
    # Define the figure keys
    figure_keys = ["Custom:", "Single column:", "Double column:", "Double column Short:", "Column-and-a-half:", "Column-and-a-half Short:"]
    # Initialize the figure key
    figure_key = None
    # Loop through the figure keys
    for i in range(len(figure_keys)):
        if figure_keys[i] in text:
            # Get the figure key
            figure_key = figure_keys[i]
            # Break out of the loop
            break
    # Return the figure key if it was found
    if figure_key is not None:
        return figure_key

# Define a function for getting the crop box from the text
def get_crop_box(text, figure_key, page_size):
    # Get the crop box from the text
    crop_box = text.split(figure_key)[1].split(" ")[1:5]
    # Further process the crop box by grabbing all of the numbers
    new_crop_box = []
    crop_box_in_pts = []
    possible_units = ["cm", "mm", "pt"]
    for i in range(len(crop_box)):
        for j in range(len(possible_units)):
            if possible_units[j] in crop_box[i]:
                # If this is the case then isolate the number 
                crop_box[i] = crop_box[i].split(possible_units[j])[0]
                # The final string should have the number and the units
                crop_box[i] = crop_box[i] + possible_units[j]
                new_crop_box.append(crop_box[i])
                # Save the crop box in pts
                if "cm" in crop_box[i]:
                    crop_box_in_pts.append(cm2pts(float(crop_box[i].split("cm")[0])))
                elif "mm" in crop_box[i]:
                    crop_box_in_pts.append(mm2pts(float(crop_box[i].split("mm")[0])))
                elif "pt" in crop_box[i]:
                    crop_box_in_pts.append(float(crop_box[i].split("pt")[0]))
    # Define the crop box
    distance_from_figure_to_edge = (page_size[0] - crop_box_in_pts[0])/2
    lower_left_x = distance_from_figure_to_edge
    lower_left_y = page_size[1] - cm2pts(0.55) - crop_box_in_pts[1]
    upper_right_x = page_size[0] - distance_from_figure_to_edge
    upper_right_y = page_size[1] - cm2pts(0.55)
    crop_box = (lower_left_x, lower_left_y, upper_right_x, upper_right_y)
    # Return the crop box
    return crop_box

#%% Get the number of pages in the PDF files and loop through them, creating a new PDF file for each figure
num_pages = len(reader.pages)
fig_num = 1
figure_keys = ["Custom:", "Single column:", "Double column:", "Double Short column:", "Column-and-a-half:", "Column-and-a-half Short:"]
figure_paths = []

# Loop through the pages
for i in range(num_pages):
    # Get the page
    page = reader.pages[i]

    # Determine the page size
    page_size = page.mediabox.upper_right

    # Extract the text from the page
    text = page.extract_text()

    # Locate which figure key is in the text
    figure_key = get_figure_key(text)

    # Get the crop box
    if figure_key is not None:
        crop_box = get_crop_box(text, figure_key, page_size)
    else:
        crop_box = (0, 0, page_size[0], page_size[1])

    # Set the crop box
    page.cropbox.upper_left = crop_box[0:2]
    page.cropbox.lower_right = crop_box[2:4]

    # Add the page to the writer 
    writer.add_page(page)
    # For every page that was a figure, i.e., contained "Double", "Single", or "Column-and-a-half" in the text
    # Write a new PDF file with the cropped pages
    if any(key in text for key in figure_keys):
        # Open a new PDF file writer 
        writer_temp = PdfWriter()
        # Compress the page before writing it to the new PDF file
        page.compress_content_streams()  # This is CPU intensive!
        # Add the page to the writer
        writer_temp.add_page(page)
        # Define the output file name
        output_temp = "figure" + str(fig_num) + ".pdf"
        output_temp = os.path.join("figures", output_temp)
        # Save the figure path to a list
        figure_paths.append(output_temp)
        # Write the new PDF file
        with open(output_temp, "wb") as fp:
            writer_temp.write(fp)
        writer_temp = PdfWriter()
        fig_num += 1

# Write the new PDF file containing all of the figures
with open(output_file, "wb") as fp:
    writer.write(fp)

#%% The next section of the code is for compressing the PDF files using PDFTron

# If the user wants to compress the PDF files
if args.compress:
    # Import Libraries
    from PDFNetPython3.PDFNetPython import PDFDoc, Optimizer, SDFDoc, PDFNet
    # You need to set the PDFNet SDK key
    if args.key is not None:
        PDFtron_SDK_key = args.key
    else:
        # Raise an error if the user did not provide a key
        raise ValueError("You need to provide a PDFNet SDK key. You can get one for free at https://www.pdftron.com")
    
    # Make sure to set the PDFNet SDK key
    PDFNet.Initialize(PDFtron_SDK_key)

    def get_size_format(b, factor=1024, suffix="B"):
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f}{unit}{suffix}"
            b /= factor
        return f"{b:.2f}Y{suffix}"

    def compress_file(input_file: str, output_file: str, key):
        """Compress PDF file"""
        if not output_file:
            output_file = input_file
        initial_size = os.path.getsize(input_file)
        try:
            # Initialize the library
            PDFNet.Initialize(key)
            doc = PDFDoc(input_file)
            # Optimize PDF with the default settings
            doc.InitSecurityHandler()
            # Reduce PDF size by removing redundant information and compressing data streams
            Optimizer.Optimize(doc)
            doc.Save(output_file, SDFDoc.e_linearized)
            doc.Close()
        except Exception as e:
            print("Error compress_file=", e)
            doc.Close()
            return False
        compressed_size = os.path.getsize(output_file)
        ratio = 1 - (compressed_size / initial_size)
        summary = {
            "Input File": input_file, "Initial Size": get_size_format(initial_size),
            "Output File": output_file, f"Compressed Size": get_size_format(compressed_size),
            "Compression Ratio": "{0:.3%}.".format(ratio)
        }
        # Printing Summary
        print("## Summary ########################################################")
        print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
        print("###################################################################")
        return True

    # Define the input and output files
    for path in figure_paths:
        # Define the input and output file names
        input_file = path
        output_file = path.split(".pdf")[0] + "_compressed.pdf"
        # Compress the PDF file
        compress_file(input_file, output_file, PDFtron_SDK_key)