# Readme ancora in fase di elaborazione riferirsi alla [risorsa](Elaborato/main.pdf)

# RACER  
## Raspberry & Arduino Car for Environmental Recognition

Progetto per il corso di AiLab Computer Vision - A.A. 2024/2025  

Docente: Daniele Pannone  

15 giugno 2025  

Col Valerio cola.2660062@studenti.uniroma1.it  
Cerboni Federico cerboni.2006100@studenti.uniroma1.it  

---

# Indice

1 Introduzione 3  
2 Progettazione del Veicolo 3  
  2.1 Arduino - Il cuore 3  
  2.2 Raspberry Pi Z2W + PiCamera V2 - Gli occhi della macchina 4  
  2.3 Comunicazione tra i moduli 4  
  2.4 Alimentazione 5  
3 Sviluppo Software 5  
  3.1 Introduzione 5  
  3.2 YoloV5s - Il Cervello 5  
    3.2.1 Cosa è YoloV5 5  
    3.2.2 Architettura 5  
    3.2.3 Perché lo abbiamo scelto 6  
    3.2.4 Training 7  
    3.2.5 Object Detection 9  
  3.3 Lane Detection 10  
4 Sviluppi futuri del progetto 12  

---

# 1 Introduzione

Il progetto RACER si incentra sullo sviluppo da zero di una macchina a guida autonoma grazie alla combinazione del Microcontrollore **Arduino Mega 2560 R3** (prodotto dalla Elegoo), il Micro‑computer **Raspberry Pi Zero 2W** e il Modello Convoluzionale **YoloV5s**. Sebbene non si tratti di una classica RC‑Car, l’idea principale è sostituire il controllo umano e il Radiocomando con un sistema basato su una rete neurale e sulla computer vision tramite OpenCV. Questo sistema è in grado di osservare l’ambiente, rilevare enti e segnali stradali e analizzare le corsie per correggere automaticamente la direzione del veicolo.

Un primo approccio ha portato il team ad utilizzare un **ESP32‑S3‑N16R8** in combinazione con una camera **OV5560**. Purtroppo la bassa potenza di calcolo e la qualità costruttiva ci ha portato a sostituirlo con un Raspberry; in particolare l’antenna WiFi era debole, i contatti della camera estremamente sensibili che portavano a un degrado delle prestazioni con minimi movimenti e il corpo macchina della OV5560 tendeva a surriscaldarsi molto velocemente portando a un ulteriore degrado delle prestazioni.

---

# 2 Progettazione del Veicolo

## 2.1 Arduino ‑ Il cuore

Alla base di ogni autovettura c’è sempre un motore, per RACER sono stati utilizzati **4 piccoli motori DC** a bassa tensione (9 V) che possono essere controllati con i pin PWM di Arduino. In particolare la struttura è **4WD (Four Wheel Drive)**, ovvero a trazione integrale dove ogni ruota è motrice e può essere impostata autonomamente.

A disposizione avevamo un solo **L293D** (dual H‑Bridge motor driver) per il controllo di direzione e velocità, sono quindi stati collegati in serie i 2 motori di destra e di sinistra. Ciò semplifica anche la gestione della svolta poiché per sterzare è necessario che i due motori di ambi i lati abbiano velocità equivalenti. I comandi che verranno gestiti sono *Start*, *Stop*, *Sterzata a destra e sinistra* e variazione di velocità a due livelli. È stato inserito anche uno schermo **LCD 16×2** che funge da debugger per comprendere in tempo reale cosa sta facendo l’Arduino.

Il “telaio” è in resina con ruote in gomma/plastica.

![Figura 1](/Elaborato/img/fig1.png)  
**Figura 1: Circuito completo dei motori.**

---

## 2.2 Raspberry Pi Z2W + PiCamera V2 ‑ Gli occhi della macchina

