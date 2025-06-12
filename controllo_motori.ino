#define m1 2   
#define m2 3 
#define m3 4  
#define m4 5 

// includere la libreria per il display LCD
#include <LiquidCrystal.h>

// inizializza i pin connessi al display LCD
const int rs = 44, en = 42, d4 = 40, d5 = 38, d6 = 36, d7 = 34;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

void setup() {
  // Riceve da RPi tramite seriale
  Serial.begin(9600);
  // Pin per controllare i motori
  pinMode(m1, OUTPUT);
  pinMode(m2, OUTPUT);
  pinMode(m3, OUTPUT);
  pinMode(m4, OUTPUT);

  // inizializza le righe e colonne del display LCD
  lcd.begin(16, 2);
}

void loop() {
    // Legge fino a newline su seriale
    String msg = Serial.readStringUntil('\n');
    Serial.println("Ricevuto: " + msg);
    // Rimuove spazi bianchi all'inizio e alla fine della stringa
    msg.trim();

    if (msg == "GO" || msg == "Semaforo Verde") {
      // Stampa messaggio GO o Semaforo Verde
      lcd.clear();
      lcd.print(msg);    
      
      // Marcia in avanti
      digitalWrite(m1, LOW);
      analogWrite(m2, 180);
      digitalWrite(m3, LOW);
      analogWrite(m4, 180);
      
      } else if (msg == "Destra") {
      // Svolta a destra
      digitalWrite(m1, LOW);
      analogWrite(m2, 30);
      digitalWrite(m3, LOW);
      analogWrite(m4, 200);
    
    } else if (msg == "Sinistra")  {

      // Svolta a sinistra
      digitalWrite(m1, LOW);
      analogWrite(m2, 200);
      digitalWrite(m3, LOW);
      analogWrite(m4, 30);
      

    } else if (msg == "Stop Rilevato") {
      // Stampa il messaggio di stop
      lcd.clear();
      lcd.print(msg);
      delay(400);
      
      // STOP
      digitalWrite(m1, LOW);
      digitalWrite(m2, LOW);
      digitalWrite(m3, LOW);
      digitalWrite(m4, LOW); 
    
    }else if(msg == "Max 50"){
      lcd.clear();
      lcd.print(msg);    
      
      // Velocità 50 km/h
      digitalWrite(m1, LOW);
      analogWrite(m2, 250);
      digitalWrite(m3, LOW);
      analogWrite(m4, 250);

    } else if(msg == "Max 20"){
      lcd.clear();
      lcd.print(msg);    
      
      // Velocità 20 km/h
      digitalWrite(m1, LOW);
      analogWrite(m2, 180);
      digitalWrite(m3, LOW);
      analogWrite(m4, 180);
    }
}