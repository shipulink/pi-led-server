import array
import ctypes
import time

import mmap

import app.dma as dma
import app.memory_utils as mu

SRC = 6  # 1 = Oscillator = 19.2MHz; 5 = PLLC = 1GHz; 6 = PLLD = 500MHz
DIV = 128
CYCLES = 128

PLAY_SECONDS = 5
DMA_CH = 0

print(1000000000 / 500000000 * (DIV * CYCLES))

# MMAP constants:
MMAP_FLAGS = mmap.MAP_SHARED
MMAP_PROT = mmap.PROT_READ | mmap.PROT_WRITE

# GPIO addresses
GPIO_BASE = 0x7E200000
GPFSEL1 = GPIO_BASE + 0x4
GPSET0 = GPIO_BASE + 0x1C
GPCLR0 = GPIO_BASE + 0x28

# DMA constants
DMA_TD_MODE = 1 << 1
DMA_WAIT_RESP = 1 << 3
DMA_DEST_INC = 1 << 4
DMA_DEST_DREQ = 1 << 6
DMA_SRC_INC = 1 << 8
DMA_SRC_IGNORE = 1 << 11
DMA_WAITS = 0 << 21
DMA_NO_WIDE_BURSTS = 1 << 26
DMA_PERMAP = 5 << 16  # 5 = PWM, 2 = PCM

DMA_FLAGS = DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP | DMA_WAITS
PWM_DMA_FLAGS = DMA_PERMAP | DMA_DEST_DREQ | DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP

# PWM addresses
PWM_BASE = 0x2020C000
PWM_BASE_BUS = 0x7E20C000
PWM_CTL = 0x0  # PWM Control
PWM_DMAC = 0x8  # DMA Configuration
PWM_RNG1 = 0x10  # PWM Channel 1 Range (we'll only be using Channel 1)
PWM_FIFO = 0x18  # FIFO Queue input. This is where we'll be writing dummy data.
PWM_CYCLES = CYCLES  # PWM period will be this many PWM clock cycles long

# PWM constants
PWM_DMAC_ENAB = 1 << 31  # Enable DMA (So PWM waits for data from DMA)
PWM_DMAC_THRSHLD = (15 << 8 | 15 << 0)  # Set DMA Panic and DREQ signal thresholds to 15.
PWM_CTL_CLRF = 1 << 6  # Clear PWM FIFO
PWM_CTL_USEF1 = 1 << 5  # Use FIFO (instead of DAT register)
PWM_CTL_MODE1 = 1 << 1
PWM_CTL_PWEN1 = 1 << 0  # Enable PWM

# PWM clock addresses and offsets
PWM_CLK_BASE = 0x7E1010A0
PWM_CLK_CTL = 0x0
PWM_CLK_DIV = 0x4

# PWM clock constants
PWM_CLK_PWD = 0x5A << 24
PWM_CLK_SRC = SRC << 0
PWM_CLK_INT_DIV = DIV << 12  # Integer divisor. Clock rate will be SRC clock rate / this.
PWM_CLK_ENAB = 1 << 4  # Enable clock.


def build_control_array(num_bytes):
    num_bits = num_bytes * 8 + 1
    c_int_arr = ctypes.c_int32 * (num_bits * 2)
    data = c_int_arr()
    base_addr = mu.virtual_to_physical_addr(ctypes.addressof(data)).p_addr

    i = 0
    while i < num_bits - 1:
        data[i] = base_addr + 4 * (i + 1)
        i += 1
    data[num_bits - 1] = base_addr
    return data


def populate_control_array(target_int_arr, src_bytes, ad_low, ad_high, ad_stop):
    if (len(src_bytes) * 8 + 1) * 2 != len(target_int_arr):
        raise Exception("Length of src_bytes is incompatible with length of target_int_arr.")

    num_bits = int(len(target_int_arr) / 2)

    bit_ind = num_bits
    i = 0
    while i < len(src_bytes):
        j = 0
        while j < 8:
            if src_bytes[i] & (128 >> j) == 0:
                target_int_arr[bit_ind] = ad_low
            else:
                target_int_arr[bit_ind] = ad_high
            bit_ind += 1
            j += 1
        i += 1
    target_int_arr[num_bits * 2 - 1] = ad_stop

    return target_int_arr


