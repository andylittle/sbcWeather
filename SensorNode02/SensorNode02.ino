#include <RF24Network.h>
#include <RF24.h>
#include <SPI.h>

#include "MQ135.h"

#include "BMP280.h"
#include "Wire.h"

//Voltage
#define NUM_SAMPLES 10
int sum = 0;                    // sum of samples taken
unsigned char sample_count = 0; // current sample number
float voltage = 0.0;            // calculated voltage

// Constants that identify this node and the node to send data to
const uint16_t this_node = 2;
const uint16_t parent_node = 0;

//MQ135 is on pin 5
MQ135 gasSensor = MQ135(5);

//bmp280
#define P0 1013.25
BMP280 bmp;


// Radio with CE & CSN connected to pins 7 & 8
RF24 radio(7, 8);
RF24Network network(radio);

// Time between packets (in ms)
const unsigned long interval = 30000;  // every 30

sec

// Structure of our message
struct message_1 {
  float pressure;
  float intemp;
  float inairqual;
  float volt;
  bool dooropen;
};
message_1 message;

// The network header initialized for this node
RF24NetworkHeader header(parent_node);

void setup(void)
{
  // Set up the Serial Monitor
  Serial.begin(9600);

  // Initialize all radio related modules
  SPI.begin();
  radio.begin();
  delay(5);
  network.begin(90, this_node);

  // Initialize the BMP library
  if(!bmp.begin()){
    Serial.println("BMP init failed!");
    while(1);
  }
  else Serial.println("BMP init success!");
  
  bmp.setOversampling(4);
}

void loop() {

  // Update network data
  network.update();
  
  //Read BMP280
  double TT,PP;
  char result = bmp.startMeasurment();
  //if(result!=0){
    delay(result);
    result = bmp.getTemperatureAndPressure(TT,PP);
  
  float p =(float) PP;
  float t = (float) TT; 
  
  //Read AQ135
  float a = gasSensor.getPPM();
   
  //Voltage 
  // take a number of analog samples and add them up
  sum = 0;
  
  sample_count= 0;
  while (sample_count < NUM_SAMPLES) {
      sum += analogRead(A1);
      sample_count++;
      delay(10);
    }
    // calculate the voltage
    // use 5.0 for a 5.0V ADC reference voltage
    // 5.015V is the calibrated reference voltage
    float v = ((float)sum / (float)NUM_SAMPLES * 5.015) / 1024.0;  
  //fake door
  bool d = HIGH;
  
  // Headers will always be type 1 for this node
  // We set it again each loop iteration because fragmentation of the messages might change this between loops
  header.type = '1';

  // Only send values if any of them are different enough from the last time we sent:
  //  0.5 degree temp difference, 1% humdity or light difference, or different motion state
  if (abs(t - message.intemp) > 0.5 || 
      abs(p - message.pressure) > 1.0   || 
      abs(a - message.inairqual) > 1.0 ||
      abs(v - message.volt) > 1.0) { 
 //     m != message.motion ||
 //     d != message.dooropen) {
    // Construct the message we'll send
    message = (message_1){ p, t, a, v, d };
    Serial.println(p);Serial.println(t);Serial.println(a);Serial.println(v);

    // Writing the message to the network means sending it
    if (network.write(header, &message, sizeof(message))) {
      Serial.print("Message sent\n"); 
    } else {
      Serial.print("Could not send message\n"); 
    }
  }
     
  // Wait a bit before we start over again
  delay(interval);
}
