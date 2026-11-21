# NEON 22森林観測サイト：木本の有効樹高・同年複数区画の実測支持（2026-11-12）

## 継続結果（2026-11-13）：採集努力と調査季節を揃えた原本検査完了

この文書の73樹高有効plot×yearsについて、別の原source-only検証で**季節・最低努力条件を満たす36 plot×years、同一NEON site/yearに2plot以上ある10 groups、甲虫trap days・植物1m²subplot・植物調査日を一致させられる35 plot pairs／10 sites／8 domains／10 siteyears**が確認された。事前の生物効果解析許可は12 siteyearsだったので、**正しい原sourceでは生物効果未実行の科学的STOP**。旧誤判定の「0 plot pairs」はsource effort列名の不一致であり、訂正済み。詳細：[2026-11-13 season/effort source audit](FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_SEASON_EFFORT_ORIGINAL_RESULT_20261113.md)、[success CI #43340430135](https://github.com/zuizui0223/Structural/actions/runs/43340430135)。既存のPREDICTS/NEON陽性・非有意スコアは封印維持。

## 実行済み結果：原データをつなぐ科学的データ取得の肯定結果

**混在景観にあるoriginal forest patchesという独立の対象母集団**について、公開元の甲虫 `neonDivData`0.3.1・植物 `neonDivData`0.3.1・別途公表された木本構造 `DP1.10098.001 RELEASE-2026` を、3資料のsource-original `siteID×plotID×year`で対応させた。

**第1段Source-only** ([#43240643741](https://github.com/zuizui0223/Structural/actions/runs/43240643741))：甲虫・植物の原plotが両方forest-NLCDである35 sites・952 plot×yearsを得て、公開VST RDSを35/35 siteで読み込めた。そのうち原VST sourceの同year同plotに森林のtree-opportunity supportと正の面積があるのは **22 NEON sites・13 ecoclimatic domains・75 plot×years**。VSTに木本測定レコードがあるもの **74 plot×years**。ここでは原`height`の数値未読で、種名・生物計数値は未開封。

**第2段真正木本個体height品質** ([#43242197939](https://github.com/zuizui0223/Structural/actions/runs/43242197939))：源の`plotID×eventID`を対応させ、支持される元`tree_support=sampled_with_records`、元正の`area_trees`、元individualIDの重複除去、`live`または元`plantStatus=Live`、growth formのsingle/multi bole tree、DBH≥10cm、原`size_height_ok`と有限正のheightを確認。**74/74 record plot×yearsで最低1個体の有効樹高**、そのうち**73/74 plot×yearsで3個体以上**。元有効樹高測定個体数のplot×year中央値は**13個体**（DBH≥10cm/原source-QA通過/元個体ID単位）。実測位置・高さ値・学名・元生物測定値そのものはGitHubに出力せず、品質支持数だけ匿名化した。

次の群集統計に使える可能性のある**同じsource site・同yearで2以上の高さ有効元forest plots**は**17 site×years、16 source sites**で観測。これらの17は非独立なsite×yearであり、独立森林n=17とは呼ばない。構造source eligibilityの最低境界（6 sites・4 domains・40 plot×years）は**22 sites・13 domains・73 plot×years**で通過。つまり「森林構造と生物群集が接続不可能」という初回strict8 forest sitesだけの狭い結論は、**対象を森林patchにした新母集団では成り立たない**。ただし元strict8 source-only STOP（7 sites/26 plot×years）は保持し、別母集団で救済したことにしてはならない。

## 対応・原データの強い制約

- source別： [NEON公式木本構造RELEASE-2026](https://data.neonscience.org/data-products/DP1.10098.001/RELEASE-2026)、DOI 10.48443/pypa-qf12。公開独立派生 [NEON Vegetation Structure Explorer](https://github.com/tgilbert14/NEON-Vegetation-Structure-Explorer) exact data-family commit `3391e702e7be80a3f049c905782661f043be8db8`、科学契約`NEON-VST-DP1.10098.001-v2`。別途公開された甲虫植物`neonDivData`0.3.1、公式site metadata 2026-08-05 SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`。
- 本段階で実際に読んだVST`height`は**有効値・個体数の存在の検査**に限定。高さの実数値分布や森林間の構造差の効果量、元の分類群の学名/捕獲数/植物被度は未解析。`height`をメカニズムを決める測定値として扱うには、地理的独立性・測定面積・森林区画の樹齢・土地利用履歴・気温条件も確認する必要がある。
- 2019–2023の年度が一致しても**同じ季節・同じ調査努力で採集されたことを保証しない**。甲虫pitfall vs 植物1m²の検出過程は異なる。植物1m²のzero-targetTaxaPresent=N行は公開派生から一部除外されているので完全なabsence/局所消失量は扱えない。
- 地表甲虫は林冠甲虫ではない。樹木高さは立体的構造の一軸であり、微気候、林床温度、空間的な樹冠被覆、高さ方向の昆虫移動を直接測っていない。検査できるのはまず「同年同plotの**地表甲虫・植物組成と樹木高さという断面**の対応」。過去のPREDICTS `+0.0942/+0.0847`は森林改変と分類群置換という別推定量であり、今回の森林patch標本ではまだ再検証していない。
- 新母集団22森林のうち7は既存のstrict forest dominantサイトで、それ以外の最大15は混在景観内にある森林パッチである。将来の生物統計では**これを先に別に区分**し、既存NEON v2で生物応答を見た森林7を未開封の独立holdoutとは呼ばない。

## 解析へ進む際の独立ゲート

(1) 原sourceの同年同plotに2以上の森林区画がある17 site×yearsにおいて、各森林区画の甲虫正常トラップ努力量と1m²植物の調査面積、季節が揃うか**生物種名・数値未読のまま判定**する。(2) 比較する構造量は元`height`の**同plot・元eventの生きたDBH≥10cm個体の90%分位**に固定し、元個体IDで重複を除く。調査努力の違いを樹高の効果と呼ばない。(3) 少なくとも**10独立sites、6 domains、12対応site×years**が残るまでは群集組成との統計モデルに進まず、site-year pairを独立forestと数えない。これを通過しても地理距離（元plot座標）と季節・検出の問題を別に監査し、因果機構を主張せず探索に限定する。

**状態**：森林構造source-only original height gate COMPLETE; [成功CI #43242197939](https://github.com/zuizui0223/Structural/actions/runs/43242197939)、匿名ZIP artifact **13956291415** SHA256 **71a5c99b072ea13402b35a7c649c40599782429818171c91af0f089ce75936f5**。次の biological slope/preregisterは未実行。以前のNEON時間同期`r=-0.0664,p=.536`・PREDICTS39研究`Δβ=+0.0942`、距離対応31`+0.0847`など凍結した元結果は変えず、eBird/TinyFish未使用。PR #469はDraft/unmerged。
