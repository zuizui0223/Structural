# NEON森林構造×甲虫×植物：元採集努力・季節・同区画の原本資格検証（2026-11-13）

## 最終原本結果（2026-11-13）：10サイト・8domains・35区画対を確認、ただし12サイト年に不足

元sourceの`date_effort_in_plot()`が出力する植物記録1m²subplot数の正式名は`recorded_one_m2_plant_subplots`だが、後段の区画間比を比較する関数が存在しない`plant_recorded_1m2_subplots`を参照していた。このため後段の判定は`NA`になり、旧CI #43338037317の**区画対0とFAILという最終判定は正当な原本結果ではない**。元固定73区画年から36区画年までの採集時期と4sample/4subplot等の前段監査結果、および同site×yearに2区画以上の10候補は有効。

この問題を合成データCI #43338958843 と #43339696607 で検出し、**項目名を正し、存在しないsourceフィールドはNAにせず明示的にSTOPする**テストを追加した。旧0および旧FAILを論文や結果要約に引用しない。訂正後の真正原本CI **[#43340430135](https://github.com/zuizui0223/Structural/actions/runs/43340430135)** がSUCCESSし、実際の区画間一致を確認した（後掲）。分類群・樹高の連続値・生物効果は未開封。

## 修正済み実測値（元source前段は変更なし）

NEON VST2026 RELEASE-2026の公開元原データと独立の`neonDivData` 0.3.1甲虫・植物を、元NEON `siteID × plotID × year`で結合。先行の元データ品質監査で**22独立sites / 13 domains / 73 元森林plot×year**が3本以上の個体別 live DBH≥10cmかつ有効樹高を持つと確定した。この**固定73**をそのまま対象とし、甲虫・植物の種名・`taxon_id`・捕獲数・β多様性・元高さの連続値を**一切読まず**、元採集日/品質/努力のみで照合した。

source-onlyで先に固定した基準：[FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_PLOT_EFFORT_SEASON_PRESPEC_20261113.md](FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_PLOT_EFFORT_SEASON_PRESPEC_20261113.md)。元樹木の測定日と植物最初の1m²調査日が90日以内、正常甲虫trap採集が植物日±30日、植物日±7日、甲虫4採集sample以上、植物で元1m²記録済みsubplot4以上、同site同年の2森林plotで甲虫trap-days総和と植物記録済みsubplots数が0.5–2倍、植物調査日のずれ30日以内という条件である。**元ネストsite/siteyear/plotを独立標本へすり替えない**。

### 原本修正後のsource-only実測値

| 非生物学的資格 / 脱落理由 | 源のplot×year / site×year |
| --- | ---: |
| 上流で高さ3個体以上の独立NEON森区画×年 | **73 plot×years** |
| 甲虫正常trapが植物調査日±30日に存在しない | 3 plot×years |
| 元source甲虫sampleまたは植物1m²subplotが4未満 | 9 plot×years |
| 樹木原event日が植物調査日から90日超 | **25 plot×years** |
| 元season/effort条件をすべて満たす | **36 plot×years** |
| 同NEON site×同yearに、そのようなsource forest plotsが2以上 | **10 site×years** |
| 同source siteyear内の2plotでtrap-days・1m²subplot数・植物調査日がすべて対応 | **10 site×years、35非独立plot対** |
| 元独立NEON site、domain、対応site×yearの支持 | **10 sites／8 domains／10 site×years** |
| 固定した次段の最小サポート（10 independent sites / 6 domains / 12 paired site×years） | **FAIL：site年10<12のみ不足** |

元sourceイベントID不一致0、元trap efforts矛盾0、樹木event日の欠測0、同plotIDと採集年の入力不一致0。**旧コードによるゼロ区画対判定は完全に撤回し、修正版の35区画対を唯一の原本結果とする。**

これを森林構造と生物群集の関連が不存在・非有意と解釈しない。事後的に90日・4採集・比0.5–2.0を緩和して有意結果に近づけることはしない。元source植物1m²派生ではtargetTaxaPresent=Nのゼロ標本が一部除外され、記録されたsubplot数は完全な努力量ではないため、この条件を満たしても観察の検出機構を一致させたことにはならない。

### 区画間一致の条件別診断（73固定plot×yearからの結果）

同一site×yearに2以上の採集適格森林plotがある10 site×yearsから、まず**41**組の非独立候補plot対を作った。甲虫トラップ日数比0.5〜2倍は**39/41**、植物1m²の記録済みsubplot数比0.5〜2倍は**41/41**、植物最初の調査日差30日以内は**36/41**、両努力量比が一致するものは**39/41**。同一plot対で**努力量比2つ・調査時期の3条件すべて**が合致するのは **35/41組** で、**10 original sites・8 domains・10 site×years**のいずれにも1組以上あった。

この修正で、採集条件がほとんど一致しないとの誤解は解消した。ただし**20か国にわたるPREDICTSのような独立原研究39群のサンプルではなく、NEON 10 sites、10 site×years**である。事前固定条件のうちsite数10/10、domain数8/6は満たしたが、site×year数10/12が不足することは、季節条件の比率を評価する以前に数学的に決まる。**生物学的構造-群集効果の推測は実行せずSCIENTIFIC STOPのまま**。恣意的にn=12の閾値を10へ緩和しない。

### 実行証拠

- GitHub Actions [run #43338037317](https://github.com/zuizui0223/Structural/actions/runs/43338037317) **SUCCESS**（これは統計的な正結果ではなく、source-only資格診断プログラムの成功）、aggregate-only artifact **13998387732**、digest `sha256:fa54c5e8ec269401674df8cbe8159bc24cb72c1251a318b3042cb37f79fa2a4f`。
- 生物応答未読、木本の高さ値そのもの未使用、元sourceネストIDやspecies raw rowsをGitHubに再配布せず。コード`analysis/forest_macro_global/neon_vst2026_forestpatch_species_source_season_effort_gate.R`、`neon_public_vst2026_forestpatch_height_quality_gate.R`、CI `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`。
- 原plot対の甲虫努力量、植物subplot、調査時期の**それぞれの分解診断も完了**。誤コードによりplant ratioがNAとなるのを防ぐため、元フィールド名の存在を合成known-truthで検査し、欠落時には明示的SCIENTIFIC STOPを出す。旧0ペア結論は無効として記録し、上記35組へ訂正済み。

## Structural の森林マクロ主線

- 既に実測で肯定的なPREDICTS 39 original study forest alteration×taxon replacement `+0.0942` / 95%CI `[+0.0638,+0.1253]` および31 studyの距離対応探索的感度 `+0.0847` / CI `[+0.0527,+0.1166]`は**この新しい source STOP で損なわれない**。NEON森林7サイトの植物×甲虫時間同期 `R=-0.0664` (p=.536) も別estimandとして凍結保持。
- 今回は森林構造を実際に測れる**10独立森林sites・8domains・35plot対**の存在を確認できたという**データ取得上の肯定結果**が出た。しかし対応のあるsite×yearは10だけで固定最低12に達せず、林冠・微気候の生態学的機構を肯定する効果量・統計検定は実行していない。研究比較は独立site数と同年反復の両方に制約される。
- BALA / THERA / GEB は変更せず、PR #469 Draft未マージ、eBird/TinyFish不使用。
