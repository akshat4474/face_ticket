import os
import cv2
import uuid
import sqlite3
import numpy as np
from deepface import DeepFace
import qrcode
import tempfile

# Database Initialization
def initialize_database():
    conn = sqlite3.connect('face_data.db')
    cursor = conn.cursor()

    # User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            embedding BLOB NOT NULL
        )
    ''')

    # Tickets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            movie_title TEXT,
            show_time TEXT,
            date TEXT,
            seat_number TEXT,
            cinema_name TEXT,
            ticket_price REAL,
            qr_code_image TEXT,
            movie_image TEXT
        )
    ''')

    conn.commit()
    conn.close()

initialize_database()

# Save user data to the database
def save_to_database(user_id, embedding):
    conn = sqlite3.connect('face_data.db')
    cursor = conn.cursor()

    embedding_blob = np.array(embedding).tobytes()

    cursor.execute('''
        INSERT INTO users (user_id, embedding) VALUES (?, ?)
    ''', (user_id, embedding_blob))

    conn.commit()
    conn.close()

# QR code generator
def generate_qr_code(user_id):
    # temp dir for the QR code
    temp_dir = tempfile.gettempdir()
    qr_code_path = os.path.join(temp_dir, f'{user_id}_qr.png')

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(user_id) 
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_code_path)

    return qr_code_path

# Ticket Details
def save_ticket_to_database(user_id, qr_code_path):
    # Modify Data according to preferences
    ticket_data = {
        'movie_title': 'Venom',
        'show_time': '7:00 PM',
        'date': '2024-11-02',
        'seat_number': 'A12',
        'cinema_name': 'Cinema 1',
        'ticket_price': 12.50,
        'qr_code_image': qr_code_path,
        'movie_image': 'img/WKM35WF.jpg'  # for image on ticket
    }

    conn = sqlite3.connect('face_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO tickets (user_id, movie_title, show_time, date, seat_number, cinema_name, ticket_price, qr_code_image, movie_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, ticket_data['movie_title'], ticket_data['show_time'], ticket_data['date'],
          ticket_data['seat_number'], ticket_data['cinema_name'], ticket_data['ticket_price'], qr_code_path, ticket_data['movie_image']))

    conn.commit()
    conn.close()

    return ticket_data

# Face Capture, Standalone file uses cicrular detection but integrated uses standard
def capture_face_image():
    cap = cv2.VideoCapture(0)
    face_detected = False
    color = (0, 0, 255)  # Default color (Red)

    while True:
        ret, frame = cap.read()
        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2
        radius = 150

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        # Check if face is inside the circle
        face_detected = False
        for (x, y, w, h) in faces:
            face_center = (x + w // 2, y + h // 2)
            distance_to_center = ((face_center[0] - center_x) ** 2 + (face_center[1] - center_y) ** 2) ** 0.5
            if distance_to_center < radius:
                face_detected = True
                break

        # Change circle color based on detection
        color = (0, 255, 0) if face_detected else (0, 0, 255)

        # Circle
        cv2.circle(frame, (center_x, center_y), radius, color, 2)
        cv2.putText(frame, "Align your face inside the circle", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Show the frame
        cv2.imshow('Capture - Press Space to Capture', frame)

        # Capture on Space key
        if face_detected and cv2.waitKey(1) & 0xFF == ord(' '):
            cap.release()
            cv2.destroyAllWindows()
            return frame

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return None

# User registration
def register_user(face_image):
    if face_image is None:
        print("Registration cancelled.")
        return None

    user_id = str(uuid.uuid4())
    try:
        result = DeepFace.represent(face_image, model_name="Facenet")
        if isinstance(result, list) and len(result) > 0:
            embedding = result[0]['embedding']
            save_to_database(user_id, embedding)

            # Generate QR Code
            qr_code_path = generate_qr_code(user_id)

            # Save ticket details
            save_ticket_to_database(user_id, qr_code_path)

            print(f"Registration Successful! Your User ID: {user_id}")
            return user_id
        else:
            print("No face embedding could be extracted.")
            return None
    except Exception as e:
        print(f"Error during registration: {e}")
        return None

# Retrieve user data from the database
def retrieve_from_database(user_id):
    conn = sqlite3.connect('face_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT embedding FROM users WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return np.frombuffer(result[0], dtype=np.float64)
    return None

# Cosine similarity function
def cosine_similarity(embedding1, embedding2):
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    return dot_product / (norm1 * norm2)

# Verify user
def verify_user(user_id, face_image):
    if face_image is None:
        print("Verification cancelled.")
        return False

    try:
        result = DeepFace.represent(face_image, model_name="Facenet")
        if isinstance(result, list) and len(result) > 0:
            new_embedding = result[0]['embedding']
        else:
            print("No face embedding could be extracted.")
            return False

        stored_embedding = retrieve_from_database(user_id)

        if stored_embedding is None:
            print("User ID not found in the database.")
            return False

        similarity = cosine_similarity(stored_embedding, new_embedding)
        return similarity >= 0.8 # Adjust the threshold as needed
    except Exception as e:
        print(f"Error during verification: {e}")
        return False
