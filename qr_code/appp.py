# old flask for old version


import threading
import cv2
from pyttsx3 import init
import csv
import pandas as pd
from statistics import mode
from pyzbar.pyzbar import decode
from flask import Flask, request, jsonify
import time
# Read the CSV file and specify the data types
df = pd.read_json('Products (1).json')
df = df.drop(['picture_url', 'brand_id', 'category_id'], axis=1)

# Initialize text-to-speech engine
engine = init()
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 35)  # Decrease the rate by 35 (adjust as needed)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

# Create a lock for the speak function
speak_lock = threading.Lock()

# Function to speak out text
def speak(text):
    with speak_lock:
        engine.say(text)
        engine.runAndWait()

# Function to decode QR code from image
def decode_qr_code(image):
    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Decode QR code
    decoded_objects = decode(gray)
    
    # If QR code is detected, return decoded data
    if decoded_objects:
        return decoded_objects[0].data.decode('utf-8')
    else:
        return None

# Flask app setup
app = Flask(__name__)

# Route to start QR code capture
@app.route('/start_capture', methods=['POST'])
def start_capture():
    thread = threading.Thread(target=capture_image) #<-----
    thread.start()
    return jsonify({"message": "QR code capture started"}), 200

# Capture image from webcam
def capture_image():
    scanned_products = set()
    scanned_products_file = 'scanned_products.csv' 
    detected_products = []
    selected_products = {}  # Change list to dictionary to store timestamp of last scan
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            cv2.imshow('QR Code Scanner', frame)
            qr_data = decode_qr_code(frame)
            if qr_data:
                current_time = time.time()
                
                # Check if the product was scanned recently (e.g., within the last 10 seconds)
                if qr_data not in selected_products or current_time - selected_products[qr_data] > 10:
                    if len(detected_products) == 10:
                        product_id = mode(detected_products)
                        # Check if the condition exists in the DataFrame
                        result = df[df['code'] == product_id]
                        if not result.empty:
                            product_info = result[['product_name', 'description', 'price', 'currency']]
                            # Convert product_info to text and speak it out
                            product_text = product_info.to_string(index=False, header=False)
                            speak(product_text)
                        selected_products[qr_data] = current_time  # Update the timestamp of the scan
                        detected_products = []
                        try:
                            with open(scanned_products_file, 'a', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow(product_text.split('\n'))  # Write each line separately
                        except IOError as e:
                            print(f"Error saving scanned product data: {e}")

                        # Add scanned product to the set
                        scanned_products.add(qr_data)
                    else:
                        detected_products.append(qr_data)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    cap.release()
    cv2.destroyAllWindows()

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True) 

