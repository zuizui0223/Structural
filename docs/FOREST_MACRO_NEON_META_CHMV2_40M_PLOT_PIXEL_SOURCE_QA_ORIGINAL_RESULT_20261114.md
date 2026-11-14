# NEON 35森林サイトのCHMv2独立林冠高ソース：237元区画の40m窓ラスタ実測品質（2026-11-14）

## GitHub Actions original public imagery を開いて確定した数値

Meta/WRI CHMv2 v2（2026年公開DINOv3衛星由来林冠高COG、CC-BY4.0）を、NEON公式site metadata 2026-08-05＋公開`neonDivData 0.3.1`の作者original`.basePlot.div/.brd`中心と結合した。独立NEON field site×plot単位の**237実区画**に対して、**40 m×40 mのEPSG:3857正方形窓**から元の1m級GeoTIFF画素をrange読取りした。サイト数35、17domains、2019–23の森林区画×年観測の**952**は、静的な237区画位置の別年重複であり、952回独立に林冠を測ったわけではない。

**原本成功CI** [#43540584860](https://github.com/zuizui0223/Structural/actions/runs/43540584860)、匿名集計ZIP artifact `14091791814`、digest `sha256:da3a99e2a98da76144025cfc67a2f581bc8a74736f381faa6b5da4139609b965`。

| 実画素Source QAの確定分母 | 値 |
| --- | ---: |
| 元NEON森林サイト | **35** |
| 全区画を元NEON原plot`basePlot`座標に一致できたサイト | **35/35** |
| 元NEON forest plot identity | **237** |
| 40m source CHM COG公開タイル / 撮影日indexの該当タイル | **39/39** |
| CHM源の40m窓が「正の画素≥25・全画素比率≥20%」を通過 | **232 / 237 source plots** |
| 正画素低被覆で不合格 | **4** |
| 全て0またはnodataで不合格（実林冠高0mを証明せず） | **1** |
| 通過した元sites / original ecoclimatic domains | **34 sites / 17 domains** |
| 通過区画の`positive-only CHM 40m p90`高さの中央値 | **19.0 m** |
| 正画素率の通過区画における中央値 | **1.0** |
| タイルの原撮影日source`acq_start/end` windowが2019〜2020と重なるもの | **36 tiles** |
| 2019年より前だけの撮影日windowを持つタイル | **3 tiles** |
| タイルwindowが元NEON site–plot採集年と重なる元観測 | **276 plot×years** |

注意：最後の276はタイル単位の撮影日**範囲**に元NEON採集年が含まれるというだけで、個々のpixelがその年に撮影された**確定日ではない**。2019–2020のCHM-positiveな元plot×yearは388あるが、それも同年撮影の証明ではない。CHMv2は静的な複合画像であり、元画像約80%が2018–2020年という概観をもつ。林冠の年次変動や森林管理介入の因果的な測定ではない。

## 修正履歴：当初317区画年という誤った制限

最初の公開Source-only座標監査 #43538599764 は、元`neon_location`のcanonical`location_id`を存在しない`.basePlot.all`と想定し、元調査サブ位置を含む中央値の場所散らばりを採用した結果、317区画年・29sitesのみ位置確定としていた。作者の元sourceは`.basePlot.div/.brd`等であり、正しい元base plot中心を優先し、全952 plotyears／35sitesへ修正した [成功CI #43539279481](https://github.com/zuizui0223/Structural/actions/runs/43539279481)。317は旧ソース選択器の人工物であり、最終生態解析に使用しない。

さらに1回目のraster pixel品質CI #43540078363 はNEON公式CSVのUTF-8 BOM/列名解釈で停止、林冠ピクセル実測前のプログラム問題だった。修正後CI #43540584860にて**237中232**の真のソース画素QAを確認。

## 意義と停止条件

ここまで得たpositiveは、**地上木本樹高の別系統にある衛星由来の静的な構造covariateを、これまでのNEON森林8siteではなく35sites・237元森林plotsのネットワークへ結合できたこと**。過去のVST source QAで2019–23の元木本構造/昆虫/植物の季節・努力まで一致した比較は**10siteyears＜事前固定12**、2014–18は元VST source-contextがあっても公開派生の有効面積×QAの原本結合0だった。旧source STOPは両方維持。Meta CHMv2を同じVST欠除の年次実測として加算しない。

次にSOURCEの**独立した計測妥当性**として、元VST 2019–23に存在した**73 truly measured forest plotyears/22sites/13domains**を元site×plot identityでCHMv2と対応させ、元VST生木(DBH>=10cm、固有individualID、source QC)のfield p90 vs 40m CHM positive p90を比較する。あらかじめ[測定チャネル比較の仕様](FOREST_MACRO_NEON_META_CHMV2_VST_FIELD_HEIGHT_CROSSSENSOR_PRESPEC_20261114.md)を生物のtaxon・捕獲数・植物種名を開く前に固定済。**画素と木本高さのproxy validityは植物×甲虫のβの予測・森林管理の介入効果を証明しない。**

元プログラム`analysis/forest_macro_global/neon_meta_chmv2_forest_plot_source_gate.R`、`neon_meta_chmv2_public_tile_probe.py`、`neon_meta_chmv2_plot40m_pixel_source_quality.py`。元座標/サイト/プロット/樹木pixel・全sample・種名をpublic GitHubに再配布していない。VST/PREDICTS/NEONの原スコアは凍結、eBird/TinyFish未使用、Draft PR #469未マージ。
