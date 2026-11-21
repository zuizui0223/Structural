# PREDICTS森林マクロ：参照林内の変動を超える群集置換を検証（解析前固定、2026-11-12）

## 本文へ採用する問い

**「森林改変に伴う分類群の入れ替わりは、同じ原研究・調査手法・対象分類群の参照森林どうしで通常見られる空間的な違いを超えるのか？」**

Thera (EFNO) の55区画×月・20区画は実際には地理的2森林群・出版済み垂直分化の可能性が強いため、全球の独立森林リプリケートとして使わない。アゾレスBALAの時間的種交代は別のendpointとして凍結維持。次の生物応答は、すでに地点メタデータだけで確認済みの **NHM PREDICTS 2016+2022、1,145森林地点、39原研究×手法×分類群比較、20か国**から取る。

ただし直近（2026年11月10日）の *Nature Ecology & Evolution* 論文（DOI 10.1038/s41559-026-03205-z）はPREDICTSの184研究・38,010地点対のBray–Curtis βを既に評価している。PREDICTSでのβ-森林改変関連そのものは既知の文脈であり、本解析は**公表済み原本の二次探索・参照内非類似度を差し引く新しい推定対象**である。独立の新野外検証でも、温度・林冠の垂直分化の検証でも、未発表の全球森林法則でもない。

## 原本入力と採集階層

- 元データ：Natural History Museum (London) PREDICTS 2016 と 2022 公開リリース、R公式 `predictsr::GetSitelevelSummaries(extract=c(2016,2022))` と `GetPredictsData(extract=c(2016,2022))`。
- ライセンス：2016 CC BY-NC-SA、2022 CC NC。GitHubに元の位置・原研究・種名・地点ID・Taxon_number・測定値・原行を再配布しない。
- 森林母集団の前段は以前の厳格定義を変更しない：**(i)** 森林/taiga/woodland生物群系、**(ii)** 原研究地点Habitat_as_describedにforest/woodland/mangrove/laurel、**(iii)** Primary/Secondary vegetationかPlantation forest。
- 参照群は原Primary vegetationかつMinimal/Light use。改変群はSecondary vegetation/Plantation forest。元Study `SS` × `Sampling_method` × `Study_common_taxon` の内部で各2地点以上。元サンプル `SSBS` で正確に結合し、同じ参照地点の全ペアは相互依存。元調査でForestと明記のない森林biomeのみの地点は入れない。
- この設計が以前の地点監査結果から乖離するなら生物応答の値を読む前にSTOP：元site summary=35,738、対象森林サイト=1,145、eligible strata=39、国数=20。実際の独立Studyは原データ値から計数して別に表示する。39 strata＝39森林地域ではない。

## 群集行列の意味と固定応答

- 元の `Diversity_metric_type` がAbundanceまたはOccurrence、`Measurement` が有限・非負・同定Taxon_numberありだけ採用し、**>0** を検出。元Species richness行はTaxon名を表さないため除外。
- `Taxon_number` は元研究内部の分類群キー。異なる原研究間で同一番号を同一種とはみなさない。元分類解像度の混在があれば「species」ではなく「source Taxon」と記す。
- 元site中に検出分類群が0、元生物出現が結合できない、またはgroupでMetric-typeが不整合なら、当該群は事前固定ルールに従いSTOP。観測なしは欠測、0値を自動で創出しない。元研究でタクサを調査していたことと、全ての種を完全検出したことは異なる。
- 各原Study×method×taxon比較群gで
  - `β_ref-ref,g` = 参照森林どうしの**Simpson species replacement component**（Abundance-free、単なる種数差/nestednessを軽減した指標）の全組平均
  - `β_altered-ref,g` = 改変森林と参照森林の同手法・同分類群内の全組平均
  - **唯一の主estimand**: `Δβ_g = mean(β_altered-ref,g) − mean(β_ref-ref,g)`。正は「改変森林の分類群構成が、同じ調査系の参照林間変動より異なる」。負ならその逆。
- これを原Study `SS` 単位で平均後、全Study等重みで主効果を推定。サイト対を独立の森林と数えない。
- 不確実性：Study単位のbootstrap 4,000、元Study効果の符号反転9,999（両側）。Study数が5未満なら主効果の推測をSTOP。いずれも原Study間独立と符号対称の近似で、調査法や地域の偏り・ランダムでない土地利用割当は解消できない。
- 健全性評価：各森林帯の得点可能な群数、主群の正/負方向、種類識別子・metric不備で除外された数、相対差のみのsummaryを保存。効果検定に有利な環境変数・taxonの切り替え、期間選択、種ごとの探索はしない。

## 先行性・主張の上限

従来の論文で自然林と改変林の分類群差は広範に報告済み。今回の統計は**原研究内の参照Forest同士の空間的変動を超えるか**という正規化された差であり、species-extinction, recolonization, dispersal, thermally driven escape, canopy height, forest matrix resistance, carbon service chain, conservation benefitの測定ではない。

**2020樹冠高との同時性**はない。サンプル最終年は2018以前のため、「2020年に林冠が高い森林で分類群が保たれた」という時間的一致や因果帰結を作らない。厳格母集団は湿潤熱帯林・温帯広葉樹林の2 biomeに偏り、全森林タイプ・全生物群の一般則とはしない。

## 実装/結果の解釈

本体：`analysis/forest_macro_global/predicts_forest_turnover_original.R`（合成既知解を先に確認、後に本物のNHM原本データを取得）。GitHub Actionsは旧site-only検査と**別ジョブ**。実行結果を読むまでは「仮説」状態。スコアが正負いずれでも、固定した数値・95%区間・Source/Study独立数・除外を報告し、PREDICTSで単独の結果が有意でもBALAやTHERAの独立再現とはしない。

前のStructural生物学的スコア（BALA 7島、GEB哺乳類、THERA未実測）を更新しない。eBird、TinyFish不使用。Draft PR #469を未マージとする。
