# NEON森林：甲虫と植物の年次群集置換の同期性（v2、2026-11-12実行結果）

## 結論：定義済みの共通年次同期は検出されず。サンプル設計は成立

**実際に原データの生物応答を一度開き、解析が完走した結果：** NEONの元森林8サイト（7生態気候ドメイン）のうち、2019–2023年の植物・地表甲虫の年次Simpson置換成分が共に得点可能だった **7森林・6生態気候ドメイン**において、サイト内平均を差し引いた両分類群の時間的対応は **R_within_site = −0.0664**。サイトブロック4,000-bootstrapの95%区間 **[−0.5776,+0.1632]**、サイト内の植物年次ラベル9,999 permutationの両側 **p=0.536**。サイト内共分散は正2森林、負5森林。独立森林nは7であり、plotやsite×year transitionを独立研究と扱わない。

**明確な読み方：** 同じ森林で同じ年に植物の記録分類群の入れ替わりが大きいからといって、地表甲虫でも同時に大きいという正の同期は観測データから支持されなかった。一方、広い負方向や弱い正方向を排除できないため、「両群が独立に変化する」「森林内の階層が完全に独立している」という結論は支持されない。林冠構造・微気候・群集間の生態学的な因果連鎖はこのデータでは検定していない。

## 生物応答開封前後の適格性と脱落（値を隠さない）

- ソース：一般公開の `neonDivData` R **0.3.1** 派生データ（甲虫NEON DP1.10022.001、植物DP1.10058.001）と公式NEON field-site CSV 2026-08-05、SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`。トークン制限NEON原生物APIを回避していない。元原レコード・分類群名・数値・位置・イベントIDは再配布なし。
- 当初のsource-only cohort：**8森林／7 domains／339同一原plotでのsampling effortと近い観察日の元plot×year**。旧「39サイト年が厳密対応」の曖昧な解釈はv2メタデータ監査で訂正済み。
- 生物値を開く前に**さらに固定した**季節・努力・反復の適格性：初回植物調査日±7日、甲虫±30日、連続2年の植物調査DOY差≤45日、甲虫正常トラップで各年4 sample以上、1m²植物で各年4記録subplots以上、年次間trappingDaysとsubplots比0.5–2、両年の同一原plot、各site×year transitionに3 plot以上。
- 上記固定適格性の実測：元source候補348 plot×years、4甲虫＋4植物で306 plot×years；努力・季節・同plotを揃えた150 plot年次転換（**非独立**）、3 plot以上がある**24 site×year transitions**、元site8・domains7、各siteが2年次転換以上持つ8/8。最初のv1「各siteに3年以上の転換がありsite単独相関が5以上」条件では4 siteだけだったため、**v1はSCIENTIFIC STOPのまま**。元の生物値を見てからそのv1条件を後から改変していない。
- 別に事前固定したv2はsite内covariance・varianceの等重み比を推定する統計で、各siteに2以上の年次転換があれば定義可能。元分類群値を開く前の適格条件「6以上site・4以上domains・16以上site×year transitions」は**8 site・7 domains・24 transition**で通過。元source metaだけで選んだコホートである。
- 生物値を使った後、両群βが同じplotで定義できるsite×year transitionsは**20/24**、4は固定β定義不能で除外。得点可能な元plot年次βペア**113件（非独立）**。サイト内共変動の推定に使える独立forest sitesは**7**、domains6、site×year transitions20。
- 研究内の平均Simpson置換（site等重み）：地表甲虫 **0.1845**、植物の記録分類群 **0.1592**。これらは別分類群の記録ベースで、同じ種に対する効果量ではない。
- Leave-one-site-outの相関範囲 **[−0.1858,+0.0217]**。元データ1森林を抜くと小さな正方向になるケースがある。符号自体が頑健な負結果とは見なさない。

### 生態学的限界

1. NEONの地表甲虫はpitfallで、樹上甲虫・訪花昆虫の代表ではない。植物調査は1m²のtargetTaxaPresent=Nの空標本が派生データで除かれており、**真の不在・絶滅・移入・加入の量**は推定していない。甲虫では一部ゼロ捕獲を努力記録に保持し、植物の存在データと同一の検出モデルではない。
2. NEONのforestラベルは元NLCDのplot-level forestとsite-level dominant森林条件を通過したが、調査期間中の林冠構造・LiDAR・温湿度は同じ原plotで結合していない。**林冠高や気候による群集非同期性を実証したわけではない。**
3. 残る森林数7で区間は広く、季節・元調査法・植物の調査努力の欠落、NEONの2023年plotサンプル縮小などを完全には補正できない。p=0.536は「同期が存在しない」の証拠ではなく、固定した正の同期仮説を支持しなかったという意味。
4. PREDICTSの20か国39原研究で得た参照林内差分を超える空間的群集置換 **+0.0942**（CI +0.0638〜+0.1253）、距離対応探索的感度 **+0.0847**（CI +0.0527〜+0.1166）は全く異なる推定量。**空間的改変林差と時間的植物×甲虫同期を因果的に結ばず、独立再現・反証と数えない。**

## 原本監査、CIと再現性

- 解析前v2仕様：`docs/FOREST_MACRO_NEON_FOREST_TEMPORAL_ALIGNMENT_V2_SOURCE_ADAPTIVE_PRESPEC_20261112.md`、v1 STOP仕様：`docs/FOREST_MACRO_NEON_FOREST_CROSS_TAXON_TEMPORAL_ALIGNMENT_PRESPEC_20261112.md`。
- 成功した原本CI：[GitHub Actions #43216964523](https://github.com/zuizui0223/Structural/actions/runs/43216964523) 、source-adaptive v2 single run SUCCESS。生物結果zip artifact **13943484010**、SHA256 **7e2e44b05435e0f68ec2f0b205fcc384f683d33515d67f2a15e98ff14f937e8d**。
- 再現コード：`analysis/forest_macro_global/neon_forest_cross_taxon_temporal_alignment_v2.R`、ワークフロー：`.github/workflows/forest-macro-belgium-dryad-source-audit.yml`内の`sourceadaptive_v2_site_centered_forest_cross_taxon_temporal`。
- 初回失敗CI #43208807136 はRの改行`else`の構文エラー、合成テストと原本サイト取得は既成功、**生物学的結果は未出**。これを修正した後の本CIで元生物値を実際に得点した。元v1のscientific STOPも維持。
- **重要：結果を見た後に同期を正にするための層、期間、taxon、相関指標、閾値を追加探索しない。同じdatasetの複数の事後検定を新しい独立陽性証拠と呼ばない。** 原データを対象とする今後の質的修正は科学的停止・監査として区別する。

## 次の主線

PREDICTSの参照林内差分を超える群集置換は肯定的な**空間パターン**、NEONの同期は支持されない**時間パターン**として別建てで保存。次は両者を無理に統合するのでなく、林冠構造・微気候を生物応答と同じ観測単位・時期で持つ**地理的に複数の独立森林**を検証する。特定の一森林の原本（ベルギー36区画）や既発表の2森林で垂直分化を再得点して全球再現のように扱わない。eBird/TinyFish不使用、PR #469はDraft・未マージ。
