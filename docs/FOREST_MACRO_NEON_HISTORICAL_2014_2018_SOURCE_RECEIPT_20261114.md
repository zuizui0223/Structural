# NEON未利用2014–2018歴史コホート：植物・地表甲虫の原区画サポート実測（2026-11-14）

## 完了判定：VST早期森林測定機会は実在、作者の採集面積・tree support QAが同時に通過した区画年は0

修正版の同年同区画VST原本診断が実際に完了した。[成功CI #43459879574](https://github.com/zuizui0223/Structural/actions/runs/43459879574)では、初期VST原本の森林測定機会は1,889行、甲虫・植物sourceと同じ森林plot×yearは**227区画年**存在した。しかし元`tree_support=sampled_with_records`・`area_trees>0`・同year森林plotのQA条件を同時に満たすVSTイベントは**0行**。したがって甲虫・植物+樹高の原データの探索的生物効果は実行していない。**これは測定がなかったという生態学的な結論ではなく、公開二次VST原本のサポート不足による科学的STOP。** 同じ現場で森林の木が存在しなかったという意味ではない。

完全なsource内訳、既存結果を変更していない境界：[2014–2018 VST source attrition最終報告](FOREST_MACRO_NEON_HISTORICAL_2014_2018_VST_ORIGINAL_QA_ATTRITION_RESULT_20261114.md)。以下の「元VSTとの結合が未確認」は**旧初回実行中の経過記録**として残し、最終判定には用いない。

## 実行済みの新しいoriginal-source metadata cohort

NEONで樹木構造と生物群集を同年同区画で比較できるかについて、旧2019–2023 cohortは**10 original forest sites、8 domains、10 site×years、35 plot pairs**が方法・季節に比較可能だったが、解析前固定の12 site×yearsに満たずSource-only Scientific STOPとして固定済み。これを事後的に救済せず、**未利用の2014–2018年**を別の観測期間として登録した。

公開NEON派生`neonDivData` 0.3.1で甲虫は2013-07-02〜2023-12-20、植物は2013-06-24〜2024-11-21、公開VST木本RELEASE-2026は2014〜2024という共通収録時期。2024年は公開派生甲虫が未収録であり、新しい生物多様性の同年確認には使わない。[公開NEON 2026木本Source](https://data.neonscience.org/data-products/DP1.10098.001/RELEASE-2026)、[neonDivData原著者のデータ一覧](https://github.com/daijiang/neonDivData)。

**公開派生の実データを原本CIで取得し、生物値を開かず確認した2014–2018年の数**：

| original source grain | 観測 |
| --- | ---: |
| 地表甲虫・植物の双方が元`nlcdClass`森林区画に観測される元NEON sites | **33** |
| 元`siteID×plotID×year`で双方の森林分類と最小正努力を持つ観測機会 | **730 plot×years** |
| 植物の初回1m²調査日±7d・甲虫±30d・双方記録済みsample/subplot4以上を満たす | **674 plot×years** |

採集努力の類別に応じて厳格にフィルタし、植物1m²のtargetTaxaPresent=Nゼロ記録が公開派生から削除済みである点を維持。元site/plot/samples、甲虫taxon・学名・捕獲数、植物生物応答値は一切読み込まず、公開集計にも書き出さない。元NEON VSTの真正有効heightとはまだ結合できておらず、**33sites・674plot×yearsを独立した森林構造のデータ数として扱ってはならない**。

- 出典CI：[GitHub Actions run #43457815687](https://github.com/zuizui0223/Structural/actions/runs/43457815687) のSource-only候補抽出ステップで実測。同CIの後続はRの複数行`else`構文エラーで終了、**樹木構造との3資料の結合結果はまだない**。
- 構文を修正したsource-only解析コード：`analysis/forest_macro_global/neon_vst2026_historical_2014_2018_source_gate.R`。原本source固定・合成既知解・VSTの`sampled_with_records`・forest区画・3本以上の別個体有効樹高・樹木元event±90d・source同年サイト内2区画努力量を同条件で検査する。
- 条件は生物値未開封の段階で[2014–2018独立source-only仕様](FOREST_MACRO_NEON_HISTORICAL_2014_2018_SOURCE_ONLY_PRESPEC_20261114.md)に固定。最低10独立site、6 domains、12 site×yearsの条件を変更しない。

今後の数値は修正後のGitHub Actionsにより木本VST sourceと照合したのち、当該文書または別結果レポートに更新する。**失敗は「樹木構造の原本結合未確認」であって生態学的な効果ゼロではない。**

PREDICTS+0.0942と距離感度+0.0847、NEON年次の−0.0664 p=.536、旧2019–23のn=10 Source STOPは凍結維持。BALA、GEB、THERAを変更せず、eBird・TinyFish使用なし。PR #469はDraft未マージ。
