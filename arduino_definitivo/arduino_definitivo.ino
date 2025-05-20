#define m1 2   
#define m2 3 
#define m3 4  
#define m4 5 

// include the library code:
#include <LiquidCrystal.h>
const int rs = 44, en = 42, d4 = 40, d5 = 38, d6 = 36, d7 = 34;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);


void setup() {
  Serial.begin(9600); // Riceve da RPi
  // Pin per controllare i motori
  pinMode(m1, OUTPUT);
  pinMode(m2, OUTPUT);
  pinMode(m3, OUTPUT);
  pinMode(m4, OUTPUT);

    // set up the LCD's number of columns and rows:
  lcd.begin(16, 2);
}

void loop() {
    String msg = Serial.readStringUntil('\n'); // Legge fino a newline
    Serial.println("Ricevuto: " + msg);
    msg.trim();

    if (msg == "GO" || msg == "Semaforo verde") {
      lcd.clear();
      lcd.print(msg);    
      
      //Condition for forward
      digitalWrite(m1, HIGH);
      digitalWrite(m2, LOW);
      digitalWrite(m3, HIGH);
      digitalWrite(m4, LOW);
                       
    } else if (msg == "Sinistra") {
      //Condition for LEFT
      digitalWrite(m1, LOW);
      digitalWrite(m2, LOW);
      digitalWrite(m3, HIGH);
      digitalWrite(m4, LOW);
    
    } else if (msg == "Destra")  {
      //Condition for RIGHT
      digitalWrite(m1, HIGH);
      digitalWrite(m2, LOW);
      digitalWrite(m3, LOW);
      digitalWrite(m4, LOW);
      delay(2000);

    } else {
      lcd.clear();
      // print the number of seconds since reset:
      lcd.print(msg);
      
      //Condition for STOP
      digitalWrite(m1, LOW);
      digitalWrite(m2, LOW);
      digitalWrite(m3, LOW);
      digitalWrite(m4, LOW); 
    
    }
  
}
/*
      //Condition for backward
      digitalWrite(m1, LOW);
      digitalWrite(m2, HIGH);
      digitalWrite(m3, LOW);
      digitalWrite(m4, HIGH);
      delay(2000);

*/
