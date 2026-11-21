# NEON 2019–2020森林CHMv2高差と地表甲虫の空間的分類群置換 — 生物値初回開封前に固定する1つの主解析（2026-11-14）

## 出発点と識別可能な質問

CHMv2をNEON原forest field plotsと結合したsource-only検査は、**2019–2020年395候補plot×year → CHM40m品質適格388 → 甲虫/植物季節・最低4採集正規化340 → 同source site/yearに3元forest plotsが相互努力/season適格な44 groups、26 NEON独立sites・15 ecoclimatic domains** で成功した（[原本CI #43562142519](https://github.com/zuizui0223/Structural/actions/runs/43562142519)）。完全互換plot cliqueの元plot×year機会は303、そこから取れるplot pairsは992（**非独立**）。同site/yearの林冠高P90 rangeの中央値**9.5m**、同plot pairの位置距離の中央値**2.2321 km**。事前固定10sites/6domains/12siteyearsのsource eligibility PASS。**この母集団は生物学的結果に一切触れずに確定した**。

別測定による樹高proxy妥当性は、静的CHMv2と独立VSTフィールドheightの22 NEON sites・72 original plotでsite-equal Spearman`ρ=+0.9063`、site-bootstrap95%CI[+0.7457,+0.9658]、現地heightとの差の絶対中央値3.57m（[CI #43561149201](https://github.com/zuizui0223/Structural/actions/runs/43561149201)）。ただしCHMv2画素取得日時は個々のplotに割当不能。2018–2020頃の**静的な高さproxy**と2019–2020年の観測群集の対応のみで、林冠高の年次変化や因果効果を観測していない。

**唯一の確認的ではない主問い（探索的）：** 「同じ元NEON森林サイト・同じ年に採集した原plot間では、静的林冠高P90の差が大きいほど、地表甲虫の記録された分類群置換成分Simpson β_simが高いか。それは地理距離を調整しても残るか」。方向は**正**が理論予測だが、p値は両側・正負両方報告する。PREDICTS39studyとの独立な新規野外確認だとは呼ばず、元NEONの公表済み生物標本の別観測contrast。

## 生物値を開封する前の固定入力／階層

1. SOURCE元資料は`neonDivData 0.3.1`の`data_beetle`,`data_plant`の元`siteID/plotID/unique_sample_id/trapID/date/trappingDays/trapConditionFlag`と植物1m²記録、公式NEON 2026-08-05元sites、公開CHMv2 DINOv3 Source Cooperativeの40m×40m元field plot centre positive pixel QA、`acq_dates`だけ。VST 2019–2023の現地同年10siteyear STOPは解除せず、CHMv2を**別の静的構造proxy**として扱う。
2. `original site×year`でsource-onlyの最大の相互比較可能plot clique（3以上）を使用。同数のcliqueは元plot ID昇順。元siteで2019と2020双方が適格なら**2020を優先**、そうでなければ2019（応答値から選ばない）。**1 NEON siteに1年・1cliqueのみ**。元site×plotの正画素P90はstaticであり複数年の新しい構造値とはみなさない。
3. Source effortは既凍結のまま：plant source最初の1m²調査日±7d、ground beetle `trappingDays>0`・unflagged・元sampleID+trapIDあり・植物日±30d、植物元記録subplots4以上・甲虫元samples4以上、元sampleIDごとの努力矛盾禁止。同site/yearの元plot同士で総trap-days・記録済み植物1m²subplot比0.5–2、植物最初の調査日差<=30d。source private CSVに固定したplot ID/date/努力を、元生物の抽出段階で再計算・照合し、source-methodの不一致なら効果を見る前にSTOP。source effectの標本条件を後から変更しない。
4. 初回開封する甲虫生物列は`taxon_id`,`taxon_rank`,`value`のみ。元`taxon_rank`がspecies/subspecies/variety、元valueが有限正、元taxon_id非欠測の**source recorded taxon incidence**を各original plot内で集合にする。元trap value=0/NAやsource flagを植物のabsenceと同一の「種欠如」にはしない。元検出分類群ゼロのplotがあるsiteは**site全体を未定義として除外**し、betaに都合よいplotだけを捨てない。共通の種ランクでないtaxonや元同定不確かをspeciesと仮称しない。
5. すべての元plot pairで`β_sim = min(b,c)/(a+min(b,c))`（a共通分類群数、b,c各plotにのみ記録された分類群数）を計算。片方のplotが未検出の場合、β_simを未定義としてsite全体STOP。地理距離は元basePlot中心の球面距離km、独立固定covariate`log(distance_km + 0.05)`。高さ差の変数は**`abs(CHMv2_40m_positive_p90_i−p90_j)/10`**、1単位が元10m差。CHMの真のnodata/0pixel分離は未解決で、positive pixel QAされたplot以外には外挿しない。

## 固定統計推定量と帰無

元siteごとの各plot pairに、記録分類群置換`y`、`h=abs(height difference)/10m`、`d=log(distance_km+0.05)`を用意。原site内の各組の`y,h,d`をそれぞれsite mean中心化し、**各siteの元plot pairに均等重み1/(そのsiteの元pair数)**を付ける。共通distance効果を線形調整した`h`の**site-equal pooled partial slope**（元β_sim単位/10mの林冠高差）だけを**主estimand**とする。site間のベースラインα差をsite interceptで除く設計で、site-year固定で1年/site。plot pairsを独立forestと数えない。

- Site-equivalent OLS nuisance sufficient sumsを用いて回帰：`β_h = (S_hy − S_hd*S_dy/S_dd) / (S_hh − S_hd²/S_dd)`、各Sは元site内でmean centered済の相関積のsite equal sum。元距離偏差が全siteで0（`S_dd=0`）、距離調整後の林冠高差の残余分散0、その他定義不能なら**SCIENTIFIC STOP**, distance controlを黙って落として有意差を出さない。
- 主方向の両側帰無は**9,999回**、各site内の**元original plotのCHM height P90ラベルだけ**をランダム並べ替え、site×yearの群集・地理位置・調査努力・元plotペアを固定。plot pairを直接shuffleしない。実現したpartial slopeの絶対値を比較しp=(1+count(|β_perm|>=|β_obs|))/10000。これは同site内でも高さが空間的に非ランダムである可能性を完全に除く方法ではない。
- 不確実性は**元NEON siteブロックbootstrap4,000** (seed=20261114)、siteを置換抽出しsource site-sufficient-statisticsを再集計、95%百分位CI。データのrankの偏り・元site内のsource taxonomic coverageを開封後に閾値で救済しない。site数**10未満**・元domain数**6未満**・有効site-year**12未満**なら、分類群の質だけでなく統計推測自体も`SCIENTIFIC_STOP_TAXON_DETECTION_SITE_SUPPORT`とする。
- 必ず元plot/siteの有効taxon単位数、siteごとの分類群ゼロ脱落、pre-outcome source三条件の採択分母、source 2019/2020内訳、源画像撮影tile windowとの重複**（plot pixel同年の証拠ではない）**、βの中央値、結果の正負、CI、pを**非有意でもそのまま保存**。元位置・個別site/plot/種名・生物valueをGitHubに出さない。

植物1m²のrecorded`taxon_id`は元targetTaxaPresent=Nのゼロsourceが一部公開派生から除かれ、同siteの真のabsenceを再構築できないため、**この主検定に混ぜない**。後で植物の結果に有意性を探して主論点へ切り替えない。後続のplant community構造との関係は**別の十分な検出モデルと事前仕様**があれば検討する。

**効果の上限**：正のβ_hでも、木本の実験的林冠改変、微気候緩衝、垂直虫相の分業、島嶼保全サービスの因果連鎖を意味しない。地理距離調整だけでは森林履歴や地表環境の共変化・採集detectabilityを完全には制御できない。負・ゼロも統計的「林冠は重要でない」の証明にはならない。旧PREDICTS/NEON生物スコア凍結、eBird/TinyFish未使用、PR #469 Draft未マージ。
