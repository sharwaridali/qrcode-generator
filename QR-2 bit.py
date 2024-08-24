import qrcode
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
import threading
import time
import csv

def record_execution_time_to_csv(code_name, start_time, end_time, qr_version, csv_filename="execution_times.csv"):
    execution_time = end_time - start_time
    file_exists = os.path.isfile(csv_filename)

    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Code Block", "Execution Time (seconds)", "QR Version"])

        writer.writerow([code_name, execution_time, qr_version])

    print(f"Execution time: {execution_time:.2f} seconds, QR Version: {qr_version}")
    return execution_time


# Function to create a QR code from a URL and save it
def create_qr_code(url, filename='qrcode.png'):
    qr = qrcode.QRCode(
        version=5,  # Controls the size of the QR Code matrix
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


# Function to find a modified URL by flipping 2 consecutive unique blocks
def find_modified_qr_code_url(original_url, fixed_positions, output_folder='modified_qr_codes', box_size=10):
    border_size = 4  # Border size in boxes
    create_qr_code(original_url)
    binary_array = qr_code_to_binary_array('qrcode.png', border_size, box_size)

    # Track the positions already modified to ensure we don't repeat
    modified_positions = set()

    for row in range(0, binary_array.shape[0], box_size):
        for col in range(0, binary_array.shape[1], box_size):
            position = (row // box_size, col // box_size)
            next_position = (row // box_size, (col + box_size) // box_size)

            # Check if this position and the next one are not fixed and are white
            if (
                    position not in fixed_positions and next_position not in fixed_positions and
                    np.all(binary_array[row:row + box_size, col:col + box_size] == 1) and
                    np.all(binary_array[row:row + box_size, col + box_size:col + 2 * box_size] == 1)
            ):
                modified_array = binary_array.copy()

                # Flip the current block and the next consecutive block
                modified_array[row:row + box_size, col:col + box_size] = 0
                modified_array[row:row + box_size, col + box_size:col + 2 * box_size] = 0

                modified_qr_filename = os.path.join(output_folder, f'modified_qr_{row}_{col}.png')
                binary_array_to_qr_code(modified_array, modified_qr_filename, border=border_size, box_size=box_size)

                modified_url = decode_qr_code(modified_qr_filename)
                print(
                    f"Modified URL from QR Code with blocks at ({row}, {col}) and ({row}, {col + box_size}) flipped: {modified_url}")

                if modified_url and modified_url != original_url and is_human_readable(modified_url):
                    return modified_url, (position, next_position)

                # Mark these positions as modified
                modified_positions.add(position)
                modified_positions.add(next_position)

    return None, None


# Function to check if the URL is human-readable (simplified check)
def is_human_readable(url):
    try:
        return all(32 <= ord(char) <= 126 for char in url)  # Check if all characters are printable ASCII
    except Exception:
        return False


# Timeout wrapper for functions
'''def run_with_timeout(func, timeout, *args, **kwargs):
    result = [None]

    def target():
        result[0] = func(*args, **kwargs)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print("Program terminated due to exceeding the time limit.")
        return None
    return result[0]'''


# Main program
if __name__ == "__main__":
    original_url = "https://www.hello.com"

    # Adjusted fixed positions to ignore the border completely
    fixed_positions = [
        # Top-left finder pattern
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
        (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
        (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7),

        # Top-right finder pattern
        (0, 17), (0, 18), (0, 19), (0, 20), (0, 21), (0, 22), (0, 23), (0, 24),
        (1, 17), (1, 18), (1, 19), (1, 20), (1, 21), (1, 22), (1, 23), (1, 24),
        (2, 17), (2, 18), (2, 19), (2, 20), (2, 21), (2, 22), (2, 23), (2, 24),
        (3, 17), (3, 18), (3, 19), (3, 20), (3, 21), (3, 22), (3, 23), (3, 24),
        (4, 17), (4, 18), (4, 19), (4, 20), (4, 21), (4, 22), (4, 23), (4, 24),
        (5, 17), (5, 18), (5, 19), (5, 20), (5, 21), (5, 22), (5, 23), (5, 24),
        (6, 17), (6, 18), (6, 19), (6, 20), (6, 21), (6, 22), (6, 23), (6, 24),
        (7, 17), (7, 18), (7, 19), (7, 20), (7, 21), (7, 22), (7, 23), (7, 24),

        # Bottom-left finder pattern
        (17, 0), (17, 1), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6), (17, 7),
        (18, 0), (18, 1), (18, 2), (18, 3), (18, 4), (18, 5), (18, 6), (18, 7),
        (19, 0), (19, 1), (19, 2), (19, 3), (19, 4), (19, 5), (19, 6), (19, 7),
        (20, 0), (20, 1), (20, 2), (20, 3), (20, 4), (20, 5), (20, 6), (20, 7),
        (21, 0), (21, 1), (21, 2), (21, 3), (21, 4), (21, 5), (21, 6), (21, 7),
        (22, 0), (22, 1), (22, 2), (22, 3), (22, 4), (22, 5), (22, 6), (22, 7),
        (23, 0), (23, 1), (23, 2), (23, 3), (23, 4), (23, 5), (23, 6), (23, 7),
        (24, 0), (24, 1), (24, 2), (24, 3), (24, 4), (24, 5), (24, 6), (24, 7),

        # Timing patterns
        (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7),
        (13, 7), (14, 7), (15, 7), (16, 7), (17, 7), (18, 7), (19, 7), (20, 7),
        (7, 6), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13),
        (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20),
    ]

    start_time = time.time()
    modified_url_data = find_modified_qr_code_url(original_url, fixed_positions)
    end_time = time.time()

    record_execution_time_to_csv("2 bit modification", start_time, end_time, qr_version=5)

    if modified_url_data:
        modified_url, positions = modified_url_data
        print(f"Successfully found a modified URL: {modified_url} with flipped blocks at {positions}")
    else:
        print("No human-readable modified URL found within the time limit.")
