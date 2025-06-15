import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('YOLOV5_Addestrato\V3\\results.csv')
df.columns = df.columns.str.strip()

print(df.columns)

# Metriche da plottare
metrics = [
    ('metrics/mAP_0.5', 'mAP@0.5'),
    ('metrics/mAP_0.5:0.95', 'mAP@0.5:0.95'),
    ('metrics/precision', 'Precision'),
    ('metrics/recall', 'Recall'),
    ('train/obj_loss', 'Training Object Loss'),
    ('train/box_loss', 'Training Box Loss'),
    ('train/cls_loss', 'Training Class Loss')
]

# Disegna i grafici per ogni metrica
for column, label in metrics:
    plt.figure(figsize=(10, 6))
    plt.plot(df[column], label=label)
    plt.xlabel('Epoch')
    plt.ylabel('Value')
    plt.title(f'YOLOv5 - {label}')
    plt.legend()
    plt.grid()
    
    filename = f"{label.replace('/', '_').replace('@', '_').replace(':', '_')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()
