import pathlib
if hasattr(pathlib, 'PosixPath'):
    pathlib.PosixPath = pathlib.WindowsPath

import torch
import cv2

# Percorso ai pesi
weights_path = 'Progetto/yolov5/runs/train/exp4/exp4/weights/last.pt'

# Carica il modello YOLOv5 personalizzato
model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, force_reload=True)

# Carica la webcam o uno stream video
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream non disponibile.")
        break

    # Converte da BGR a RGB per YOLO
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Esegue inferenza
    results = model(img_rgb)

    # Disegna i bounding box direttamente sul frame
    results.render()  # modifica i tensori delle immagini internamente

    # Mostra l'immagine con bounding box in OpenCV (usa BGR)
    rendered_frame = results.ims[0]  # è un array numpy in BGR
    cv2.imshow("RGB View", cv2.cvtColor(rendered_frame, cv2.COLOR_BGR2RGB))


    # Esci col tasto 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera risorse
cap.release()
cv2.destroyAllWindows()
