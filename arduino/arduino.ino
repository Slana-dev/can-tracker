#include <AccelStepper.h>
#include <string.h>
#include <stdbool.h>
#include <Servo.h>
Servo ESC1;
Servo ESC2;

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

#define X_EDGE_RIGHT 16
#define X_EDGE_LEFT 17 

#define ESC_PIN1 4
#define ESC_PIN2 6

#define POLZ_PIN 27

AccelStepper stepperX(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN);
AccelStepper stepperY(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN);

const int bytes = 9;
byte podatki[bytes];

int hitrosti[] = {
  1200,
  1245,
  1300,
  1400,
  
};

int stepsX = 0;
int stepsY = 0;

int speed1 = 0;
int speed2 = 0;

int edgeXright;
int edgeXleft;
int multX = 1;
int multY = 1;
int lastStateXright = HIGH;
int lastStateXleft = HIGH;
bool strel = false;

void setup()
{
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  stepperX.setMaxSpeed(10000);
  stepperX.setAcceleration(1000);

  stepperY.setMaxSpeed(10000);
  stepperY.setAcceleration(1000);
  Serial.begin(9600);

  pinMode(X_MS1, OUTPUT);
  pinMode(X_MS2, OUTPUT);
  pinMode(X_MS3, OUTPUT);
  pinMode(Y_MS1, OUTPUT);
  pinMode(Y_MS2, OUTPUT);
  pinMode(Y_MS3, OUTPUT);
  pinMode(X_EDGE_RIGHT, INPUT_PULLUP);
  pinMode(X_EDGE_LEFT, INPUT_PULLUP);

  pinMode(POLZ_PIN, OUTPUT);
  
  ESC1.attach(ESC_PIN1);
  ESC2.attach(ESC_PIN2);
  ESC1.writeMicroseconds(1200); // nastavi minimum throttle
  ESC2.writeMicroseconds(1200);
  delay(1000);
}

void setMicrosteppingX(bool enable)
{
  digitalWrite(X_MS1, enable ? HIGH : LOW);
  digitalWrite(X_MS2, enable ? HIGH : LOW);
  digitalWrite(X_MS3, enable ? HIGH : LOW);
}

void setMicrosteppingY(bool enable)
{
  digitalWrite(Y_MS1, enable ? HIGH : LOW);
  digitalWrite(Y_MS2, enable ? HIGH : LOW);
  digitalWrite(Y_MS3, enable ? HIGH : LOW);
}

void loop()
{

  edgeXright = digitalRead(X_EDGE_RIGHT);
  edgeXleft = digitalRead(X_EDGE_LEFT);
  if (lastStateXright == LOW && edgeXright == HIGH)
  {
    Serial.write('1');
  }
  if (lastStateXleft == LOW && edgeXleft == HIGH)
  {
    Serial.write('2');
  }
  lastStateXright = edgeXright;
  lastStateXleft = edgeXleft;

  if (Serial.available() >= bytes)
  {
    Serial.readBytes(podatki, bytes);
    int8_t smerX = (int8_t)podatki[0];
    int8_t smerY = (int8_t)podatki[1];
    stepsX = podatki[2] * 7;
    stepsY = (podatki[3]*5)/2;
    speed1 = podatki[4];
    speed2 = podatki[5];
    strel = (podatki[6] == 1);
    multX = (podatki[7]);
    multY = podatki[8];

    setMicrosteppingX(true);
    stepsX *= multX;

    setMicrosteppingY(true);
    stepsY *= multY;

    stepperX.move(stepsX * smerX);
    stepperY.move(stepsY * smerY);

    ESC1.writeMicroseconds(hitrosti[speed1]);
    ESC2.writeMicroseconds(hitrosti[speed2]);

    digitalWrite(POLZ_PIN, strel ? HIGH : LOW);
  }
  stepperX.run();
  stepperY.run();
}