Per catturare i dati ambientali abbiamo utilizzato un **Raspberry Pi Z2W**, dotato di processore Quad‑core Cortex‑A53 a 1.0 GHz a 64 bit e 512 MB LPDDR2 di RAM, in combinazione con una **PiCamera V2** che monta un sensore Sony IMX219 da 8 Megapixel. Entrambi i componenti sono stati montati in un case apposito della Raspberry mostrato in figura e montato nella parte anteriore del veicolo.

Questo modulo si occuperà di:

- Catturare un flusso video 720×1280 e streammarlo su una rete locale (Hotspot Cellulare). Lo streaming sarà in contemporanea catturato mediante OpenCV su un PC che sta eseguendo il programma principale di analisi ambientale.
- Gestire connessioni TCP con un terminale per lo scambio di messaggi.
- Inoltro dei comandi ad Arduino.

---

## 2.3 Comunicazione tra i moduli

1. **PC** collegato alla stessa rete del Raspberry cattura con OpenCV lo streaming video.
2. Con la libreria **Socket** invierà i comandi/messaggi utilizzando il protocollo TCP su porta 5005 al Raspberry.
3. Una volta ricevuti, il Raspberry li inoltrerà all’Arduino tramite il collegamento **UART0** (Universal Asynchronous Receiver‑Transmitter) che permette lo scambio su porta seriale in modo asincrono. Abbiamo deciso di rendere la comunicazione unidirezionale, solo il Pi invia *Pin TX Pi → Pin Rx Arduino*.

![Figura 2](/Elaborato/img/fig2.png)  
**Figura 2: Collegamento UART**

4. **Streaming Video Raspberry**  
   Abbiamo creato un’app **WebCamera Server** utilizzando il framework *Flask* e le librerie *PiCamera2* e *OpenCV* per catturare i frame dalla PiCamera. L’app si occupa di inviare il flusso di frame catturato dalla camera al dispositivo connesso su porta 8080. Successivamente abbiamo reso lo script in un servizio linux, in modo che venga eseguito in automatico all’accensione. Per la realizzazione dell’app ci siamo affidati alla seguente repository.  
   <https://github.com/miguelgrinberg/flask-video-streaming/tree/v1>


---

## 2.4 Alimentazione

- **Arduino:** Batteria 9 V.  
- **Motori:** Batteria 9 V.  
- **Raspberry:** Powerbank 5 V/1 A.

---

# 3 Sviluppo Software

## 3.1 Introduzione

Il programma di elaborazione dei frame sfrutta il multithreading per ottenere prestazioni ottimali e fluide e si suddivide come segue:

- **Thread Principale:** esegue la Lane Detection e invia i comandi relativi a direzione e ciò che Yolo ha individuato solo se il Thread 1 ha acquisito il frame.
- **Thread 1:** si occupa di acquisire i frame.
- **Thread 2:** esegue l’inferenza di Yolo e salva le classi immagazzinate.

Di seguito è rappresentato il flusso di computazione semplificato:  
*Thread 1 Frame Acquisito → Thread 2 Oggetti individuati nel frame → Thread Principale Lane Detection + Invio Comandi*

---

## 3.2 YoloV5s ‑ Il Cervello

### 3.2.1 Cosa è YoloV5

YOLO (You Only Look Once) è una serie di modelli di riconoscimento degli oggetti in tempo reale basati sulla rete neurale convoluzionale. Il suo nome fa riferimento alla caratteristica che lo contraddistingue da modelli simili precedenti, ovvero che il modello richiede un solo passaggio di propagazione in avanti per poter fare delle previsioni. Il modello è stato creato da *Joseph Redmon*, che ha sviluppato le prime tre versioni e pubblicate sul suo sito web. Successive versioni sono state sviluppate da altri enti; la versione utilizzata da noi (v5) ad esempio è stata sviluppata dalla *Ultralytics*.

### 3.2.2 Architettura

Modelli di riconoscimento di oggetti classici richiedono due passaggi dell’immagine in input, la prima per generare un insieme di potenziali posizioni di oggetti (proposte), la seconda serve per raffinare tali proposte e ottenere le previsioni finali. Inoltre, alcuni modelli, come del tipo *Region Proposal Networks*, eseguono diverse istanze del modello per una singola immagine, una per ogni regione separatamente. Tutto ciò richiede una quantità di risorse considerevole.

