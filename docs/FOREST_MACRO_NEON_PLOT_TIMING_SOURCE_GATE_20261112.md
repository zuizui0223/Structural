# NEON 公開派生データ：同一区画・季節・努力の観測支持監査（2026-11-12）

## 2026-11-12：原本スキーマ・区画・採集努力の厳格一致が完了

公式サイト原本（2026-08-05 SHA固定）×公開 `neonDivData` 0.3.1により、**森林8サイト、7生態気候ドメイン、2019–2023年の40サイト年**を原本で確認。全40サイト年に両分類群が記録された元同一plotIDがあり、計83の元plot keysが2分類群で少なくとも一度共有された。

初版v1では「サイト年内のどこかに同じplot」「どこかに採集努力」「どこかの採集日が30日以内」を別plotで満たせたため、**39/40を『厳密同一区画一致』とした解釈を撤回**。修正版v2は、**同一original plotID・同年・正常フラグ甲虫trappingDays>0・植物1m²・両群30日以内**を全て同一区画で必須化した。合成テストは、条件が異なるplotに分散する偽陽性とフラグ付きトラップを拒否し、原本 [GitHub Actions #43204131183](https://github.com/zuizui0223/Structural/actions/runs/43204131183) でSUCCESS。

| 修正後の原本集計 | 数 |
| --- | ---: |
| 同一plotでの厳格採集条件を満たすplot×year | **339** |
| 元plotIDが2年以上残るもの | **81** |
| 同じ元plotIDの隣接年の機会数 | **242（非独立）** |
| 厳格条件のあるsite×year | **39/40** |
| 同じ元plotが隣接年に残るsite×year遷移 | **30** |
| 独立forest site（site-context）とdomains | **8 sites / 7 domains** |
| 2022→2023で同一plotを保てたsite | **8** |

この条件は**採集可能性**のみで、種・個体数・群集βを読んだ結果ではない。2023年の甲虫区画数中央値は6（2019–2022の各年10）と異なり、site-yearが一致するだけで同じサンプル面積・調査努力が保証されるわけではない。

元パッケージ文書によると、甲虫はゼロ捕獲を努力標本として保存する一方、植物1m²のtargetTaxaPresent=Nの空標本は派生データから削除済み。よって植物の記録済みsubplots数は元のすべての調査単位数ではない。[NEON package beetle documentation](https://daijiang.github.io/neonDivData/reference/data_beetle.html)、[plant documentation](https://daijiang.github.io/neonDivData/reference/data_plant.html)。植物の真の不在や植生の消失をこの派生データだけで確証しない。

次の一度限りの探索的生物スコアは[解析前固定仕様](FOREST_MACRO_NEON_FOREST_CROSS_TAXON_TEMPORAL_ALIGNMENT_PRESPEC_20261112.md)に分離し、サイト/plot階層を尊重する。PREDICTSの39研究主スコア・31研究感度は再採点しない。森林構造/微気候の因果も主張しない。

## 研究主線

PREDICTSの39研究で参照林内の変動を超える群集置換が+0.0942（Study bootstrap 95%CI [0.0638,0.1253]）、地理距離対応の探索的31研究でも+0.0847（CI [0.0527,0.1166]）という既存肯定結果は一度の解析後凍結済み。PREDICTSの結果を林冠構造や温度の因果的効果に昇格しない。今回の目的は、**北米NEONの森林観測ネットワークで植物と地表甲虫を同じplotID/年に標準化して比較できるか**を、分類群値を開く前に確定すること。

## 使用する実在資料と独立単位

1. 一般公開の研究者派生Rパッケージ `neonDivData` **0.3.1** の甲虫 `data_beetle`（DP1.10022.001）と植物 `data_plant`（DP1.10058.001）。**現在のNEON生物データAPIを認証回避して取得したものではない**。元データから著者が加工した派生版である。
2. 元の公式NEON 2026-08-05 field-site CSV（81サイト） SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`。独立forest site候補は元`dominant_nlcd_classes`がDeciduous Forest, Evergreen Forest, Mixed Forestだけからなるsiteに限る。**site-level forest classであって観測した全plotsが森林とは限らない**。
3. 実行済みメタデータ-only CI #43200825696：派生甲虫全152,774行・植物1,343,756行、2019–2023甲虫74,583行・植物539,793行、47共通sites・223共通site×years。このうちsite-level厳格森林で**8サイト×40サイト年・7生態気候ドメイン**が共通し、公式site平均canopy heightは8サイトで正値。**高さは現地plot/採集時点の数値でない**。
4. original `plotID`（NEON Distributed base plot）を一次のフィールド階層とし、年を反復単位、siteID・domainIDを空間階層として別に保持。甲虫ピットフォールと植物subplotの観察量・検出方法は異なる。公式NEON site designは地表甲虫と植物をbase plotsの一部にco-locateしているが、実データに同じ`plotID`が存在するか別に数える。<https://www.neonscience.org/data-samples/data-collection/observational-sampling/site-level-sampling-design>
5. 植物1m²の調査サンプルを時間的比較の第一候補に限定（10/100m²はNEONでは近年隔年になることがある）。甲虫は`trappingDays>0`の元distinct sample keyのみ数える。trapConditionFlagの内容を残し、不良トラップ標本を正常な努力量と合算しない。
6. 植物と甲虫の同一original `plotID`・同年・採集日30日以内を**観測の時間空間的近接支持条件**とする。この条件でも直接の物種相互作用・送粉・栄養塩伝達・微気候の作用は証明されない。
7. `neonDivData 0.3.1` の実際の元`nlcdClass`値を生物応答を見ずに監査すると、`evergreenForest`, `deciduousForest`, `mixedForest` という**camelCase**だった。旧解析の`Deciduous Forest`など空白区切りに限定した0件は**文字列コードブックの誤指定**であり、森林区画なしという科学的な結果ではない。修正後、同一元`plotID`で両群とも元のforestラベルを持つことを明示的に要求する。原siteが森林であるだけの比較をbio endpointへは進めない。

## 2023年採集プロトコルの構造的変化

NEON公式地表甲虫ユーザーガイド（2025年改訂F）では **2013–2022: 10 Distributed plots／site、2023以降: 6 plots／site** を明記している。原区画の退役や位置移動もあり得る。<https://data.neonscience.org/api/v0/documents/NEON_beetle_userGuide_vF?inline=true>。「同じsiteID・異なる年」だけで種交代を計算してはならない。次段の時間軸候補は、連続年**両方**で植物1 m²・甲虫努力正・採集日30日以内という条件を満たす**同一元plotID**が最低1つ残るsite×year遷移に限る。2022→2023のプロトコル変更を独立感度層とし、結果の符号を見て2023年の採用を選択しない。

## 原本検査の次段階への定量的ゲート（生物応答を見る前に固定）

- `analysis/forest_macro_global/neon_divdata_forest_plot_temporal_gate.R` は**サイト/年、元plotとsample ID、採集努力・面積・月だけ**を読む。種名、taxon_id、taxon_name、value、植物種数を一切読まず、元サイト・区画座標を出力しない。
- Exploratory cross-taxon forest temporal beta の生物応答を開く条件は、(a)同一plotの甲虫・植物・同年・30日以内かつ植物1m²と正の甲虫trap daysがある**6以上の元forest site**、(b)**4以上の元ecoclimatic domains**、(c)同じ原plotIDが両年に残る条件の連続した年の比較機会が**16以上**（ただし独立サンプルn=最大8 site）を同時に満たすこと。各条件は生物応答の符号やp値に関係なく固定。条件未達なら**SCIENTIFIC_STOP_SAMPLE_HIERARCHY_INSUFFICIENT**、分類群スコアを開かず別設計を検討。
- 生物値を開くことが可能であっても、sampled plotsの空間同一性、品質フラグ、植物調査面積による努力差を原単位で固定するまで、全サイト年の単純なspecies-richness/turnover統合は行わない。独立性はsite単位（その背後の7 domainsでの階層を保つ）、40 siteyears=40独立森林と数えない。
- 元生物スコアを後から都合良く「林冠高」「微気候」「生態系サービス連鎖」の因果機構と結びつけず、外部森林構造の同時点・同plot field joinの別確認を必要とする。

進捗：新規site-level森林8×40×7は確認済み。plot-level/季節/努力監査は新しいCIに実装し実行、結果は完了後にsource-only reportとして固定する。BALA・GEB・PREDICTS・THERAの生物学的凍結結果を更新しない。eBird/TinyFish不使用。PR #469はDraftのまま。
