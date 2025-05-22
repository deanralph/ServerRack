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

# Proxmox API configuration
import proxmoxdeets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Functions
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

def bytesToGb(b):
    return round(b / (1024 ** 3), 2)

def getTextPosition(text, font, centerX, centerY, draw):
    bbox = draw.textbbox((0, 0), text, font=font)
    textWidth = bbox[2] - bbox[0]
    textHeight = bbox[3] - bbox[1]
    return centerX - textWidth / 2, centerY - textHeight / 2

def getAngle(cpu, maxMem, memUsed):
    cpuAngle = (cpu / 100) * 150
    memAngle = (memUsed / maxMem) * 150
    return cpuAngle, memAngle

def getBarColour(percent):
    if percent < 70:
        return "GREEN"
    elif percent < 85:
        return "ORANGE"
    else:
        return "RED"
    
def getNodeStats(node):
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/status"
    resp = requests.get(url, headers=HEADERS, verify=False)
    return resp.json().get('data', {})

def getNodes():
    url = f"{PROXMOX_HOST}/api2/json/nodes"
    resp = requests.get(url, headers=HEADERS, verify=False)
    return resp.json().get('data', [])

def getRunningVms(node):
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu"
    resp = requests.get(url, headers=HEADERS, verify=False)
    return [vm for vm in resp.json().get('data', []) if vm.get('status') == 'running']

def getVmStats(node, vmid):
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/current"
    resp = requests.get(url, headers=HEADERS, verify=False)
    return resp.json().get('data', {})

def displayStats(name, cpuPct, memUsed, memTotal, fontLarge, fontSmall):
    nodeDict = nodeHandler.get_or_create_node(name)
    if nodeDict["logo"] != "TempIndex":
        image_2 = Image.open(nodeDict["logo"])
    else:
        image_2 = Image.new("RGB", (disp_2.width, disp_2.height), "BLACK")
    draw_2 = ImageDraw.Draw(image_2)

    memText = f"{memUsed}GB"
    cpuFill, memFill = getAngle(cpuPct, memTotal, memUsed)

    image_0 = Image.new("RGB", (disp_0.width, disp_0.height), "BLACK")
    image_1 = Image.new("RGB", (disp_1.width, disp_1.height), "BLACK")

    draw_0 = ImageDraw.Draw(image_0)
    draw_1 = ImageDraw.Draw(image_1)
    draw_0.rounded_rectangle((9, 24, 151, 56),radius=5, fill=getBarColour(memFill))
    draw_1.rounded_rectangle((9, 24, 151, 56),radius=5, fill=getBarColour(cpuFill))
    draw_1.rounded_rectangle((10, 25, 150, 55),radius=5, fill="BLACK")
    draw_0.rounded_rectangle((10, 25, 150, 55),radius=5, fill="BLACK")
    draw_1.rounded_rectangle((150 - cpuFill, 25, 150, 55),radius=5, fill=getBarColour(cpuFill))
    draw_0.rounded_rectangle((150 - memFill, 25, 150, 55),radius=5, fill=getBarColour(memFill))

    #nameX, nameY = getTextPosition(name, fontLarge, 120, 50, draw_2)
    cpuX, cpuY = getTextPosition(f"{cpuPct}%", fontSmall, 80, 40, draw_1)
    memX, memY = getTextPosition(memText, fontSmall, 80, 40, draw_0)

    draw_2.rounded_rectangle((1, 1, 239, 44), radius=5, fill="WHITE")
    draw_2.rounded_rectangle((2, 2, 238, 43), radius=5, fill="BLACK")
    draw_2.text((10, 10), nodeDict["softname"], fill="ORANGE", font=fontLarge)
    draw_1.text((cpuX, cpuY), f"{cpuPct}%", fill="WHITE", font=fontSmall)
    draw_0.text((memX, memY), memText, fill="WHITE", font=fontSmall)
    draw_2.text((10, 55), nodeDict["ip"], fill="WHITE", font=fontSmall)
    disp_0.ShowImage(image_0)
    disp_1.ShowImage(image_1)
    disp_2.ShowImage(image_2.rotate(90))


# Initial Boot up
# Load the logo image
image1 = Image.new("RGB", (disp_0.width, disp_0.height), "BLACK")
image2 = Image.open('pic/logo.png')	
im_r=image2.rotate(90)
disp_2.ShowImage(im_r)
disp_0.ShowImage(image1)
disp_1.ShowImage(image1)
time.sleep(1)

# Clear the display
disp_0.clear()
disp_1.clear()
disp_2.clear()
image1 = Image.new("RGB", (disp_2.width, disp_2.height), "BLACK")
disp_2.ShowImage(image1)

fontLarge = ImageFont.truetype(f"Font/sono-bold.ttf", 25)
fontSmall = ImageFont.truetype(f"Font/sono-bold.ttf", 20)


while True:
    for nodeInfo in getNodes():
            node = nodeInfo['node']
            nodeStats = getNodeStats(node)

            nodeCpuPct = round(nodeStats.get('cpu', 0) * 100, 1)
            memInfo = nodeStats.get('memory', {})
            nodeMemUsed = bytesToGb(memInfo.get('used', 0))
            nodeMemTotal = bytesToGb(memInfo.get('total', 1))

            displayStats(node, nodeCpuPct, nodeMemUsed, nodeMemTotal, fontLarge, fontSmall)
            time.sleep(3)

            for vm in getRunningVms(node):
                vmid = vm['vmid']
                name = vm['name']
                nodeHandler.get_or_create_node(name)
                vmStats = getVmStats(node, vmid)

                vmCpuPct = round(vmStats.get('cpu', 0) * 100, 1)
                vmMemUsed = bytesToGb(vmStats.get('mem', 0))
                vmMemTotal = bytesToGb(vmStats.get('maxmem', 1))

                displayStats(name, vmCpuPct, vmMemUsed, vmMemTotal, fontLarge, fontSmall)
                time.sleep(3)