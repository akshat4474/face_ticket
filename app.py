import os
import subprocess
from flask import Flask, render_template, redirect, url_for, send_file, request, jsonify,after_this_request
from face_ticket_model import register_user, verify_user
import sqlite3
import base64
import cv2
import numpy as np
import tempfile

# Look at line 148,151,28 for file location mapping
app = Flask(__name__)

#Session Key
app.secret_key = os.urandom(24)

from flask import session

#Base64 to openCV image
def decode_base64_image(base64_image):
    image_data = base64.b64decode(base64_image.split(",")[1])
    np_image = np.frombuffer(image_data, dtype=np.uint8)
    return cv2.imdecode(np_image, cv2.IMREAD_COLOR)

# Homepage displaying the generated ticket.
@app.route('/')
def home():
    conn = sqlite3.connect('face_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, movie_title, show_time, date, seat_number, cinema_name, ticket_price, qr_code_image 
        FROM tickets
        ORDER BY id DESC LIMIT 1
    ''')
    ticket = cursor.fetchone()
    conn.close()

    if ticket:
        # Map ticket details to a dictionary
        ticket_keys = ['user_id', 'movie_title', 'show_time', 'date', 'seat_number', 'cinema_name', 'ticket_price', 'qr_code_image']
        ticket_data = dict(zip(ticket_keys, ticket))
    else:
        ticket_data = None  # No ticket found
        return render_template('register.html')

    return render_template('register.html')

# User registration and generates a ticket with a QR code.
@app.route('/register', methods=['POST'])
def register():
    image_data = request.json.get('image')  # Get base64 image from request
    if not image_data:
        return jsonify({"error": "No image provided for registration"}), 400

    # Decode the base64 image into an OpenCV image
    face_image = decode_base64_image(image_data)

    user_id = register_user(face_image)
    if user_id:
        session['user_id'] = user_id
        return jsonify({"message": "Registration successful!", "redirect_url": url_for('ticket', user_id=user_id)}), 200
    else:
        return jsonify({"error": "Registration failed."}), 500

# Dynamically render a ticket based on user_id passed as a query parameter.
@app.route('/ticket')
def ticket():
    user_id = request.args.get('user_id')
    if not user_id:
        return "User ID is required to view the ticket.", 400

    # Retrieve ticket details from the database
    conn = sqlite3.connect('face_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, movie_title, show_time, date, seat_number, cinema_name, ticket_price, qr_code_image, movie_image 
        FROM tickets WHERE user_id = ?
    ''', (user_id,))
    ticket = cursor.fetchone()
    conn.close()

    if not ticket:
        return "Ticket not found for the provided User ID.", 404

    # Map ticket details to a dictionary
    ticket_keys = ['user_id', 'movie_title', 'show_time', 'date', 'seat_number', 'cinema_name', 'ticket_price', 'qr_code_image', 'movie_image']
    ticket_data = dict(zip(ticket_keys, ticket))

    print("Ticket Data: ", ticket_data)  # Debugging statement to check ticket_data

    if not ticket_data.get('movie_image'):
        ticket_data['movie_image'] = 'img/default_movie_image.png'  # Set a default image

    return render_template('ticket.html', ticket=ticket_data)

# Starts the QR code scanning process using scanner.py.
    
@app.route('/start-scan')
def start_scan():
    try:
        # Run the scanner.py script to scan the QR code
        result = subprocess.run(['python', 'scanner.py'], capture_output=True, text=True)
        scanned_qr = result.stdout.strip()

        if scanned_qr:
            # Redirect to the verify page with the scanned user_id
            return redirect(url_for('verify', user_id=scanned_qr))
        else:
            return "No QR code detected. Please try again.", 404
    except Exception as e:
        print(f"Error while scanning QR code: {e}")
        return "Failed to scan QR code.", 500

# Serve the verify page to allow users to scan their face for verification.
@app.route('/verify')
def verify():
    return render_template('verify.html')


# Face Verification
@app.route('/verify-face', methods=['POST'])
def verify_face():
    user_id = request.json.get('user_id')
    image_data = request.json.get('image')

    if not user_id or not image_data:
        return jsonify({"error": "Invalid input provided."}), 400

    face_image = decode_base64_image(image_data)
    verified = verify_user(user_id, face_image)

    if verified:
        return jsonify({"message": f"Face verified successfully.\n Welcome {user_id}. \n Access granted!", "user_id": user_id}), 200
    else:
        # Clear any residual session data related to verification(Retention Issue)
        session.clear()
        return jsonify({"error": "Face verification failed. Access denied!"}), 403

# Generate a ticket image and serve it for download.
@app.route('/generate-tickets')
def generate_tickets():
    user_id = request.args.get('user_id')  # Get the user ID dynamically
    if not user_id:
        return "User ID is required to generate the ticket.", 400

    # Create the ticket image in a temporary location
    output_path = os.path.join(tempfile.gettempdir(), f'{user_id}_ticket.png')
    ticket_url = f'http://127.0.0.1:5000/ticket?user_id={user_id}' # Modify this this string to your actual URL(website_url/ticket?user_id={user_id)
    try:
        result = subprocess.run([
            r'C:\Program Files\wkhtmltox\bin\wkhtmltoimage.exe',# wkhtml requred for html to image, map this to your exe file
            '--width', '400',
            ticket_url, output_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("STDOUT:", result.stdout.decode())
        print("STDERR:", result.stderr.decode())
    except subprocess.CalledProcessError as e:
        print("Command failed with exit code:", e.returncode)
        print("Error:", e.stderr.decode())
        return "Error generating ticket image.", 500

    if not os.path.exists(output_path):
        print("Output file was not created.")
        return "Ticket image could not be created.", 500

    # Remove the ticket and QR code files after the response is sent
    @after_this_request
    def remove_files(response):
        try:
            os.remove(output_path)
            print(f"Deleted file: {output_path}")

            qr_code_path = os.path.join(tempfile.gettempdir(), f'{user_id}_qr.png')
            if os.path.exists(qr_code_path):
                os.remove(qr_code_path)
                print(f"Deleted QR code file: {qr_code_path}")
        except OSError as e:
            print(f"Error deleting file {output_path}: {e}")
        return response

    # Serve the ticket for download
    response = send_file(output_path, as_attachment=True)

    return response
# Serve the QR code from the temporary directory.
@app.route('/get-qr/<user_id>')
def get_qr(user_id):
    temp_dir = tempfile.gettempdir()
    qr_code_path = os.path.join(temp_dir, f'{user_id}_qr.png')

    if os.path.exists(qr_code_path):
        return send_file(qr_code_path, mimetype='image/png')
    else:
        return "QR code not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
