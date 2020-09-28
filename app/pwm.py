import time

import app.dma as dma
import app.memory_utils as mu

# PWM addresses
PWM_BASE_PHYS = 0x2020C000
PWM_BASE_BUS = 0x7E20C000

# PWM register offsets
PWM_CTL = 0x0  # PWM Control
PWM_DMAC = 0x8  # DMA Configuration
PWM_RNG1 = 0x10  # PWM Channel 1 Range (we'll only be using Channel 1)
PWM_FIFO = 0x18  # FIFO Queue input. This is where we'll be writing dummy data.

# PWM CTL register bits
PWM_CTL_PWEN1 = 1 << 0  # Enable PWM
PWM_CTL_RPTL1 = 1 << 2
PWM_CTL_USEF1 = 1 << 5  # Use FIFO (instead of DAT register)
PWM_CTL_CLRF = 1 << 6  # Clear PWM FIFO

# PWM DMAC register bits
PWM_DMAC_THRSHLD = (15 << 8 | 15 << 0)  # Set DMA Panic and DREQ signal thresholds to 15.
PWM_DMAC_ENAB = 1 << 31  # Enable DMA (So PWM waits for data from DMA)

# PWM clock addresses
PWM_CLK_BASE_BUS = 0x7E1010A0

# PWM clock register offsets
PWM_CLK_CTL = 0x0
PWM_CLK_DIV = 0x4

# PWM clock CTL and DIV register bits
PWM_CLK_PWD = 0x5A << 24
PWM_CLK_ENAB = 1 << 4  # Enable clock.

# Clock source indices
CLK_SRC_OSCILLATOR = 1
CLK_SRC_PLLC = 5
CLK_SRC_PLLD = 6

# Clock source rates in Hz
CLK_SRC_RATES = {
    CLK_SRC_OSCILLATOR: 19200000,
    CLK_SRC_PLLC: 1000000000,
    CLK_SRC_PLLD: 500000000
}

__allowed_clk_src_list = {CLK_SRC_OSCILLATOR, CLK_SRC_PLLC, CLK_SRC_PLLD}


def configure_and_start_pwm(dma_ch, pwm_clk_src, pwm_clk_div_int, pwm_clk_div_frac, pwm_cycles):
    if pwm_clk_src not in __allowed_clk_src_list:
        raise Exception("{} is not a valid clock source.".format(pwm_clk_src))

    if pwm_clk_div_int < 2:
        raise Exception("Clock integer divider must be 2 or greater.")

    pwm_period_ns = 1000000000 / CLK_SRC_RATES[pwm_clk_src] * ((pwm_clk_div_int + pwm_clk_div_frac / 4096) * pwm_cycles)
    print("Starting PWM with a period of " + str(pwm_period_ns) + " ns.")

    clk_cb = dma.ControlBlock()
    clk_cb.set_destination_addr(PWM_CLK_BASE_BUS)
    clk_cb.set_transfer_information(
        dma.DMA_TI_NO_WIDE_BURSTS | dma.DMA_TI_WAIT_RESP | dma.DMA_TI_SRC_INC | dma.DMA_TI_DEST_INC)

    # Stop and configure PWM clock
    clk_cb.set_transfer_length(8)
    clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | pwm_clk_src)
    clk_cb.write_word_to_source_data(PWM_CLK_DIV, PWM_CLK_PWD | pwm_clk_div_frac | pwm_clk_div_int << 12)
    dma.activate_channel_with_cb(dma_ch, clk_cb.addr)
    time.sleep(0.1)

    # Start PWM clock
    clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | pwm_clk_src | PWM_CLK_ENAB)
    dma.activate_channel_with_cb(dma_ch, clk_cb.addr)
    time.sleep(0.1)

    # Configure and start PWM
    with mu.mmap_dev_mem(PWM_BASE_PHYS) as m:
        mu.write_word_to_byte_array(m, PWM_CTL, 0)  # Reset PWM
        mu.write_word_to_byte_array(m, PWM_RNG1, pwm_cycles)
        mu.write_word_to_byte_array(m, PWM_DMAC, PWM_DMAC_ENAB | PWM_DMAC_THRSHLD)
        mu.write_word_to_byte_array(m, PWM_CTL, PWM_CTL_CLRF)  # Clear FIFO
        mu.write_word_to_byte_array(m, PWM_CTL, PWM_CTL_USEF1 | PWM_CTL_RPTL1 | PWM_CTL_PWEN1)
        time.sleep(0.1)


def stop_pwm(dma_ch, pwm_clk_src):
    if pwm_clk_src not in __allowed_clk_src_list:
        raise Exception("{} is not a valid clock source.".format(pwm_clk_src))

    # Reset PWM
    with mu.mmap_dev_mem(PWM_BASE_PHYS) as m:
        mu.write_word_to_byte_array(m, PWM_CTL, PWM_CTL_CLRF)  # Clear FIFO
        mu.write_word_to_byte_array(m, PWM_CTL, 0)  # Reset PWM

    time.sleep(0.1)

    # Stop PWM Clock
    clk_cb = dma.ControlBlock()
    clk_cb.set_destination_addr(PWM_CLK_BASE_BUS)
    clk_cb.set_transfer_information(
        dma.DMA_TI_NO_WIDE_BURSTS | dma.DMA_TI_WAIT_RESP | dma.DMA_TI_SRC_INC | dma.DMA_TI_DEST_INC)
    clk_cb.write_word_to_source_data(PWM_CLK_CTL, PWM_CLK_PWD | pwm_clk_src)
    dma.activate_channel_with_cb(dma_ch, clk_cb.addr)
    time.sleep(0.1)
