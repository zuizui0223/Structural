# NEON：混在景観の森林区画における樹木構造×植物×地表甲虫の同年同plot原本（2026-11-12）

## 2つの事前母集団は分離：strict森林優占siteとmixed景観内の森林patch

最初に固定していた、**サイト全域の公式NLCD主要景観が森林カテゴリーに限られる8 sites**では、neonDivData0.3.1の甲虫・植物の元同一区画・同年採集と、公開VST2026の元tree sampling opportunityが重なったのは**7 sites・7 domains・26 plot×years**。最小支持6 sites/4 domains/40 plot×yearsには足らず、[元strictコホート結果](FOREST_MACRO_NEON_VST2026_STRICT_FOREST_ORIGINAL_PLOTYEAR_RESULT_20261112.md)は**SCIENTIFIC STOP**、生物応答を開かず凍結。

別母集団として先に固定したのが、サイト全域が森林でなくても**森林分類のoriginal plotだけ**を使う mixed-landscape forest patches である。甲虫・植物・木本VST 3つの別データで独立に同plotの森林NLCD（Evergreen/Deciduous/Mixed forest）を確認し、原plotID×暦年で一致させた。

## 実際に実行した原本監査（分類群値は全て未開封）

| source-only母数 | 実測 |
| --- | ---: |
| 甲虫と植物の双方が元plotでforest分類される独立NEON sites | **35** |
| 上記の元同plot×2019–2023年・甲虫正常trap-days正・植物1m²観測機会 | **952** |
| 35 sitesのうち公開VST42-site RELEASE-2026 RDSを実際に取得・契約確認 | **35/35** |
| 3資料が同plot・同yearで揃い、VST木本sampling opportunityに元support/areaがある | **75 plot×years** |
| うちVST `sampled_with_records`の樹木測定レコードが存在 | **74 plot×years** |
| 75 plot×yearsが分布する元NEON独立sites | **22** |
| 当該sitesの生態気候NEON domains | **13** |
| 元8-site strict森林優占母集団に属するsites（75内） | **7** |

**予め固定した source-only次段の最小支持 6 sites / 4 domains / 40 plot×years は、22/13/75で通過。** これは**森林構造による群集効果がある**という結果ではなく、初めて同plot/同yearで構造と生物群集を結ぶ実際の比較母集団が得られたという**データ取得／設計上の肯定結果**。

- VST側も原plot `nlcdClass`が明示的に森林に該当し、`tree_support`が`sampled_with_records`または`sampled_absence`、元`area_trees>0`のイベントだけを許可。held/missingをゼロに変換しない。高さ・幹径の数値自体はこのstageでは読んでおらず、`height`列の存在だけ確認。
- 元対象サイト22は独立NEON観測site単位、13 domainsにネストされる。75 site-plot-yearsや対象木本行数を独立森林数として数えない。
- 既存NEON v2年次同調率`r=-0.0664,p=.536`は厳密な8 forest-dominant source sitesの7スコア可能sitesで既に得た異なる推定対象。今回の75を使ってその検定の正の結果を選び直したり、PREDICTS`+0.0942`との因果を捏造しない。
- 3資料の採集日そのものは同じと限らない。構造の同年測定機会は地表温度や微気候の同じ月日の測定ではない。公式VST Distributed plotsは原則5年周期で、Tower plotsの一部は年次、測定法に非対称性がある。

## 出典とコード

- 原ソースNEON VST`DP1.10098.001` official RELEASE-2026 DOI 10.48443/pypa-qf12。42-site別公開二次アーカイブ：[tgilbert14/NEON-Vegetation-Structure-Explorer](https://github.com/tgilbert14/NEON-Vegetation-Structure-Explorer)固定commit `3391e702e7be80a3f049c905782661f043be8db8`。
- 公開甲虫・植物`neonDivData` v0.3.1 とNEON公式 site context 2026-08-05（SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`）。派生元記録・元site/plot/year・種名・元樹木RDSをStructuralのGitに置かない。
- 成功したCI [#43240643741](https://github.com/zuizui0223/Structural/actions/runs/43240643741)、匿名集計artifact **13954835925**、zip SHA256 **28f76b79aa96037034174b6c9cede4e008798176c981954461305331642809ae**。
- 実装 `analysis/forest_macro_global/neon_public_vst2026_mixedlandscape_forest_patches_gate.R`、CI `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`。
- 次の独立ゲート：元`trees`に有効な樹高が少なくとも各元plot×yearに**3本の別個体**存在し、**6 sites・4 domains・40 plot×years**が残るか、**同site同yearで複数元plotsがあるか**を原木本データだけで確認する。木本の`live`・`size_height_ok`、DBH≥10cm、個体IDで重複除去。被験群集のtaxon/valueを再開封しない。条件未達なら**SCIENTIFIC STOP**。

PR #469はDraft、既存PREDICTS 39Study/31Study、NEON v1 STOP/v2非有意、BALA/THERA/GEBは凍結維持。eBird/TinyFish不使用。
