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

# Carico il modello YOLOv5, con i pesi addestrati con il nostro dataset
weights_path = 'YOLOV5_Addestrato/V3/weights/last.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path)

# Imposto il modello in modalità di inferenza e disattiva i gradienti (non ci interessano in quanto non stiamo addestrando)
model.eval()
torch.set_grad_enabled(False)

# Video stream da porta 8080 del Raspberry Pi Zero 2W 
url = "http://192.168.14.79:8080"
cap = cv2.VideoCapture(url)

# Utilizziamo il protocollo TCP con la libreria socket per lo scambio di messaggi su porta 5005
# tra PC e Raspberr, TCP è migliore di UDP perchè garantisce l'integrità e l'ordine dei messaggi
ip = "192.168.14.79"
port = 5005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

# Variabili condivise
# Flag di controllo, quando il thread principale termina verrà impostata a True
# di conseguenza gli altri 2 thread usciranno dai propri while loop terminando 
stop_threads = False

# Variabile per il frame più recente
latest_frame = None

# Variabile per le classi rilevate
detections = []

classes = ['Pedestrians', 'green_light', 'ped_crossing', 'red_light', 'speed_limit_20', 'speed_limit_50', 'stop']

prev_objects = None
counter_persistance = 20

# Flag per segnale di stop
flag_start = False

# Lock per evitare conflitti di accesso alle variabili condivise
lock = threading.Lock()

import math
fov_deg = 62.2
fov_rad = math.radians(fov_deg)
width_px = 960
focal_length_px = (width_px * 0.5) / math.tan(fov_rad * 0.5)
H_real = 7

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

        # Memorizziamo la classe che ha la confidenza più alta
        local_detections = []
        best_obj = -1
        best_conf = 0
        for idx, (x1, y1, x2, y2, conf, cls) in enumerate(results.xyxy[0]):
            confidence = float(conf)  
            if confidence > best_conf and confidence > 0.4:
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

    # Se il frame è quindi stato elaborato ed è stato rilevato un oggetto
    if frame is not None:
        # Se è stato rilevato un oggetto
        if current_detections:

            x1,y1,x2,y2, actual_class, confidence = current_detections[0]
           
            height_pixel = y2 - y1
            distance_cm = (H_real * focal_length_px) / height_pixel
            cv2.putText(frame, f"Distanza: {distance_cm:.2f} cm", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Controllo se la classe è cambiata rispetto alla precedente
            # Se la classe è cambiata resetto il contatore di persistenza
            if actual_class != prev_objects:
                counter_persistance = 30
                print("Classe rilevata:", actual_class, "Confidenza:", confidence)
                prev_objects = actual_class
            
            # Se la classe è una di quelle che ci interessano e la distanza è entro i limiti di tolleranza invia i comandi
            if((actual_class == 'stop' or actual_class == "Pedestrians" or actual_class == "red_light") and flag_start == True and distance_cm < 20 and distance_cm > 16):
                s.sendall(b'Stop Rilevato\r\n') 
                flag_start = False
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")
            elif(actual_class == "speed_limit_20" and flag_start == True and distance_cm < 29 and distance_cm > 16):
                s.sendall(b'Max 20\r\n')
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")
            elif(actual_class == "speed_limit_50" and flag_start == True and distance_cm < 29 and distance_cm > 19):
                s.sendall(b'Max 50\r\n')
                try:
                    print("RPI 2→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")
            elif(actual_class == "green_light" and flag_start == True and distance_cm < 23 and distance_cm > 19):
                s.sendall(b'Semaforo Verde\n')
                try:
                    print("RPI→", s.recv(1024).decode().strip())
                except socket.timeout:
                    print("Nessuna risposta, msg non ricevuto")

            
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f"{actual_class} {confidence:.2f}", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        #Faccio un check per evitare falsi
        # Se non è stata rilevata alcuna classe decremento il timer di tolleranza, altrimenti resetto il timer e segna l'effettiva assenza di classi    
        else:
            counter_persistance -= 1
            if prev_objects is not None and counter_persistance == 0:
                print("Nessuna classe rilevata")
                prev_objects = None

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

# Imposto il flag di stop per terminare i thread
# e attende che terminino
stop_threads = True
t1.join()
t2.join()
cap.release()
cv2.destroyAllWindows()
s.close()
