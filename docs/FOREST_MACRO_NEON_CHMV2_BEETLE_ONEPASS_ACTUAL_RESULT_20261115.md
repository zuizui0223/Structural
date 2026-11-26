# NEON 2019–2020 森林CHMv2樹冠高差と地表甲虫の空間的Simpson置換：固定済み主解析の実結果（2026-11-15監査）

## 判定：検定まで実行済み、正の傾きは有意な支持に至らず

2026-11-14の[原本GitHub Actions #43563278455](https://github.com/zuizui0223/Structural/actions/runs/43563278455)では、事前に固定した**唯一の**地表甲虫分類群Simpson空間置換×40m衛星CHMv2静的P90高差の一次探索的解析が、元source取り込み・合成既知解・源原plot同定確認・site単位ブートストラップ・plotラベル置換検定の全ステップを通過し**SUCCESS**した。結果は方向として正だが、不確実性がゼロをまたぎ、固定した両側検定も有意でない。

| 観測項目 | 実測・実計算 |
| --- | ---: |
| 生物値開封前の森林original source資格 | **26 sites、15 domains、44 eligible site×years** |
| 一森林につき2019/2020の一方だけ採用（2020優先） | **26 original site-cliques** |
| 種ランクの甲虫recorded taxon incidenceが定義できず全cliqueを除外 | **8 sites** |
| 生物学的βが定義できる最終独立NEON sites / domains | **18 sites / 10 domains** |
| 解析された元original forest plots / pair comparisons | **121 plots / 379 pairs（後者は非独立）** |
| 林冠CHMv2 P90絶対高差 **10 m** 当たり、原site等重み・距離調整済み `β_sim` 傾き | **+0.0349** |
| 元siteブロックbootstrap **4,000**回の百分位95%区間 | **[−0.0158, +0.1079]** |
| 各source site内の原plot **CHM高ラベルのみ**を9,999回置換した両側p値 | **0.1759** |
| 元site等重み平均のplot間Simpson置換 | **0.4088** |
| 元plot対プール中央値（記述的、非独立） | **0.5000** |

**実結果判定：仮説「同site・同年の森林plot間で樹冠高の差が大きいほど、地表甲虫の分類群置換が大きい」は今回は支持されない。** ただし信頼区間は中程度の正の値も負の値も含み、樹冠構造が無関係・生態学的等価・正の関係が存在しないと立証したわけではない。検定後に分類群・β指標・年・地理閾値・height集計幅を変更して正の効果を探すことはしない。

### 厳密に保存した推定対象

[生物値を開く前の単一主解析の固定仕様](FOREST_MACRO_NEON_CHMV2_2019_2020_BEETLE_SPATIAL_REPLACEMENT_PRIMARY_PRESPEC_20261114.md)に従う。2019/2020の原forest plot×year同一性、季節・元sampleID数・trap日数・plant1m²記録subplot数、元site×yearで３区画以上相互比較可能なclique、元siteで年は一つ（2020優先）、衛星元40m×40m positive-pixel P90のQAを、生物値の開封前に固定。初回開封後はunflagged ground beetleの有限正値とoriginal taxon_rank species/subspecies/varietyの元`taxon_id`だけを使用し、分類群検出ゼロのoriginal plotが一つでも含まれるsite-cliqueは全体を非定義として除外した。

各plot pairに `β_sim=min(b,c)/(a+min(b,c))`、静的`abs(CHM_p90_i−CHM_p90_j)/10m`、`log(geodesic_distance_km+0.05)`を計算。原site内の応答・林冠高差・地理距離を中心化、1site=1重みの距離偏回帰を実施。p値はplot pairを独立に並べ替えるのでなく、**各site内の元plot樹冠高ラベルのみ**を入れ替える9,999置換から算出した。幅の不確実性は元siteを再標本化する4,000ブートストラップ。379 plot pairを379独立森林とカウントしない。

## 構造測定の別の肯定結果と、その推論境界

同じNEONの**別の構造同士の測定比較**では、現地live DBH10木本P90と衛星CHMv2 40m P90のsource-site等重みSpearman順位相関は **ρ=+0.9063**（22 sites・13 domains・72 physical plots、site-bootstrap95%CI [+0.7457,+0.9658]）。現地−衛星構造の較正としては強い結果だが、**生物応答との関係の有意性を保証しない**。根拠：[独立現地-衛星比較](FOREST_MACRO_NEON_CHMV2_VST_FIELD_HEIGHT_CROSSSENSOR_ORIGINAL_RESULT_20261114.md)、[Actions #43561149201](https://github.com/zuizui0223/Structural/actions/runs/43561149201)。

CHMv2は単一静的衛星合成で、元plot別の画素取得年が確認できず、現地VST測定年と一致する保証がない。40m正方形は実際のauthor field plot polygonでもない。βとの比較は地理距離とsite効果を調整した**観測上のpartial slope**であり、forest management・微気候・垂直資源・移入供給源配置の因果効果ではない。pitfall地表甲虫であり林冠甲虫の垂直分化の試験ではない。site内の高さラベル交換可能性を空間的森林履歴が破る可能性も残る。

## 他の森林マクロ結果との関係（同じ効果量として統合しない）

- PREDICTS 39独立原研究・20か国の**改変林−参照林 vs 参照林−参照林**のSimpson検出分類群置換差は **+0.0942**（95%CI [+0.0638,+0.1253]、36/39研究正）。元study内地理距離を対応させた31研究の**事後的・探索的**感度では **+0.0847**（CI [+0.0527,+0.1166]）。これらは元森林改変との空間的関連であり、**今回の高さproxy差とは説明変数・地域・推定量が異なる**ため正負を競わせたりメタ解析平均したりしない。
- NEONの既封印の植物×甲虫時間的β共変動 `r=−0.0664, p=0.536`は不支持の別推定量で、今回の同一サイト空間ペアβの独立反証ではない。
- 2019–2023 VST元同年同季節の**10siteyear<固定最低12**、2014–2018の元VST QA 0、およびDATASAPROX `ID_condition` 高さ×処理交絡の科学的STOPを変更しない。eBird/TinyFish不使用。旧BALA・GEB凍結済み解析結果と確認用holdoutも再開封しない。

現時点の生態学的問いは「森林改変に伴う分類群入れ替わりが認められる一方、**単一の静的林冠高指標だけで局所の甲虫群集差まで説明できるのか**」。今回の１回の高さ検定では答えはまだ**未識別・不支持**。今後は新しい独立森林系で樹種構成、林冠多層性、微気候、調査努力、種同定精度を**同一site・時期**で備えるsource cohortが必要。同じNEONデータで新しい正方向のvariantを選び直してはならない。

## 実装・保存した監査証拠

- [GitHub Actions #43563278455](https://github.com/zuizui0223/Structural/actions/runs/43563278455) `one_shot_original_neon_chmv2_beetle_spatial_simpson_distance_adjusted` **SUCCESS**、biological known-truth tests **PASS**。
- aggregate-only artifact **14100848147**、GitHub保存ZIP SHA256 **`be5a36bd8b60366d6094b3b76a53525718a4d7983879200fe251b8a7226fbfc8`**。元coordinates、site plot ID、元taxon ID、個別群集、樹高pixel、bio-row数値の保存・再配布はしない。
- 元実行コード `analysis/forest_macro_global/neon_chmv2_2019_2020_beetle_spatial_beta_onepass.R`、field frame `neon_chmv2_2019_2020_forest_community_source_triads.R`、workflow `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`。
- [source-only 26site/44siteyear判定](FOREST_MACRO_NEON_CHMV2_2019_2020_FOREST_COMMUNITY_SOURCE_TRIADS_RESULT_20261114.md) と本実効果を区別。結果が非支持でも、26site source designの達成自体は元method/metadata上の確定結果。

## 2026-11-15 workflow-only 修正の記録

旧NEON `forest-macro-neon-cross-taxon-temporal.yml` と `forest-macro-datasaprox-project-table7-crosswalk.yml` はステップ名中の引用されない `:` によりGitHub Actionsにジョブ0件の即時failureを起こしていた。**ステップ名３か所を引用符で囲むだけ**の修正をdraftブランチに実施：
- NEON workflow label fix commit [`e6204b8`](https://github.com/zuizui0223/Structural/commit/e6204b8c5953c1f63e0a085175ff699f5072588b) → [run #43670406767](https://github.com/zuizui0223/Structural/actions/runs/43670406767) は正しくパースされ、元v1科学的停止の `if: false` により**意図したskipped**。生物応答を再開封していない。
- DATASAPROX workflow label fix commit [`48fa1fb`](https://github.com/zuizui0223/Structural/commit/48fa1fbfb61f2cf13ed51ca5c726a09ef23bbb80) → [run #43670406808](https://github.com/zuizui0223/Structural/actions/runs/43670406808) **SUCCESS、1実ジョブ**、Table 7 元Methods crosswalkの原本応答は未開封。aggregate artifact **14143882589** SHA256 `93d5678d23b64601bdac9859803eeead6608a2933a1d9d2f21c325289d4dcae2`。
- CIジョブ修復は**新しい生物学的肯定結果を示すものではない**。Draft PR #469 未マージ。
