import pathlib
if hasattr(pathlib, 'PosixPath'):
    pathlib.PosixPath = pathlib.WindowsPath

# Sopprime i FutureWarning di PyTorch relativi a utilizzo di cuda (non il nostro caso)
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


import cv2
import numpy as np
import socket
import torch

# Carico il modello YOLOv5, con i pesi addestrati con il nostro dataset

weights_path = 'runs/train/exp2_def/weights/last.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path)

# Imposto il modello in modalità di inferenza e disattiva i gradienti (non ci interessano in quanto non stiamo addestrando)
model.eval()
torch.set_grad_enabled(False)

# Video stream da porta 8080 del Raspberry Pi Zero 2 W 
url = "http://192.168.228.79:8080"
cap = cv2.VideoCapture(url)

# Utilizziamo il protocollo TCP con la libreria socket per lo scambio di messaggi su porta 5005
# tra PC e Raspberr, TCP è migliore di UDP perchè garantisce l'integrità e l'ordine dei messaggi
ip = "192.168.228.79"
port = 5005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)


while True:
    ret, frame = cap.read()
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if not ret:
        print("Stream non disponibile.")
        s.sendall(b"STOP_SERVER\n")
        break
    
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = model(img_rgb)
    yes = True
    
    for *box, conf, cls in results.xyxy[0]:
        class_name = model.names[int(cls)]
        yes = False    
        print("Classe rilevata:", class_name)
    
    if yes == True:    
        print("Nulla")
    
    
    cv2.imshow("YOLOv5 Stream", frame)
    
    # Comandi per inviare segnali al Raspberry 
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        s.sendall(b"STOP_SERVER\n")
        break
    elif key == ord('w'):
        s.sendall(b'GO\r\n')
        flag_stop = False
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")
    elif key == ord('s'):
        s.sendall(b'Stop Rilevato\r\n')
        flag_stop = True
        try:
            print("RPI→", s.recv(1024).decode().strip())
        except socket.timeout:
            print("Nessuna risposta, msg non ricevuto")