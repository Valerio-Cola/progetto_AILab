import cv2 
import cv2
import socket

# Imposta l'URL dello streaming e la porta per la connessione TCP
url = "http://192.168.14.79:8080"
cap = cv2.VideoCapture(url)
ip = "192.168.14.79"
port = 5005

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

# Flag per non far ripartire il veicolo se è stato inviato  il comando di stop
flag_movimento = False

# Variabili per la correzione della traiettoria, necessarie per evitare 
# uno spam inutile di comandi equivalenti
correzione_precedente = "Centro"
correzine_attuale = None

#print(img.shape[1], img.shape[0], img.shape[2], img.size) 
# 960 720 3 2073600

while True:
    # Lettura del frame dalla videocamera
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if not ret:
        print("Stream non disponibile.")
        s.sendall(b"STOP_SERVER\n")
        break
    
    # Conversione in scala di grigi
    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
    
    green = (0, 255, 0)
    rosso = (0, 0, 255)
    bianco = (255, 255, 255)

    # Tag rosso disegnato sulla linea di corsia individuata 
    spessore_tag = 10

    center_right = 1000

    # Definiamo un threshold per l'intensità del colore, poichè non può esssere bianco assoluto
    threshold_intensità_colore = 100
    
    sx = 0
    dx = 0
    # Analizziamo una riga di pixel per trovare la linea di corsia e le sue coordinate
    for i in range(550, 1280):
        intensita = img_gray[500, i]
        #print(f"Intensità: {intensita}")
        
        if intensita > 250 - threshold_intensità_colore:
            if i > sx and sx == 0:
                sx = i 
            cv2.line(frame, (i, 500), (i, 500), rosso, spessore_tag)

        if img_gray[500, i-1] > 250 - threshold_intensità_colore and sx != 0:
            dx = i-1

    centro_tag = (sx + dx) / 2


    # Range di Correzione
    #|  dx   |      c      |   sx    |
    #550 900 1000 1050  1090 1150  1280

    # Definizione dei range di correzione
    if centro_tag >= 550 and centro_tag < 1000:
        correzine_attuale = "Sinistra"
    elif centro_tag >= 1000 and centro_tag <= 1090:
        correzine_attuale = "Centro"
    elif centro_tag > 1090 and centro_tag <= 1280:
        correzine_attuale = "Destra"
    else:
        correzine_attuale = correzione_precedente
    

    # Se la correzione attuale è diversa da quella precedente, invia il comando
    # e aggiorna la variabile di correzione precedente
    intensita_svolta = 0
    cv2.putText(frame, f"Direzione: {correzine_attuale}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, green, 2)
    
    # Controllo se il veicolo è in movimento
    if flag_movimento:
        # Invia il comando di correzione solo se la direzione è cambiata
        if correzione_precedente != correzine_attuale:
            correzione_precedente = correzine_attuale 

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

    # Linea analizzata da OpenCV
    cv2.line(frame, (550, 500), (1280, 500), green, 2)
    
    # Linea di riferimento, la linea di corsia si deve sovrapporre ad essa
    cv2.line(frame, (1000, 510), (1090, 510), bianco, 2)
    
    
    cv2.imshow("YOLOv5 Stream", frame)
    

    # Debug da tastiera
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    
    # Comando per avviare il veicolo
    elif key == ord('w'):
        s.sendall(b'GO\r\n')
        flag_movimento = True
        correzione_precedente = "Centro"
        correzine_attuale = None
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    
    # Comando per fermare il veicolo
    elif key == ord('s'):
        s.sendall(b'Stop Rilevato\r\n')
        flag_movimento = False
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    
    # Comandi per la sterzata del veicolo
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
