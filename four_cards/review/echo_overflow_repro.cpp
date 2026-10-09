#include "application.h"
#include "cards.h"
#include <cassert>
#include <cstring>
#include <cstdio>

static CardImage banks[4], cache;
static int8_t held = -1, selected = -1;
static bool fail_write = false;
void cards_setup() { selected = -1; }
int8_t cards_button() { return held; }
int8_t cards_slot() { return selected; }
bool cards_held() { return selected >= 0 && selected == held; }
CardImage *cards_image() { return selected < 0 ? nullptr : &cache; }
bool cards_select(int8_t slot) {
  selected = -1;
  if (slot < 0 || slot > 3 || held != slot) return false;
  selected = slot; cache = banks[slot]; return true;
}
bool cards_persist(uint8_t offset, const uint8_t *src, uint8_t len) {
  if (!cards_held() || fail_write || unsigned(offset) + len > 224) return false;
  std::memcpy(reinterpret_cast<uint8_t *>(&banks[selected]) + offset, src, len);
  return true;
}
void generate_random_bytes(uint8_t *out, size_t len) { std::memset(out, 0x5A, len); }
static uint8_t poll[] = {6, 0, 0xFF, 0xFF, 0, 0};
static void frame(uint8_t *out, uint8_t code, uint8_t length) {
  std::memset(out, 0, 64); out[0]=length; out[1]=code;
  std::memcpy(out+2,cache.idm,8);
}
void original_main() {
  for (uint8_t mask=0; mask<64; ++mask) {
    const uint8_t relevant=mask & 0x3C;
    const int8_t slot=card_from_buttons(mask);
    if (relevant==4 || relevant==8 || relevant==16 || relevant==32) assert(slot>=0);
    else assert(slot==-1);
  }
  initialize(); assert(process(poll)==nullptr);
  for (int i=0;i<4;++i) {
    banks[i].idm[0]=1; banks[i].idm[1]=i+1;
    banks[i].system_code[0]=0x12; banks[i].system_code[1]=0xFC;
    banks[i].blocks[0][0]=0x10+i;
    held=i;assert(select_card(i));
    auto r=process(poll);assert(r && r[0]==18 && r[3]==i+1);
    uint8_t cmd[64];frame(cmd,CMD_READ_WO_ENC,16);
    cmd[10]=1;cmd[11]=0xFF;cmd[12]=0xFF;cmd[13]=1;cmd[14]=0x80;
    r=process(cmd);assert(r && r[13]==0x10+i);
    cmd[1]=CMD_WRITE_WO_ENC;cmd[0]=32;std::memset(cmd+16,0xA0+i,16);
    r=process(cmd);assert(r && r[10]==0);
    held=-1;assert(process(poll)==nullptr);assert(process(cmd)==nullptr);
  }
  for(int i=0;i<4;++i) {
    held=i;assert(select_card(i));assert(cards_image()->blocks[0][0]==0xA0+i);
    uint8_t cmd[64];frame(cmd,CMD_WRITE_WO_ENC,32);
    cmd[10]=1;cmd[11]=cmd[12]=0xFF;cmd[13]=1;cmd[14]=0x80;cmd[15]=0x83;
    std::memcpy(cmd+16,cache.idm,8);std::memcpy(cmd+24,cache.pmm,8);cmd[17]=0x20+i;
    auto r=process(cmd);assert(r && r[10]==0);assert(banks[i].idm[1]==0x20+i);
    fail_write=true;frame(cmd,CMD_WRITE_WO_ENC,32);
    cmd[10]=1;cmd[11]=cmd[12]=0xFF;cmd[13]=1;cmd[14]=0x80;cmd[15]=0x83;
    std::memset(cmd+16,0xEE,16);
    r=process(cmd);assert(r && r[10]==0xFF && r[11]==0xB0);
    assert(cache.idm[1]==0x20+i);fail_write=false;
    held=(i+1)%4;assert(process(poll)==nullptr);
  }
  held=-1;assert(!select_card(-1));assert(process(poll)==nullptr);
  puts("PASS: all button masks, four independent banks, read/write, reload, IDm update, release/change gating and storage failure");
}

int main() { initialize(); held=0; assert(select_card(0)); uint8_t cmd[209] = {}; cmd[0]=209; cmd[1]=CMD_ECHO; process(cmd); }
