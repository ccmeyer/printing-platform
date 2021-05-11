#include <Wire.h>
// int data[7]; // seven bytes sent to Arduino each time
//  int count = 0;
//  int start = 0;

const int valveP = 2;  // for Pulse
const int valveR = 3;  // for Refill

byte datard[16] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
int PW;
int Freq;
int RePW;
int pulsecount;
int pulseswitch = 0;
int DeTi = 50;

int i = 0;
int j = 0;
int lim = 0;
int tp = 0;
byte inByte = 0;

void ParamPass()     // receive cmd data after flush the buffer, while stopping output pulse
{
  
  if (Serial.available()) {
    for (i = 0; i < 16; i++){
      datard[i] = 0;
    }
    i = 0;
    while (Serial.available()){
      inByte = Serial.read();
//      Serial.write(inByte);
      if (i < 12){
        datard[i] = inByte;
        i++;
      } 
      else {
        while (Serial.available()){
          inByte = Serial.read();
        }
        break;
      }
    }
    i = 0;
    while (i <= 8){
      if (datard[i] == 255 && datard[i + 1] == 255) {
        if (datard[i + 2] == 254 && datard[i + 3] == 254) {   // FE FE
          pulseswitch = 0;
          i=i+4;
          //break;
        } else if (datard[i + 2] == 239 && datard[i + 3] == 239) {   // EF EF
          pulseswitch = 1;
          //break;
          i=i+4;
        } else if (datard[i + 2] == 237 && datard[i + 3] == 237) {   // EF EF
          pulseswitch = 2;
          //break;
          i=i+4;
        } else if (datard[i + 2] == 235 && datard[i + 3] == 235) {   // EF EF
          pulseswitch = 3;
          //break;
          i=i+4;
        } 
        else {
          Freq = datard[i + 2];
          tp = 1000 / Freq;
          PW = datard[i + 4] * 256 + datard[i + 3];
          RePW = datard[i + 6] * 256 + datard[i + 5];
          pulsecount = datard[i + 7];
          i=i+8;
          //break;
        }
      } else {
        i++;
      }
    }
  }
}



void setup() { // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.setTimeout(100);
//  Serial.write('R');
  while (!Serial) {
  ;   // wait for serial port to connect. Needed for Leonardo only  
  }
    pinMode(2, OUTPUT);
    pinMode(3, OUTPUT);
    pinMode(4, OUTPUT);
    pinMode(5, OUTPUT);
    pinMode(6, OUTPUT);
    pinMode(7, OUTPUT);
    pinMode(8, OUTPUT);
    pinMode(9, OUTPUT);
    pinMode(10, OUTPUT);
    pinMode(11, OUTPUT);
    pinMode(12, OUTPUT);
    pinMode(13, OUTPUT);
    digitalWrite(2, LOW);
    digitalWrite(3, LOW);
    digitalWrite(4, LOW);
    digitalWrite(5, LOW);
    digitalWrite(6, LOW);
    digitalWrite(7, LOW);
    digitalWrite(8, LOW);
    digitalWrite(9, LOW);
    digitalWrite(10, LOW);
    digitalWrite(11, LOW);
    digitalWrite(12, LOW);
    digitalWrite(13, LOW);
  }

void loop() {
  ParamPass();
  if (pulseswitch == 1) {
    if(PW == 0){    // Refuel test
      for(j=0; j < pulsecount; j++){
        delay(1000/Freq/2 - RePW/1000/2);
        digitalWrite(valveR, HIGH);
        delayMicroseconds(RePW);
        digitalWrite(valveR, LOW);
        delay(1000/Freq/2 - RePW/1000/2);
      } 
    }
    else if(RePW == 0){   //Pulse test
      for(j=0; j < pulsecount; j++){
        delay(1000/Freq/2 - PW/1000/2);
        digitalWrite(valveP, HIGH);
        delayMicroseconds(PW);
        digitalWrite(valveP, LOW);
        delay(1000/Freq/2 - PW/1000/2);
      } 
    }
    
    else {    //Normal droplet printing with refuel open when not pulsing
      for(j=0; j < pulsecount; j++){
        delay(1000/Freq/2 - PW/1000/2);
        digitalWrite(valveR, LOW);
        digitalWrite(valveP, HIGH);
        delayMicroseconds(PW);
        digitalWrite(valveP, LOW);
        digitalWrite(valveR, HIGH);
        delay(1000/Freq/2 - PW/1000/2);
      } 
    }
    digitalWrite(valveP, LOW);
    digitalWrite(valveR, LOW);
    pulseswitch = 0;
    Serial.write('C');
    delay(100);
    Serial.write('C');
    delay(100);
    Serial.write('E');

  } else if (pulseswitch == 2) {
//    digitalWrite(valveP, LOW);
    digitalWrite(valveR, HIGH);
    delay(100);
  } else if (pulseswitch == 3) {
    digitalWrite(valveP, HIGH);
//    digitalWrite(valveR, LOW);
    delay(100);
  } else {
    digitalWrite(valveP, LOW);
    digitalWrite(valveR, LOW);
    delay(100);
  }
}
