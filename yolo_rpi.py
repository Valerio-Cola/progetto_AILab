import cv2
import numpy as np
import socket

# === Impostazioni ===
url = "http://192.168.228.79:8080"
ip = "192.168.228.79"
port = 5005
onnx_path = "runs/train/exp/weights/last.onnx"

# === Carica modello YOLOv5 ONNX ===
net = cv2.dnn.readNetFromONNX(onnx_path)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# === Connessione socket ===
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.settimeout(0.2)

# === Video stream ===
cap = cv2.VideoCapture(url)
flag_stop = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream non disponibile.")
        s.sendall(b"STOP_SERVER\n")
        break

    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    original = frame.copy()
    h, w = frame.shape[:2]

    # === Preprocessing per YOLOv5 ONNX ===
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward()

    # === Post-processing ===
    rows = outputs.shape[1]
    boxes = []
    confidences = []
    class_ids = []

    for i in range(rows):
        row = outputs[0][i]
        conf = row[4]
        if conf >= 0.4:
            scores = row[5:]
            class_id = np.argmax(scores)
            score = scores[class_id]
            if score > 0.4:
                cx, cy, w_box, h_box = row[0:4]
                x = int((cx - w_box / 2) * w / 640)
                y = int((cy - h_box / 2) * h / 640)
                w_box = int(w_box * w / 640)
                h_box = int(h_box * h / 640)
                boxes.append([x, y, w_box, h_box])
                confidences.append(float(score))
                class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.5)
    indices = indices.flatten() if len(indices) > 0 else []

    # === Disegna bounding box ===
    for i in indices:
        x, y, w_box, h_box = boxes[i]
        color = (0, 255, 0) if class_ids[i] == 0 else (255, 0, 0)  # verde per 'person'
        label = f"ID:{class_ids[i]} Conf:{confidences[i]:.2f}"
        cv2.rectangle(original, (x, y), (x + w_box, y + h_box), color, 2)
        cv2.putText(original, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imshow("YOLOv5-ONNX Stream", original)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
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

cap.release()
cv2.destroyAllWindows()
s.close()
