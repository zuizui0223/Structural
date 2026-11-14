# NEON 2019–2020：静的CHMv2林冠高コントラスト×地表甲虫組成のsource eligibility（分類群値未開封で事前固定、2026-11-14）

## 新しい問い（以前のVST同年採集STOPとは別のsource）

VST樹木実測と3資料の同season比較では、2019–2023に10 sites/8domains/10siteyears・35 source plot pairsしか得られず、事前固定12siteyearsを満たさなかった。VST2014–2018原sourceもsource QA0で別STOP。これはVST樹木測定を対象にした**年次×区画実測の分母**として引き続き維持する。

別系統の静的衛星由来Meta/WRI CHMv2（2026公開、原画像は大部分2018–2020）の地理的構造proxyは、実COG画素で**237 original forest plot中232plot（34NEON sites/17domains）**が固定40m正方形正画素QA通過。独立の現地VST field-height検証でも、**22sites・72plots**でsite等重みSpearman`ρ=+0.9063` (site-bootstrap 95%CI +0.7457〜+0.9658)、高さ差中央値−2.77mを観測した。[Source validation run #43561149201](https://github.com/zuizui0223/Structural/actions/runs/43561149201)。ただしVSTとCHMv2のsource imagery windowがfield survey yearと重なるのは8/72plotsのみで、衛星40m窓は正しい現地plot polygonではない。

このsourceを**2019–2020年という旧画像の主要撮影時期に比較的近い固定2暦年**の、NEON森林plotの甲虫・植物組成の**空間的非類似度**という別推定量のためのsourceとして評価する。これはVST同年林冠を補完した時系列ではない。2019–2020を選んでも、CHMv2の各pixelがその年に撮影されたという証拠はなく、空間的な林冠proxyと2019–2020年の生物群集という**時点ずれのある観測横断面**。以前のNEON 7森林の時間的同調nullとPREDICTS主結果を再得点していない。新しい生物解析は将来実行する場合も結果を知った上で始める**探索的二次解析**。

## source-only eligibility：元生物taxon・valueを一切見ずに決定する

- 公開`neonDivData 0.3.1`、公式2026-08-05 NEON site×domain原資料、元original`.basePlot.div/.brd`中心、Meta/WRI CHMv2 v2 `acq_dates.parquet` / CHM40m画素QAv1を固定。森林plot = 甲虫・植物両sourceに元`nlcdClass`が`deciduousForest,evergreenForest,mixedForest`のいずれかであり、site全体がforest-dominantであることは要求しない。元2019/2020年の観測のみ。元plotsはsite×plotID×yearで照合、複数年の構造pixelは1回測定のCHM固定値であり独立構造nにしない。
- 各元plot×yearで、最初の有効な植物1m²元sampleの調査日を固定。植物はその日±7dの記録だけ。甲虫は`trapConditionFlag`なし、`trappingDays>0`、元sampleID/trapIDが両方あり、植物日±30dの記録だけ。元sampleIDでtrap-daysが矛盾すれば明示STOP。甲虫`unique_sample_id`は**4以上**、植物の記録`subplotID`は**4以上**。植物のtargetTaxaPresent=Nゼロ記録が公開派生から除去済みなので、このsubplot数は真の検出努力量そのものではない。
- CHMv2の元plot40m窓`positive_pixels>=25`かつ`positive_fraction>=.20`の固定pixel QAに合格した元plotだけを使う。源CHMの原画素ゼロを林冠高0mと判断しない。陽性p90は**静的な2018–2020頃のproxy**であり、元地点2019・2020年ごとに独立に変化したことにはしない。
- 元site×同calendar yearの異なる原plot pairが、①甲虫正常`trappingDays`の総和比0.5–2.0、②植物記録済み1m² subplots数比0.5–2.0、③植物最初の調査日の差が30d以下、の**3条件全部**を満たす場合のみ距離と構造差の比較候補。位置sourceで元plot間の地理距離も計算し、距離0/座標重複/極端なplot重複を別に監査。
- 一つのsource site×yearにつき**3元plotが互いの3ペアで同条件を満たす完全なtriad**を最低1つ必要とし、さらにCHM-p90に2以上の異なる値が必要。triadが複数ある場合は**source metadataだけを使用**して最大サイズの完全互換plotセットを選び、同数なら原plotIDの辞書順という固定アルゴリズムを採用する。群集taxonの応答に合わせたplot選択はしない。
- 許可基準は、上記のtriad sourceを含む**10以上の独立NEON sites、6以上のecoclimatic domains、12以上のsite×year**。独立統計nはsite単位、同site内2年観測や多数のplotペアを独立森林とは数えない。満たさなければ`SCIENTIFIC_STOP_NEON_CHMV2_SPATIAL_FOREST_PLOT_TRIAD_SUPPORT`とし、植物・甲虫種名と元測定`value`を開けない。基準未達時に期間・努力・画素・triad条件を緩めて追試しない。
- 公開元source imagery datesの`acq_start/end` windowが同NEON年と重なる元plots・siteyearsの数を別に記述するが、画素単位撮影日はないためこれは生物解析への適格の証明ではない。`static scene`と`annual survey`の相対時期は重要な交絡として常に本文で示す。

## もしsource-onlyが許可された場合の生物解析の主線（未実行、別途完全なestimand固定が必要）

**問い**：「同一NEON森林site・同じ採集年の森林plot同士では、静的林冠高の違いが大きいほど地表甲虫群集の分類群置換も大きくなるか。地理距離を加えたときに残るか」。主要応答は同site×year内`ground beetle`のoriginal`taxon_id`（species階級・元value>0）に基づくSimpson置換、固定構造説明量はsite内plot pairの`abs(CHMv2_p90_i−CHMv2_p90_j)`。原plot中心からの距離log(km+0.05)は先に想定する交絡。植物1m²のrecorded taxon置換は別channel探索的対照であり、ゼロ調査母数を完全として扱わない。原plot pairを独立標本とみなさないsite-year内plotラベル置換／siteブロック不確実性を用いる。細部の統計設計と元taxonomyの粒度は**source-only gate結果を見た後でもspecies応答を見る前に**もう一段確定する。

**このstageではsourceの採集可能性だけ。** PREDICTS `+0.0942`、距離感度`+0.0847`、NEON temporal`−0.0664,p=.536`は固定し再採点せず、VST source STOPも取り消さない。eBird/TinyFish不使用、PR #469 Draft未マージ。
