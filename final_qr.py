import qrcode
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os


# Function to create a QR code from a URL and save it
def create_qr_code(url, filename='qrcode.png'):
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR Code matrix
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # About 7% or less error can be corrected
        box_size=10,  # Controls how many pixels each “box” of the QR code is
        border=4,  # Controls how many boxes thick the border should be
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)


# Function to convert QR code to a binary 2D array, ignoring the border
def qr_code_to_binary_array(qr_code_path, border, box_size):
    img = cv2.imread(qr_code_path, cv2.IMREAD_GRAYSCALE)

    # Remove the border by cropping the image
    img_cropped = img[border * box_size: -border * box_size, border * box_size: -border * box_size]

    # Convert the cropped image to binary (0 and 1)
    _, thresh = cv2.threshold(img_cropped, 127, 1, cv2.THRESH_BINARY)

    print(thresh, "\n", thresh.shape)
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
    original_url = "https://www.hello.com"

    # Adjusted fixed positions to ignore the border completely
    fixed_positions = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
        (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 0), (3, 1), (3, 2),
        (3, 3), (3, 4), (3, 5), (3, 6), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (5, 0),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
        (6, 6), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (8, 0), (8, 1), (8, 2), (8, 3),
        (8, 4), (8, 5), (8, 6), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (10, 0), (10, 1),
        (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (11, 0), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5),
        (11, 6), (12, 0), (12, 1), (12, 2), (12, 3), (12, 4), (12, 5), (12, 6), (13, 0), (13, 1), (13, 2),
        (13, 3), (13, 4), (13, 5), (13, 6), (14, 0), (14, 1), (14, 2), (14, 3), (14, 4), (14, 5), (14, 6),
        (15, 0), (15, 1), (15, 2), (15, 3), (15, 4), (15, 5), (15, 6), (16, 0), (16, 1), (16, 2), (16, 3),
        (16, 4), (16, 5), (16, 6), (17, 0), (17, 1), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6), (18, 0),
        (18, 1), (18, 2), (18, 3), (18, 4), (18, 5), (18, 6), (19, 0), (19, 1), (19, 2), (19, 3), (19, 4),
        (19, 5), (19, 6), (20, 0), (20, 1), (20, 2), (20, 3), (20, 4), (20, 5), (20, 6)
    ]

    modified_url, position = find_modified_qr_code_url(original_url, fixed_positions)
    if modified_url:
        print(f"Modified URL: {modified_url}")
        print(f"Block flipped at position: {position}")
    else:
        print("No valid modification found.")
