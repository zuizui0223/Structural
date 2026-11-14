# NEON原forest区画×Meta/WRI CHMv2：40 m中心窓の公開画素・撮影時期の品質監査（2026-11-14、画素未読時に固定）

## 成果と研究上の境界

前段原source CI [#43539279481](https://github.com/zuizui0223/Structural/actions/runs/43539279481) SUCCESSで、`neonDivData 0.3.1`の2019–2023年に森林元plotで甲虫と植物双方に正常採集機会がある**35 independent NEON sites・17 domains・237 original field plots／952 plot×years**全件について、元`neon_location`作者の`.basePlot.div`・`.basePlot.brd`等のoriginal plot centresと、公開Meta/WRI CHMv2 v2 **39タイル**が全て一致した。公開ファイル39件はHTTP HEAD 200、39件の`acq_dates.parquet` source metadataも存在。**これは画素の林冠高が実在することでも、2019〜2023年の年次林冠実測でもない**。以前の初回317区画年という暫定値は、元basePlotを誤って`.basePlot.all`と想定したコードを修正した結果、完全に**952区画年へ置換**した。

## 本stageで初めて読む値、元の母集団、固定QA

1. 元データは[Meta/WRI CHMv2 2026](https://registry.opendata.aws/dataforgood-fb-forestsv2/)、source mirror [Taylor Geospatial Source Cooperative](https://source.coop/tge-labs/meta-chm-v2/)。1.19m級Web Mercator COG、2026年MLモデル、元衛星画像は約80%が2018–2020年。NEON公式の2019–2023同年LiDARではない。公開mirrored元sourceの`acq_dates.parquet`には`quadkey,acq_start,acq_end,acq_n`があることを原本で確認済。
2. 元NEON sourceは前段952 original plot×yearsの**237異なるfield plot**（位置が元`basePlot`で同定済）を**一度ずつ**CHMで測る。複数年の同じplotに同じ静的CHM画素を複製して、952独立構造測定と呼ばない。
3. 各元plot center（WGS84）をCHMv2元EPSG:3857へ投影し、その点を中心とした**40m×40mの正方形窓**を固定して元COGから取得する。これは原NEON base plotの正確な境界polygonと一致することを保証しない**測定prox(y)窓**である。林冠の上下層や微気候を実測しているわけではない。複数のquadkeyまたぎ窓、元COGの範囲外、pixel取得失敗はsource不可とする（境界をまたいだ隣のtileへ自動補完しない）。
4. CHMv2はuint8メートルで、**0は本当に林冠高0mとnodataの両方の意味**を持ちうる。そこで最初に`positive_pixels / all_window_pixels`をsource index別に数え、0画素を真の森林消失/草地/陰性捕獲として数えない。著者作成の有効なnodata maskがない限り、`>0`の画素だけに限ったp90 heightを**source-quality descriptives**として表示。元plotに少なくとも**25正の画素**、窓の正画素率が**20%以上**ある場合を本stageのsource-positive eligible plotと固定し、10%、50%の別閾値は感度として**数を示すだけ**。この閾値によるサンプルの地理的偏りを別途明記し、効果に有利な窓・閾値を事後変更しない。
5. 39 quadkeyの元`acq_dates.parquet`で取得撮影日の**タイルレベル`acq_start/end` window**を読み、sourceの元撮影日が2019–2020を含むタイルとそうでないタイルを匿名計数する。タイル内でも使用画像の撮影日はpixelごとに異なる可能性があり、元plotに該当する撮影日、同月同年の森林状態としては認定しない。タイムラグの有無をsource識別子抜きの集計で可視化する。
6. GitHub ActionsでCHMv2 COGを**HTTP Range**で中心窓からだけ読み込み、39枚を全てダウンロードすることはしない。元forest site/plot/coord, tile IDs, pixel arrays, source species counts/TaxonID、旧VST`height`、元群集の生物応答はGit/公開artifactへ一切出さない。各元siteに何plotがQA通過し、いくつのサイト/ドメインがCHM実画素を持つかを匿名aggregateで保存する。

## このstageの停止条件

- source 952 original plot×years、35 sites、237 distinct plots、39 publicly available zoom10 CHM tiles、39 tile date-window indexに一致しなければ原因を監査して**原結果と混ぜない**。
- raster pixel read/affine coordinate transform/HTTP 200が失敗する場合、源がない・ダウンロードできないという**data-source status**であり、有効高さが0mと偽らない。
- **少なくとも6独立元NEON sitesと40元field plots**でCHMのpositive 40m窓が測れなければ、元木本実測の代替的な探索的構造covariateとして生物応答を開く資格なし。ただし通過しても年次plot×year同時点の証明はないため、最終段は**CHMv2 source scene date（画素レベルでなくtile window）とNEONの2000年代以降の土地利用・攪乱、元測定フットプリントを別の方法で検証**して初めて別の探索的な群集組成比較を提案する。既存VSTの12 siteyear STOPは不変。
- データ接続は独立に公開されたCHMラスタの新しい**構造説明変数**だけで、NEONの生物応答の独立再観測・PREDICTSの独立確認でもない。PREDICTS+0.0942、距離対応+0.0847、NEON年次−0.0664(p=.536)を再採点しない。eBird/TinyFish不使用、PR #469 Draft・未マージ。

実装`analysis/forest_macro_global/neon_meta_chmv2_plot40m_pixel_source_quality.py`、既存の元位置抽出RとともにR+Python Github Actionsで1回だけsource-qualityを監査する。
