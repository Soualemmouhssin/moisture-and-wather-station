# moisture-and-wather-station
This project uses a micropython with ESP nodemcu  to control moisture of plants using MQTT Protocol 
This project allows to control moisture and autmate irrigation process for plants using ESP8266 and MQTT Server and getting the temperature and humidity of the GREEn HOUSE 
The user can modify all configuration by the config.txt file which allows the user to modify network configuration and MQTT Server infromations 
The device could work on two modes 
Automatic : the user set the threshold value of moisture and the device control the relay on pin 16 
Manual : user can command dirctly the relay pin sending values 0 , 1 
The project includes a captive portal that allows users to change the wifi network credentials 
