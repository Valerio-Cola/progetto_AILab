# sudo systemctl enable streamserver.service
# systemctl is-enabled streamserver.service


import cv2 
import numpy as np
import cv2
import socket

url = "http://192.168.228.79:8080"
cap = cv2.VideoCapture(url)

ip = "192.168.228.79"
port = 5005

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

flag_stop = False

while True:
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if not ret:
        print("Stream non disponibile.")
        s.sendall(b"STOP_SERVER\n")
        break
    
    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Converti in scala di grigi
    green = (0, 255, 0)
    rosso = (0, 0, 255)

    spessore_linea = 2
    spessore_tag = 10


    center_right = (900 + 700) /2 # 800 XD
    threshold_intensità = 50

    sx = 0
    dx = 0
    for i in range(700, 900):
        intensita = img_gray[450, i]

        if intensita > 250 - threshold_intensità:
            if i > sx and sx == 0:
                sx = i 
            cv2.line(frame, (i, 450), (i, 450), rosso, spessore_tag)
            #print(f"({i}, 450)")

        if img_gray[450, i-1] > 250 - threshold_intensità and sx != 0:
            dx = i-1

#print("sx:", sx)
#print("dx:", dx)
    centro_tag = (sx + dx) / 2
    threshold_linea = 15

    intensita_svolta = 0

    if flag_stop:
        if centro_tag - threshold_linea > center_right:
            intensita_svolta = centro_tag - center_right
            print("Svolta a sinistra con intensità: ", intensita_svolta)
            s.sendall(b'Sinistra\r\n')
            try:
                print("RPI→", s.recv(1024).decode().strip())
            except socket.timeout:
                print("Nessuna risposta, msg non ricevuto")

        elif centro_tag + threshold_linea < center_right:
            intensita_svolta = center_right - centro_tag
            print("Svolta a destra con intensità: ", intensita_svolta)
            s.sendall(b'Destra\r\n')
            try:
                print("RPI→", s.recv(1024).decode().strip())
            except socket.timeout:
                print("Nessuna risposta, msg non ricevuto")
        else:
            print("Dritto")
    #cv2.line(frame, (100, 450), (300,450), green, spessore_linea)
    cv2.line(frame, (700, 450), (900, 450), green, spessore_linea)
    
    
    
    cv2.imshow("YOLOv5 Stream", frame)
    

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('w'):
        s.sendall(b'GO\r\n')
        #s.sendall(b'Semaforo verde\r\n')
        flag_stop = False
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('s'):
        s.sendall(b'Stop Rilevato\r\n')
        #s.sendall(b'Pedone rilevato\r\n')
        #s.sendall(b'Semaforo rosso\r\n')
        flag_stop = True
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")

cap.release()
cv2.destroyAllWindows()
s.close()

#print(img.shape[1], img.shape[0], img.shape[2], img.size) 
# 960 720 3 2073600

#blu = img[450, i, 0]
#verde = img[450, i, 1]
#rosso = img[450, i, 2]

#print(f"Pixel ({i}, {450} - B: {blu}, G: {verde}, R: {rosso})")


