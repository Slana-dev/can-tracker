#include <AccelStepper.h>
#include <string.h>
#include <stdbool.h>

#define X_STEP_PIN   54
#define X_DIR_PIN    55

#define Y_STEP_PIN   60
#define Y_DIR_PIN    61

#define X_MS1 45
#define X_MS2 32
#define X_MS3 47

#define Y_MS1 43
#define Y_MS2 41
#define Y_MS3 39
#define ENABLE_PIN 38

AccelStepper stepperX(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN );
AccelStepper stepperY(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN );
const int bytes = 11;
byte podatki[bytes];

const int microMultiplier = 16;
int faktor = 1;
int stepsX = 0;
int stepsY = 0;
float kotX = 0;
float kotY = 0;

void setup() {
  pinMode(ENABLE_PIN, OUTPUT);         // Set pin 38 as output
  digitalWrite(ENABLE_PIN, LOW);   
  
  stepperX.setMaxSpeed(1000);         
  stepperX.setAcceleration(100000);      

  stepperY.setMaxSpeed(1000);
  stepperY.setAcceleration(100000);
  Serial.begin(9600);

  pinMode(X_MS1, OUTPUT);
  pinMode(X_MS2, OUTPUT);
  pinMode(X_MS3, OUTPUT);
  pinMode(Y_MS1, OUTPUT);
  pinMode(Y_MS2, OUTPUT);
  pinMode(Y_MS3, OUTPUT);
}

void setMicrosteppingX(bool enable) {
  digitalWrite(X_MS1, enable ? HIGH : LOW);
  digitalWrite(X_MS2, enable ? HIGH : LOW);
  digitalWrite(X_MS3, enable ? HIGH : LOW);
}

void setMicrosteppingY(bool enable) {
  digitalWrite(Y_MS1, enable ? HIGH : LOW);
  digitalWrite(Y_MS2, enable ? HIGH : LOW);
  digitalWrite(Y_MS3, enable ? HIGH : LOW);
}

void loop() {
  if (Serial.available() == bytes) {
    Serial.readBytes(podatki, bytes);
    bool smerX = (podatki[0] == 1);
    bool smerY = (podatki[1] == 1);
    bool microstepping = podatki[10] == 1;

    int directionX = smerX ? 1 : -1;
    int directionY = smerY ? 1 : -1;
    memcpy(&kotX, &podatki[2], 4);
    memcpy(&kotY,&podatki[6], 4 );

    faktor = microstepping ? 1 : microMultiplier;
    if(microstepping){
      setMicrosteppingX(true);
      setMicrosteppingY(true);
    }else{
      setMicrosteppingX(false);
      setMicrosteppingY(false);
    }
    stepsX = int(kotX/(1.8 / faktor));

    stepperX.moveTo(stepperX.currentPosition() + stepsX * directionX  );
  }

  stepperX.run();
  stepperY.run();

}
