from PIL import Image

def main():
   
    # take input for file path
    file_path = input("Enter the path to the raw10 file: ")
    try:
        with open(file_path, "rb") as file:
            buffer = file.read()
    except FileNotFoundError:
        print(f"Error: File not found at path {file_path}")
        return
    except IOError as e:
        print(f"Error reading file: {e}")
        return

    # Create a buffer for the image data with the proper width and height.
    width, height = 2048, 1536
    image_data = [0] * (width * height)

    # Process the buffer
    for i in range(0, len(buffer), 5):
        base_index = i // 5 * 4
        # Decode 10-bit values from the 5 bytes
        image_data[base_index] = ((buffer[i] << 2) | (buffer[i + 1] >> 6)) & 0x3FF  # First pixel (P1)
        image_data[base_index + 1] = (((buffer[i + 1] & 0x3F) << 4) | (buffer[i + 2] >> 4)) & 0x3FF  # Second pixel (P2)
        image_data[base_index + 2] = (((buffer[i + 2] & 0x0F) << 6) | (buffer[i + 3] >> 2)) & 0x3FF  # Third pixel (P3)
        image_data[base_index + 3] = (((buffer[i + 3] & 0x03) << 8) | buffer[i + 4]) & 0x3FF  # Fourth pixel (P4)

    # Demosaicing process to convert Bayer pattern to RGB (not implemented)
    demosaiced_data = [[0] * (width * 3) for _ in range(height)]  # 3 channels for RGB

    for y in range(height):
        for x in range(width):
            color = get_bayer_color(x, y)
            index = y * width + x
            red, green, blue = 0, 0, 0

            if color == 'r':
                # For red pixels, red is directly available, green and blue are interpolated
                red = image_data[index]  # Red value is directly from the sensor data
                green = interpolate_green(x, y, width, height, image_data)  # Call your interpolation method for green
                blue = interpolate_blue(x, y, width, height, image_data)  # Call your interpolation method for blue
            elif color == 'g':
                # For green pixels, green is directly available, red and blue are interpolated
                # Check the row to decide whether to interpolate red or blue next to the green pixel
                green = image_data[index]  # Green value is directly from the sensor data
                if x % 2 == 0:
                    # This is a green pixel on a blue row
                    red = interpolate_red(x, y, width, height, image_data)  # Call your interpolation method for red
                    blue = interpolate_blue(x, y, width, height, image_data)  # Call your interpolation method for blue
                else:
                    # This is a green pixel on a red row
                    red = interpolate_red(x, y, width, height, image_data)  # Call your interpolation method for red
                    blue = interpolate_blue(x, y, width, height, image_data)  # Call your interpolation method for blue
            elif color == 'b':
                # For blue pixels, blue is directly available, green and red are interpolated
                blue = image_data[index]  # Blue value is directly from the sensor data
                green = interpolate_green(x, y, width, height, image_data)  # Call your interpolation method for green
                red = interpolate_red(x, y, width, height, image_data)  # Call your interpolation method for red

            demosaiced_data[y][x * 3] = red
            demosaiced_data[y][x * 3 + 1] = green
            demosaiced_data[y][x * 3 + 2] = blue

    # Convert to 8-bit and save as image (not implemented)
    # Assuming you have a width and height defined, and your demosaiced data
    img = Image.new("RGB", (width, height))

    # Fill the image buffer with 8-bit data
    for y in range(height):
        for x in range(width):
            # Calculate the index for the red component
            base_index = x * 3
            red = to_8bit(demosaiced_data[y][base_index])  # Convert red component
            green = to_8bit(demosaiced_data[y][base_index + 1])  # Convert green component
            blue = to_8bit(demosaiced_data[y][base_index + 2])  # Convert blue component

            # Make sure that the x and y values are within the bounds of the image
            if x < width and y < height:
                img.putpixel((x, y), (red, green, blue))
    
    #can change to .png if desired
    img.save("output_image.jpg")

def to_8bit(value):
    # Scale the 10-bit data (0-1023) to 8-bit (0-255)
    return int(value * 255.0 / 1023.0)

def get_bayer_color(x, y):
    if y % 2 == 0:  # Even row
        return 'g' if x % 2 == 0 else 'r'
    else:  # Odd row
        return 'b' if x % 2 == 0 else 'g'

# Interpolate the green value for red or blue pixels
def interpolate_green(x, y, width, height, data):
    sum_val = 0
    count = 0

    if x > 0:
        sum_val += data[y * width + x - 1]
        count += 1
    if x < width - 1:
        sum_val += data[y * width + x + 1]
        count += 1
    if y > 0:
        sum_val += data[(y - 1) * width + x]
        count += 1
    if y < height - 1:
        sum_val += data[(y + 1) * width + x]
        count += 1

    return sum_val // count

# Interpolate the red value for green and blue pixels
def interpolate_red(x, y, width, height, data):
    sum_val = 0
    count = 0

    # Check corners and edges to avoid accessing out-of-bounds memory
    if y % 2 == 0:  # On a green pixel in a red row
        if x > 0:
            sum_val += data[y * width + x - 1]
            count += 1
        if x < width - 1:
            sum_val += data[y * width + x + 1]
            count += 1
    else:  # On a blue pixel
        if y > 0:
            sum_val += data[(y - 1) * width + x]
            count += 1
        if y < height - 1:
            sum_val += data[(y + 1) * width + x]
            count += 1

    return sum_val // count

# Interpolate the blue value for green and red pixels
def interpolate_blue(x, y, width, height, data):
    sum_val = 0
    count = 0

    # Check corners and edges to avoid accessing out-of-bounds memory
    if y % 2 == 1:  # On a green pixel in a blue row
        if x > 0:
            sum_val += data[y * width + x - 1]
            count += 1
        if x < width - 1:
            sum_val += data[y * width + x + 1]
            count += 1
    else:  # On a red pixel
        if y > 0:
            sum_val += data[(y - 1) * width + x]
            count += 1
        if y < height - 1:
            sum_val += data[(y + 1) * width + x]
            count += 1

    return sum_val // count

if __name__ == "__main__":
    main()
