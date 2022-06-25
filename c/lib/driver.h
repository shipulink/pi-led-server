#ifndef driver
#define driver

int stripCount;
int ledsPerStrip;

void init(int numStrips, int stripLength, int gpioPinNumbers[]);
void start();
void stop();
void processFrame(unsigned char data[stripCount][ledsPerStrip][3]);

#endif // driver
