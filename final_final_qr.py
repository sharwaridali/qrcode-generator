import qrcode
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os


# Function to create a QR code from a URL and save it
def create_qr_code(url, qr_version= 1, filename='qrcode.png'):
    qr = qrcode.QRCode(
        version=qr_version,  # Controls the size of the QR Code matrix
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # About 7% or less error can be corrected
        box_size=10,  # Controls how many pixels each “box” of the QR code is
        border=4,  # Controls how many boxes thick the border should be
    )
    qr.add_data(url)
    qr.make()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)


# Function to get all the fixed positions in the QR code
def generate_fixed_positions(qr_code_shape, qr_version):
    # Calculate the size of the finder patterns based on the QR code version
    border = 4
    rows, cols = qr_code_shape
    print(rows,cols)
    fixed_positions = set()

    # Finder pattern size is 7x7, but including the separator it's 8x8
    finder_pattern_size = 7 + 2 * (qr_version - 1)
    alignment_pattern_locations = {
        2: [18], 3: [22], 4: [26], 5: [30], 6: [34], 7: [22, 38],
        8: [24, 42], 9: [26, 46], 10: [28, 50], 11: [30, 54], 12: [32, 58],
        13: [34, 62], 14: [26, 46, 66], 15: [26, 48, 70], 16: [26, 50, 74],
        17: [30, 54, 78], 18: [30, 56, 82], 19: [30, 58, 86], 20: [34, 62, 90],
        21: [28, 50, 72, 94], 22: [26, 50, 74, 98], 23: [30, 54, 78, 102],
        24: [28, 54, 80, 106], 25: [32, 58, 84, 110], 26: [30, 58, 86, 114],
        27: [34, 62, 90, 118], 28: [26, 50, 74, 98, 122], 29: [30, 54, 78, 102, 126],
        30: [26, 52, 78, 104, 130], 31: [30, 56, 82, 108, 134], 32: [34, 60, 86, 112, 138],
        33: [30, 58, 86, 114, 142], 34: [34, 62, 90, 118, 146], 35: [30, 54, 78, 102, 126, 150],
        36: [24, 50, 76, 102, 128, 154], 37: [28, 54, 80, 106, 132, 158], 38: [32, 58, 84, 110, 136, 162],
        39: [26, 54, 82, 110, 138, 166], 40: [30, 58, 86, 114, 142, 170],
    }

    # Top-left finder pattern (8x8 including the separator)
    for row in range(finder_pattern_size + 1):
        for col in range(finder_pattern_size + 1):
            fixed_positions.add((row, col))
            #print("Top left",row,col)

    # Top-right finder pattern (8x8 including the separator)
    for row in range(finder_pattern_size + 1):
        for col in range(cols - finder_pattern_size - 5, cols - border):
            fixed_positions.add((row, col))
            #print("Top right", row, col)

    # Bottom-left finder pattern (8x8 including the separator)
    for row in range(rows - finder_pattern_size - 5, rows - border):
        for col in range(finder_pattern_size + 1):
            fixed_positions.add((row, col))
            #print("bottom left", row, col)

    # Timing patterns
    for i in range(finder_pattern_size + 1, cols - finder_pattern_size - 5):
        fixed_positions.add((finder_pattern_size, i))  # Horizontal timing pattern
        fixed_positions.add((i, finder_pattern_size))  # Vertical timing pattern

    # Alignment patterns
    if qr_version >= 2:
        positions = alignment_pattern_locations.get(qr_version, [])
        for row in positions:
            for col in positions:
                if not ((row <= finder_pattern_size and col <= finder_pattern_size) or  # top-left
                        (row <= finder_pattern_size and col >= cols - finder_pattern_size - 1) or  # top-right
                        (row >= rows - finder_pattern_size - 1 and col <= finder_pattern_size)):  # bottom-left
                    fixed_positions.add((row - 1, col - 1))  # Alignment pattern centers

    return fixed_positions

# Function to convert QR code to a binary 2D array, ignoring the border
def qr_code_to_binary_array(qr_code_path, border, box_size):
    img = cv2.imread(qr_code_path, cv2.IMREAD_GRAYSCALE)

    # Remove the border by cropping the image
    img_cropped = img[border * box_size: -border * box_size, border * box_size: -border * box_size]

    # Convert the cropped image to binary (0 and 1)
    _, thresh = cv2.threshold(img_cropped, 127, 1, cv2.THRESH_BINARY)

    return thresh


# Function to convert the binary 2D array back to QR code
def binary_array_to_qr_code(binary_array, output_path='modified_qr.png', border=4, box_size=10):
    reshaped_array = binary_array * 255  # Scale binary values back to 0-255

    # Re-add the border
    border_array = np.ones(
        (reshaped_array.shape[0] + 2 * border * box_size, reshaped_array.shape[1] + 2 * border * box_size),
        dtype=np.uint8) * 255
    border_array[border * box_size: -border * box_size, border * box_size: -border * box_size] = reshaped_array

    # Save the modified QR code image
    cv2.imwrite(output_path, border_array)


# Function to decode a QR code image to get the URL
def decode_qr_code(qr_code_path):
    img = cv2.imread(qr_code_path)
    decoded_objects = decode(img)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None


# Function to find a modified URL by flipping bits
def find_modified_qr_code_url(original_url, fixed_positions, output_folder='modified_qr_codes', box_size=10):
    border_size = 4  # Border size in boxes
    create_qr_code(original_url)
    binary_array = qr_code_to_binary_array('qrcode.png', border_size, box_size)

    # Iterate over the 2D array and modify white squares (10x10 blocks)
    for row in range(0, binary_array.shape[0], box_size):
        for col in range(0, binary_array.shape[1], box_size):
            position = (row // box_size, col // box_size)
            print("Positions: ", position)
            if position not in fixed_positions and np.all(binary_array[row:row + box_size, col:col + box_size] == 1):
                modified_array = binary_array.copy()
                modified_array[row:row + box_size, col:col + box_size] = 0  # Flip the block to black
                modified_qr_filename = os.path.join(output_folder, f'modified_qr_{row}_{col}.png')
                binary_array_to_qr_code(modified_array, modified_qr_filename, border=border_size, box_size=box_size)
                modified_url = decode_qr_code(modified_qr_filename)
                print(f"Modified URL from QR Code with block at ({row}, {col}) flipped: {modified_url}")
                if modified_url and modified_url != original_url and is_human_readable(modified_url):
                    return modified_url, position  # Return the modified URL and the position of the flip
    return None, None


# Function to check if the URL is human-readable (simplified check)
def is_human_readable(url):
    try:
        return all(32 <= ord(char) <= 126 for char in url)  # Check if all characters are printable ASCII
    except Exception:
        return False


# Main program
if __name__ == "__main__":
    original_url = input("Enter the URL: ")
    qr_v = int(input("Enter QR code version: "))

    # Create a QR code to determine its dimensions
    create_qr_code(original_url, qr_version=qr_v)
    img = cv2.imread('qrcode.png', cv2.IMREAD_GRAYSCALE)
    qr_code_shape = img.shape[0] // 10, img.shape[1] // 10  # Calculate rows and cols from image size divided by box_size

    fixed_positions = generate_fixed_positions(qr_code_shape, qr_v)

    modified_url, position = find_modified_qr_code_url(original_url, fixed_positions)
    if modified_url:
        print(f"Modified URL: {modified_url}")
        print(f"Block flipped at position: {position}")
    else:
        print("No valid modification found.")
