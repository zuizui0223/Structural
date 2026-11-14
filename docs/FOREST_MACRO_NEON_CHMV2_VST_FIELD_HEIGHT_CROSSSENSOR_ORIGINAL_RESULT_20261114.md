# NEON 22森林・13domains：独立衛星CHMv2と現地VST樹高の空間的整合性（2026-11-14）

## 実行済みの肯定的な原本の別測定比較

Meta/WRI 2026公開CHMv2（DINOv3衛星画像由来の1m級COG）と、別系統の公開NEON VST `DP1.10098.001 RELEASE-2026`（元生木DBH≥10cm高さ）を**同じ元site×plotID**で比較した。

- **原本成功CI**： [GitHub Actions #43561149201](https://github.com/zuizui0223/Structural/actions/runs/43561149201)、両ソースの合成既知解と原本計算SUCCESS。公開匿名集計artifact **14100297592**、ZIP digest **sha256:7ac4a776e59ac73a3dcc80a7bcaf5478cd0e0278703e9c3f63572e778fb2f480**。原source位置、元VST生の木個体・樹高値、COG画素値、学名・生物個体数をGitHubやartifactに出さない。
- 前に確定した現地VSTの**73 plot×years、22 original NEON sites、13 domains**を、元`trees`の著者contract、`sampled_with_records`、`area_trees>0`、forest NLCD、source`size_height_ok`、元`live`/plantStatus、DBH≥10cm、single/multi bole tree、生存かつ有限正height、元`individualID`単位に再現。原同一年別の73は**72独立site×plotID**だった（1区画は複数年）。元2020年から最も近い有効VST年を先に選ぶ固定ルール、同距離は古い年を優先し、Satellite値による採択はしていない。
- 選択された独立72 plotsを、固定済CHMv2 **40m×40m original NEON`.basePlot.div/.brd`中心**で実ラスタ読取りしたところ**72/72が、正画素25以上かつ被覆率20%以上を通過**。**22 source sites・13 domains**がそのまま残った。対象CHM pixelと元VST original field plotの面積・測定時期は同一ではない。
- **主推定量**：元各siteでplot別の現地VST live DBH10個体height P90とCHMv2の正画素P90をそれぞれsite中央値とし、**22元site等重みでSpearman順位相関 `ρ=+0.9063148569`**。事前固定のsite単位4000 bootstrap百分位95%CI **[+0.74571535,+0.96584126]**。NEON plot年72を独立森林72と数えない。
- **元plotの高さ比較**：VST field P90中央値**22.48m**、CHMv2 40m positive-pixel P90中央値**20.5m**、衛星−現地の差の中央値**−2.77m**、絶対差中央値**3.57m**。plot別絶対誤差をsite中央値にし22site等重みで平均すると**3.3918m**。16 source sitesに2以上のmatched原plotがあり、site中心化したplotレベルのPearsonは**+0.6726（記述的のみ、確認検定は未実施）**。
- VST原field survey year内訳（73plotyears）：**2019:0、2020:17、2021:17、2022:13、2023:26**。同site×plotで1年だけを固定選択後72plotsは2020:17、2021:17、2022:13、2023:25。CHMv2の**tile-level`acq_start/end`が選択VST調査年と重なるのは8/72plots、2sites**だけ。元source image yearがplot-levelに厳密に一致したと主張する根拠はない。
- 著者release・固定ソース：Meta/WRI CHMv2 public S3 `dataforgood-fb-data/forests/v2/global/dinov3_global_chm_v2_ml3`、[Source Cooperative](https://source.coop/tge-labs/meta-chm-v2/)、別原本VSTの [NEON Vegetation Structure Explorer](https://github.com/tgilbert14/NEON-Vegetation-Structure-Explorer)固定commit `3391e702e7be80a3f049c905782661f043be8db8`、公式NEON sites2026-08-05、`neonDivData 0.3.1`はサイト/区画の**空間identityと採集source metadataのみ**に使用。応答先の甲虫/植物 taxon/valueは一切未読。

## 正の結果が示すことと示さないこと

**支持する限定的な結論**：複数のNEON生態気候領域にまたがる現地森林sitesで、独立の静的衛星CHMが現地VSTで測定された大きな**site間の樹木高順位**をかなりよく再現する。森林間で相対的に高い林冠と低い林冠を粗く区別する**静的な構造proxyの資格**が得られた。構造データの元サイトが一地域限定（ドイツ2region・ベルギー1forest等）の研究より広いが、**北米NEON 22sites**であり全球全バイオーム検証でもない。

**支持できない結論**：CHMv2画素が現地VSTと同じ日に取得されたこと。VSTの実測木本1株と40m正方形（1600m²）の衛星樹冠高pixelの完全一致（現地木本original`area_trees`の面積・個体発見努力とは別）。CHMv2の0 pixelにおける樹木ゼロ（source nodataとの識別が必要）。2019–2023年の毎年の林冠高変動。衛星の樹冠高が正確な真値（中央値−2.77mの系統差がある）、あるいはplot-levelに誤差がないこと。衛星画像には時点の偏りがあり、古い林冠高の観測が2023年の現地森林管理や攪乱と一致するとは限らない。

**生物学的効果は未検定**：これでPREDICTSの森林改変×分類群置換`Δβ_sim=+0.0942`と、31研究距離対応`+0.0847`、NEON植物×甲虫年次同期`R=-0.0664,p=.536`に「林冠高が原因」と追加解釈するのは誤り。元2019–2023 VST同年同時点・採集努力条件の**10siteyears<事前閾値12**による科学的STOP、2014–2018のsource VST QA 0のSTOPは継続。**今回の強い`ρ`は現地樹高×衛星樹高という2つの構造測定だけを比べた肯定結果**であり、別生物標本による新しい生態法則の再現ではない。

## 次の実行済み解析と未解決の境界

実装コード：`analysis/forest_macro_global/neon_chmv2_vst_field_height_source.R`と`analysis/forest_macro_global/neon_chmv2_vst_crosssensor_height_check.py`、GitHub Actions `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`。Source-only spec [FOREST_MACRO_NEON_META_CHMV2_VST_FIELD_HEIGHT_CROSSSENSOR_PRESPEC_20261114.md](FOREST_MACRO_NEON_META_CHMV2_VST_FIELD_HEIGHT_CROSSSENSOR_PRESPEC_20261114.md) に書いた閾値（最低10sites・25 plots・6 domains）、原区画1回、site等重み・4000 site bootstrapを事前に固定して実行。CHMv2全237plotの画素QAの別実測[成功CI #43540584860](https://github.com/zuizui0223/Structural/actions/runs/43540584860)では232 QA+ plots・34sites/17domainsで、今回の72 field-matched sitesは全部含まれていた。

次の生物学的問いを進める場合は、新しく**単一の年代に限定したNEON forest-patch原source採集設計と、site内森林区画間のCHM構造差と甲虫/植物の分類群組成差**を、種群を再開封する**前に**別途登録し、採集の品質・地理距離・調査努力をsource-onlyで確定する。その際2026 CHMv2は静的なproxyとして使い、同年の測定値、温度緩衝、垂直階層、森林改変の因果的メカニズムとは呼ばない。eBird/TinyFish不使用、PR #469 Draft未マージ。
