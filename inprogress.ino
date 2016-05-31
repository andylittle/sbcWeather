
//thanks to mwall for the packet debug info.
//First pass at aruino weater output to weewx. The ws1 uses serial to output the data
// so maybe make a modifed peetbros packet (@@ without hex) and modify the ws1 driver
// to read it
//        WS1 station emits data in PeetBros format:
//        http://www.peetbros.com/shop/custom.aspx?recid=29
//        Each line has 50 characters - 2 header bytes and 48 data bytes:
//        !!000000BE02EB000027700000023A023A0025005800000000
//          SSSSXXDDTTTTLLLLPPPPttttHHHHhhhhddddmmmmRRRRWWWW
//          SSSS - wind speed (0.1 kph)
//          XX   - wind direction calibration
//          DD   - wind direction (0-255)
//          TTTT - outdoor temperature (0.1 F)
//          LLLL - long term rain (0.01 in)
//          PPPP - pressure (0.1 mbar)
//          tttt - indoor temperature (0.1 F)
//          HHHH - outdoor humidity (0.1 %)
//          hhhh - indoor humidity (0.1 %)
//          dddd - date (day of year)
//          mmmm - time (minute of day)
//          RRRR - daily rain (0.01 in)
//          WWWW - one minute wind average (0.1 kph)
     
// Example sketch for DHT22 humidity - temperature sensor
// Written by cactus.io, with thanks to Adafruit for bits of their library. public domain


#include "cactus_io_DHT22.h" //TempSensor lib
#include "BMP280.h" //BMP280 libs
#include "Wire.h"   //BMP280 libs

#define DHT22_PIN 2     // what pin on the arduino is the DHT22 data line connected to
#define P0 1013.25 //BMP280 ? 

// For details on how to hookup the DHT22 sensor to the Arduino then checkout this page
// http://cactus.io/hookups/sensors/temperature-humidity/dht22/hookup-arduino-to-dht22-temp-humidity-sensor

// Initialize DHT sensor for normal 16mhz Arduino. 
DHT22 dht(DHT22_PIN);
// Note: If you are using a board with a faster processor than 16MHz then you need
// to declare an instance of the DHT22 using 
// DHT22 dht(DHT22_DATA_PIN, 30);
// The additional parameter, in this case here is 30 is used to increase the number of
// cycles transitioning between bits on the data and cloines. For the
// Arduino boards that run at 84MHz the value of 30 should be about right.

BMP280 bmp;

void setup() 
{
  Serial.begin(9600); 

  dht.begin();
  bmp.begin();
 // if(!bmp.begin()){
   // Serial.println("BMP init failed!");
  //  while(1);
//  }
//  else Serial.println("BMP init success!");
  
  bmp.setOversampling(4);  
}

void loop() 
{
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  dht.readHumidity();
  dht.readTemperature();
  

  // Check if any reads failed and exit early (to try again).
  if (isnan(dht.humidity) || isnan(dht.temperature_C)) {
    Serial.println("DHT sensor read failure!");
    //return;
    
    
  double T,P;
  char result = bmp.startMeasurment();
 
  if(result!=0){
    delay(result);
    result = bmp.getTemperatureAndPressure(T,P);
    //Serial.println(T,2);
    //Serial.println(P,2);
      if(result!=0)
      {
        double A = bmp.altitude(P,P0);
    //    int ALT = (A,2); 
        Serial.println(T,2);
        Serial.println(P,2);   
      }
      else {
        Serial.println("Error.");
      }   
    // return; 
  }
 } 
  
  int outTEM = (dht.temperature_F * 100);
  int inHUM = (dht.humidity * 100);
  //int inTEM = (100);
  //int inPRE = 100;
  
  Serial.print("!!");
  Serial.print("0000"); //WindSpeed
  Serial.print("00");  //Wind direction calibration
  Serial.print("BE");   // Wind direction 
  Serial.print(outTEM,HEX); //outTEM
  Serial.print("0000");  //longterm rain
  //Serial.print(inPRE,HEX); //pressure
  //Serial.print(inTEM,HEX); //inTemp
  Serial.print(inHUM,HEX); //inHum
  Serial.print("023A");
  Serial.print("0025");   
  Serial.print("0058");
  Serial.print("0000"); 
  Serial.println("0000");  
  //Serial.println(inTEM);
  //Serial.println(inPRE);  

  

  // Wait a few seconds between measurements. The DHT22 should not be read at a higher frequency of
  // about once every 2 seconds. So we add a 3 second delay to cover this.
  delay(3000);
}
//        !!000000BE02EB000027700000023A023A0025005800000000
//          SSSSXXDDTTTTLLLLPPPPttttHHHHhhhhddddmmmmRRRRWWWW
//          SSSS - wind speed (0.1 kph)
//          XX   - wind direction calibration
//          DD   - wind direction (0-255)
//          TTTT - outdoor temperature (0.1 F)
//          LLLL - long term rain (0.01 in)
//          PPPP - pressure (0.1 mbar)
//          tttt - indoor temperature (0.1 F)
//          HHHH - outdoor humidity (0.1 %)
//          hhhh - indoor humidity (0.1 %)
//          dddd - date (day of year)
//          mmmm - time (minute of day)
//          RRRR - daily rain (0.01 in)
//          WWWW - one minute wind average (0.1 kph)
