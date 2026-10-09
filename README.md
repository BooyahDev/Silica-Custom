# SiliCa Custom — 4カード切替版

[19AJ137/SiliCa](https://github.com/19AJ137/SiliCa)を元に、4組のカード情報を外付けEEPROMへ保存し、4つのボタンで選択して応答する試作基板です。

回路・ファームウェアの修正、JLCPCB向けの標準0.3mmビアを使用した基板、製造データを収録しています。ボタンの動作、書込み、製造条件、検証結果は[詳細README](four_cards/README.md)を参照してください。

- 修正済みKiCadプロジェクト: `four_cards/cad/four_cards/`
- ファームウェアソース: `four_cards/src/1_1/`
- 書込み用HEXと手順: `four_cards/firmware/`
- 製造用Gerber: `four_cards/production/SiliCa_4cards_standard_via.zip`
- 実装部品表・配置: `four_cards/production/BOM.csv`、`CPL.csv`
- 検査報告: `four_cards/review/REVIEW.md`

基板5枚・5枚すべて上面実装を想定。DRCエラー・未配線0件、回路図の全77ピンと基板の接続一致を確認しています。RF応答、受動給電、EEPROM書込み時の電圧は実機未検証です。本設計は非暗号化応答の試作であり、任意のFeliCaカードの認証機能を代替するものではありません。

元リポジトリのライセンスは[UNLICENSE](UNLICENSE)です。
