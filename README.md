# Face Recognition System with DeepFace and SQLite

This repository implements a face recognition system using **DeepFace** for embedding generation and **SQLite** for data storage. The system supports face registration and verification with real-time webcam input and a circular guide for alignment.

## Features
- **Face Registration**: Captures a face using a webcam, generates embeddings with DeepFace, and stores them in an SQLite database.
- **Face Verification**: Matches a captured face against stored embeddings to verify identity.
- **Embedding Storage**: Uses SQLite to store face embeddings as binary blobs.

## Prerequisites, Packages and Dependencies 
- Python 3.x
- Webcam-enabled system
- TensorFlow-compatible CPU (optional: GPU for better performance)
- pyzbar: For QR code scanning.
- qrcode: To generate QR codes for each user.
- SQLite3: The database used to store user embeddings and ticket details.
- OpenCV (cv2): Used for image processing and face detection.
- Flask: For creating the web application.
- wkhtmltoimage : To generate images from HTML templates.(Download From website)
- numpy: For numerical computations.
- tempfile: for temporary storage

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/akshat4474/face_ticket.git
   ```

2. Install required dependencies:
   ```bash
   pip install opencv-python deepface numpy sqlite3 pyzbar qrcode Flask tempfile
   ```

3. Ensure `haarcascade_frontalface_default.xml` is available in OpenCV's data directory.

## Usage

### 1. Initialize the Database
Run the script to initialize the SQLite database. This will create a `users` table for storing face embeddings and user IDs.
```python
initialize_database()
```

### 2. Register a User
To register a new user:
```python
register_user()
```
- Click on capture face button to capture a face image
- If registration is successful, a unique `user_id` will be displayed. Save this ID for future verification.

### 3. Verify a User
To verify a registered user:
```python
verify_user(user_id)
```
- Scan the QR code generated for the user for user id.
- Press **Space** to capture and verify your face.
- The system will check the similarity between the captured face and the stored embedding.

## How It Works
### 1. Registration
- Captures the user's face using OpenCV.
- Generates a unique `user_id`.
- Uses DeepFace to extract a 128-dimensional embedding from the face.
- Saves the `user_id` and the embedding in SQLite.

### 2. Ticket Generation
- Uses the `user_id` to generate a qr code
- Attaches the qr code to the ticket format
- Ticket download option is provided for the user
- Verify ticket option

### 3. Verification
- Captures a face using OpenCV.
- Uses DeepFace to extract a new embedding.
- Retrieves the stored embedding for the given `user_id` from SQLite.
- Compares the embeddings using **cosine similarity**.
- Outputs whether the face matches the stored embedding based on a similarity threshold (default: 0.8).

## Code Structure
- `initialize_database()`: Creates the SQLite database and the `users` table.
- `save_to_database(user_id, embedding)`: Stores user data in the database.
- `capture_face_image()`: Captures a face image using the webcam with a circular alignment guide.
- `register_user()`: Handles face registration and saves embeddings.
- `retrieve_from_database(user_id)`: Retrieves stored embeddings for a user.
- `cosine_similarity(embedding1, embedding2)`: Calculates the similarity between two embeddings.
- `verify_user(user_id)`: Verifies a captured face against stored embeddings.


## Troubleshooting
1. **Face Not Detected**: Ensure proper lighting and that your face is fully visible within the camera frame.
2. **Multiple Faces Detected**: Ensure only one person is visible during registration or verification.
3. **DeepFace Errors**: Check TensorFlow installation and compatibility.
4. **Database Issues**: Ensure `face_data.db` is writable and located in the current directory.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- **OpenCV (cv2)**: Used for image processing and face detection.
- **DeepFace**: Employed for facial recognition.
- **NumPy**: Used for numerical operations, including managing face embeddings.
- **SQLite3**: The database used to store user embeddings and ticket details.
- **Flask**: A lightweight web framework for creating the web application.
- **Pyzbar**: Utilized for QR code scanning.
- **qrcode**: To generate QR codes for user verification.
- **wkhtmltopdf / wkhtmltoimage**: This utility is used to generate the ticket images from HTML templates, making our tickets visually rich and customizable.

---
Feel free to contribute to this project by submitting pull requests or reporting issues!

