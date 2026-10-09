# SiliCa — 4枚切替試作版

ATtiny1616を1個使い、4枚分のIDm・PMm・サービスコード・システムコード・12データブロックを、外付け24AA08に独立して保存する構成です。

- SW1〜SW4のうち1つを押している間だけ、そのカードが応答します。
- 未押下・複数同時押しでは応答しません。送信直前にも再確認します。
- カードを切り替えた最初の受信フレームは破棄して、選択カードの情報をRAMへ読み込みます。次のリーダのポーリングから応答します。読み込みには数十msを見込みますが実測は必要です。
- 4枚の保存先は256バイトずつの別バンクです。エラーログ32バイトはRAM内のみで、選択変更・電源断で消えます。
- ボタンは通信フレーム間と送信直前に判定します。通信フレームの送信を開始した後のリリースでは、そのフレームは完了します。

## ハードウェア

`cad/four_cards/four_cards.kicad_sch` と `four_cards.kicad_pcb` が変更後の回路図・基板です。80×50mmの元の外形とアンテナを維持し、上側に4つのスイッチを横並びに配置します。

| 部品 | 接続・仕様 |
| --- | --- |
| SW1 | PB2（U1 pin 12）—GND |
| SW2 | PB3（U1 pin 11）—GND |
| SW3 | PB4（U1 pin 10）—GND |
| SW4 | PB5（U1 pin 9）—GND |
| U2 | 24AA08T-I/SN（SOIC-8）、VCC/VSSは既存の整流電源 |
| U2 SDA / SCL | PA1（U1 pin 20）/ PA2（U1 pin 1） |
| U2 WP | GND。A0/A1/A2は内部未接続（基板ではGNDへ接続） |
| R4 / R5 | SDA / SCLの10kΩプルアップ |
| C5 | U2の電源デカップリング100nF |

追加配線は幅0.1mm、ビアはランド径0.45mm・ドリル径0.3mmを使用しています。JLCPCBの2層・1ozの仕様に合わせ、最小配線間隔0.1mm、穴対銅箔間隔0.2mm等のルールをプロジェクトに保存しました。最小ビア0.3mmを発注時に指定します。小径ビアの追加加工費を避けるため、IC周辺を引き直し、R1〜R3・C3/C4を右へ4mm移動しました。アンテナの銅箔配線は維持し、QFN露出パッドは表面配線でGNDへ接続しています。

スイッチはJLCPCB実装対象のXKB TS-1187A-B-A-B（C318884）です。メーカー寸法図に合わせ、パッド1.0×0.75mm、中心X=±3.0mm、Y=±1.875mmとしました。上側の端子1–2、下側の3–4がそれぞれ常時導通し、押すと上下がつながります。PB2〜PB5は内部プルアップを使用します。

PA1/PA2をEEPROMに使うため、従来のTxD/RxDはSDA/SCLに変更します。UARTデバッグは使えません。UPDIは従来のままです。

24AA08は1.7Vから使用でき、ソフトウェアI2Cは100kHz以下です。受動給電ではEEPROMの読み書きに必要な電流と電源保持時間が増えます。ネイティブKiCadのERC/DRCを実施し、エラーと未配線は0件です。書き込み中のVCC低下、RF応答時間、アンテナの同調は受領後に実機で確認してください。本版はその検証用試作です。

## ファームウェア・設定

```sh
cd src/1_1
pio run
```

24AA08には工場出荷時のカード情報はありません。各ボタンを押したまま、既存の`write.py`でそのカードを個別に設定します。例：

```sh
# SW1を押したまま、リーダ上で各コマンドを実行
python write.py idm 1122334455667788
python write.py sys ABCD
python write.py ser 000B
python write.py 0 00112233445566778899AABBCCDDEEFF
```

SW2〜SW4にも、それぞれ異なるIDmと必要なデータを設定してください。12ブロック全部を必要な内容に初期化します。書き込み完了表示までボタンを保持します。書き込み途中で給電が途切れるとページの内容が不完全になる可能性があるため、読み戻して確認します。元のマイコン内蔵EEPROMからの自動移行は行いません。

`RANDOMID`は選択時にRAM上で生成します。同じ選択を維持している間は同じIDmですが、再選択・再給電では変わり得ます。

## 検証

ATtiny1616向けPlatformIOビルド成功：RAM 1293 / 2048バイト（63.1%）、Flash 4599 / 16384バイト（28.1%）。

```sh
clang++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined \
  -I src/1_1/src tests/cards_test.cpp src/1_1/src/application.cpp \
  -o /tmp/silica-cards-test
/tmp/silica-cards-test
```

ホストテストでは全ボタン組合せ、4つの保存バンクの分離、読み書き・再選択後の保持、IDm更新、未押下・別ボタン時の応答停止、メモリ書き込み失敗時の応答を確認しています。I2CとRFの実機動作はこのテストの対象外です。

`python tests/check_cad.py`では、KiCadファイル構文、追加30パッドの回路図と基板のネット一致、部品のインスタンス対応、PB2〜PB5の割当を確認しています。これはKiCadネイティブのERC/DRCの代替ではありません。

## 製造・書込みデータ

`production/SiliCa_4cards_standard_via.zip`、`production/BOM.csv`、`production/CPL.csv`が本版の製造データです。2層FR-4、80×50mm、厚さ1.6mm、銅厚1oz、上面実装18部品/枚。5枚すべてを実装します。U1の実装角度は、元のカスタムフットプリントのピン番号の向きに合わせ270°です。U2もJLCPCBの配置モデルに合わせ270°に修正し、左右の端子と左上のピン1マークの一致を確認しました。ダイオードはプレビュー詳細モデルがないため元CPLの180°を維持し、工場DFMで要照合です。

AE1は基板アンテナの端子表示、J1はUPDI接続用の未実装スルーホールです。外付けアンテナやJ1のピンヘッダは部品実装に含みません。書込み時にはJ1のUPDI/GND/VCCを使用してください。ファームウェアは`firmware/four_cards.hex`です。工場での書込みは依頼しません。

`fuses.c`のヒューズ値はFlash HEXに含まれません。Flashを書いて照合するだけではBOD等は設定されないため、書込みツールでヒューズも別途設定・読み戻してください。UPDIを無効化しないでください。具体的な値は`firmware/PROGRAMMING.md`を参照してください。

`tools/build_cad.py`と`tools/route_added.py`は初期試作の生成スクリプトです。本版の修正済みCADに対して再実行すると変更が失われるため、再生成せずKiCadファイルを編集してください。ローカル部品ライブラリを同梱しています。

## 参照

- 指定部品：https://www.switch-science.com/products/39
- スイッチ寸法図：https://cdn.sparkfun.com/assets/2/7/d/f/0/SMD-Button.pdf
- 24AA08データシート：https://ww1.microchip.com/downloads/en/DeviceDoc/24AA08-24LC08B-24FC08-8K-I2C-Serial-EEPROM-20001710N.pdf
- ATtiny1616データシート：https://ww1.microchip.com/downloads/en/DeviceDoc/ATtiny1614-16-17-DataSheet-DS40002204A.pdf
