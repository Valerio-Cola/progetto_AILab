## 📦 Download del Dataset

### 🐧 Da Terminale
Per scaricare il dataset completo del progetto, basta eseguire i seguenti comandi nel terminale:

```bash
curl -L "https://app.roboflow.com/ds/dhH8eqpKDK?key=y8e471XHSi" -o roboflow.zip
unzip roboflow.zip
rm roboflow.zip
```
### 📁 Pagina del progetto su Roboflow

Per ulteriori informazioni sul dataset, visita la pagina del progetto su Roboflow:

[Road Object Detection v0.8.1a](https://app.roboflow.com/yolorc-rrbm0/road-object-detection-v081a/)


cartello irl = 12 cm
import math

fov_deg = 60
fov_rad = math.radians(fov_deg)

            '''
            width_px = frame.shape[1]            
            height_pixel = y2 - y1

            focal_length_px = (width_px * 0.5) / math.tan(fov_rad * 0.5)
            H_real = 12

            distance_cm = (H_real * focal_length_px) / height_pixel
            print(f"Distanza stimata: {distance_cm:.2f} cm")
            '''