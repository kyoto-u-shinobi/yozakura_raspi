Hardware and Software Setup
===========================

The Raspberry Pi in use is a Raspberry Pi B+. The RPi 2 B+ will also work.

-----------------
Environment setup
-----------------
First, set up the base station and RPi environments.

While they work on any flavour of Linux, this guide assumes that the base station runs Ubuntu, and the RPi runs Raspbian.

Ubuntu setup
------------
* Install pygame for Python 3.x. You might need to compile from source.
* Set the static IP to 192.168.54.200

Raspbian setup
--------------
* Setup I2C
* Install Python 3.4
* ``pip install PySerial RPi.GPIO smbus-cffi``
* Install RTIMULib. You will need to compile from source.
* Clone Yozakura locally
* Set the static IP to 192.168.54.210


-----------
Peripherals
-----------
The base station and the RPi use a CONTEC router to connect wirelessly. The wireless cameras connect to an elecom router. Also connected is a URG laser range finder.

CONTEC
------
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CONTEC station (connected to base station)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Authentication is blank
* Set the IP address to 192.168.54.220
* Set the connection mode to IEEE 802.11n (5 GHz)
* Select compatible infrastructure
* Set the ESSID to RRL10_SHINOBI_TELE_YOZAKURA_44ch
* Set the security to WPA2-PSK (AES)
* 1:8

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CONTEC access point (connected to RPi)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Authentication is admin:pass
* Set the IP address to 192.168.54.225
* Set the connection mode to IEEE 802.11n (5 GHz)
* Select compatible infrastructure
* Set the ESSID to RRL10_SHINOBI_TELE_YOZAKURA_44ch
* Set the security to WPA2-PSK (AES)
* 1:8

Cameras
-------
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ai-Ball access point (elecom)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* set the IP address to 192.168.54.150
* Set the ESSID to elecom2g-d3f474
* Set the security to WPA2-PSK (AES)
* 3582988152694

~~~~~~~~~~~~~~~~~~~
Camera IP addresses
~~~~~~~~~~~~~~~~~~~
* Overview: 192.168.54.160
* Front: 192.168.54.161
* Rear: 192.168.54.162
* Arm: 192.168.54.163

URG (UST-10LX)
--------------
IP Address: 192.168.54.170

Reference documentation:

* https://www.hokuyo-aut.co.jp/02sensor/07scanner/ust_10lx_20lx.html  
* https://www.hokuyo-aut.co.jp/02sensor/07scanner/download/ust-10lx_spec.pdf  
* http://www.hokuyo-aut.co.jp/02sensor/07scanner/download/pdf/UST_protocol_ja.pdf  
* http://www.hokuyo-aut.co.jp/02sensor/07scanner/download/data/UrgBenri_ja.htm  


--------------
Hardware setup
--------------
Wiring
------
~~~~~~~~~~~~
Raspberry Pi
~~~~~~~~~~~~
.. image:: _static/images/rpi_pinout.png
   :width: 600px
   :alt: RPi B+ pinout diagram

================================ ======= === ======= ================================
 Connection                       Pin #       Pin #   Connection
================================ ======= === ======= ================================
 3.3V bus                         1           2   
 SDA bus to I2C devices           3           4   
 SDC bus to I2C devices           5           6  
 Motor RST bus                    7           8       Left motor FF1 
 Ground bus                       9           10      Left motor FF2 
 Right motor FF1                  11          12      Left motor current sensor AL 
 Right motor FF2                  13          14   
 Right motor current sensor AL    15          16      Battery current sensor AL
\                                 17          18   
 Right flipper FF1                19          20  
 Right flipper FF2                21          22      Left flipper FF1 
 Right flipper current sensor AL  23          24      Left flipper FF2 
\                                 25          26      Left flipper current sensor AL 
================================ ======= === ======= ================================


mbed
~~~~
.. image:: _static/images/mbed_pinout.png
   :width: 400px
   :align: right
   :alt: mbed LPC1768 pinout diagram

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