# Build control array from incoming bytes
ints = [0b10110110]
# ints = [0b11111111]
# ints = [0b0]
# ints = [0b11110000]
byte_arr = array.array("B", ints)
ctl_arr = build_control_array(len(byte_arr))

# Allocate enough memory for all the CBs. For each CB, 32 bytes for config, 32 bytes for data.
shared_mem = mu.ctypes_alloc_aligned(1024, 32)

# CBs common to both the Zero and One flows.
CB_WAIT = dma.ControlBlock2(shared_mem, 0x0)
CB_WAIT_L = dma.ControlBlock2(shared_mem, 0x40)
CB_UPD = dma.ControlBlock2(shared_mem, 0x80)  # Needs stride. Updates its own src addr and CB_DATA_WAIT's next CB addr
CB_DATA_WAIT = dma.ControlBlock2(shared_mem, 0xC0)
CB_STOP = dma.ControlBlock2(shared_mem, 0x100)

# CBs for representing a zero
CB_ZERO_H1 = dma.ControlBlock2(shared_mem, 0x140)
CB_ZERO_W1 = dma.ControlBlock2(shared_mem, 0x180)
CB_ZERO_L1 = dma.ControlBlock2(shared_mem, 0x1C0)

# CBs for representing a one
CB_ONE_H1 = dma.ControlBlock2(shared_mem, 0x200)
CB_ONE_W1 = dma.ControlBlock2(shared_mem, 0x240)
CB_ONE_W2 = dma.ControlBlock2(shared_mem, 0x280)
CB_ONE_L1 = dma.ControlBlock2(shared_mem, 0x2C0)

# Configure Common CBs
CB_WAIT.set_transfer_information(PWM_DMA_FLAGS)
CB_WAIT.set_destination_addr(PWM_BASE_BUS + PWM_FIFO)
CB_WAIT.set_next_cb(CB_WAIT_L.addr)

CB_WAIT_L.set_transfer_information(DMA_FLAGS)
CB_WAIT_L.write_word_to_source_data(0x0, 1 << 18)  # pin 18
CB_WAIT_L.set_destination_addr(GPCLR0)
CB_WAIT_L.set_next_cb(CB_WAIT.addr)

src_stride = int(len(ctl_arr) / 2) * 4
dest_stride = CB_DATA_WAIT.addr + 0x14 - (CB_UPD.addr + 0x4)
CB_UPD.set_transfer_information(DMA_FLAGS | DMA_TD_MODE)
CB_UPD.set_source_addr(mu.virtual_to_physical_addr(ctypes.addressof(ctl_arr)).p_addr)
CB_UPD.set_destination_addr(CB_UPD.addr + 0x4)
CB_UPD.set_transfer_length_stride(4, 2)
CB_UPD.set_stride(src_stride, dest_stride)
CB_UPD.set_next_cb(CB_DATA_WAIT.addr)

CB_DATA_WAIT.set_transfer_information(PWM_DMA_FLAGS)
CB_DATA_WAIT.set_destination_addr(PWM_BASE_BUS + PWM_FIFO)

CB_STOP.set_transfer_information(DMA_FLAGS)
CB_STOP.write_word_to_source_data(0x0, CB_WAIT.addr)
CB_STOP.set_destination_addr(CB_WAIT_L.addr + 0x14)
CB_STOP.set_next_cb(CB_WAIT.addr)

# Configure CBs for representing a zero
CB_ZERO_H1.set_transfer_information(DMA_FLAGS)
CB_ZERO_H1.write_word_to_source_data(0x0, 1 << 18)  # pin 18
CB_ZERO_H1.set_destination_addr(GPSET0)
CB_ZERO_H1.set_next_cb(CB_ZERO_W1.addr)

CB_ZERO_W1.set_transfer_information(PWM_DMA_FLAGS)
CB_ZERO_W1.set_destination_addr(PWM_BASE_BUS + PWM_FIFO)
CB_ZERO_W1.set_next_cb(CB_ZERO_L1.addr)

CB_ZERO_L1.set_transfer_information(DMA_FLAGS)
CB_ZERO_L1.write_word_to_source_data(0x0, 1 << 18)  # pin 18
CB_ZERO_L1.set_destination_addr(GPCLR0)
CB_ZERO_L1.set_next_cb(CB_UPD.addr)

