from flask import Flask, request
import requests
from pyzbar.pyzbar import decode
import pyttsx3
import base64
app = Flask(__name__)

def send_to_api(code):
    url = f"https://802b-197-53-109-195.ngrok-free.app/api/Product/{code}"
    response = requests.get(url)
    return response

def decode_qr_code_string(qr_data_string):  # Handles string input instead of image processing
    if isinstance(qr_data_string, str):  # Check if qr_data is a string
        decoded_data = base64.b64decode(qr_data_string ,validate=False).decode('utf-8')
    else:
        return None

def speak(text):
    engine = pyttsx3.init()

    # Adjust voice properties as desired
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 35)  # Decrease speaking rate by 35 (adjust as needed)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # Set voice to second voice (adjust index)

    engine.say(text)
    engine.runAndWait()

@app.route('/process_qr', methods=['POST'])
def process_qr():
    qr_data = request.form.get('qr_data')
    decoded_data = decode_qr_code_string(qr_data)  # Process the received QR code data

    if decoded_data:
        # Send QR code data to your API (assuming data is a string)
        response = send_to_api(decoded_data)
        if response.status_code == 200:
            data = response.json()

            # Extract product information from API response (assuming structure)
            product_name = data.get('product_name')
            description = data.get('description')
            price = data.get('price')
            currency = data.get('currency')

            # Construct product information text for TTS
            product_text = f"Product Name: {product_name}\nDescription: {description}\nPrice: {price} {currency}"

            # Speak the product information
            speak(product_text)
            return "QR code processed successfully!", 200
        else:
            print(f"Error: {response.status_code}")
            return "Error processing QR code", 500
    else:
        return "Invalid QR code data", 400

if __name__ == '__main__':
    app.run(debug=True)
