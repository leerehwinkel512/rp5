import psutil
import time
import math
from gpiozero import OutputDevice
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    return psutil.virtual_memory().percent

def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
            temp_c = float(temp_file.read()) / 1000.0
            return (temp_c * 9/5) + 32  # Convert Celsius to Fahrenheit
    except:
        return None

def draw_progress_bar(draw, x, y, width, height, progress, max_value=100):
    draw.rectangle((x, y, x + width, y + height), outline="white", fill="black")
    bar_width = int((progress / max_value) * width)
    draw.rectangle((x, y, x + bar_width, y + height), outline="white", fill="white")

def draw_spinning_square(draw, center_x, center_y, size, angle):
    half_size = size / 2
    points = [
        (-half_size, -half_size),
        (half_size, -half_size),
        (half_size, half_size),
        (-half_size, half_size)
    ]
    
    rotated_points = []
    for x, y in points:
        rx = x * math.cos(angle) - y * math.sin(angle)
        ry = x * math.sin(angle) + y * math.cos(angle)
        rotated_points.append((center_x + rx, center_y + ry))
    
    draw.polygon(rotated_points, outline="white")

def startup_animation(device):
    frames = 60
    for i in range(frames):
        with canvas(device) as draw:
            # Draw title
            draw.text((25, 5), "System Monitor", fill="white")
            
            # Draw spinning square
            angle = (i / frames) * 2 * math.pi
            draw_spinning_square(draw, 64, 40, 30, angle)
        
        time.sleep(1 / 30)  # Aim for 30 FPS


def main():
    
    # Initialize the gpio
    fan        = OutputDevice(17)
    trans_oled = OutputDevice(18)
    
    # switch transistor on
    fan.off()
    trans_oled.on()
    time.sleep(5)
    
    # Initialize the OLED display
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial)
    
    # Run startup animation
    startup_animation(device)    
    
    while True:
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()
        temperature = get_temperature()
        
        # Control the fan based on temperature
        if temperature is not None and temperature > 100:
            fan.on()
        else:
            fan.off()
        
        # Clear the display and draw the new information
        with canvas(device) as draw:
            # CPU Usage
            draw.text((0, 0), "CPU", fill="white")
            draw_progress_bar(draw, 0, 12, 100, 10, cpu_usage)
            draw.text((105, 12), f"{cpu_usage:.0f}%", fill="white")
            
            # Memory Usage
            draw.text((0, 26), "MEM", fill="white")
            draw_progress_bar(draw, 0, 38, 100, 10, memory_usage)
            draw.text((105, 38), f"{memory_usage:.0f}%", fill="white")
            
            # Temperature
            if temperature is not None:
                draw.text((0, 52), f"TEMP: {temperature:.0f}°F", fill="white")
                # Display fan status
                fan_status = "ON" if temperature > 100 else "OFF"
                draw.text((80, 52), f"FAN: {fan_status}", fill="white")
            else:
                draw.text((0, 52), "TEMP: N/A", fill="white")
        
        time.sleep(2)  # Update every 2 seconds for a more responsive feel

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program stopped by user")
