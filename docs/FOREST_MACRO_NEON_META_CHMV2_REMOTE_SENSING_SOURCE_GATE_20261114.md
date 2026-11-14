# NEON森林×独立Meta/WRI林冠高CHMv2：公開タイル・画素の取得可能性を原応答未開封で監査（2026-11-14）

## 元の科学的STOPは変更しない

Structuralの森林マクロ生態学で既凍結の生物学的知見は、PREDICTS 39 original Studies／20か国の`Δβ_sim=+0.0942`（研究bootstrap95%CI +0.0638〜+0.1253、36/39正）、距離を揃えた31研究の探索的再解析`+0.0847`、NEON 7森林の植物×甲虫年次置換の相関`−0.0664,p=.536`（正の同期未支持）。これらは群集応答を新しいデータで再採点しない。

2026年公開樹木VST・甲虫・植物の同`siteID×plotID×year`を揃えたmixed-landscape forest-patch sourceでは、**22 sites／13 domains／73 DBH10cm＋生存木・元height QA plotyears**から季節・sample effort対応36plotyears、同site/yearで比較可能な**10 sites／8domains／10 siteyears・35区画対**を確保したが、元解析前固定の最低**12 siteyearsに不足**した（[成功CI #43340430135](https://github.com/zuizui0223/Structural/actions/runs/43340430135)）。これは旧VST source-onlyゲートとして**SCIENTIFIC STOPのまま維持**。2014–2018の歴史コホートは甲虫・植物730plotyears、うち674 effort-readyでも、VST公開派生の当該forest sampled+area QAに適合した初期測定が0（ただし元plot×year文脈の一致227）。旧VSTを閾値・時間の補完で「救済」しない。

## 今回の新規sourceは、同じVSTとは独立した林冠高さのリモートセンシング観測

- **Meta／World Resources Institute 2026 Canopy Height Map Version 2（CHMv2）**。DINOv3モデルを用いたVantor/Maxar系の高解像度衛星画像からの樹冠高推定。公表された数値は約1.19m native raster、Web Mercator(EPSG:3857)、zoom10の10桁quadkeyで管理されるCOGs。森林構造の連続値の別個の測定・推定チャネルとして利用可能。正式版[CC-BY-4.0 AWS Open Data](https://registry.opendata.aws/dataforgood-fb-forestsv2/)の公開S3`s3://dataforgood-fb-data/forests/v2/global/dinov3_global_chm_v2_ml3/chm/`および[公開CORS付きSource Cooperativeミラー](https://source.coop/tge-labs/meta-chm-v2/)をsourceとする。認証必須のNEON公式生物データAPIを回避したものではない。
- 著者・公開データのsource画像の**約80%が2018–2020年**とされるだけで、2020年に統一撮影した、特定plotが2019年に撮影された、という意味ではない。CHMv2のモデル・公開時点は2026年でも、元撮影年月日は異なる。従って**CHMv2を2019–2023の年別樹高時系列やNEON AOP LiDARの真値と同一視しない**。同NEON site/plotの森林管理変化、自然攪乱が挟まれば、古い画像に依存したCHMは群集の変動に対応しない可能性がある。
- 別途公開のSource Cooperativeには原タイルの`tiles.parquet`、撮影期間サマリー`acq_dates.parquet`、STAC`items.parquet`がある。元sourceは2026 Meta CHMv2の**タイルカバレッジと撮影日情報**の独立検査に使う。個別のplot撮影日の等価性はタイルwindowの日付だけでは証明できない。
- 元NEONは`neonDivData`0.3.1の`neon_location`（作者が配布する`siteID, plotID, location_id, latitude, longitude`）を使用し、元サイト×plotの`basePlot.all`基準点を優先。基準点のsource不在の場合、座標が50m以内に収まる場合に限り複数位置の中央値を**tile coverageの探索的近似**とし、元plotの確定geometryとは呼ばない。異なる元投影系や緯度範囲外を黙って丸めない。
- 生物responseを含む元`neonDivData::data_beetle/data_plant`からはsourceメタデータ列`siteID,plotID,observation_datetime,nlcdClass,trapConditionFlag,trappingDays,unique_sample_id,trapID,sample_area_m2`だけを選択。以前の2019–2023別母集団の**35 original NEON sites・952森林plot×years**に一致しないなら樹冠タイルの照合前にSTOP。元`taxon_id`,`taxon_name`,`value`,旧β、原木本`height`は一切読まない。

## 実際のデータ取得手順と解釈範囲

1. 元NEON`neon_location`のplot座標が何plot／siteに存在するか、basePlot中心が存在するか、元plot内位置が分散するかを元site/plot匿名集計で証明する。元座標・site ID・plot ID・quadkeyをrunner-private CSVで一時保存し、GitHub artifactには出さない。
2. 元座標からWeb Mercator zoom10 quadkeyを計算して、公開S3とCORS mirrorの**元COGファイルにHEAD 200が実際に返るか**を確認する。元GeoTIFFの数値・樹高値は本stageでは読まない。HTTP 403、ネットワーク不通やsource障害は「forest height=0」に変換せず`SOURCE_UNAVAILABLE_OR_UNVERIFIED`と明示。
3. 公開`acq_dates.parquet`のHTTP可用性・列スキーマ・サンプル内のtile key対応を別検査する。元撮影日が不明なplotは同期する林冠高と見なさない。タイルへのHEAD 200も、NEON原plot中心の画素が有効であることや全plotの樹冠高（0m vs nodata）を保証しない。
4. **第2段生物モデルの許可条件はこの段階で一切認定しない。** 公開CHMタイルが少なくとも6 independent NEON sitesを覆い、原plot中心のsource品質と元撮影時期が適格と確認できた場合にのみ、**別事前仕様の空間的な林冠構造proxyと群集組成の探索的比較**を新設する。既存VSTの10/12 source STOPに新たなCHM siteyearを単純加算しない。2020〜2023毎年の樹高変動・気温緩衝・生態系サービス連鎖や因果的なforest modificationの影響として報告しない。

実装`analysis/forest_macro_global/neon_meta_chmv2_forest_plot_source_gate.R`、`analysis/forest_macro_global/neon_meta_chmv2_public_tile_probe.py`と新規GitHub Actions（元NEON raw座標・taxonは非公開）。source version、仮説と調査単位は固定し、sourceの品質を見てから生物学的応答を追加得点する際には必ず`separate exploratory, non-independent NEON population`と明示。PR #469 Draft未マージ。eBird、TinyFish不使用。
