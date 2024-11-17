import cv2
import pyzbar.pyzbar as pyzbar

def scan_qr_code():
    # Initialize webcam
    cap = cv2.VideoCapture(0)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Failed to capture image")
            break

        # Detect QR codes in the frame
        decoded_objects = pyzbar.decode(frame)

        for obj in decoded_objects:
            qr_code_data = obj.data.decode('utf-8')
            print(f"QR Code detected: {qr_code_data}")

            # Save the scanned user ID to a temporary file
            with open('static/temp_user_id.txt', 'w') as file:
                file.write(qr_code_data)
            print("User ID saved for verification.")

            # Stop scanning once a QR code is found
            cap.release()
            cv2.destroyAllWindows()
            return

        # Display the frame
        cv2.imshow('QR Code Scanner', frame)

        # Stop scanning with 'q' key(for standalone execution)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_qr_code()
