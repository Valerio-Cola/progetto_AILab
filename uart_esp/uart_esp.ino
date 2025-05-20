#define m1 2   
#define m2 3 
#define m3 4  
#define m4 5 

void setup() {
  Serial.begin(115200); // Riceve da ESP32
  // Pin per controllare i motori
  pinMode(m1, OUTPUT);
  pinMode(m2, OUTPUT);
  pinMode(m3, OUTPUT);
  pinMode(m4, OUTPUT);
}

void loop() {
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n'); // Legge fino a newline
    Serial.println("Ricevuto: " + msg);
    msg.trim();

    if (msg == "GO") {
      // Azione in risposta al comando
      Serial.println("Comando GO riconosciuto!");
      //Condition for forward
      digitalWrite(m1, HIGH);
      digitalWrite(m2, LOW);
      digitalWrite(m3, HIGH);
      digitalWrite(m4, LOW);
                       

      //Condition for backward
      /*digitalWrite(m1, LOW);
      digitalWrite(m2, HIGH);
      digitalWrite(m3, LOW);
      digitalWrite(m4, HIGH);
      delay(2000);

      //Condition for RIGHT
      digitalWrite(m1, HIGH);
      digitalWrite(m2, LOW);
      digitalWrite(m3, LOW);
      digitalWrite(m4, LOW);
      delay(2000);

      //Condition for LEFT
      digitalWrite(m1, LOW);
      digitalWrite(m2, LOW);
      digitalWrite(m3, HIGH);
      digitalWrite(m4, LOW);
      delay(2000);
*/
    } else if (msg == "STOP") {
      Serial.println("Comando STOP riconosciuto!");
      //Condition for STOP
      digitalWrite(m1, LOW);
      digitalWrite(m2, LOW);
      digitalWrite(m3, LOW);
      digitalWrite(m4, LOW);
    }
  }
}
