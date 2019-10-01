# pi-led-server
A Rest API LED strip (NeoPixel) controller for Raspberry Pi Zero

To ensure smooth operation:
1. Disable on-board audio by blacklisting the audio kernel module:  
Add `blacklist snd_bcm2835` to `/etc/modprobe.d/snd-blacklist.conf` (create the file if it isn't there)
2. Disable video output (your pi will have to be headless):  
Add `/usr/bin/tvservice -o` to `/etc/rc.local`.

Note: These changes will take effect only after restarting your Pi.