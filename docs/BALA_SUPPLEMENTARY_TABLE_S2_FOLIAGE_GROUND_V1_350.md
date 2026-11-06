# BALA v1.350 — 地表と樹上植生の採集法を比較した補足解析

**2026年11月6日。原本を再読込しない、既存のv1.316・v1.318集計値の監査。JBI本文の主要な地表性節足動物の結果を置き換える新規検証ではない。**

## 原著の採集方法と「林冠」の意味

BALAの原著 [Pozsgai et al. (2024), Scientific Data, DOI 10.1038/s41597-024-03174-7](https://doi.org/10.1038/s41597-024-03174-7) は、`pitfall` と `beating` をそれぞれ地表徘徊性および樹上生活性節足動物の採集法と説明している。

- **地表（Pitfall solution）**：150 mのトランセクトに5 m間隔の30基のトラップを置き、14夜連続採集。地表で活動する節足動物の活動密度と検出可能性に影響される。
- **樹上植生（Open beating tray with bag）**：主要な在来樹木3種を対象に各10サンプル、ピットフォール線からおよそ5 m以内の樹木の枝を高さ**約1.5〜2 m**で**5回**叩いて採集。原著ではcanopy-dwelling arthropodsと呼ぶが、**林冠上部の高さ別測定ではない**。
- **採集努力の定義**：既存のv1.313で元の29物理トランセクトに揃えられた、各調査期あたり地表781 Event、樹上植生759 Event。同じEvent数になるよう規準化しても、14夜の地表トラップと5回の枝叩きは、採集努力や検出率が生物学的に同じという意味ではない。
- **樹種の情報**：原著の主な採集候補は *Juniperus brevifolia*, *Erica azorica*, *Ilex azorica*, *Laurus azorica*, *Vaccinium cylindraceum*。**宿主樹種別の作用は本補足では解析していない**。

## 原本既存集計で確かめられること

| 検証済み指標（島等重みの既存集計） | 地表・ピットフォール | 樹上植生・叩き落とし |
|---|---:|---:|
| クモ類：時間的Sørensen非類似度・同一調査期内の標本差 | 0.2952 | 0.2260 |
| クモ類：B1–B3間Sørensen非類似度 | 0.4860 | 0.3379 |
| **クモ類：調査期間間−同一期内の超過** | **+0.1908** | **+0.1119** |
| クモ類：Simpson種置換の超過 | +0.1677 | +0.0642 |
| **クモ類：島内森林間の空間Simpson β変化（B3−B1）** | **+0.0224** | **−0.0579** |
| クモ類：物理トランセクト数 | 29 | 29 |
| 甲虫類：時間的Sørensenの超過 | +0.2212（26区画） | **STOP（13区画）** |
| 甲虫類：森林間Simpson β変化 | −0.1753（28区画） | **STOP（22区画）** |

**クモ類について**、どちらの方法でも時間的な群集非類似度の超過は正。一方、森林間の空間Simpson βは、地表群集の平均が小さく正（+0.0224）、樹上植生側が負（−0.0579）だった。これは**方法／採集対象によって記述的な結果が異なる**という証拠であり、縦方向の種の分業や林冠特有の機構を統計的に確立した証拠ではない。

**甲虫類について**、既存の決められた品質ゲートは叩き落としデータの時間解析を13区画、空間解析を22区画で停止。負の効果やゼロ効果のどちらも推定したことにせず、**評価不能**として扱う。

## なぜ「地表と林冠の分業」という主張にはしないか

今回の二つの採集群には、**樹木からの採集か地面のトラップかという採集法と、生物が利用する微小生息場所という二つの要因が完全に交絡している**。また、叩き落としは高さ1.5〜2 m付近の枝であり、低木・林冠・樹幹を複数の高さで比較していない。したがって、次の推論は**未検証**である。

- 森林の上層と下層で群集組成変化の方向が系統的に逆転する。
- 林冠被度や樹冠高、林縁からの距離が、今回の蜘蛛の符号差を引き起こした。
- 特定の在来宿主樹木の減少が、森林間の均質化を説明した。
- 地表甲虫の均質化と樹上甲虫の方向性が異なる（樹上甲虫はそもそも品質ゲートを通過していない）。
- クモの採集方法×時間・空間の交互作用に統計的有意差がある（樹上植生側の島別推定と不確実性は凍結集計には存在せず、同一原本の追加採点もしない）。

## JBI原稿への最も妥当な取り込み方

地表甲虫の長期群集・空間構造を本文の中心に据えたまま、**補足表S2（樹上植生という採集方法の感度／範囲の限界）**とするのが妥当である。

本文では例えば以下のように一文で触れる。

*The archived foliage-beating records offered a distinct methodological perspective: temporal spider assemblage dissimilarity exceeded within-campaign sampling differences (+0.112 Sørensen), whereas the mean spatial Simpson change was negative (−0.058), unlike the small positive ground-pitfall spider mean (+0.022). Because beating sampled tree foliage near 1.5–2 m and differed fundamentally in capture process, this contrast does not establish a canopy-height effect; foliage-beetle endpoints failed pre-specified detectability gates (Table S2).*

査読で求められた場合に備え、元データの高木上層・樹種別解析を追加するのではなく、**元の枝叩き採集区画×樹種×期に対応する独立の検出／努力量情報**が必要と説明する。

## 再現性と停止条件

元の生物学的出現記録は再読込**0件**。検証対象は既存の固定集計 `development/bala_within_campaign_detection_original_result_freeze_v1_316.json` と `development/bala_spatial_original_result_freeze_v1_318.json` のみ。原本Field ZIP SHA256は `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2`。

`development/bala_ground_foliage_method_sourcefree_protocol_v1_350.json` の採集法・母数・ゲートを固定し、`scripts/bala_sourcefree_ground_foliage_method_audit_v1_350.py` とソースフリーCIで再監査。原本v1.314、v1.316、v1.318生物学的採点は**SEALED**、全球哺乳類GEB原稿の科学的HOLD、確証的システム追加0件、eBird不使用を継続する。
