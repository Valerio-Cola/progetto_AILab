# Necessario per problemi di compatibilità tra le directory:
#   Il modello è stato addestrato su sistema Linux (CoLab Nvidia T4) ed utilizza formati directory Linux
#   Il codice di inferenza gira su Windows e in questo modo è possibile unificare i percorsi
#   senza dover modificare il codice di addestramento
import pathlib
if hasattr(pathlib, 'PosixPath'):
    pathlib.PosixPath = pathlib.WindowsPath

import cv2
import torch

# Percorso al file dei pesi allenati (assicurarsi che il file sia presente in questa directory)
model_path = "YOLOV5_Addestrato/V2/weights/best.pt"

# Carica il modello YOLOv5 custom utilizzando i pesi specificati
model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path)

# Avvia il flusso video dalla webcam (modifica l'indice se hai più di una videocamera)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Errore nell'apertura dello stream video")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Errore nella lettura del frame")
        break

    # Esegui la rilevazione su ogni frame
    results = model(frame)

    # Renderizza i risultati sul frame (aggiunge i riquadri e le etichette)
    annotated_frame = results.render()[0]

    cv2.imshow("Detezzione YOLOv5", annotated_frame)

    # Premi 'q' per uscire
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()