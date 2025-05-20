import cv2
import socket

url = "http://192.168.228.79:8080"
cap = cv2.VideoCapture(url)

ip = "192.168.228.79"
port = 5005

# Connessione TCP 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

while True:
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if not ret:
        print("Stream non disponibile.")
        s.sendall(b"STOP_SERVER\n")
        break
    cv2.imshow("RTSP Stream", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('w'):
        s.sendall(b'GO\r\n')
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('s'):
        s.sendall(b'STOP\r\n')
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
cap.release()
cv2.destroyAllWindows()
s.close()