# NEONの未利用2014–2018年：独立した歴史的観測コホートのSource-only登録（2026-11-14）

## 対象と新設理由

公式・公開派生`neonDivData 0.3.1`が保持する地表甲虫 `DP1.10022.001` は2013-07-02〜2023-12-20、植物`DP1.10058.001`は2013-06-24〜2024-11-21までの観測であり、別の木本構造RELEASE-2026 `DP1.10098.001` は2014-01〜2024-12で42 sitesである。したがって2024年を足しても公開版甲虫の同年記録は得られないが、**従来の森林2019–2023 cohortで未使用の2014–2018年を新しいsource-only cohortとして検査できる**。外部根拠：[neonDivData公開README](https://github.com/daijiang/neonDivData)、[NEON VST RELEASE-2026](https://data.neonscience.org/data-products/DP1.10098.001/RELEASE-2026)。

2019–2023の従来の混在景観forest patchesについて、真正な有効VST高さ73 plot×yearsから、植物/甲虫の調査時期・努力一致を確保したのは36 plot×years、そのうち**10独立forest sites・8 domains・10 site×years・35非独立plot pairs**があり、固定した最低12 site×yearsに足らず、分類群を開く前にSCIENTIFIC STOPで封印した。[訂正済み原本CI #43340430135](https://github.com/zuizui0223/Structural/actions/runs/43340430135)。元「0 plot pairs」は項目名のバグとして訂正済み。

**本2014–2018コホートは過去の2019–2023 cohortのn=12を事後的に満たしたことにしない。** 別時代の歴史的観測を、新たなsampling-method QAのSource-only候補として評価する。以前にNEON 2019–23同期の生物結果`r=-0.0664,p=.536`を見た後に導入するため、後続の生物効果はどのみち探索的で独立検証とは呼べない。

## Source-only不変ルール（生物taxon値を一切開かずに計数）

1. 公開`neonDivData 0.3.1`の**2014-01-01から2018-12-31**だけ。甲虫、植物の元`siteID×plotID×year`が一致し、**両資料が明示的に`nlcdClass` forest（deciduousForest / evergreenForest / mixedForest）**のoriginal plotsに限定する。サイト全域の主要景観がforestかどうかは要求しないmixed-landscape forest patchesという**独立観測母集団**に限定する。
2. 最初のvalid 1m²植物`sample_area_m2=1`、`unique_sample_id`、`subplotID`の記録された調査日を固定し、植物記録はその日±7d。甲虫は正常（`trapConditionFlag`空）、`trappingDays>0`、`unique_sample_id`と`trapID`が揃い、植物日±30dのsource samplesだけを使う。**元分類群・捕獲数・taxon名は開かない**。最低4甲虫sampleIDと4植物記録済みsubplots。
3. 公開VST`RELEASE-2026`のsite別`list(trees,plots,opportunity_source,meta,contract)`、契約`NEON-VST-DP1.10098.001-v2`、固定元GitHub commit `3391e702e7be80a3f049c905782661f043be8db8`。元VST forest`nlcdClass`、`tree_support=sampled_with_records`、`area_trees>0`、元event dateが植物最初の調査日±90d、同元plot×eventの生きたsingle/multi bole trees・DBH≥10cm・source QC pass・有効高さを持つ**異なる個体3以上**。ゼロ記録や欠損/heldを有効樹高に変換しない。樹高の数値はpresence/quality条件の判定に限り効果へ回帰しない。
4. 同じ元site/yearに2以上の有効forest plotが残り、そのplot対で甲虫`trappingDays`総和比、植物recorded1m²subplots数比がそれぞれ0.5〜2.0、最初の植物調査日の差≤30日。サイト年と区画対を別に数える。
5. 最低適格性を**10独立NEON sites、6 ecoclimatic domains、12同site×yearに2plot以上の資格のある組**と固定。未達なら`SCIENTIFIC_STOP_HISTORICAL_SOURCE_PLOT_SEASON_EFFORT_INSUFFICIENT`、生物taxon/plant cover/pitfall abundanceを一切開かない。適格であってもこのSource-onlyゲートは生物効果の証明ではない。
6. Source-onlyの欠損項目、元event/plant ID矛盾、2014–2018のVST対応欠落、甲虫歴史的調査法の変更、木本年と生物年のずれは除外数に明記する。現行/既存NEONのn=10を救済するために期間幅、樹高本数、努力閾値を後から変更しない。

## 終了条件・運用

本Source-onlyコホートは最低採集適格性を調べるところまで実装する。**旧PREDICTS 39研究`+0.0942`・距離対応31研究`+0.0847`・NEON 7森林年次同期`-0.0664,p=.536`は自動再採点済み停止のまま**。BALA/GEB/THERAも触れない。元観測siteID、plotID、木本individual ID、学名、taxon/abundance、生物値、座標は GitHubコミットや公開artifactに出さず、厳格な匿名aggregate-only数値だけを残す。eBird・TinyFish不使用、Draft PR #469未マージ。
