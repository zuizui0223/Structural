# NEON森林構造×甲虫×植物：元採集努力・季節・同区画の原本資格検証（2026-11-13）

## 実際に完走した原本メタデータ結果：厳格な局所比較は科学的STOP

NEON VST2026 RELEASE-2026の公開元原データと独立の`neonDivData` 0.3.1甲虫・植物を、元NEON `siteID × plotID × year`で結合。先行の元データ品質監査で**22独立sites / 13 domains / 73 元森林plot×year**が3本以上の個体別 live DBH≥10cmかつ有効樹高を持つと確定した。この**固定73**をそのまま対象とし、甲虫・植物の種名・`taxon_id`・捕獲数・β多様性・元高さの連続値を**一切読まず**、元採集日/品質/努力のみで照合した。

source-onlyで先に固定した基準：[FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_PLOT_EFFORT_SEASON_PRESPEC_20261113.md](FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_PLOT_EFFORT_SEASON_PRESPEC_20261113.md)。元樹木の測定日と植物最初の1m²調査日が90日以内、正常甲虫trap採集が植物日±30日、植物日±7日、甲虫4採集sample以上、植物で元1m²記録済みsubplot4以上、同site同年の2森林plotで甲虫trap-days総和と植物記録済みsubplots数が0.5–2倍、植物調査日のずれ30日以内という条件である。**元ネストsite/siteyear/plotを独立標本へすり替えない**。

### 一度目のsource-only原本ラン実測値

| 非生物学的資格 / 脱落理由 | 源のplot×year / site×year |
| --- | ---: |
| 上流で高さ3個体以上の独立NEON森区画×年 | **73 plot×years** |
| 甲虫正常trapが植物調査日±30日に存在しない | 3 plot×years |
| 元source甲虫sampleまたは植物1m²subplotが4未満 | 9 plot×years |
| 樹木原event日が植物調査日から90日超 | **25 plot×years** |
| 元season/effort条件をすべて満たす | **36 plot×years** |
| 同NEON site×同yearに、そのようなsource forest plotsが2以上 | **10 site×years** |
| 同source siteyear内の2plotでtrap-days・1m²subplot数・植物調査日がすべて対応 | **0 site×years** |
| 固定した次段の最小サポート（10 independent sites / 6 domains / 12 paired site×years） | **FAIL** |

元sourceイベントID不一致0、元trap efforts矛盾0、樹木event日の欠測0、同plotIDと採集年の入力不一致0。**データ内に高さがないという失敗ではなく、採集努力・季節を適切に揃えて比較できる2つのplotが、同じsite/yearで得られなかったという設計上の制約。**

これを森林構造と生物群集の関連が不存在・非有意と解釈しない。事後的に90日・4採集・比0.5–2.0を緩和して有意結果に近づけることはしない。元source植物1m²派生ではtargetTaxaPresent=Nのゼロ標本が一部除外され、記録されたsubplot数は完全な努力量ではないため、この条件を満たしても観察の検出機構を一致させたことにはならない。

### 実行証拠

- GitHub Actions [run #43338037317](https://github.com/zuizui0223/Structural/actions/runs/43338037317) **SUCCESS**（これは統計的な正結果ではなく、source-only資格診断プログラムの成功）、aggregate-only artifact **13998387732**、digest `sha256:fa54c5e8ec269401674df8cbe8159bc24cb72c1251a318b3042cb37f79fa2a4f`。
- 生物応答未読、木本の高さ値そのもの未使用、元sourceネストIDやspecies raw rowsをGitHubに再配布せず。コード`analysis/forest_macro_global/neon_vst2026_forestpatch_species_source_season_effort_gate.R`、`neon_public_vst2026_forestpatch_height_quality_gate.R`、CI `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`。
- **次のSource-only原因帰属**は10 site×yearsで候補になる原plot対について、甲虫trapdays比・植物陽性subplot比・固定植物調査日の差を別々に集計する診断（**条件を変更せず、群集分類群も開かない**）。この追加診断の原本値はまだ記載しない。ここまでの0ペア結論は固定して保持する。

## Structural の森林マクロ主線

- 既に実測で肯定的なPREDICTS 39 original study forest alteration×taxon replacement `+0.0942` / 95%CI `[+0.0638,+0.1253]` および31 studyの距離対応探索的感度 `+0.0847` / CI `[+0.0527,+0.1166]`は**この新しい source STOP で損なわれない**。NEON森林7サイトの植物×甲虫時間同期 `R=-0.0664` (p=.536) も別estimandとして凍結保持。
- 今回は林冠・微気候の機構を追加で肯定する結果は出ていない。森林構造実測と同時点の昆虫/植物群集を多地域で検証する際は、採集デザインの不一致を先に示す必要がある。
- BALA / THERA / GEB は変更せず、PR #469 Draft未マージ、eBird/TinyFish不使用。
