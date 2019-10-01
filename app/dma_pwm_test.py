import time

import mmap

import app.dma as dma
import app.memory_utils as mu

SRC = 5  # 1 = Oscillator = 19.2MHz; 5 = PLLC = 1GHz; 6 = PLLD = 500MHz
DIVISOR = 8
PWM_CYCLES = 8

PLAY_SECONDS = 5
DMA_CH = 0

# DMA constants
DMA_CHA = 0x100 * DMA_CH
DMA_DIS_DEBUG = 1 << 29
DMA_NO_WIDE_BURSTS = 1 << 26
DMA_WAITS = 0 << 21
DMA_PERMAP = 5 << 16  # 5 = PWM, 2 = PCM
DMA_SRC_IGNORE = 1 << 11
DMA_SRC_INC = 1 << 8
DMA_DEST_IGNORE = 1 << 7
DMA_DEST_DREQ = 1 << 6
DMA_DEST_INC = 1 << 4
DMA_WAIT_RESP = 1 << 3

DMA_RESET = 1 << 31
DMA_INT = 1 << 2
DMA_END = 1 << 1

PWM_DMA_FLAGS = 0
PWM_DMA_FLAGS |= DMA_PERMAP
PWM_DMA_FLAGS |= DMA_DEST_DREQ
# PWM_DMA_FLAGS |= DMA_WAITS
# PWM_DMA_FLAGS |= DMA_SRC_IGNORE
# PWM_DMA_FLAGS |= DMA_DEST_IGNORE
PWM_DMA_FLAGS |= DMA_NO_WIDE_BURSTS
PWM_DMA_FLAGS |= DMA_WAIT_RESP

freq = 0
if SRC == 1:
    freq = 19200000
elif SRC == 5:
    freq = 1000000000
elif SRC == 6:
    freq = 500000000

width = 1000000000 / (freq / (DIVISOR * PWM_CYCLES)) + 4 * (DMA_WAITS >> 21)
print(width)

MMAP_FLAGS = mmap.MAP_SHARED
MMAP_PROT = mmap.PROT_READ | mmap.PROT_WRITE

# PWM Clock addresses and offsets
PWM_CLK_BASE = 0x7E1010A0
PWM_CLK_BASE_PHYS = 0x20101000
PWM_CLK_CTL = 0x0
PWM_CLK_DIV = 0x4

# PWM Clock constants
PWM_CLK_PWD = 0x5A << 24
PWM_CLK_SRC = SRC << 0
PWM_CLK_INT_DIV = DIVISOR << 12  # Integer divisor. Clock rate will be SRC clock rate / this.
PWM_CLK_ENAB = 1 << 4  # Enable clock.

# PWM addresses and offsets
PWM_BASE = 0x2020C000
PWM_BASE_BUS = 0x7E20C000
PWM_CTL = 0x0  # PWM Control
PWM_DMAC = 0x8  # DMA Configuration
PWM_RNG1 = 0x10  # PWM Channel 1 Range (we'll only be using Channel 1)
PWM_FIFO = 0x18  # FIFO Queue input. This is where we'll be writing dummy data, from what I understand.

# PWM constants
PWM_DMAC_ENAB = 1 << 31  # Enable DMA (So PWM waits for data from DMA)
PWM_DMAC_THRSHLD = (15 << 8 | 15 << 0)  # Set DMA Panic and DREQ signal thresholds to 15.
PWM_CTL_CLRF = 1 << 6  # Clear PWM FIFO
PWM_CTL_USEF1 = 1 << 5  # Use FIFO (instead of DAT register)
PWM_CTL_PWEN1 = 1 << 0  # Enable PWM
PWM_CTL_MODE1 = 1 << 1

# GPIO addresses
GPIO_BASE = 0x7E200000
GPFSEL1 = GPIO_BASE + 0x4
GPSET0 = GPIO_BASE + 0x1C
GPCLR0 = GPIO_BASE + 0x28

SLEEP_TIME = .1

clk_cb = dma.ControlBlock()
clk_cb.set_destination_addr(PWM_CLK_BASE)
clk_cb.set_transfer_information(DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP | DMA_SRC_INC | DMA_DEST_INC)

