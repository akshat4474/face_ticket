import cv2
import numpy as np
import sqlite3
from deepface import DeepFace

def capture_image():
    cap = cv2.VideoCapture(0)
    print("Press 's' to capture the image.")

    while True:
        ret, frame = cap.read()
        cv2.imshow("Capture Image", frame)
        if cv2.waitKey(1) & 0xFF == ord('s'):
            captured_frame = frame
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured_frame

def extract_face_features(image):
    try:
        embedding = DeepFace.represent(image, model_name="Facenet", enforce_detection=True)[0]["embedding"]
        return np.array(embedding)
    except Exception as e:
        raise ValueError(f"Error extracting face features: {e}")

conn = sqlite3.connect('face_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS face_features (user_id TEXT PRIMARY KEY, features BLOB)''')

def store_face_features(user_id, features):
    features_binary = features.tobytes()
    c.execute("INSERT OR REPLACE INTO face_features (user_id, features) VALUES (?, ?)", 
              (user_id, features_binary))
    conn.commit()

def verify_face(user_id):
    c.execute("SELECT features FROM face_features WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    if not result:
        return "User ID not found"

    stored_features = np.frombuffer(result[0], dtype=np.float64)
    print("Capture an image for verification.")
    live_image = capture_image()
    live_features = extract_face_features(live_image)
    similarity = 1 - np.dot(stored_features, live_features) / (
        np.linalg.norm(stored_features) * np.linalg.norm(live_features)
    )

    if similarity < 0.4:  # Adjust threshold as needed
        return "Verification successful"
    else:
        return "Verification failed"

def main():
    print("1. Register")
    print("2. Verify")
    choice = input("Choose an option: ")

    if choice == '1':
        user_id = input("Enter unique ID: ")
        print("Capture an image for registration.")
        captured_image = capture_image()
        features = extract_face_features(captured_image)
        store_face_features(user_id, features)
        print("Registration successful!")
    elif choice == '2':
        user_id = input("Enter unique ID: ")
        result = verify_face(user_id)
        print(result)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
