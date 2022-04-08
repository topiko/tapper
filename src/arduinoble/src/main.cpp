#include <Wire.h>
#include <Arduino_LSM9DS1.h>


#define BAUDRATE 115200
#define SWPIN 7
#define LEDPIN 10


float ax, ay, az;
float wx, wy, wz;
int n;
uint8_t mode = 0; // Operation mode: 0 == FAILSAFE
uint8_t switchState = 0; // Operation mode: 0 == FAILSAFE
unsigned long lastWrite = 0;
unsigned long sinceLastWrite;
static unsigned long PERIOD = 10000; // # 1 / freq[hz] * mus/s 

struct StateStruct {
  float accel[3];             // 4*3 = 12 The order is important here!!! --> 32bit system likes to make everything 32bit...
  float w[3];                 // 12
  uint16_t deltaT;            // 2
  uint8_t switchState;        // 1
  byte end='\x0A';            // 1
                              //------
                              // 28
};

StateStruct state;

void setup()
{
  Serial.begin(BAUDRATE);
  Serial.println("BLESense intitalizing:");
  delay(1000);

  pinMode(SWPIN, INPUT_PULLUP);
  pinMode(LEDPIN, OUTPUT);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  Serial.print("Accelerometer sample rate = ");
  Serial.print(IMU.accelerationSampleRate());
  Serial.println(" Hz");

}

void writeSerial(){
  lastWrite = micros();
  Serial.write((byte *) &state, sizeof(state));
}

uint8_t readSwitch(){
  switchState = (uint8_t)digitalRead(SWPIN);

  if (switchState){digitalWrite(LEDPIN, HIGH);}
  else {digitalWrite(LEDPIN, LOW);}

  return switchState;
}

void loop(){
  
  
  // Get acceleration:
  
  while (IMU.accelerationAvailable()){
    IMU.readAcceleration(ax, ay, az);
    state.accel[0] = az;
    state.accel[1] = -ax;
    state.accel[2] = -ay;
  }

  // Get gyro:
  while (IMU.gyroscopeAvailable()){
    IMU.readGyroscope(wx, wy, wz);
    state.w[0] = -wz;
    state.w[1] = wx;
    state.w[2] = wy;
  }
  

  sinceLastWrite = micros() - lastWrite;
  if (mode==1 && sinceLastWrite>PERIOD){
    state.deltaT = (uint16_t)sinceLastWrite; 
    state.switchState = readSwitch(); 
    writeSerial();
  }
  
  // Check if commands are waiting. Note, serialEvent() does not work on nano33ble... 
  while (Serial.available()){
    mode = (uint8_t)Serial.read();
    if (mode==0) digitalWrite(LEDPIN, LOW);
  }
 
}




