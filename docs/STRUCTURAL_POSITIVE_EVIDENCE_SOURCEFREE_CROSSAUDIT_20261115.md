# Structural 肯定結果の独立集計算術監査と生態学的証拠階層（2026-11-15）

## 監査対象・実施方法

- 対象：Draft [PR #469](https://github.com/zuizui0223/Structural/pull/469)、[PR #461](https://github.com/zuizui0223/Structural/pull/461)、[PR #463](https://github.com/zuizui0223/Structural/pull/463)、[PR #454](https://github.com/zuizui0223/Structural/pull/454)、既存の凍結済み哺乳類集計（main）。
- **今回実施した作業**：各解析の元手法、独立標本単位、原本→推定量、帰無、CI/pの意味を照合し、**既保存の集計数値だけ**から足し算・平均・比率・正確符号検定の整合を別計算した。元の種/地点別応答、予測確率、長期BALA原種記録、哺乳類holdout等は**一切再開封・再スコアしない**。
- 判定の階層：**A = 観測された群集差（条件付き・探索的）**, **B = 凍結モデルの予測改善（原因不明）**, **C = 記述的方向のみ・集団水準不確実**, **D = 数学的構成例**, **HOLD = 新規生物実証なし**。これらを異なる研究の「メタ解析用共通効果量」へ統合しない。
- このノートは**独立した原データ再現検証ではない**。CIの成功ログとSHA付き元成果物は既存の各PRにある。今回の追加検証は**source-free aggregate arithmetic / claim-boundary audit**だけ。

## 肯定・非支持を混同しない比較表

| 系・独立単位 | 凍結原解析の結果 | 監査判定・解釈上限 |
| --- | --- | --- |
| **島嶼哺乳類**：IUCN由来のmapped island×species、529 focal species・4,126 heldout islands・110 positive-bearing blocks | C−R3 のpresence-specific log-loss **−0.5962587**、95%CI **[−0.7439,−0.4645]**。20 rewired Cの平均 **−0.5377335**、元kNN特有の差 **−0.0585252** | **B**。グラフ・mapped presenceの予測差。現地の個体群存在、移動、再定着、絶滅・保全効果は未検証。全球哺乳類GEBは**SCIENTIFIC HOLD**。IUCN mammal-positiveで元島ノード選択が条件づけられている点も重要。[accounting](../development/global_mammals_graph_gain_accounting_v1_197.json)／[PR447](https://github.com/zuizui0223/Structural/pull/447) |
| **BALA 7島**：実原forest transects 29、元島n=7 | within-site temporal Sørensen identity-change excess：クモ **+0.1907755**、甲虫 **+0.2212088**、いずれも7/7島正・exact signflip **p=.015625** | **A（観測上の時間的種交代）**。同時期half-trap抽出の異質性より大きいが、絶滅・移民・検出補正済み真の遷移ではない。[v1.346 receipt](https://github.com/zuizui0223/Structural/blob/science/bala-multi-island-composition-v1-310/development/bala_jbi_seven_island_uncertainty_sourcefree_receipt_v1_346.json) |
| **BALA 7島**：同一群集の空間βの別終点 | 甲虫Simpson B3−B1平均 **−0.1753015**、島t95 **[−0.43994,+0.08934]**、exact signflip **p=.1875**。7/7 leave-one-island-out平均は負 | **C**。標本平均の空間的収束傾向だが集団水準の普遍的収束は**未支持**。LOO7回は独立反復ではない。Flores・São Jorge・Santa Mariaではlocal α増加と同時にsample β低下。[PR461](https://github.com/zuizui0223/Structural/pull/461) |
| **SLAM native vs mixed/exotic forests**：3島・33物理plot／664 original events | native−modified forest、同一島×quarterで固有分類群 **+2.335 taxa/event**、外来 **−2.515**、固有の方向3/3島一致 | **A（観測条件付き）**。約75%のdouble-contrast寄与はFlores。元forest habitatは標高・歴史・methodと交絡、改変の因果効果ではない。[PR463](https://github.com/zuizui0223/Structural/pull/463) |
| **PREDICTS**：39 original studies／20 countries | altered/reference − reference/reference Simpson replacement **+0.0942**、study bootstrap95 **[+0.0638,+0.1253]**、36/39 study正。距離対応の別次探索：31 study **+0.0847** [+.0527,+.1166]、25/31正 | **A（観測条件付き）**。改変林でtaxonomy組成が離れるという相対差。歴史的調査・座標誤差・距離/環境交絡、同一原本再解析で独立外部確認ではない。[primary](FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_ORIGINAL_RESULT_20261112.md)／[distance](FOREST_MACRO_PREDICTS_DISTANCE_MATCHED_SECONDARY_RESULT_20261112.md) |
| **Thailand vertical beetles**：同森林内18物理station・36 station×campaign pairs | 上層899／下層723個体、同method; station paired差 **+4.889 beetles/station×campaign**、18-station signflip **p=.0043945**、forest-stratified bootstrap [+2.306,+7.611] | **A（観測上の個体数差）**。2森林の反復であって18森林ではない。別の種多様性・林冠高の因果効果と取り違えない。[PR469](https://github.com/zuizui0223/Structural/pull/469) |
| **Nardi urban-gradient beetles**：13 landscapes、207 original traps | 景観内都市化指数差に対応するspatial Simpson replacement傾き **+0.0146126/1SD**、13景観 bootstrap95 [+0.003167,+0.027825]、p=.0062 | **A（探索的）**。元著者の既刊研究と地理距離・捕獲効率の問題あり。移動や林冠/林床差ではない。[result](FOREST_BEETLE_13_LANDSCAPE_TURNOVER_URBAN_DIFFERENCE_RESULT_20261108.md) |
| **Burner Host_tree guild**：3 country source matrices、original 1,622 *sample columns* | observed mean sqrt-JSD **0.240841** − within-country species label shuffle null **0.149782** = **D=+.091059**、conditional 2-sided p=.000333 | **A（species-label交換可能性条件付き）**。sample columnsは物理林ではない。系統保存、地理的自己相関、trait missingnessなどは未除去。新しい樹種資源測定の証拠ではない。[result](FOREST_BEETLE_THREE_REGION_HOST_GUILD_TURNOVER_RESULT_20261115.md) |
| **Finland physical-site sensitivity**：142 author-verifiable sites | 10,011 site-pairs、observed sqrt-JSD .118481 − trait-label null .083244 = **D=+.035237**, conditional p=.000333 | **A（同一研究内頑健性）**。旧Finland sample-column D=.034683と整合。3-country結果とは**独立の新森林コホートではない**。[site result](FOREST_BEETLE_FINLAND_AUTHOR142_SITE_HOSTGUILD_ACTUAL_SENSITIVITY_20261115.md) |
| **Finland VD10 deadwood**：142物理sites・9 spatial cells | ブロック等重みの out-of-block ΔHellinger² **+0.00024237**、cell-bootstrap95 [+.00012123,+.00035658]、conditional 9999 signflip **p=.0150**、7/9 block改善。site-equal error .00574894→.00556866 | **B（同一データ・小さな予測増分）**。local total deadwood author-log-z追加の約3.14%誤差縮小。9セルのうち最小1地点、cellの交換可能性・境界空間相関を十分評価できない。樹種別deadwood資源・因果機構は未測定。[prespec](FOREST_BEETLE_FINLAND_142SITE_DEADWOOD_HOSTGUILD_SPATIAL_HOLDOUT_PRESPEC_20261115.md)／[result](FOREST_BEETLE_FINLAND_142SITE_DEADWOOD_HOSTGUILD_SPATIAL_HOLDOUT_ACTUAL_RESULT_20261115.md) |
| **NEON CHMv2 height × ground beetle β**：18 sites・10 domains | 10m CHM P90差当たり +.0349、site-bootstrap95 [−.0158,+.1079]、plot-label p=.1759 | **C（主仮説の非支持）**。NEON現地木本P90×衛星P90の構造測定のρ=.9063は別の**測定較正の肯定結果**であり、生物学的height依存の証拠ではない。[result](FOREST_MACRO_NEON_CHMV2_BEETLE_ONEPASS_ACTUAL_RESULT_20261115.md) |
| **Higher-order donor cutset**：16-state exact hypothetical probability laws | 同じ単独・pair reliability / global count / topologyでも受容島A/Bの高リスク順位は反転。成功率 q=1 の理想介入でpolicy regret **1/8**、q=.5では**1/16** | **D（厳密なモデル反例）**。生態学的に検定すべき機構を指定するが、実際の繁殖・再定着・管理の観測効果量ではない。[PR454](https://github.com/zuizui0223/Structural/pull/454) |

## 別実装の集計算術検証（元source valuesを使わずに計算）

1. Mammal identity: `−0.5377334912434378 − 0.058525177248239975 = −0.5962586684916778`（保存 −0.5962586684916777 との差は浮動小数点丸めのみ）。平均rewired相当 **90.1846%**、元kNN特有 **9.8154%** は**点推定の比**であり分散説明率や因果内訳ではない。
2. BALA 7島すべて同符号の両側exact signflip下限は `2 / 2^7 = 0.015625`、報告値と一致。甲虫空間βのt95区間はゼロを含み、`p=.1875` と整合。temporalとspatialを「7/7有意」とまとめない。
3. Thai counts `(899−723)/723 = +24.3430%`；18個の**独立したforest**とは言わない。
4. Burner eligible sample columns `153+376+1093=1622`；country mean `(.117609+.326269+.278645)/3=.240841`、null `(.082926+.191254+.175166)/3=.149782`、差 **+.091059**。142 Finnish site-pairs `142×141/2=10011`、site-level差 `.118481−.083244=.035237`。各元summaryと一致。
5. Finland site-equal lossの表示値差 `.00574894−.00556866=.00018028`、相対 **3.13588%**。原結果のdelta `.00018027`との1e−8差は**各loss表示の独立丸め**に起因し得るため、集計不整合と判定しない（原非丸め値は今回再読せず）。primary block-equal `.00024237` と site-equal `.00018027` は**別の重み**であり混ぜない。
6. Finland **7/9** の正方向「だけ」を使った両側exact binomial sign testは `2×(C(9,7)+C(9,8)+C(9,9))/2^9 = .1796875`。報告の **p=.0150** は各cellの**効果の大きさ**を使う符号反転であり、両pが違うこと自体はバグではない。9ブロック・1地点cellの感度とexchangeability未検証ゆえ、**幅方向だけで頑健性を誇張しない**。
7. 16-state conservation hypothetical q=1 の regret `3/16−1/16=1/8`、q=.5 では `(1/8)×.5=1/16`。実データでの移入確率へ読み替えない。

**算術監査：7/7チェック系で上記の等式・分母・区間解釈はPASS。** これは独立原sourceの再実行・CI監査の全件検証ではない。

## 生態学的に何が言えるか

複数の独立観測設計で**種数だけでは見えない群集の差（replacement / host-affiliation composition / origin-specific shifts）**が実測された。そこから一歩進んだ「構造化された群集配置が新しい条件の下で繁殖・移動・存続を左右する」ことは、**独立した縦断的遷移・送出個体・受容先の加入・観測努力**がなければ識別できない。PREDICTSのSimpson置換、Thai個体数、Finnish Hellinger予測差、mammal log-lossを**一つの統計的メタ平均**にしない。

特に哺乳類では、元kNN固有の予測情報は総改善の点推定の約9.8%で、多くはrewired surrogateでも得られる。**「正確な島のつながりが救済を決める」より「供給源候補の占有状態が予測の役に立つが、真の移動ネットワークは不明」が支持範囲**。森林側では、元sourceに測定されたtotal deadwoodがわずかな追加予測を持つが**host tree species-specific resource availabilityと群集形成を接続する新規独立検定は未達**。

## 今後の検証ゲート（既封印の生物結果を開き直さない）

独立の元データで同一`field site / year / sampling method / sampling effort`を確認し、**木本資源の量と樹種同定**を事前に固定してから、甲虫のHost_treeギルド構成が**地理＋林齢＋気候＋努力量**を越えて新しい地域で予測できるかを、原現地地点・地域のholdoutで比較する。未完了の現状は次の通り。

- Sweden Ramberg original 23 sites/3 regions：Dryad正式の8ファイルmanifest確認、READMEの公式file GET **HTTP401**、生物値ゼロ開封。
- Poland 2026：source xlsx実ファイルMD5と48行×2表のsheet shapeは確認したが、同じ行番号＝同じ元physical siteとは未立証。species-outcome値ゼロ開封。
- Lettenmaier長期実丸太：522 long candidateと525 community IDs、固定6順列中の最高一致**359/522**だけで、**163 long-only、166 community-only**。原作者対応表がない限り生物スコアSTOP。
- BELongDead 30plots/379 source logs：30plot同定は成功。ただし元31124→31123に**15** unmatched TrapID、2012 ambient wood 1,385 itemsの元`L7`表記と単位説明`T7`が衝突。元`T/L`のm³と`S`のm³/haを合算禁止。2012資源と2010–2017 beetle captureの時間的対応も必要。**新しい生物係数は0件**。

新しい独立実験の許可基準を勝手に緩めず、上記「何が実際に不明か」を原author methodsと明示的crosswalkで解決する。源原species-values再採点、既存GEB confirmatory-heldout、BALA biological scorersの再実行、eBird/TinyFish利用はしない。

**保存状態：追加したのはsource-free集計・解釈監査だけ。元PR #469はDraft・main未変更。原解析・公表・外部投稿アクションは行っていない。**
