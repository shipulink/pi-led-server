#include <stdio.h>

#include "driver.h"

int stripCount;
int ledsPerStrip;

//TODO: port over the following Python files:
//      dma.py
//      gpio.py
//      led_frame_data.py
//      memory_utils.py
//      neopixel_driver (this)
//      pwm.py

int dmaData;
int gpioPins;
int sharedMemory; // memory allocated for all the CBs

// CBs:
int cbIdleWait;
int cbIdleClr;

int cbDataAdvance;
int cbDataUpdate;

int cbDataWait1;
int cbDataSetClr;
int cbDataWait2;
int cbDataClr;

int cbPause;

void init(int numStrips, int stripLength, int gpioPinNumbers[]) {

    stripCount = numStrips;
    ledsPerStrip = stripLength;

}

void start() {

}

void stop() {

}

void processFrame(unsigned char data[stripCount][ledsPerStrip][3]) {

}