# Configure CBs for representing a one
CB_ONE_H1.set_transfer_information(DMA_FLAGS)
CB_ONE_H1.write_word_to_source_data(0x0, 1 << 18)  # pin 18
CB_ONE_H1.set_destination_addr(GPSET0)
CB_ONE_H1.set_next_cb(CB_ONE_W1.addr)

CB_ONE_W1.set_transfer_information(PWM_DMA_FLAGS)
CB_ONE_W1.set_destination_addr(PWM_BASE_BUS + PWM_FIFO)
CB_ONE_W1.set_next_cb(CB_ONE_W2.addr)

CB_ONE_W2.set_transfer_information(PWM_DMA_FLAGS)
CB_ONE_W2.set_destination_addr(PWM_BASE_BUS + PWM_FIFO)
CB_ONE_W2.set_next_cb(CB_ONE_L1.addr)

CB_ONE_L1.set_transfer_information(DMA_FLAGS)
CB_ONE_L1.write_word_to_source_data(0x0, 1 << 18)  # pin 18
CB_ONE_L1.set_destination_addr(GPCLR0)
CB_ONE_L1.set_next_cb(CB_UPD.addr)

populate_control_array(ctl_arr, byte_arr, CB_ZERO_H1.addr, CB_ONE_H1.addr, CB_STOP.addr)

ad_info = mu.virtual_to_physical_addr(ctypes.addressof(ctl_arr))
with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096 * 4, MMAP_FLAGS, MMAP_PROT, offset=ad_info.frame_start) as m:
        str_arr = []
        k = 0
        while k < (len(byte_arr) * 8 + 1) * 2:
            start = ad_info.offset + k * 4
            end = start + 4
            str_arr.append(''.join(format(x, '02x') for x in m[start:end][::-1]))
            k += 1
        print(':'.join(str_arr))

########################################
# Stop, configure, and start PWM clock #
########################################
clk_cb = dma.ControlBlock()
clk_cb.set_destination_addr(PWM_CLK_BASE)
clk_cb.set_transfer_information(DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP | DMA_SRC_INC | DMA_DEST_INC)

# Stop and configure PWM clock
clk_cb.init_source_data(8)
clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | PWM_CLK_SRC)
clk_cb.write_word_to_source_data(PWM_CLK_DIV, PWM_CLK_PWD | PWM_CLK_INT_DIV)
dma.activate_channel_with_cb(DMA_CH, clk_cb.addr)
time.sleep(0.1)

# Start PWM clock
clk_cb.init_source_data(4)
clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | PWM_CLK_SRC | PWM_CLK_ENAB)
dma.activate_channel_with_cb(DMA_CH, clk_cb.addr)
time.sleep(0.1)

###########################
# Configure and start PWM #
###########################
with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=PWM_BASE) as pwm_mem:
        mu.write_word_to_byte_array(pwm_mem, PWM_CTL, 0)  # Reset PWM
        mu.write_word_to_byte_array(pwm_mem, PWM_RNG1, PWM_CYCLES)
        mu.write_word_to_byte_array(pwm_mem, PWM_DMAC, PWM_DMAC_ENAB | PWM_DMAC_THRSHLD)
        mu.write_word_to_byte_array(pwm_mem, PWM_CTL, PWM_CTL_CLRF)  # Clear FIFO
        mu.write_word_to_byte_array(pwm_mem, PWM_CTL, PWM_CTL_USEF1 | PWM_CTL_MODE1 | PWM_CTL_PWEN1)
time.sleep(0.1)

#############
# Init GPIO #
#############
cb_gpio_conf = dma.ControlBlock()
cb_gpio_conf.init_source_data(4)
cb_gpio_conf.write_word_to_source_data(0x0, 1 << 24)
cb_gpio_conf.set_transfer_information(DMA_WAIT_RESP)
cb_gpio_conf.set_destination_addr(GPFSEL1)
dma.activate_channel_with_cb(DMA_CH, cb_gpio_conf.addr)
time.sleep(0.1)

#############
# Start DMA #
#############
dma.activate_channel_with_cb(DMA_CH, CB_WAIT.addr)
time.sleep(0.1)

start = time.time()
while time.time() - start < PLAY_SECONDS:
    CB_WAIT_L.set_next_cb(CB_UPD.addr)
    # time.sleep(.01)

############
# Stop PWM #
############
clk_cb.init_source_data(4)
clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | PWM_CLK_SRC)
dma.activate_channel_with_cb(DMA_CH, clk_cb.addr)
time.sleep(0.1)
