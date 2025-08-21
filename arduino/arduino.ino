#include <AccelStepper.h>
#include <string.h>
#include <stdbool.h>

#define X_STEP_PIN 54
#define X_DIR_PIN 55

#define Y_STEP_PIN 60
#define Y_DIR_PIN 61

#define X_MS1 45
#define X_MS2 32
#define X_MS3 47

#define Y_MS1 43
#define Y_MS2 41
#define Y_MS3 39
#define ENABLE_PIN 38

#define X_EDGE 16
#define Y_EDGE 17

AccelStepper stepperX(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN);
AccelStepper stepperY(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN);
const int bytes = 6;
byte podatki[bytes];

const int microMultiplier = 16;
int stepsX = 0;
int stepsY = 0;
int edgeX;
int edgeY;
int lastStateX = HIGH; 
int lastStateY = HIGH;

void setup() {
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  stepperX.setMaxSpeed(10000);
  stepperX.setAcceleration(700);

  stepperY.setMaxSpeed(10000);
  stepperY.setAcceleration(700);
  Serial.begin(9600);

  pinMode(X_MS1, OUTPUT);
  pinMode(X_MS2, OUTPUT);
  pinMode(X_MS3, OUTPUT);
  pinMode(Y_MS1, OUTPUT);
  pinMode(Y_MS2, OUTPUT);
  pinMode(Y_MS3, OUTPUT);
  pinMode(X_EDGE, INPUT);
  pinMode(Y_EDGE, INPUT);
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
  edgeX = digitalRead(X_EDGE);
  edgeY = digitalRead(Y_EDGE);
  if (lastStateX == HIGH && edgeX == LOW){
    Serial.write('1');
  }
  if (lastStateY == HIGH && edgeY == LOW){
    Serial.write('2');
  }
  lastStateX = edgeX;
  lastStateY = edgeY;
  if (Serial.available() == bytes) {
    Serial.readBytes(podatki, bytes);
    int8_t smerX = (int8_t)podatki[0];
    int8_t smerY = (int8_t)podatki[1];
    stepsX = podatki[2];
    stepsY = podatki[3];
    bool microX = podatki[4] == 1;
    bool microY = podatki[5] == 1;

    if (microX) {
      setMicrosteppingX(true);
      stepsX *= 8;
    } else {
      setMicrosteppingX(false);
    }
    if (microY) {
      setMicrosteppingY(true);
      stepsY *= 8;
    } else {
      setMicrosteppingY(false);
    }
    stepperX.move(stepsX * smerX);
    stepperY.move(stepsY * smerY);
  }
  stepperX.run();
  stepperY.run();
}