Il modello **YOLO** esegue un singolo passaggio dell’immagine in input sia per le proposte sia per la previsione finale, inoltre esegue le previsioni sull’immagine in input nella sua interezza nello stesso momento, grazie all’uso di un singolo layer completamente connesso. Infine, la struttura stessa di YOLO è relativamente semplice: una singola rete convoluzionale esegue le previsioni sia delle classi sia dei bounding box.

La rete convoluzionale di YOLO viene suddivisa in tre parti:

- **Backbone:** responsabile dell’estrazione delle caratteristiche dall’immagine di input.
- **Neck:** esegue trasformazioni sulle caratteristiche estratte dalla Backbone.
- **Head:** si occupa delle previsioni finali. Versioni successive di YOLO sono aggiornamenti e modificazioni di questi tre moduli.

![Figura 3](/Elaborato/img/fig3.png)  
**Figura 3: Architettura YoloV5**

YOLO divide l’immagine in input in una griglia *S×S*. Se il centro di un oggetto si trova dentro una cella, quella cella si occuperà di rilevare quell’oggetto. Ogni cella prevede *B* bounding box e un punteggio di confidenza per ognuno di quei box. La confidenza quantifica la probabilità di quel box di contenere un oggetto e con quale precisione. Inoltre ad ogni cella prevede *C* probabilità di classe, ovvero che tipo di oggetto si trova dentro la cella. Queste due informazioni vengono unite per produrre le previsioni finali.

![Figura 4](/Elaborato/img/fig4.png)  
**Figura 4: Tiling Input**

### 3.2.3 Perché lo abbiamo scelto

Grazie a questo, **YOLO** è estremamente veloce, in grado di elaborare un flusso di immagini in tempo reale con bassissima latenza, pur mantenendo un’alta precisione, e ciò è proprio il nostro caso di utilizzo: l’automobile deve riconoscere rapidamente i vari ostacoli e situazioni che si presentano lungo la strada, ed attuare strategie di correzione tempestivamente.

### 3.2.4 Training

Il modello è stato addestrato su **Google Colab**. Abbiamo utilizzato un dataset creato sulla piattaforma *Roboflow*, composto da circa **2700 immagini** di risoluzione 640×640, ed è stato aumentato ruotando immagini e aggiungendo rumore.

Le classi sono le seguenti:

- Pedoni: 1173  
- Segnale di Stop: 261  
- Segnale di limite a 50 km/h: 254  
- Segnale di limite a 20 km/h: 423  
- Semaforo rosso: 149  
- Semaforo verde: 167  

**Iperparametri:**

- 150 epoche  
- Dimensione batch 64  
- Learning rate 0.01

...

![Figura 5](/Elaborato/img/fig5.png)  
**Figura 5: Intersection over Union**

...

<table>
<tr><td align="center"><img src="/Elaborato/img/fig6a.png" alt="(a) Box Loss" width="45%"></td><td align="center"><img src="/Elaborato/img/fig6b.png" alt="(b) Class Loss" width="45%"></td></tr>
<tr><td align="center">(a) Box Loss</td><td align="center">(b) Class Loss</td></tr>
<tr><td align="center"><img src="/Elaborato/img/fig6c.png" alt="(c) Object Loss" width="45%"></td><td align="center"><img src="/Elaborato/img/fig6d.png" alt="(d) mAP 0.5" width="45%"></td></tr>
<tr><td align="center">(c) Object Loss</td><td align="center">(d) mAP 0.5</td></tr>
<tr><td align="center"><img src="/Elaborato/img/fig6e.png" alt="(e) Precision" width="45%"></td><td align="center"><img src="/Elaborato/img/fig6f.png" alt="(f) Recall" width="45%"></td></tr>
<tr><td align="center">(e) Precision</td><td align="center">(f) Recall</td></tr>
</table>

