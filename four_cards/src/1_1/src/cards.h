#pragma once
#include <stdint.h>

// One 256-byte bank per card in a 24AA08 external EEPROM.
struct CardImage {
  uint8_t idm[8];
  uint8_t pmm[8];
  uint8_t service_code[8];
  uint8_t system_code[8];
  uint8_t blocks[12][16];
  uint8_t errors[2][16]; // volatile diagnostics, never written during idle RF
};
static_assert(sizeof(CardImage) == 256, "EEPROM bank layout");

inline int8_t card_from_buttons(uint8_t pressed) {
  pressed &= 0x3C; // PB2..PB5, active low at the physical pins
  switch (pressed) {
  case 0x04: return 0;
  case 0x08: return 1;
  case 0x10: return 2;
  case 0x20: return 3;
  default: return -1;
  }
}
void cards_setup();
int8_t cards_button();
int8_t cards_slot();
bool cards_held();
bool cards_select(int8_t slot);
CardImage *cards_image();
bool cards_persist(uint8_t offset, const uint8_t *src, uint8_t length);
