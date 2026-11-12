# Structural / THERA — 原本地理監査と既発表研究への位置づけ（2026-11-12）

## 判定：原本の地理的階層を特定。全球・独立多森林の新発見ではない

本資料は新たな種データの解析ではない。DATASAPROX v1.6の原本Occurrence core 675,525行のうち、THERA（EFNO）に属する標本の**採集設計・座標列だけ**を参照した。元論文からTable 7のTHERAが**complete**（44科、1イベント中央値18分類群）であることをすでに確認している。

- 元ソース：DATASAPROX v1.6、UUID \`d050a143-2e62-4908-9d9e-a7f541eab94d\`、ZIP SHA256 \`4163a2f8f72d756e74f64319b8e199b284ecc6414196147e4465d342d7dcb6d0\`。
- 原本監査：GitHub Actions [#43126599073](https://github.com/zuizui0223/Structural/actions/runs/43126599073)、**SUCCESS**（最初のCIは無関係のテスト文字列 \`event\` による偽陽性、修正後は合成テスト・原本監査ともPASS）。元イベント座標値、区画ID、種名、各個体数は一切公開しない。
- スクリプト \`analysis/forest_macro_global/datasaprox_thera_spatial_schema_gate.py\`、テスト \`analysis/forest_macro_global/test_datasaprox_thera_spatial_schema_gate.py\`。既存Draft PR #469のみ、未マージ。

### 実行済み原本の地理的証拠（response unopened）

| 判定対象 | 実測・監査結果 |
| --- | ---: |
| 2上層+2下層、元採集期間差7日以内の均等採集 | **55 plot×month** |
| 元実区画キー | **20** |
| 上記イベントID | **220** |
| 20元区画の座標欠測／同一イベント内座標矛盾 | **0／0** |
| 同一区画内元イベントの最大座標オフセット中央値・最大 | **0.0／0.0 km** |
| 異なる区画の中心点間距離（中央値、最小、最大） | **78.818、0.843、90.550 km** |
| 区画中心の距離しきい値連結成分 | **0.5 km:20、1 km:19、5 km:2、20 km:2** |
| species/taxon/individual response read | **0** |

距離しきい値連結成分は**近距離グループの診断**にすぎず、実森林境界・行政区域・独立森林ネットワークの証明ではない。座標が区画キー単位で完全一致したということは元イベント間の位置分解能が無く、実トラップの水平距離や正確な樹上高度を示さない。元 \`coordinateUncertaintyInMeters\` 列は存在するが、その値分布は未読。

### 重要な既発表論文：垂直分化そのものは新規性がない

Balvay et al. (2026), *Forest Ecology and Management* 618:124001, DOI **10.1016/j.foreco.2026.124001**, "The taxonomic and functional stratification of saproxylic beetle communities in temperate oak forests is altered by forest decline", はフランス Loire Basinの**2 oak forests × 20 plots**を対象に、Lindgrenトラップで**understory, lower canopy, upper canopy**を比較した。すでに甲虫の分類群・機能組成の垂直差、上層での個体捕獲数の多さ、diebackに伴う群集均質化を報告している（出版日2026-10-15）。

THERAの元ソースには20区画、Lindgren、supra/infra canopyと同様のフィールド構造があり、地理も5〜20 kmの連結成分で二群を示す。**既発表Balvay論文と同一フィールド系列である可能性が高い**。ただし論文・原イベントIDの実在するクロスウォークは未取得で、**同一データと確定したわけではない**。確認がないまま「独立再現」として計数しない。

このため、THERAのspecies beta、上層優勢、森林衰退による均質化を再採点して「Structuralの新発見」と呼ぶことは禁止。現段階でのTHERAの役割は、これからのクロス地域データベースに対する**原本監査技術・採集法の正例／既発表の比較参照**に限定する。

### 残る統計上の問題

1. 比較単位は55 plot×monthではなく20 plotであり、実際の独立**森林**は2候補にとどまる。森林を無視して20独立森林の検定をしてはならない。
2. 元データはOccurrence coreに現れたイベントだけ。捕獲ゼロのEvent原本や観測努力の完全分母は未確保。元Occurrence行で現れない種・イベントを生態学的な真の不在とみなさない。
3. \`ID_condition\`が層／黒色Lindgrenを文字列に含むことは監査済みだが、元文献の原設計上の他の操作・サンプリング選別・trapsの物理独立性は未認証。
4. \`scientificName\`, \`taxonID\`, \`taxonRank\`, \`organismQuantity\`列は**存在**するだけ確認。実際の同定階級分布や計数定義は一切読み込んでいない。

## マクロ生態学主線への接続：次の独立証拠が必要

森林の三次元ニッチについて、タイの2森林（すでに原著で縦層比較がある）とTHERA候補の2温帯森林を統計的な全球再現n=4として扱わない。採集法・分類解像度が異なり、どちらも元研究の二次利用である。

次の大目標は**「地理的に独立した森林・バイオームで、林冠の階層差が群集の組成・機能・温度環境とどう結びつくか」**を、原研究と異なる未探索の応答あるいは独立森林の検証で示すこと。以前の世界PREDICTS 4,920森の候補（64か国）は垂直サンプルが同一設計で揃ったデータでなく、Theraの代替証拠としてそのまま足せない。データを追加する前に採集法・高さ・分類解像度・独立森林単位を確定し、当初の植生構造・群集組成の研究目的から脱線しない。

**状態:** THERA地理・スキーマ監査はDONE。THERAの全球森林分化証拠への昇格は**SCIENTIFIC HOLD**、種組成を開封して新規効果を追う作業はしない。BALAの既凍結スコア、GEBの哺乳類holdout、eBird不使用、PR Draftは維持。
