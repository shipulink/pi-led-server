#include <stddef.h>
#include "dma.h"

// DMA physical addresses:
int DMA_BASE_PHYS = 0x20007000;
int DMA_BASE_CH15_PHYS = 0x20E05000;

// DMA register byte offsets (from the base address of a channel)
int DMA_CS = 0x0;
int DMA_CB_AD = 0x4;
int DMA_TI = 0x8;
int DMA_DEBUG = 0x20;

// DMA CS register bits
int DMA_CS_RESET = 1 << 31;
int DMA_CS_ACTIVE = 1 << 0;
int DMA_CS_END = 1 << 1;
int DMA_CS_INT = 1 << 2;
int DMA_CS_PRIORITY = 8 << 16;
int DMA_CS_PANIC_PRIORITY = 8 << 20;
int DMA_CS_WAIT_FOR_OUTSTANDING_WRITES = 1 << 28;

// DMA DEBUG register bits
int DMA_DEBUG_CLR_ERRORS = 0b111;  // Clear Read Error, FIFO Error, Read Last Not Set Error

// DMA TI register bits
int DMA_TI_TD_MODE = 1 << 1;
int DMA_TI_WAIT_RESP = 1 << 3;
int DMA_TI_DEST_INC = 1 << 4;
int DMA_TI_DEST_DREQ = 1 << 6;
int DMA_TI_SRC_INC = 1 << 8;
int DMA_TI_SRC_IGNORE = 1 << 11;
int DMA_TI_NO_WIDE_BURSTS = 1 << 26;
int DMA_TI_PERMAP = 5 << 16;  // 5 = PWM, 2 = PCM

// CB register word (4-byte) offsets
int CB_TI = 0;
int CB_SRC_ADDR = 1;
int CB_DEST_ADDR = 2;
int CB_TXFR_LEN = 3;
int CB_STRIDE = 4;
int CB_NEXT = 5;

struct ControlBlock {
    const int *memory; // shared_mem
    const int wordOffset; // word_offset
    const int address; // addr
    const int dataAddress; // data_addr
};

struct ControlBlock createControlBlockWithSharedMemory(const int *sharedMemory, const int wordOffset) {


    struct ControlBlock cb = {
            .memory = sharedMemory,
            .wordOffset = wordOffset,
            .address = 0,
            .dataAddress = 0
    };
    return cb;
}

struct ControlBlock createControlBlock() {
    return createControlBlockWithSharedMemory(NULL, 2);
}

