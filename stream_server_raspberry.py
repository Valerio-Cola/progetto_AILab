# Utilizziamo Flask per creare una web app che trasmette i frame della videocamera 
from flask import Flask, Response

# La libreria Picamera2 per interagire con la videocamera Raspberry Pi
from picamera2 import Picamera2

import cv2 

# La libreria socket per gestire le connessioni TCP
import socket

# La libreria serial per comunicare con Arduino via UART
import serial


# Setup TCP server non bloccante su porta 5005
TCP_IP = "0.0.0.0"
TCP_PORT = 5005
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((TCP_IP, TCP_PORT))
server_sock.listen(1)

# Imposta il socket in modalità non bloccante in questo modo non blocca l'esecuzione del programma 
# in attesa di nuove connessioni o messaggi
server_sock.setblocking(False)

# Variabili globali per gestire la connessione 
conn = None 
addr = None

print("TCP server avviato su porta 5005")

# Inizializza app Flask
app = Flask(__name__)

# Setup della Camera
camera = Picamera2()
video_config = camera.create_video_configuration(
    main={"size": (720, 1280)},
    controls={"FrameDurationLimits": (33333, 33333)}
)
camera.configure(video_config)
camera.options['buffer_count'] = 1
camera.start(show_preview=False)

# Setup della connessione seriale con Arduino
try:
    arduino = serial.Serial('/dev/serial0', 9600, timeout=1)
    print("Connessione seriale con Arduino stabilita")
except serial.SerialException as e:
    print(f"Errore apertura porta seriale: {e}")
    arduino = None

# Funzione per generare i frame della videocamera e gestire le connessioni TCP
def generate_frames():
    global conn, addr
    while True:
        # Prova ad accettare una nuova connessione se non c'è una connessione già attiva
        if conn is None:
            try:
                conn, addr = server_sock.accept()
                conn.setblocking(False)
                print(f"Connessione stabilita con {addr}")
            except BlockingIOError:
                pass

        # Prova a leggere dati da una connessione attiva
        if conn is not None:
            try:
                # Legge i dati dalla connessione TCP
                data = conn.recv(1024)
                if not data:
                    print("Connessione chiusa")
                    conn.close()
                    conn = None
                else:
                    # Decodifica il messaggio ricevuto
                    msg = data.decode().strip()

                    # Se il messaggio è "STOP_SERVER", chiude la connessione
                    if msg == "STOP_SERVER":
                        conn.close()
                        conn = None
                    
                    # Altrimenti, stampa il messaggio, invia l'ACK al dispositivo connesso e invia ad Arduino il messaggio
                    else:
                        print(f"Messaggio ricevuto: {msg}")
                        conn.sendall(b"ACK\n")

                        # Invia ad Arduino via UART
                        try:
                            # è importante aggiungere il newline per terminare il messaggio
                            arduino.write((msg + '\n').encode())  
                            print("Inviato ad Arduino")
                        except serial.SerialException as e:
                            print(f"Errore durante l'invio: {e}")

            # Gestione delle eccezzioni
            # Se la connessione è bloccata, ad esempio se viene saltato un frame la connessione non viene chiusa 
            except BlockingIOError:
                pass
            except (ConnectionResetError, BrokenPipeError):
                print("Connessione interrotta")
                conn.close()
                conn = None

        # Cattura e invia frame
        frame = camera.capture_array()

        # Conversione in RGB per Flask
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Codifica del frame in JPEG per la trasmissione
        ret, buffer = cv2.imencode('.jpg', frame,  [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        frame = buffer.tobytes()

        # Genera il frame in formato MJPEG per la trasmissione via HTTP
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Quando il dispositivo connesso accede alla pagina web genera una richiesta GET,
# Flask quindi risponde invocando la funzione index, che invoca generate_frames().
# A questo punto inizia il loop infinito e la generazione dei frame. 
@app.route('/')
def index():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Avvio dell'app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 