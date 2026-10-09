# 元リポジトリとの照合

取得日: 2026-10-09 JST
URL: https://github.com/19AJ137/SiliCa
コミット: 1cb23a23983eb8a869c0f0b5d651f9bc45ab33e5

手元の cad/baseline/1_1.kicad_sch は、このコミットの元回路図とバイト単位で一致しました。元回路図にも値はR/Cのままですが、production/bom.csvにLCSC番号があります。以下はその番号をLCSC商品ページと照合した値です。

|参照|値/型番|メーカー型番|LCSC|基板1枚の数量|
|---|---|---|---|---|
|C1|47pF C0G 50V ±5%|0402CG470J500NT|C1567|1|
|C2|10nF X7R 50V ±10%|CL05B103KB5NNNC|C15195|1|
|C3, C4|1nF X7R 50V ±10%|0402B102K500NT|C1523|2|
|R1, R2|1kΩ ±1% 62.5mW|0402WGF1001TCE|C11702|2|
|R3|510Ω ±1% 62.5mW|0402WGF5100TCE|C25123|1|
|D1, D2|CBI BAT54ST / SOT-523|BAT54ST|C2919808|2|
|U1|ATtiny1616 / VQFN-20|ATTINY1616-MNR|C507118|1|

参照: https://github.com/19AJ137/SiliCa/blob/1cb23a23983eb8a869c0f0b5d651f9bc45ab33e5/cad/1_1/production/bom.csv

商品ページ:
- https://www.lcsc.com/product-detail/C1567.html
- https://www.lcsc.com/product-detail/C15195.html
- https://www.lcsc.com/product-detail/C1523.html
- https://www.lcsc.com/product-detail/C11702.html
- https://www.lcsc.com/product-detail/C25123.html
- https://www.lcsc.com/product-detail/C2919808.html
- https://www.lcsc.com/product-detail/C507118.html

## BOMを転用する際の問題

元BOMのQuantityはC1/C2/C3/C4各行が4、R1/R2/R3各行が3、D1/D2各行が2となっています。各行のDesignatorは単一部品なので基板1枚当たりは各1です。元CSVは証拠として原文保存していますが、そのまま製造用に使わないでください。

元のpositions.csvとGerber ZIPは元基板用です。4枚切替版のスイッチ・EEPROM・追加配線を含まないので発注に転用できません。

LCSC番号が判明したこととJLCPCBの実装用在庫が確保できることは別です。追加8部品を含めた調達と実装方向の確認は未完了です。基板・ファームウェアの前回の問題も未修正です。

C2は10nFで、4枚版のC5は100nFです。追加EEPROMとプルアップによる負荷、および増えた電源容量の充電時間を含む給電・起動時間の検証が必要です。元基板の動作をもって変更後の動作保証にはできません。
