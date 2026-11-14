# NEON 2014–2018森林パッチ：甲虫・植物・VST木本構造の元資料同年対応と科学的STOP（2026-11-14）

## 最終判定（元分類群・生態効果を開かずに取得した実測）

新しい独立**観測期間**2014–2018年を、2019–2023既凍結のNEON source cohortと**別**に検査した。新しい甲虫・植物の観測地点群は33 original NEON sitesだが、それを33の新しい独立森林研究／出版済PREDICTS39原研究の独立再現と呼ぶことはできない。同じNEON観測ネットワークの歴史期だからである。

Source-only原本監査の出典：[2026-11-14 GitHub Actions run #43459879574](https://github.com/zuizui0223/Structural/actions/runs/43459879574) **SUCCESS**、別の同一修正版原本run #43459879263も成功。匿名source-only artifact **14054839489** digest **sha256:cb534b545457d6ed10ce0d7a85cb16cbff23e6150cc00bf8b87a547e915db5ee**（run #43459879574）。実装 `analysis/forest_macro_global/neon_vst2026_historical_2014_2018_source_gate.R`、配布源は`neonDivData 0.3.1`と公開VST42-site source commit `3391e702e7be80a3f049c905782661f043be8db8`、元VST契約 `NEON-VST-DP1.10098.001-v2`。公式NEON 2026-08-05 field-sites 81 sites CSV SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`。

| Source-only測定単位／脱落ステージ | 実際の元資料数 |
| --- | ---: |
| 甲虫・植物が同forest original plotID×yearで観測されるoriginal NEON sites | **33** |
| 両分類群の元森林plot×year、正常甲虫trap positive effortと植物1m² sourceあり | **730** |
| うち植物最初の調査日±7d・甲虫±30d、甲虫sampleID≥4・植物記録subplotID≥4 | **674** |
| 両群の最小標本不足で脱落 | 42 |
| 調査季節に甲虫・植物の両sourceがないため脱落 | 14 |
| 元VSTの2014–2018 plot×event context rows（33 VSTサイト原本） | **2,780** |
| うち元VST`nlcdClass`森林plot context rows | **1,889** |
| 同VST森林plotの一意な年次区画キー | **1,878** |
| **甲虫・植物730原forest plot×yearと同じ元VST森林plot×yearが存在** | **227** |
| **VST`sampled_with_records`かつ`area_trees>0`、元森林plot・2014–2018年という作者QAの全条件を満たすforest plot event rows** | **0** |
| 上記を通過したVST forest plot×year | **0** |
| 有効樹高3別個体以上・植物調査とVST±90dの最終結合plot×year | **0** |
| 努力量／季節を揃えた同site/yearの森林plot対 | **0** |

植物・甲虫の**2024**同時観測については、公開`neonDivData 0.3.1`の甲虫が2023-12で終了するため2024は本研究の三者共通観測年にならない（植物は2024年、VSTも2024年まである）。2014–2018年の甲虫/植物源のoriginal plot×yearの年別数は**2014:67、2015:128、2016:150、2017:178、2018:207**。

### 0という数値の意味

**重要：2014–2018に樹木が存在しなかった、測定がなかった、林冠構造と群集間に関係がなかったという生物学的なゼロではない。** 元VST原本には早期の測定機会forest contextsが1,889行あり、甲虫・植物と一致する元区画年も227存在する。最終の構造値に使える支持が0なのは、公開VST `plots`において同じ年・forest/positive tree area/`sampled_with_records`の品質**組合せが全く通過しない**というsource data-quality上の科学的STOPである。なお、現在の集計だけでは「正のsource areaだけがない」のか「元`tree_support`がheld/unsupportedのため」なのかを**別々には断定していない**。両者を欠測のない0m樹高や`sampled_absence`へ置換して救済することは不可。元VST作者データ辞書・早期`vst_perplotperyear`への供給経路が原因究明の焦点になる。

NEON sampling protocolは本来「甲虫はDistributed base plotsの部分集合、植物は原base plots、VST Distributedは概ね5年周期」であり、同じ年を条件にすると欠測・サンプリングの段階的展開により多数が落ちうる。[NEON site-level sampling design](https://www.neonscience.org/data-samples/data-collection/observational-sampling/site-level-sampling-design)。さらに甲虫原プロトコルは2014–2017の4 pitfall traps/plotを2018年に3へ変更したため、異なる年のraw sample countsを同一検出努力と扱えない。[NEON ground beetle sampling change](https://projects.ecoforecast.org/neon4cast-docs/Beetles.html)。

### 変更していない科学的結論

**2019–2023の原forest patch source**は、22 original sites・13 domains・73 live DBH≥10cm高さ有効plotyearsから**10 sites・8 domains・10 siteyears・35 source-comparable plot pairs**（3source日差・努力一致）を得たが、先に固定した最小12 siteyearsに未達で**Scientific STOP**。この2014–2018コホートのzero-source-valid woodyを2019–2023へ自動加算し、旧比較規則を事後救済しない。過去の0 plot pairsというプログラムの人工物は修正済みであり、今回の0 woody source-quality eventは**別データ期間・別のsource field gate**である。

PREDICTS主効果 **+0.0942**（Study95%CI [0.0638,0.1253]、36/39原研究正）、距離対応の探索的二次 **+0.0847**（31 studies）、NEON植物甲虫の年次同期 **r=−0.0664、p=.536** は、元の異なるestimandとして一切再採点・変更なし。原species/taxon/name/abundance/plant cover、元heightの連続値、NEON原siteID/plotID/tree IDsを原Gitやartifactへ出さず、eBird/TinyFish不使用。

## 次に判定すべき物理的データ不足

現段階で過去の調査年を増やしても、**現行の公開VST派生アーカイブの元site/year/forestの作者QAサポートは増えない**。次のデータ取得源は①`vst_perplotperyear`の当時の元測定面積と作者の`tree_support`欠測の意味を、原NEON sourceから確認する、②新しい別資料として同時点の現地林冠高/LiDARが原森林plotに割り当てられるかを独立に調べる、のいずれかである。元公開派生データのsource-quality欠落を任意の0や補完で「修正」しない。

**状態：独立2014–2018 Source-only cohort 実測完了、SCIENTIFIC_STOP_HISTORICAL_SOURCE_PLOT_SEASON_EFFORT_INSUFFICIENT。** 植生構造→生物群集の因果・相関はこの観測で**未検証**。Draft PR #469未マージ。