# Stop and configure the PWM clock
clk_cb.init_source_data(8)
clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | PWM_CLK_SRC)
clk_cb.write_word_to_source_data(PWM_CLK_DIV, PWM_CLK_PWD | PWM_CLK_INT_DIV)
dma.activate_channel_with_cb(0, clk_cb.addr)
time.sleep(SLEEP_TIME)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=PWM_CLK_BASE_PHYS) as pwm_clk_mem:
        print('PWM_CLK_CTL: ' + ':'.join(format(x, '08b') for x in pwm_clk_mem[0xA0:0xA4][::-1]))
        print('PWM_CLK_DIV: ' + ':'.join(format(x, '08b') for x in pwm_clk_mem[0xA4:0xA8][::-1]))

# Enable the PWM clock
clk_cb.init_source_data(4)
clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | PWM_CLK_SRC | PWM_CLK_ENAB)
dma.activate_channel_with_cb(0, clk_cb.addr)
time.sleep(SLEEP_TIME)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=PWM_CLK_BASE_PHYS) as pwm_clk_mem:
        print('PWM_CLK_CTL: ' + ':'.join(format(x, '08b') for x in pwm_clk_mem[0xA0:0xA4][::-1]))

# Configure and start PWM
with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=PWM_BASE) as pwm_mem:
        mu.write_word_to_byte_array(pwm_mem, PWM_CTL, 0)  # Reset PWM
        mu.write_word_to_byte_array(pwm_mem, PWM_RNG1,
                                    PWM_CYCLES)  # PWM will run for this many clock cycles, then ask for more data
        mu.write_word_to_byte_array(pwm_mem, PWM_DMAC, PWM_DMAC_ENAB | PWM_DMAC_THRSHLD)
        mu.write_word_to_byte_array(pwm_mem, PWM_CTL, PWM_CTL_CLRF)  # Clear FIFO
        mu.write_word_to_byte_array(pwm_mem, PWM_CTL, PWM_CTL_USEF1 | PWM_CTL_MODE1 | PWM_CTL_PWEN1)

        print('PWM_DMA: ' + ':'.join(format(x, '08b') for x in pwm_mem[PWM_DMAC:PWM_DMAC + 4][::-1]))
        print('PWM_RNG: ' + ':'.join(format(x, '08b') for x in pwm_mem[PWM_RNG1:PWM_RNG1 + 4][::-1]))
        print('PWM_CTL: ' + ':'.join(format(x, '08b') for x in pwm_mem[PWM_CTL:PWM_CTL + 4][::-1]))

time.sleep(SLEEP_TIME)

# Configure GPIO
cb_gpio_conf = dma.ControlBlock()
cb_gpio_conf.init_source_data(4)
cb_gpio_conf.write_word_to_source_data(0x0, 1 << 24)
cb_gpio_conf.set_transfer_information(DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP | DMA_SRC_INC | DMA_DEST_INC)
cb_gpio_conf.set_destination_addr(GPFSEL1)
dma.activate_channel_with_cb(0, cb_gpio_conf.addr)
time.sleep(SLEEP_TIME)

# Create 4 CBs. CB0: Wait, CB1: Set pin, CB2: Wait, CB3: Clear pin
cbs = dma.build_linked_cb_list(6)

cbs[0].init_source_data(4)
# cbs[0].write_word_to_source_data(0x0, 0)
cbs[0].set_transfer_information(PWM_DMA_FLAGS)
cbs[0].set_destination_addr(PWM_BASE_BUS + PWM_FIFO)

cbs[1].init_source_data(4)
cbs[1].write_word_to_source_data(0x0, 1 << 18)  # pin 18
cbs[1].set_transfer_information(DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP | DMA_WAITS)
cbs[1].set_destination_addr(GPCLR0)

cbs[2].init_source_data(4)
# cbs[2].write_word_to_source_data(0x0, 0)
cbs[2].set_transfer_information(PWM_DMA_FLAGS)
cbs[2].set_destination_addr(PWM_BASE_BUS + PWM_FIFO)

cbs[3].init_source_data(4)
cbs[3].write_word_to_source_data(0x0, 1 << 18)  # pin 18
cbs[3].set_transfer_information(DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP | DMA_WAITS)
cbs[3].set_destination_addr(GPSET0)
cbs[3].set_next_cb(cbs[0].addr)

dma.activate_channel_with_cb(0, cbs[0].addr)

# Have to sleep because otherwise the program finishes too early,
# and the CBs in memory get cleaned up, so there's nothing for the DMA to reference.
time.sleep(PLAY_SECONDS)

# Stop the PWM clock when we're done
clk_cb.init_source_data(4)
clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | PWM_CLK_SRC)
dma.activate_channel_with_cb(0, clk_cb.addr)
time.sleep(SLEEP_TIME)
