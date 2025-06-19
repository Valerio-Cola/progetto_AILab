# Necessario per problemi di compatibilità tra le directory:
#   Il modello è stato addestrato su sistema Linux (CoLab Nvidia T4) ed utilizza formati directory Linux
#   Il codice di inferenza gira su Windows e in questo modo è possibile unificare i percorsi
#   senza dover modificare il codice di addestramento
import pathlib
if hasattr(pathlib, 'PosixPath'):
    pathlib.PosixPath = pathlib.WindowsPath

# Sopprime i FutureWarning di PyTorch relativi a utilizzo di cuda (non il nostro caso)
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Imposta il numero di thread fisici che PyTorch può utilizzare  
import torch 
torch.set_num_threads(8)
import os
os.environ["OMP_NUM_THREADS"] = "8"
os.environ["MKL_NUM_THREADS"] = "8"

import cv2
import socket
import threading
import time
import sys

# Carico il modello YOLOv5, con i pesi addestrati con il nostro dataset
weights_path = 'YOLOV5_Addestrato/V3/weights/last.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path)

# Imposto il modello in modalità di inferenza e disattiva i gradienti (non ci interessano in quanto non stiamo addestrando)
model.eval()
torch.set_grad_enabled(False)



# Utilizziamo il protocollo TCP con la libreria socket per lo scambio di messaggi su porta 5005
# tra PC e Raspberr, TCP è migliore di UDP perchè garantisce l'integrità e l'ordine dei messaggi
ip = sys.argv[1]
#ip = "192.168.160.79"
port = 5005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

# Video stream da porta 8080 del Raspberry Pi Zero 2 W 
url = f"http://{ip}:8080"
#url = "http://192.168.160.79:8080"
cap = cv2.VideoCapture(url)

# Variabili condivise
# Flag di controllo, quando il thread principale termina verrà impostata a True
# di conseguenza gli altri 2 thread usciranno dai propri while loop terminando 
stop_threads = False

# Variabile per il frame più recente
latest_frame = None

# Variabile per le classi rilevate
detections = []

classes = ['Pedestrians', 'green_light', 'red_light', 'speed_limit_20', 'speed_limit_50', 'stop']

prev_objects = None
counter_persistance = 20
counter_stop = -1
flag_pedestrian = False

# Flag per segnale di stop
flag_start = False

# Lock per evitare conflitti di accesso alle variabili condivise
lock = threading.Lock()

flag_stop = False

import math
fov_deg = 50
fov_rad = math.radians(fov_deg)
width_px = 1280
focal_length_px = (width_px * 0.5) / math.tan(fov_rad * 0.5)
# Altezza reale dell'oggetto in cm, utilizzata per calcolare la distanza
H_real = None

# Variabili per la correzione della traiettoria, necessarie per evitare 
# uno spam inutile di comandi equivalenti
correzione_precedente = "Centro"
correzine_attuale = None

# Primo thread si occuperà di leggere lo stream video (frame) 
def frame_reader():
    global latest_frame, stop_threads

    # Se il thread principale non ha terminato
    while not stop_threads:
        ret, frame = cap.read()
        if not ret:
            print("Stream non disponibile.")
            try:
                s.sendall(b"STOP_SERVER\n")
            except:
                pass
            stop_threads = True
            break
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # Imposto il lock per evitare conflitti di accesso alla variabile latest_frame
        with lock:
            latest_frame = frame
        time.sleep(0.01)  

# Secondo thread si occuperà di eseguire l'inferenza di YOLOv5 e salvare le classi rilevate
def detection_worker():
    global detections, stop_threads

    # Se il thread principale non ha terminato
    while not stop_threads:
        
        # Prendiamo il frame più recente
        with lock:
            # Se latest_frame è None, vuol dire che frame_reader ha inviato il segnale di terminazione
            # e quindi non possiamo continuare
            if latest_frame is None:
                continue
            # Se no prende il frame
            frame = latest_frame.copy()
        
        # Convertiamo il frame da BGR a RGB per YOLOv5
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Inferenza per cercare le classi
        results = model(img_rgb)

        # Memorizziamo le classi rilevate
        local_detections = []
        best_obj = -1
        best_conf = 0
        for idx, (x1, y1, x2, y2, conf, cls) in enumerate(results.xyxy[0]):
            confidence = float(conf)  
            if confidence > best_conf and confidence > 0.2:
                best_obj = idx
                best_conf = confidence

        if best_obj != -1:
            x1, y1, x2, y2, conf, cls = results.xyxy[0][best_obj]
            local_detections.append((x1, y1, x2, y2, model.names[int(cls)], float(conf)))

        # Impone il lock per evitare conflitti di accesso alla variabile detections
        with lock:
            detections = local_detections
        time.sleep(0.05)

# Avvio dei thread
t1 = threading.Thread(target=frame_reader)
t2 = threading.Thread(target=detection_worker)
t1.start()
t2.start()

