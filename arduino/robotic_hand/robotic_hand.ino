#include <Servo.h>

struct FingerServo {
  Servo servo;
  const char* name;
  int pin;
  int minAngle;
  int maxAngle;
  int currentAngle;
};

FingerServo fingers[5] = {
  {Servo(), "thumb", 3, 10, 105, 10},
  {Servo(), "index", 5, 15, 120, 15},
  {Servo(), "middle", 6, 15, 120, 15},
  {Servo(), "ring", 9, 20, 125, 20},
  {Servo(), "pinky", 10, 25, 130, 25}
};

String inputLine = "";

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 5; i++) {
    fingers[i].servo.attach(fingers[i].pin);
    fingers[i].servo.write(fingers[i].currentAngle);
  }
}

void loop() {
  readSerialLine();
}

void readSerialLine() {
  while (Serial.available() > 0) {
    char incoming = Serial.read();
    if (incoming == '\n') {
      processAngles(inputLine);
      inputLine = "";
    } else if (incoming != '\r') {
      inputLine += incoming;
    }
  }
}

void processAngles(const String& line) {
  int parsed[5];
  int startIndex = 0;

  for (int i = 0; i < 5; i++) {
    int commaIndex = line.indexOf(',', startIndex);

    if (i < 4 && commaIndex == -1) {
      return;
    }

    String token;
    if (commaIndex == -1) {
      token = line.substring(startIndex);
    } else {
      token = line.substring(startIndex, commaIndex);
      startIndex = commaIndex + 1;
    }

    parsed[i] = token.toInt();
  }

  for (int i = 0; i < 5; i++) {
    int target = constrain(parsed[i], fingers[i].minAngle, fingers[i].maxAngle);
    fingers[i].currentAngle = target;
    fingers[i].servo.write(target);
  }
}
