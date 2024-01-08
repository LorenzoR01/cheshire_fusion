#ifndef _RISCV_DEVICES_H
#define _RISCV_DEVICES_H

#include "decode.h"
#include <cstdlib>
#include <string>
#include <map>
#include <vector>
#include <fstream>

class processor_t;

class abstract_device_t {
 public:
  virtual bool load(reg_t addr, size_t len, uint8_t* bytes) = 0;
  virtual bool store(reg_t addr, size_t len, const uint8_t* bytes) = 0;
  virtual ~abstract_device_t() {}
};

class bus_t : public abstract_device_t {
 public:
  bool load(reg_t addr, size_t len, uint8_t* bytes);
  bool store(reg_t addr, size_t len, const uint8_t* bytes);
  void add_device(reg_t addr, abstract_device_t* dev);

  std::pair<reg_t, abstract_device_t*> find_device(reg_t addr);

 private:
  std::map<reg_t, abstract_device_t*> devices;
};

class rom_device_t : public abstract_device_t {
 public:
  rom_device_t(std::vector<char> data);
  bool load(reg_t addr, size_t len, uint8_t* bytes);
  bool store(reg_t addr, size_t len, const uint8_t* bytes);
  const std::vector<char>& contents() { return data; }
 private:
  std::vector<char> data;
};

class mem_t : public abstract_device_t {
 public:
  mem_t(size_t size) : len(size) {
    if (!size)
      throw std::runtime_error("zero bytes of target memory requested");
    data = (char*)calloc(1, size);
    if (!data)
      throw std::runtime_error("couldn't allocate " + std::to_string(size) + " bytes of target memory");
  }
  mem_t(const mem_t& that) = delete;
  ~mem_t() { free(data); }

  bool load(reg_t addr, size_t len, uint8_t* bytes) { return false; }
  bool store(reg_t addr, size_t len, const uint8_t* bytes) { return false; }
  char* contents() { return data; }
  size_t size() { return len; }

 private:
  char* data;
  size_t len;
};

class clint_t : public abstract_device_t {
 public:
  clint_t(std::vector<processor_t*>&);
  bool load(reg_t addr, size_t len, uint8_t* bytes);
  bool store(reg_t addr, size_t len, const uint8_t* bytes);
  void reset();
  size_t size() { return CLINT_SIZE; }
  void increment(reg_t inc);
 private:
  typedef uint64_t mtime_t;
  typedef uint64_t mtimecmp_t;
  typedef uint32_t msip_t;
  std::vector<processor_t*>& procs;
  mtime_t mtime;
  std::vector<mtimecmp_t> mtimecmp;
};

class uart_t : public abstract_device_t {
 public:
  uart_t();
  bool load(reg_t addr, size_t len, uint8_t* bytes);
  bool store(reg_t addr, size_t len, const uint8_t* bytes);
  int  tick(reg_t dec);
 private:
  uint8_t ier;
  uint8_t dll;
  uint8_t dlm;
  uint8_t lcr;
  uint8_t lsr;
  uint8_t scr;
  uint8_t msr;
  uint8_t mcr;
  bool fifo_enabled;
  uint64_t tx_counter;
};

class dump_t : public abstract_device_t {
 public:
  dump_t();
  bool load(reg_t addr, size_t len, uint8_t* bytes);
  bool store(reg_t addr, size_t len, const uint8_t* bytes);
 private:
  std::ofstream ofs;
};

class cheshire_reg_t : public abstract_device_t {
 public:
  cheshire_reg_t();
  bool load(reg_t addr, size_t len, uint8_t* bytes);
  bool store(reg_t addr, size_t len, const uint8_t* bytes);
  void reset();
  size_t size() { return CHESHIRE_REG_SIZE; }
 private:
  typedef struct cheshire_reg_hw_features {
    uint32_t bootrom;
    uint32_t llc;
    uint32_t uart;
    uint32_t spi_host;
    uint32_t i2c;
    uint32_t gpio;
    uint32_t dma;
    uint32_t serial_link;
    uint32_t vga;
    uint32_t axirt;
    uint32_t clic;
    uint32_t irq_router;
    uint32_t bus_err;
  } cheshire_reg_hw_features_t;

  typedef struct cheshire_reg_vga_params {
    uint32_t red_width;
    uint32_t green_width;
    uint32_t blue_width;
  } cheshire_reg_vga_params_t;

  uint32_t                    scratch[16];
  uint32_t                    boot_mode;
  uint32_t                    rtc_freq;
  uint32_t                    platform_rom;
  uint32_t                    num_int_harts;
  cheshire_reg_hw_features_t  hw_features;
  uint32_t                    hw_features_reg;

  uint32_t                    llc_size;
  cheshire_reg_vga_params_t   vga_params;
  uint32_t                    vga_params_reg;
};

#endif
