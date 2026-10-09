#include "cards.h"
#include <avr/io.h>
#include <util/delay.h>
#include <string.h>

// Software I2C, PA1=SDA and PA2=SCL. Open drain, 10k external pullups.
// Conservative 5us half-period for the 24AA08 at VCC >= 1.7V.
namespace {
constexpr uint8_t SDA = PIN1_bm, SCL = PIN2_bm;
CardImage image;
int8_t selected = -1;
void low(uint8_t pin) { PORTA.DIRSET = pin; }
void release(uint8_t pin) { PORTA.DIRCLR = pin; }
void pause() { _delay_us(5); }
bool clock_high() {
  release(SCL);
  // Bounded clock-stretch wait: a disconnected/stuck device cannot hang RF.
  for (uint8_t i = 0; i < 100; ++i) {
    if (PORTA.IN & SCL) { pause(); return true; }
    pause();
  }
  return false;
}
bool start() {
  release(SDA);
  if (!clock_high()) return false;
  if (!(PORTA.IN & SDA)) return false;
  low(SDA); pause(); low(SCL); pause();
  return true;
}
void stop() {
  low(SDA); pause(); clock_high(); release(SDA); pause();
}
bool put(uint8_t byte) {
  for (uint8_t i = 0; i < 8; ++i) {
    if (byte & 0x80) release(SDA); else low(SDA);
    pause();
    if (!clock_high()) return false;
    low(SCL); pause(); byte <<= 1;
  }
  release(SDA); pause();
  if (!clock_high()) return false;
  const bool ack = !(PORTA.IN & SDA);
  low(SCL); pause();
  return ack;
}
bool get(uint8_t &byte, bool ack) {
  byte = 0;
  release(SDA);
  for (uint8_t i = 0; i < 8; ++i) {
    pause();
    if (!clock_high()) return false;
    byte = (byte << 1) | ((PORTA.IN & SDA) ? 1 : 0);
    low(SCL); pause();
  }
  if (ack) low(SDA); else release(SDA);
  pause();
  if (!clock_high()) return false;
  low(SCL); release(SDA); pause();
  return true;
}
uint8_t address(uint8_t bank) { return 0xA0 | (bank << 1); }
bool ready(uint8_t bank) {
  for (uint8_t tries = 0; tries < 60; ++tries) {
    const bool ack = start() && put(address(bank));
    stop();
    if (ack) return true;
    _delay_us(100);
  }
  return false;
}
bool read_image(uint8_t bank) {
  if (!ready(bank) || !start() || !put(address(bank)) || !put(0) ||
      !start() || !put(address(bank) | 1)) {
    stop(); return false;
  }
  uint8_t *dest = reinterpret_cast<uint8_t *>(&image);
  // Metadata and data only. Diagnostics are reset in RAM on selection.
  for (uint8_t i = 0; i < 224; ++i) {
    if (!get(dest[i], i != 223)) { stop(); return false; }
  }
  stop(); memset(image.errors, 0, sizeof image.errors);
  return true;
}
}
void cards_setup() {
  PORTB.DIRCLR = 0x3C;
  PORTB.PIN2CTRL = PORT_PULLUPEN_bm;
  PORTB.PIN3CTRL = PORT_PULLUPEN_bm;
  PORTB.PIN4CTRL = PORT_PULLUPEN_bm;
  PORTB.PIN5CTRL = PORT_PULLUPEN_bm;
  PORTA.OUTCLR = SDA | SCL;
  release(SDA | SCL);
  // Recover a device interrupted in the middle of an EEPROM read.
  for (uint8_t i = 0; i < 9; ++i) { low(SCL); pause(); clock_high(); }
  stop();
  selected = -1;
}
int8_t cards_button() { return card_from_buttons(~PORTB.IN); }
int8_t cards_slot() { return selected; }
bool cards_held() { return selected >= 0 && cards_button() == selected; }
CardImage *cards_image() { return selected >= 0 ? &image : nullptr; }
bool cards_select(int8_t slot) {
  selected = -1;
  if (slot < 0 || slot > 3 || !read_image(slot) || cards_button() != slot)
    return false;
  selected = slot;
  return true;
}
bool cards_persist(uint8_t offset, const uint8_t *src, uint8_t length) {
  if (!cards_held() || static_cast<uint16_t>(offset) + length > 224)
    return false;
  const uint8_t bank = selected;
  while (length) {
    const uint8_t chunk = (length < 16 - (offset & 15)) ? length : 16 - (offset & 15);
    if (!ready(bank) || !start() || !put(address(bank)) || !put(offset)) {
      stop(); return false;
    }
    for (uint8_t i = 0; i < chunk; ++i) {
      if (!put(src[i])) { stop(); return false; }
    }
    stop();
    if (!ready(bank)) return false;
    offset += chunk; src += chunk; length -= chunk;
  }
  return true;
}
