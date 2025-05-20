import cv2
import socket 

#esp32_ip = '192.168.37.79'  # Sostituisci con l'indirizzo IP del tuo ESP32
#port = 12345

webcam = cv2.VideoCapture("http://192.168.37.79:8889/cam")


# Connessione TCP una volta sola
#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((esp32_ip, port))
#s.settimeout(0.2)

try:
    while True:
        ret, frame = webcam.read()
        if not ret:
            print("Frame non ricevuto, esco.")
            break

        cv2.imshow('Frame', frame)
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        #elif key == ord('w'):
            #s.sendall(b'GO\r\n')
            #try:
            #    print("ESP32→", s.recv(1024).decode().strip())
            #except socket.timeout:
            #    print("Nessuna risposta")
        #elif key == ord('s'):
        #    s.sendall(b'STOP\r\n')
        #    try:
        #        print("ESP32→", s.recv(1024).decode().strip())
        #    except socket.timeout:
        #        print("Nessuna risposta")
finally:
    #s.close()
    webcam.release()
    cv2.destroyAllWindows()