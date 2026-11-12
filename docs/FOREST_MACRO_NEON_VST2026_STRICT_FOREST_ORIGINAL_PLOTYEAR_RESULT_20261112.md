# NEON森林8サイト：公式RELEASE-2026の実測植生構造との原区画×年クロスウォーク結果（2026-11-12）

## 実行結果と判定

**原本source-only接続の実測成功**：公開されている独立VST2026派生リポ `tgilbert14/NEON-Vegetation-Structure-Explorer`、固定commit `3391e702e7be80a3f049c905782661f043be8db8` から、neonDivData 0.3.1の原植物・甲虫サンプルに対応する**8/8 strict NLCD forest NEON sites**の公開 `data/sites/<SITE>.rds` を取得。元RDS `list(trees,plots,opportunity_source,meta,contract)` と元契約 `NEON-VST-DP1.10098.001-v2` を確認し、元の `sampled_with_records / sampled_absence / held_*` を区別した。

- 元植物・甲虫2019–2023のsite×plot×yearの単純共在＋元beetle正常トラップ正努力・植物1m²に合致した **348候補plot×year**。これは元source-only季節±30日を含む厳密コホート339より広い**元のメタデータ機会母数**であり、339/348をすべて同じ年の有効な生物統計と同一視しない。
- VST同year・同original plotIDに対応するサポート済みtree source sampling opportunityは **26 original plot×year**、**7森林sites／7 NEON domains**。元8森林すべて公開VST bundle自体は存在するが、1サイトはサポートある同年同区画の結合なし。
- 26組は全て `sampled_with_records` を含む元VST source opportunity、元高さ列 `height` の存在は8/8 bundleで確認。ただし**実際の樹高値の有効性や分布は未読**。木本構造・甲虫・植物の同年同区画での気温・VPDなどは別原本を取得していない。
- **事前に凍結した次段の最小支持：6 sites、4 domains、40 original plot×year**のうちsite/domainは満たすが、plot×yearは**26 < 40**。よって厳格な森林一様サイトコホートに関する構造→群集効果は **SCIENTIFIC_STOP_INSUFFICIENT_CONTEMPORANEOUS_PLOTYEAR_LINKAGE** とする。**効果量・有意検定を実行していない**。
- 同じsiteの別区画、別年の木本測定を同年としてすり替えず、`held_sampling_impractical`, `held_missing_area`, `held_identity_conflict`, `held_opportunity_source_missing`を数値ゼロとして扱わない。VST `sampled_absence`に林冠高を0 mとして割り当てない。

### Provenance

- 元公開植生構造プロダクト [NEON `DP1.10098.001`, RELEASE-2026](https://data.neonscience.org/data-products/DP1.10098.001/RELEASE-2026)、DOI 10.48443/pypa-qf12。プロトコル上、Distributed plotsは原則5年周期、Tower plotsは一部年次測定であり、2019–2023の毎年の生物群集と同年に一致するとは限らない。
- 派生VST公開データ [NEON Vegetation Structure Explorer](https://github.com/tgilbert14/NEON-Vegetation-Structure-Explorer) commit 3391e702e7be80a3f049c905782661f043be8db8、元sourceの契約 `NEON-VST-DP1.10098.001-v2`。一次NEON公式の認証が必要なAPIを回避して取得したデータではなく、別途一般公開された派生bundle。
- 甲虫・植物公開派生 `neonDivData` version0.3.1、公式site context 2026-08-05 SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`。
- 原本GitHub CI [#43238833529](https://github.com/zuizui0223/Structural/actions/runs/43238833529) **SUCCESS**、匿名集計artifact **13953957759** SHA256 **c84a2ed0361f732187666bd0281956c97e8d2e1e6be6004d17e6d9cd70bf736e**。著者元RDS、元site/plot/date/trees、木本height、元生物種名をGitHub/Artifactに再配布せず。
- コード `analysis/forest_macro_global/neon_public_vst42_original_plotyear_join.R`、source-only workflow `.github/workflows/forest-macro-neon-vst2026-public-structure-join.yml`。

## 次の標本母集団（別設計、未スコア）

今回の「サイト全体がstrict NLCD forestしか含まない森林8サイト」は、同年同plot×年の木本構造26しか残らない。しかしNEONの全47 beetle/plant observational sitesには**サイト全体の主要景観が森林でなくても、原plotの`nlcdClass`がforestである区画**がありうる。次に、これらを「mixed-landscape forest patches」という**別個のフィールド母集団**としてsource-only適格性評価する意義がある。

その別設計でも、各元plotの3データ（甲虫/植物/VST）の森林ラベル・元plotID×same year・VST対応area/tree channel supportを必須化する。追加の元生物応答を見て支持に有利なforest定義やsampling lagを変更せず、**source-onlyで6以上のsites・4以上domains・40以上plot×year**（mixed landscape母集団の独立性はsite単位）の支持がなければ林冠効果の生物統計へ進まない。多域森林の測定として十分でも、後からの新生物効果がPREDICTS既有意の「独立確認」になるわけではない。

他の凍結済生物結果（PREDICTS 39研究+0.0942、距離対応31研究+0.0847、NEON 7サイト年次同期−0.0664 p=.536、THERA/BALA/GEB）は一切再採点しない。eBird/TinyFish不使用。Structural PR #469はDraft未マージ。