**Figura 6: Andamento delle metriche durante l’addestramento del modello: perdite e performance.**

### 3.2.5 Object Detection

...

<table>
<tr><td align="center"><img src="/Elaborato/img/fig7a.png" alt="(a) Pedone" width="45%"></td><td align="center"><img src="/Elaborato/img/fig7b.png" alt="(b) Segnale Stop" width="45%"></td></tr>
<tr><td align="center">(a) Pedone</td><td align="center">(b) Segnale Stop</td></tr>
<tr><td align="center"><img src="/Elaborato/img/fig7c.png" alt="(c) Segnale 20 km/h" width="45%"></td><td align="center"><img src="/Elaborato/img/fig7d.png" alt="(d) Segnale 50 km/h" width="45%"></td></tr>
<tr><td align="center">(c) Segnale 20 km/h</td><td align="center">(d) Segnale 50 km/h</td></tr>
</table>

**Figura 7: Object Detection: esempi di classi individuate con accuratezza e stima della distanza.**

---

## 3.3 Lane Detection

...

<table>
<tr><td align="center"><img src="/Elaborato/img/fig8a.png" alt="(a) Veicolo Centrato" width="45%"></td><td align="center"><img src="/Elaborato/img/fig8b.png" alt="(b) Svolta a Destra" width="45%"></td></tr>
<tr><td align="center">(a) Veicolo Centrato, prosegue dritto.</td><td align="center">(b) Svolta a Destra</td></tr>
<tr><td align="center"><img src="/Elaborato/img/fig8c.png" alt="(c) Svolta a Sinistra" width="45%"></td></tr>
<tr><td align="center">(c) Svolta a Sinistra</td></tr>
</table>

**Figura 8: Lane Detection**

---

# 4 Sviluppi futuri del progetto

1. Migliorare il comparto Hardware sostituendo il Pi Z2W con un Pi 4/5 in combinazione con una camera con FOV maggiore. In questo modo la macchina sarà del tutto autonoma poiché il modello girerà direttamente sul Raspberry.  
2. Implementare una lane detection più complessa:  
   - Prenda in considerazione entrambe le strisce di corsia.  
   - Calcoli un valore di intensità di svolta.  
3. Ottimizzare l’alimentazione in un’unica soluzione.

---

# Riferimenti bibliografici

[Bou] Paul Bourke. *Field of view and focal length.* <https://paulbourke.net/miscellaneous/lens/index.html>  
[Ele] Elegoo. *Arduino Mega 2560 R3.* <https://eu.elegoo.com/it-it/products/elegoo-mega-2560-r3-board?srsltid=AfmBOoqlCYHo64N17LxwVv7XPuF1ZlfI-sFE9XTx8FvvoUylTrOLYtfg>  
[Gee] GeeksForGeeks. *Multithreading Tutorial.* <https://www.geeksforgeeks.org/multithreading-python-set-1/>  
[Gri] Miguel Grinberg. *Video Streaming with Flask.* <https://blog.miguelgrinberg.com/post/video-streaming-with-flask>  
[Kun] Rohit Kundu. *YOLO: Algorithm for Object Detection Explained [+Examples].* <https://www.v7labs.com/blog/yolo-object-detection>  
[Rasa] Raspberry. *Raspberry Pi Camera V2.* <https://www.raspberrypi.com/products/camera-module-v2/>  
[Rasb] Raspberry. *Raspberry Pi Zero 2W.* <https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/>  
[Ros] Adrian Rosebrock. *Find distance from camera to object/marker using Python and OpenCV.* <https://pyimagesearch.com/2015/01/19/find-distance-camera-objectmarker-using-python-opencv>  
[Ulta] Ultralytics. *YoloV5.* <https://github.com/ultralytics/yolov5>  
[Ultb] Ultralytics. *YoloV5 Tutorials.* <https://docs.ultralytics.com/yolov5/tutorials/architecture_description/>