while True:
    
    # Appena il lock di entrambi i thread si liberano il thread principale esegue il lock
    # e copia le variabili latest_frame e detections in modo da poterci lavorare in modo autonomo
    # e non introdurre overhead
    with lock:
        # Copiamo il frame appena elaborato da frame_reader
        if latest_frame is not None:
            frame = latest_frame.copy()
        else:
            # Se latest_frame è None, vuol dire che frame_reader ha inviato il segnale di terminazione
            # e quindi non possiamo continuare
            frame = None
               
        # Copiamo le detections appena elaborate da detection_worker
        current_detections = detections.copy()

    # Se il frame è quindi stato elaborato eseguiamo lane detection e invio comandi al Raspberry
    if frame is not None:
        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Converti in scala di grigi
        green = (0, 255, 0)
        rosso = (0, 0, 255)

        spessore_linea = 2
        # Tag rosso disegnato sulla linea di corsia individuata
        spessore_tag = 10


        center_right = 1000
        threshold_intensità_colore = 80

        sx = 0
        dx = 0
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
        
        # Definizione dei range di correzione
        if centro_tag >= 550 and centro_tag < 1000:
            correzine_attuale = "Sinistra"
        elif centro_tag >= 1000 and centro_tag <= 1090:
            correzine_attuale = "Centro"
        elif centro_tag > 1090 and centro_tag <= 1280:
            correzine_attuale = "Destra"
        else:
            correzine_attuale = correzione_precedente  # fallback se fuori range

        intensita_svolta = 0
        cv2.putText(frame, f"Direzione: {correzine_attuale}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, green, 2)
        
        # Controllo se il veicolo è in movimento
        if flag_start:
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
        cv2.line(frame, (550, 500), (1280, 500), green, spessore_linea)
        
        # Linea di riferimento, la linea di corsia si deve sovrapporre ad essa
        cv2.line(frame, (1000, 510), (1090, 510), (255,255,255), 2)

        # Se è stato rilevato un oggetto
        if counter_stop > 0:
            counter_stop -= 1
            print("Contatore stop:", counter_stop)
        elif counter_stop == 0:
            counter_stop = -1
            flag_start = True
            correzine_attuale = None
            correzione_precedente = "Centro"
            s.sendall(b'Max 20\r\n')
            try:
                print("RPI→", s.recv(1024).decode().strip())
            except socket.timeout:
                print("Nessuna risposta, msg non ricevuto")


        if current_detections and counter_stop == -1:

            
            x1,y1,x2,y2, actual_class, confidence = current_detections[0]
           
            height_pixel = y2 - y1
            if actual_class == "Pedestrians":
                H_real = 7.5
            elif actual_class == "red_light" or actual_class == "green_light":
                H_real = 3.5
            else:
                H_real = 5
            distance_cm = (H_real * focal_length_px) / height_pixel

            # Controllo se la classe è cambiata rispetto alla precedente
            # Se la classe è cambiata resetto il contatore di persistenza
            if actual_class != prev_objects:
                counter_persistance = 100
                print("Classe rilevata:", actual_class, "Confidenza:", confidence)
                prev_objects = actual_class
            
            # Se la classe è una di quelle che ci interessano e la distanza è entro i limiti di tolleranza invia i comandi
            if(actual_class == 'stop' and flag_start == True and distance_cm < 35 and distance_cm > 30):
                s.sendall(b'Stop Rilevato\r\n') 
                flag_start = False
                counter_stop = 1000
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")

            elif(actual_class == "Pedestrians" and flag_start == True and distance_cm < 25 and distance_cm > 20):
                s.sendall(b'Pedone Rilevato\r\n')
                flag_pedestrian = True
                flag_start = False
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")

            elif(actual_class == "speed_limit_20" and flag_start == True and distance_cm < 35 and distance_cm > 30):
                s.sendall(b'Max 20\r\n')
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")
            elif(actual_class == "speed_limit_50" and flag_start == True and distance_cm < 35 and distance_cm > 30):
                s.sendall(b'Max 50\r\n')
                try:
                    print("RPI 2→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")
            elif(actual_class == "green_light" and distance_cm < 33 and distance_cm > 10):   
                flag_start = True
                correzine_attuale = None 
                correzione_precedente = "Centro"
                s.sendall(b'Semaforo Verde\r\n')
                try: 
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:         
                    print("Nessuna risposta, msg non ricevuto")
            elif(actual_class == "red_light" and flag_start == True and distance_cm < 40 and distance_cm > 32):
                flag_start = False 
                s.sendall(b'Semaforo Rosso\r\n')
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")
    
            
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f"{actual_class} {confidence:.2f} {distance_cm:.2f} ", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        #Faccio un check per evitare falsi
        # Se non è stata rilevata alcuna classe decremento il timer di tolleranza, altrimenti resetto il timer e segna l'effettiva assenza di classi    
        else:
            counter_persistance -= 1
            if prev_objects is not None and counter_persistance == 0:
                print("Nessuna classe rilevata")
                prev_objects = None
                if flag_pedestrian:
                    flag_pedestrian = False
                    flag_start = True
                    correzine_attuale = None
                    correzione_precedente = "Centro"
                    s.sendall(b'GO\r\n')
                    try:
                        print("RPI→", s.recv(1024).decode().strip())
                    except socket.timeout:
                        print("Nessuna risposta, msg non ricevuto")


                

        cv2.imshow("YOLOv5 Stream", frame)

    # Comandi di debug per inviare segnali al Raspberry da tastiera 
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        s.sendall(b"STOP_SERVER\n")
        break
    elif key == ord('w'):
        flag_start = True
        correzine_attuale = None
        correzione_precedente = "Centro"
        s.sendall(b'GO\r\n')
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('s'):
        flag_start = False
        s.sendall(b'Stop Rilevato\r\n')
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

# Imposto il flag di stop per terminare i thread
# e attende che terminino
stop_threads = True
t1.join()
t2.join()
cap.release()
cv2.destroyAllWindows()
s.close()