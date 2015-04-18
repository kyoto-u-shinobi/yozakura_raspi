YOZAKURA
========

京都大学メカトロニクス研究室メンバー
SHINOBI遠隔班
夜桜

#Settings
##Contec  
**CONTEC access point (yozakura side)     admin:pass**  
IP Address: 192.168.54.225  
IEEE802.11n (2.4 GHz)  10 channels  
コンパチブルインフラストラクチャ  
ESSID SHINOBI_TELE_YOZAKURA_10ch  
WPA2-PSK(AES)  
1:8  

**CONTEC station (opstn side)     blank**  
IP Address: 192.168.54.220  
IEEE802.11n (2.4GHz)  
コンパチブルインフラストラクチャ  
ESSID SHINOBI_TELE_YOZAKURA_10ch  
WPA2-PSK(AES)  
1:8  

##PC  
**Operator Station PC**  
IP Address: 192.168.54.200

**Robot PC (Rasberry Pi)**  
IP Address: 192.168.54.210  

##Camera
**Access point for Ai-Ball**
IP Address: 192.168.54.150  
SSID elecom2g-d3f474  
WPA2-PSK(AES)  
3582988152694  

**AI-Ball for Arm**  
IP Address: 192.168.54.160  

**AI-Ball for Front body**  
IP Address: 192.168.54.161  

**AI-Ball for Back body**  
IP Address: 192.168.54.162  

**AI-Ball for Overview**  
IP Address: 192.168.54.163  

## Others  
**URG(UST-10LX)**  
IP Address: 192.168.54.170  
ref:  
https://www.hokuyo-aut.co.jp/02sensor/07scanner/ust_10lx_20lx.html  
https://www.hokuyo-aut.co.jp/02sensor/07scanner/download/ust-10lx_spec.pdf  
http://www.hokuyo-aut.co.jp/02sensor/07scanner/download/pdf/UST_protocol_ja.pdf  
http://www.hokuyo-aut.co.jp/02sensor/07scanner/download/data/UrgBenri_ja.htm  



#Wiring
##Raspberry Pi

<img src="http://www.element14.com/community/servlet/JiveServlet/previewBody/68203-102-6-294412/GPIO.png" alt="RPi B+ Pinout Diagram" width="600x">

| Connection | Pin # |   | Pin # | Connection |
| ---------: | ----: | :-: | :---- | :--------- |
| 3.3V bus | 1 | | 2 |  |
| SDA bus to I2C devices | 3 | | 4 |  |
| SDC bus to I2C devices | 5 | | 6 | |
| Motor RST bus | 7 | | 8 | Left motor FF1 |
|  Ground bus | 9 | | 10 | Left motor FF2 |
| Right motor FF1 | 11 | | 12 | Left motor current sensor AL |
| Right motor FF2 | 13 | | 14 |  |
| Right motor current sensor AL | 15 | | 16 | Battery current sensor AL|
|  | 17 | | 18 |  |
| Right flipper FF1 | 19 | | 20 | |
| Right flipper FF2 | 21 | | 22 | Left flipper FF1 |
| Right flipper current sensor AL | 23 | | 24 | Left flipper FF2 |
| | 25 | | 26 | Left flipper current sensor AL |

##mbed
<img src="http://nora66.com/mbed/pinout.png" alt="mbedLPC1768 Pinout Diagram" width="400x" align="right">
* p19: Left flipper position ADC
* p20: Right flipper position ADC
* p23: Right flipper PWM
* p24: Left flipper PWM
* p25: Right motor PWM
* p26: Left motor PWM
* p27: Left motor DIR
* p28: Right motor DIR
* p29: Left flipper DIR
* p30: Right flipper DIR

#Raspbian Setup
* Setup I2C
* Install Python 3.4
* `pip install PySerial RPi.GPIO smbus-cffi`
* Install RTIMULib
* Clone Yozakura
* Setup static IP
* If the Base Station is running, run `sudo python3 -m rpi`
