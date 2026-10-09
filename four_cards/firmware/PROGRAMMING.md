# UPDI書込み手順

工場でU1へのプログラム書込みは行わない。受領後にJ1のUPDI、GND、VCCを使う。書込み中は安定した外部電源を供給し、RFリーダの上には置かない。UPDI信号の電圧を基板VCCに合わせる。

Flashは`four_cards.hex`。ATtiny1616用にビルド済み。ヒューズは別途設定が必要。

| Fuse offset | 名称 | 値 | 意味 |
|---|---|---|---|
|0|WDTCFG|0x00|WDT既定|
|1|BODCFG|0x04|BOD有効、level 0（公称1.8V）|
|2|OSCCFG|0x02|既定値|
|3|TCD0CFG|0x00|既定値|
|5|SYSCFG0|0xC5|UPDI維持、内蔵EEPROMをerase時に保存|
|6|SYSCFG1|0x01|起動待ち1ms|
|7|APPEND|0x00|既定値|
|8|BOOTEND|0x00|既定値|

offset4は予約領域なので書かない。値はビルド済みELFの.fuse節と、使用ツールチェーンのiotn1616.hから照合済み。外部クロックの使用はファームウェア内で設定する。

pymcuprogとSerialUPDIを使う場合の例。`PORT`を実際のポート名に置き換え、firmwareディレクトリから実行する。

```sh
PORT=/dev/cu.YOUR_UPDI_PORT
pymcuprog ping -t uart -d attiny1616 -u "$PORT" -c 115200
pymcuprog write -t uart -d attiny1616 -u "$PORT" -c 115200 --erase -f four_cards.hex --verify
pymcuprog write -t uart -d attiny1616 -u "$PORT" -c 115200 -m fuses -o 0 -l 0x00 0x04 0x02 0x00 --verify
pymcuprog write -t uart -d attiny1616 -u "$PORT" -c 115200 -m fuses -o 5 -l 0xC5 0x01 0x00 0x00 --verify
pymcuprog read -t uart -d attiny1616 -u "$PORT" -c 115200 -m fuses
```

SYSCFG0のUPDI設定を変更しない。各verifyの成功とヒューズ読戻しを確認してから電源を切る。

書込み後、SW1〜4を押しながら各バンクにIDm・PMm・システムコード・サービスコード・12ブロックを設定し、読み戻す。書込み中にカードの給電が途切れないようにする。外付けEEPROMには自動移行や工場でのカード情報設定はない。

CLI構文の参照: [Microchip pymcuprog公式ヘルプ](https://github.com/microchip-pic-avr-tools/pymcuprog/blob/main/help.md)。この手順は実デバイス未接続のため実行検証は未実施。
