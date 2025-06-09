# sudo systemctl enable streamserver.service
# systemctl is-enabled streamserver.service

import cv2 
import numpy as np
import cv2
import socket

url = "http://192.168.14.79:8080"
cap = cv2.VideoCapture(url)

ip = "192.168.14.79"
port = 5005

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

flag_movimento = False

correzione_precedente = "Centro"
correzine_attuale = None


while True:
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    # 720 1280
    if not ret:
        print("Stream non disponibile.")
        s.sendall(b"STOP_SERVER\n")
        break
    
    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Converti in scala di grigi
    green = (0, 255, 0)
    rosso = (0, 0, 255)

    spessore_linea = 2
    spessore_tag = 10


    center_right = 1000
    threshold_intensità_colore = 100

    sx = 0
    dx = 0
    for i in range(550, 1280):
        intensita = img_gray[500, i]
        #print(f"Intensità: {intensita}")
        
        if intensita > 250 - threshold_intensità_colore:
            if i > sx and sx == 0:
                sx = i 
            cv2.line(frame, (i, 500), (i, 500), rosso, spessore_tag)
            #print(f"({i}, 450)")

        if img_gray[500, i-1] > 250 - threshold_intensità_colore and sx != 0:
            dx = i-1

#print("sx:", sx)
#print("dx:", dx)
    centro_tag = (sx + dx) / 2
    #print("centro_tag:", centro_tag)
    threshold_linea = 15

    intensita_svolta = 0

    # Range di Correzione
    #|  dx   |      c      |   sx    |
    # 850 900 950 1000 1050 1100 1150

    # da 120 a 25
    # 2 range di sterzata da 120 a 25 : [120, 95], [94, 25]
    #    
    if centro_tag >= 550 and centro_tag < 1000:
        correzine_attuale = "Sinistra"
    elif centro_tag >= 1000 and centro_tag <= 1090:
        correzine_attuale = "Centro"
    elif centro_tag > 1090 and centro_tag <= 1280:
        correzine_attuale = "Destra"
    else:
        correzine_attuale = "Centro"  # fallback se fuori range
    
    if flag_movimento:
        if correzione_precedente != correzine_attuale:
            correzione_precedente = correzine_attuale  # Aggiorna solo se è cambiata

            if correzine_attuale == "Sinistra":
                intensita_svolta = abs(centro_tag - center_right)
                print("Svolta a sinistra con intensità: ", intensita_svolta)
                s.sendall(b'Sinistra\r\n')

            elif correzine_attuale == "Destra":
                intensita_svolta = abs(center_right - centro_tag)
                print("Svolta a destra con intensità: ", intensita_svolta)
                s.sendall(b'Destra\r\n')

            elif correzine_attuale == "Centro":
                print("Dritto")
                s.sendall(b'GO\r\n')

   
    
    cv2.line(frame, (550, 500), (1280, 500), green, spessore_linea)
    cv2.line(frame, (1000, 550), (1090, 550), green, spessore_linea)
    
    
    cv2.imshow("YOLOv5 Stream", frame)
    

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('w'):
        s.sendall(b'GO\r\n')
        flag_movimento = True
        correzione_precedente = "Centro"
        correzine_attuale = None

        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('s'):
        s.sendall(b'Stop Rilevato\r\n')
        flag_movimento = False
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('a'):
        s.sendall(b'Sinistra\r\n')
        flag_movimento = True
        correzione_precedente = "Sinistra"
        correzine_attuale = "Sinistra"
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('d'):
        s.sendall(b'Destra\r\n')
        flag_movimento = True
        correzione_precedente = "Destra"
        correzine_attuale = "Destra"
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


