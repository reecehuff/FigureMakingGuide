#%% Import packages
from PyPDF2 import PdfWriter, PdfReader
import os 
import argparse
from tqdm import tqdm

# Parse the command line arguments
parser = argparse.ArgumentParser(description="Crop the PDF file containing all of the figures")
# Add an argument for the input file name
parser.add_argument("-i", "--input", help="Input file name", type=str, default="figure.making.guide.pdf")
# Add an argument for the save directory
parser.add_argument("-s", "--save_dir", help="Save directory", type=str, default="figures")
# Add an argument for how you want your figures saved
parser.add_argument("-f", "--fig_format", help="Figure format", type=str, default="png", choices=["png", "pdf", "both"])
# Add an argument for the dpi of the PNG file
parser.add_argument("-d", "--dpi", help="DPI of the PNG file", type=int, default=1200)
# Add an optional argument for converting final PNG files into a single PDF (default is True)
parser.add_argument("-c", "--compile", help="Convert final PNG's into a single PDF", action="store_false")
# Add an optional argument including the title page (default is True)
parser.add_argument("--compile_title", help="Include the title page in the compiled PDF", action="store_false")
# Add an argument for the output file name if you are compiling the PNG files into a single PDF
parser.add_argument("-o", "--output", help="Output file name if compiling PNG's into a single PDF", type=str, default="all_figures.pdf")

# Parse the args
args = parser.parse_args()

# If the save directory exists then delete it
if os.path.exists(args.save_dir):
    os.system("rm -rf %s" % args.save_dir)

# Make a save directory if it doesn't already exist
if not os.path.exists(args.save_dir):
    os.makedirs(args.save_dir)

# Define the input and output file names
input_file = args.input
output_file = args.output
output_file_path = os.path.join(args.save_dir, output_file)

#%% Define some useful functions
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
    figure_keys = ["Custom:", "Single column:", "Double column:", "Column-and-a-half:"]
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
    possible_units = ["cm", "mm", "pts"]
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
                elif "pts" in crop_box[i]:
                    crop_box_in_pts.append(float(crop_box[i].split("pts")[0]))
    # Define the crop box
    distance_from_figure_to_edge = (page_size[0] - crop_box_in_pts[0])/2
    lower_left_x = distance_from_figure_to_edge
    lower_left_y = page_size[1] - cm2pts(0.55) - crop_box_in_pts[1]
    upper_right_x = page_size[0] - distance_from_figure_to_edge
    upper_right_y = page_size[1] - cm2pts(0.55)
    crop_box = (lower_left_x, lower_left_y, upper_right_x, upper_right_y)
    # Return the crop box
    return crop_box

def get_file_name(text):
    # If the text doesn't contain the file name then return None
    if "Figure file name:" not in text:
        return "template"
    # Get the figure name from the text
    figure_name = text.split("Figure file name: ")[1].split(".pdf")[0]
    # If there is a new line character in the figure name, then isolate the figure name
    if "\n" in figure_name:
        figure_name = figure_name.split("\n")[0]
    # Return the figure name
    return figure_name

def unique(input_list):
    # initialize a null list
    unique_list = []
    # traverse for all elements
    for x in input_list:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list
 

def get_figure_paths(input_file, args):
    reader_2_figures = PdfReader(input_file)
    figure_paths = []
    figure_paths_dict = {}
    for i in tqdm(range(len(reader_2_figures.pages)), desc="Getting figure paths"):
        # Get the page
        page = reader_2_figures.pages[i]
        # Extract the text from the page
        text = page.extract_text()
        # Get the figure name
        figure_name = get_file_name(text)
        # If the figure name is not None then append it to the list
        if figure_name is not None and "template" not in figure_name:
            figure_path = os.path.join(args.save_dir, figure_name + ".pdf")
            figure_paths.append(figure_path)
            figure_paths_dict[str(i)] = figure_path
    # If any of the figure paths are duplicates, then go in and change them to be unique
    unique_figure_paths = unique(figure_paths)
    for p in unique_figure_paths:
        # Get the indices of the figure paths
        indices = [i for i, x in enumerate(figure_paths) if x == p]
        # If there are more than one index, then change the figure paths
        if len(indices) > 1:
            # Loop through the indices
            for i in range(len(indices)):
                # Get the figure path
                figure_path = figure_paths[indices[i]]
                # Change the figure path
                figure_path = figure_path.split(".pdf")[0] + "_" + str(i+1) + ".pdf"
                # Save the figure path
                figure_paths[indices[i]] = figure_path
    # Loop through the new figure paths and update the figure paths dictionary
    for p, i in zip(figure_paths, figure_paths_dict.keys()):
        figure_paths_dict[i] = p

    # Return the figure paths and the figure paths dictionary
    return figure_paths, figure_paths_dict

