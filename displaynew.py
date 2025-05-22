# Main display for server Rack
#
# Desgined to run on waveshare Zero Hat A
# 
# Imports
import spidev as SPI
from lib import LCD_1inch3
from lib import LCD_0inch96
from PIL import Image,ImageDraw,ImageFont
import RPi.GPIO as GPIO
import time
import urllib3
import requests
import nodeHandler

# Global Variables
display0 = {"RST" :24, "DC" : 4, "BL" : 13, "bus" : 0, "device" : 0}
display1 = {"RST" :23, "DC" : 5, "BL" : 12, "bus" : 0, "device" : 1}
display2 = {"RST" :27, "DC" : 22, "BL" : 19, "bus" : 1, "device" : 0}
disp_0 = LCD_0inch96.LCD_0inch96(spi=SPI.SpiDev(display0["bus"], display0["device"]),spi_freq=10000000,rst=display0["RST"],dc=display0["DC"],bl=display0["BL"])
disp_1 = LCD_0inch96.LCD_0inch96(spi=SPI.SpiDev(display1["bus"], display1["device"]),spi_freq=10000000,rst=display1["RST"],dc=display1["DC"],bl=display1["BL"])
disp_2 = LCD_1inch3.LCD_1inch3(spi=SPI.SpiDev(display2["bus"], display2["device"]),spi_freq=10000000,rst=display2["RST"],dc=display2["DC"],bl=display2["BL"])

# Display setup
disp_0.Init()
disp_1.Init()
disp_2.Init()
disp_0.clear()
disp_1.clear()
disp_2.clear()
disp_0.bl_DutyCycle(50)
disp_1.bl_DutyCycle(50)
disp_2.bl_DutyCycle(50)

def get_max_fitting_text_position(text, box, font_path, max_font_size=300, min_font_size=5):
    """
    Calculates the maximum font size to fit `text` in `box`, and returns center (x, y) coords.

    Parameters:
        text (str): The text to measure.
        box (tuple): (x0, y0, x1, y1) bounding box.
        font_path (str): Path to a .ttf font file.
        max_font_size (int): Upper limit for font size.
        min_font_size (int): Lower limit for font size.

    Returns:
        (font_size, x, y): Best fitting font size, and top-left x,y to center it in the box.
    """
    dummy_image = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_image)
    x0, y0, x1, y1 = box
    box_width = x1 - x0
    box_height = y1 - y0

    best_size = min_font_size
    best_bbox = None

    while min_font_size <= max_font_size:
        mid = (min_font_size + max_font_size) // 2
        font = ImageFont.truetype(font_path, mid)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if text_width <= box_width and text_height <= box_height:
            best_size = mid
            best_bbox = bbox
            min_font_size = mid + 1
        else:
            max_font_size = mid - 1

    if best_bbox is None:
        return None  # Text doesn't fit even at minimum size

    final_font = ImageFont.truetype(font_path, best_size)
    bbox = draw.textbbox((0, 0), text, font=final_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = x0 + (box_width - text_width) // 2
    y = y0 + (box_height - text_height) // 2

    return best_size, x, y

def create_gradient(size, start_color, end_color):
    """Creates a vertical gradient image from start_color to end_color."""
    gradient = Image.new("RGBA", size)
    for y in range(size[1]):
        ratio = y / (size[1] - 1)
        r = int(start_color[0] + ratio * (end_color[0] - start_color[0]))
        g = int(start_color[1] + ratio * (end_color[1] - start_color[1]))
        b = int(start_color[2] + ratio * (end_color[2] - start_color[2]))
        for x in range(size[0]):
            gradient.putpixel((x, y), (r, g, b, 255))
    return gradient

def draw_gradient_rounded_rectangle(image_size, rect, radius, start_color, end_color):
    # Step 1: Create gradient
    gradient = create_gradient(image_size, start_color, end_color)

    # Step 2: Create mask with rounded rectangle
    mask = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(rect, radius=radius, fill=255)

    # Step 3: Apply mask to gradient
    result = Image.new("RGBA", image_size, (0, 0, 0, 0))
    result.paste(gradient, mask=mask)

    return result

violet = (32, 0, 50)  # Desaturated violet
cyan = (74, 0, 94)  # Desaturated cyan

# Usage
size = (80, 160)
rect_bounds = (0, 0, 80, 160)  # (x0, y0, x1, y1)

grad_image = draw_gradient_rounded_rectangle(size, rect_bounds, radius=0, start_color=violet, end_color=cyan)

textString = "Jenkins"

font_path = "Font/OriginTech.ttf"  # Replace with actual TTF path
titlebox = (20, 10, 220, 60)
nodeBox = (20, 70, 220, 120)
statusBox = (20, 170, 220, 220)
text = textString

title_font_size, title_x, title_y = get_max_fitting_text_position(text, titlebox, font_path)
nodeName_font_size, nodeName_x, nodeName_y = get_max_fitting_text_position("10.0.0.250", nodeBox, font_path)
Status_font_size, Status_x, Status_ = get_max_fitting_text_position("Running", statusBox, font_path)

title_fontLarge = ImageFont.truetype("Font/OriginTech.ttf", title_font_size)
nodeName_fontLarge = ImageFont.truetype("Font/OriginTech.ttf", nodeName_font_size)
Status_fontLarge = ImageFont.truetype("Font/OriginTech.ttf", Status_font_size)

image_1 = Image.open("pic/synthwavebg2.jpg")
image_2 = Image.open("pic/synthwavebg.jpg")
draw_2 = ImageDraw.Draw(image_2)
draw_2.text((title_x, title_y), textString, fill=(255, 46, 207), font=title_fontLarge)
draw_2.text((nodeName_x, nodeName_y), "10.0.0.250", fill=(254, 223, 176), font=nodeName_fontLarge)
draw_2.text((Status_x, Status_), "Running", fill=(46, 250, 223), font=Status_fontLarge)

disp_0.ShowImage(grad_image.rotate(270))
disp_2.ShowImage(image_2.rotate(270))
time.sleep(10)  