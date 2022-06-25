#include "memoryUtils.h"
#include <stdio.h>
#include <sys/mman.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdbool.h>

// MMAP constants:
const int MMAP_FLAGS = MAP_SHARED;
const int MMAP_PROT = PROT_READ | PROT_WRITE;
const int PAGEMAP_LENGTH = 8; // Data in pagemap is stored in 64-bit (8-byte) chunks. One per mapping.
const int PAGE_SHIFT = 12;

FILE *pagemap = 0;

struct FileInfo {
    const int fileDescriptor;
    const struct stat statBuffer;
};

struct MmapInfo {
    const struct stat statBuffer;
    void *ptr;
};

struct AddrInfo {
    const unsigned long frameStart;
    const unsigned int offset;
    const unsigned long pAddr;
};

FILE *getPagemap() {
    if (!pagemap) {
        pagemap = fopen("/proc/self/pagemap", "rb");
    }
    return pagemap;
}

void closePagemap() {
    fclose(pagemap);
    pagemap = 0;
}

struct FileInfo openFile(char filePath[]) {
    // Try to open file
    int fileDescriptor = open(filePath, O_RDWR);
    if (fileDescriptor < 0) {
        printf("ERROR: Could not open file %s\n", filePath);
        exit(1);
    }

    struct stat statBuffer;
    int err = fstat(fileDescriptor, &statBuffer);
    if (err < 0) {
        printf("ERROR: Could not open file %s\n", filePath);
        exit(2);
    }

    struct FileInfo f = {
            fileDescriptor,
            statBuffer
    };

    return f;
}

void closeFile(struct FileInfo f) {
    close(f.fileDescriptor);
}

struct MmapInfo mmapDevMem(long addr) {
    char filePath[] = "/dev/mem";
    struct FileInfo f = openFile(filePath);

    // Try to map file memory
    void *ptr = mmap(NULL, f.statBuffer.st_size, MMAP_PROT, MMAP_FLAGS, f.fileDescriptor, addr);
    closeFile(f);
    if (ptr == MAP_FAILED) {
        printf("ERROR: Failed to map %s\n", filePath);
        exit(3);
    }

    struct MmapInfo mi = {
            f.statBuffer,
            ptr
    };

    return mi;
}

void munmapDevMem(struct MmapInfo mi) {
    int err = munmap(mi.ptr, mi.statBuffer.st_size);
    if (err != 0) {
        printf("WARN: Failed to unmap memory.\n");
    }
}

struct AddrInfo virtualToPhysicalAddress(void *buffer) {
    unsigned long offset = (unsigned long) buffer / getpagesize() * PAGEMAP_LENGTH;
    if (fseek(getPagemap(), (long) offset, SEEK_SET) != 0) {
        printf("ERROR: Failed to seek pagemap to proper location\n");
        exit(5);
    }

    // The page frame number is in bits 0-54 so read the first 7 bytes and clear the 55th bit
    unsigned long pageFrameNumber = 0;
    fread(&pageFrameNumber, 1, PAGEMAP_LENGTH - 1, pagemap);

    pageFrameNumber &= 0x7FFFFFFFFFFFFF;

    unsigned long frameStart = pageFrameNumber << PAGE_SHIFT;
    unsigned int addrOffset = (unsigned long) buffer % getpagesize();
    unsigned long physicalAddr = frameStart + addrOffset;

    struct AddrInfo addrInfo = {
            frameStart,
            addrOffset,
            physicalAddr
    };

    return addrInfo;
}

bool checkPhysicallyContiguous(void *buffer, int byteSize) {
    char *byteBuffer = (char *) buffer;
    char originalLastByte = byteBuffer[byteSize - 1];
    char newLastByte;

    if (originalLastByte == 0) {
        newLastByte = 1;
    } else {
        newLastByte = 0;
    }

    byteBuffer[byteSize - 1] = newLastByte;

    struct AddrInfo bufferAddrInfo = virtualToPhysicalAddress(buffer);
    struct MmapInfo devMem = mmapDevMem((long) bufferAddrInfo.frameStart);
    char result = ((char *) devMem.ptr)[bufferAddrInfo.offset + byteSize - 1];
    bool isContiguous = result == newLastByte;
    munmapDevMem(devMem);
    byteBuffer[byteSize - 1] = originalLastByte;
    return isContiguous;
}

void *mallocPhysicallyContiguous(int byteSize) {
    void *ptr = malloc(byteSize);
    int fails = 0;
    while (fails < 5) {
        if (checkPhysicallyContiguous(ptr, byteSize)) {
            return ptr;
        }
        fails++;
    }
    exit(4);
}

int *mallocAligned(int byteSize, int byteAlignment) {
    // TODO: Implement this!
    // https://stackoverflow.com/questions/227897/how-to-allocate-aligned-memory-only-using-the-standard-library
}