#%% Get the number of pages in the PDF files and loop through them, creating a new PDF file for each figure

# Define the figure keys and the figure paths
figure_keys = ["Custom:", "Single column:", "Double column:", "Column-and-a-half:"]
figure_paths, figure_paths_dict = get_figure_paths(input_file, args)

# Open the PDF file
reader = PdfReader(input_file)
# Loop through the pages
for i in tqdm(range(len(reader.pages)), desc="Cropping figures"):
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
    # As long as the page is within the figure_paths dictionary, then save it as a new PDF file
    if str(i) in figure_paths_dict.keys():
        # Open a new PDF file writer 
        writer_temp = PdfWriter()
        # Add the page to the writer
        writer_temp.add_page(page)
        # Write the new PDF file
        with open(figure_paths_dict[str(i)], "wb") as fp:
            writer_temp.write(fp)

#%% Convert the PDF files to PNG files
# Import Libraries
from pdf2image import convert_from_path
# Loop through the figure paths
for i in tqdm(range(len(figure_paths)), desc="Saving figures as PNG's"):
    # Get the figure path
    figure_path = figure_paths[i]
    # Convert the PDF file to a PNG file
    pages = convert_from_path(figure_path, args.dpi, use_cropbox=True)
    # Define the output file name
    output_file_name = figure_path.split(".pdf")[0] + ".png"
    # Save the PNG file
    for page in pages:
        page.save(output_file_name, "PNG")
# Remove all PDF's from save folder
os.system("rm -rf %s/*.pdf" % args.save_dir)

#%% If at the very end you want to delete the PDFs from before and save the final pngs as a pdf
if args.compile:
    print("Compiling figures into a single PDF file...")
    # Get the figure paths
    png_figure_paths = [path.replace("pdf", "png") for path in figure_paths]
    # If you wish to compile the title slide, then do so
    if args.compile_title:
        # Read in the first page of the PDF and save it as a PNG
        pages = convert_from_path(input_file, 800, use_cropbox=True)
        # Define the output file name
        output_file_name = os.path.join(args.save_dir, "title.png")
        # Save the PNG file
        for page in pages:
            page.save(output_file_name, "PNG")
            break
        # Make sure the title slide is first
        png_figure_paths.insert(0, "%s/title.png" % args.save_dir)

    # Import PIL
    from PIL import Image
    images = [Image.open(f) for f in png_figure_paths]
    images[0].save(output_file_path, "PDF" ,resolution=100.0, save_all=True, append_images=images[1:])

    # Remove the title slide
    if args.compile_title:
        os.system("rm -rf %s/title.png" % args.save_dir)

#%% If at the very end use the final pngs to create new pdfs
if args.fig_format == "pdf" or args.fig_format == "both":
    print("Converting PNG's into PDF's...")
    # Convert final PNG's into individual pdf's
    png_figure_paths = [path.replace("pdf", "png") for path in figure_paths]
    from PIL import Image
    for pdf_path, png_path in zip(figure_paths, png_figure_paths):
        image = Image.open(png_path)
        image.save(pdf_path, "PDF" ,resolution=100.0)

#%% If you just want the PDFs and not the PNGs, then remove the PNGs
if args.fig_format == "pdf":
    os.system("rm -rf %s/*.png" % args.save_dir)
