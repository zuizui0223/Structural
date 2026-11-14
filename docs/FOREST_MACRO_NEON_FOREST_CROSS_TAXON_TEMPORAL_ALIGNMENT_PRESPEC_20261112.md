# NEON森林8サイト・植物／地表甲虫の年次群集置換 — 生物値を開く前の固定仕様（2026-11-12）

## 問いと既知結果の保持

PREDICTS 39原研究×20か国の参照林との差 `Δβ_sim=+0.0942` と距離対応31研究の二次感度 `+0.0847` は凍結済み。本検証は**独立米国NEON森林ネットワーク**の同一原`plotID`について、**植物の記録分類群と地表甲虫の分類群が、同じ年次転換時にともに大きく入れ替わるか**を問う。森林改変、林冠上下層、構造因果、送粉・捕食という機構を直接検証する設計ではない。

## 環境・観測前適格性

- データは独立配布 `neonDivData` R 0.3.1、甲虫DP1.10022.001と植物DP1.10058.001。原公式NEONサイトメタデータ2026-08-05のSHA `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`。CC0公開派生データでありtoken制限NEON 2026原生物APIの回避なし。データの版固定（0.3.1）に失敗ならSTOP。
- 対象2019–2023、元NEON siteが「dominant_nlcd_classesの全ラベルがDeciduous/Evergreen/Mixed Forest」、元派生`nlcdClass`がcamelCaseの3森林クラスの元plotsのみ。サイト森林ラベルは現場の森林専門生物・林冠状態を証明しない。
- 原資料だけのv2監査（GitHub Actions #43204131183）で**8 forest sites、7 domains、39 site×years、339 site×plot×years、81原plotIDが2年以上、242同一区画の連続年比較（非独立）、30 site×yearの連続比較**。元ソース-only段階での既知母数。旧v1の「39 site×yearに方法・努力・期間が一致」とした評価は複数の異なるplotをまたぐ可能性があったためv2で置換。
- 同一原plotID×年の`trappingDays>0`、sample ID, trapIDがある**フラグ未記載の甲虫トラップ**と、`sample_area_m2==1`の植物記録、元の日付差30日以内。これらは全て**同じplot**内で成立し、別区画の条件を組み合わせて適格にしない。
- 季節を固定：元plot×年の1m²植物記録から**最初の調査日**を採用。植物はその日±7日、甲虫はその日±30日の正常ピットフォール記録だけをその年の群集に含める。連続年の植物起点日の通日（DOY）差が45日を超えたplotは除外。ほかの時期を有意結果に合わせて選び直さない。
- 生物値を開く前の追加努力同等性：甲虫の異なる正常採集sampleID **各年4以上**、植物1m²の異なる`subplotID` **各年4以上**。連続年ペア間の甲虫総trappingDaysと植物記録済みsubplots数の比は**0.5–2.0**。植物調査は元パッケージが1m²のtargetTaxaPresent=N標本を除外しているため、このsubplots数は**観測された植物があるsubplots数**であり、完全な採集努力ではない。
- 適格なplot×年次転換を各サイト年に3本以上、最低6 sites、4 ecoclimatic domains、16 site×year transitions（各サイトの反復年は非独立）確保できなければ、**SCIENTIFIC_STOP_SAME_PLOT_EFFORT_TEMPORAL_SUPPORT**。この前段はtaxon_id, taxon_name, value, species richnessを一切読まず計数し、原サイト・plot・元サンプルIDを出力しない。

## 生物学的estimand（後付け探索、事前固定後に一回開封）

- 元派生で`taxon_id`があり、`taxon_rank`がspecies/subspecies/varietyのレコードだけを選び、甲虫は`value>0`、植物1m²は元パッケージの記録されたtaxon出現を使用。Beetleの`value=NA`ゼロ採集とPlantの`value=NA`存在のみを同一の0とは扱わない。高階級/重複や学名未同定をspeciesとして加算しない。
- 生物endpointは、同じNEON原plotIDの連続した年の二値species incidence集合でのSimpson置換成分 `β_sim=min(b,c)/(a+min(b,c))`（同種共有a、各年独自b,c）、甲虫と植物で別々に計算する。元植物の1m²ゼロ標本が派生パッケージから一部落ちているので**見かけの記録分類群入れ替わり**であり真の局所絶滅・加入を主張しない。
- 同じ年次転換に対し、双方で定義できた同じ原plotだけを残し、site×year転換単位にそれぞれ平均。その後site内中心化した年次βが甲虫と植物でどれだけ**同期**するかを主記述統計（siteごとのPearson相関の等重み平均）として記述。サイト内3転換以上・両群で分散ありの場合のみ相関を定義する。相関が定義できるsiteが**5未満**なら同期の推測STOP。
- 各site×年次転換で**3つ以上の同一plotの両群β**が定義できる場合のみsite×transitionの平均を計算する。分類群の非検出や定義不能で減少したplot/transitionを全件数で報告する。
- 原site内で植物の年次ラベルを9,999回ランダム入れ替える、年次の非同期nullを固定。各site独立シャッフル、same-plot反復は個体の独立nと数えない。site-bootstrap 4,000で95%百分位区間を提示。方向が正でも負でも公開。**データを見てから類似度指標／分類群／期間／しきい値を変更しない**。
- 保存するのは集約数値のみ：site数・原plot/year counts・分類群有効率・同期統計・CI/帰無p・各群の平均β、site and domain leave-one-out方向の頑健性（任意の片方だけを肯定に使わない）。原ID、種名、元個体数、元座標は出力しない。

## 証拠の上限

これはNEON森林8サイト・7 domainsからの**探索的多サイトの同時変動**で、全世界森林・林冠の垂直ニッチ・森林改変の因果は未検証。共有する季節・検出期間・採集被覆や地域環境が両群に影響しても同期は生じ得る。元の植物ゼロ標本欠落と2018以降の甲虫3trap固定化・2023年のNEON全体の採集plot縮小を保持。PREDICTSは歴史的森林改変の空間比較、NEONは近年の時系列反復であるため、直接同じβをプールしない。

元データの欠測・方法不一致があれば効果に不利でもSTOP。BALA/THERA/GEBおよびPREDICTS原スコアは改変しない。eBird使用なし、Draft PR #469未マージ。
