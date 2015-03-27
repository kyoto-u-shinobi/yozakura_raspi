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
**AI-Ball for Arm**  
IP Address: 192.168.54.160  

**AI-Ball for Front body**  
IP Address: 192.168.54.161  

**AI-Ball for Back body**  
IP Address: 192.168.54.162  

**AI-Ball for Overview**  
IP Address: 192.168.54.163  

#Wiring
##Raspberry Pi

<img src="http://www.element14.com/community/servlet/JiveServlet/previewBody/68203-102-6-294412/GPIO.png" alt="RPi B+ Pinout Diagram" width="490x" align="right">
* Pin 1: Power bus to devices
* Pin 3: SDA bus to devices
* Pin 5: SDC bus to devices
* Pin 6: Ground bus
* Pin 7: Reset motors bus
* Pin 8: Left motor FF1
* Pin 10: Left motor FF2
* Pin 11: Right motor FF1
* Pin 12: Left motor current alert
* Pin 13: Right motor FF2
* Pin 15: Right motor current alert
* Pin 16: Battery current alert
* Pin 19: Right flipper FF1
* Pin 21: Right flipper FF2
* Pin 22: Left flipper FF1
* Pin 23: Right flipper current alert
* Pin 24: Left flipper FF2
* Pin 26: Left flipper current alert
* Pin 16: Right flipper FF1
* Pin 18: Right flipper FF2

##mbed
<img src="http://nora66.com/mbed/pinout.png" alt="mbedLPC1768 Pinout Diagram" width="400x" align="right">
* Pin 19: Left flipper position ADC
* Pin 20: Right flipper position ADC
* Pin 23: Right flipper PWM
* Pin 24: Left flipper PWM
* Pin 25: Right motor PWM
* Pin 26: Left motor PWM
* Pin 27: Left motor DIR
* Pin 28: Right motor DIR
* Pin 29: Left flipper DIR
* Pin 30: Right flipper DIR
