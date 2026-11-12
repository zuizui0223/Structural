# 森林構造 × 微気候 × 群集 — 独立データ取得・追加検証の現状（2026-11-12）

## NEON source-onlyゲート通過から一度限りの生物解析まで（本日の確定結果）

公開派生`neonDivData` 0.3.1と固定NEON公式森林メタデータを用い、8森林・7生態気候domains・39/40適格site-years・339採集条件一致plot-years・81反復元plot・242同一区画の連続年比較可能性を確認した。季節や努力を追加一致させた一度限りのv1構成では、8 sites・24 site×year transitionsでも個別site相関が定義できる3以上の反復を持つサイトが4しかなく**科学的STOP**。値を見てv1閾値を下げず、**別のサイト内中心化した共変動**というv2推定量を応答未開封の段階で新規固定した。

v2は8 sites・7 domains・24 year transitionsでsource-only gateを通過。分類群を初めて一度スコアした結果、**7 forest sites・6 domains・20 site transitions・113 original plot transitions**に対し、植物と地表甲虫の年次Simpson置換のサイト内中心化相関 **r=−0.0664、site-bootstrap95%CI[−0.5776,+0.1632]、9,999同siteランダム化p=0.536**。共分散正2・負5。結論は「正の年次同期を検出できない」であり「種群が独立に変わる」との証明ではない。CI [#43216964523](https://github.com/zuizui0223/Structural/actions/runs/43216964523) 成功、artifact #13943484010。最終数値と出典は[FOREST_MACRO_NEON_8FOREST_CROSS_TAXON_TEMPORAL_V2_ORIGINAL_RESULT_20261112.md](FOREST_MACRO_NEON_8FOREST_CROSS_TAXON_TEMPORAL_V2_ORIGINAL_RESULT_20261112.md)。v1/v2とも自動再採点を停止した。**林冠構造・微気候と同年同plotの種構成の機構は未検証**、PREDICTS +0.0942/+0.0847は別の肯定的な空間結果として保持。

## 主線：既存PREDICTSの群集置換を「林冠の作用」と取り違えない

Structuralでは、NHM PREDICTS 20か国・39原研究の参照林間変動を差し引いたSimpson分類群置換差 **+0.0942** (95% Study bootstrap CI +0.0638〜+0.1253; 36/39正) と、距離対応後31研究の探索的二次感度 **+0.0847** (CI +0.0527〜+0.1166; 25/31正) が完走・スコア凍結済。どちらも林冠高、LiDAR構造、林床温度の**測定効果ではない**。今度は構造・微気候・生物群集を同時点で測った独立観測の適格性を、**元森林地域**を独立単位として探索する。

## ドイツ/中央欧州 Pierick et al. 2026 — 原本の測定構造を実確認

- 原本 v1 [Zenodo 10.5281/zenodo.19883322](https://zenodo.org/records/19883322) / 出版論文 *Ecological Indicators* DOI 10.1016/j.ecolind.2026.114874.
- **オリジナル main_dataset.csv 347,901 bytes, MD5 8fca5fca0fbb7c9918f90efef4390bae** をGitHub Actionsで取得成功。source metadata script `analysis/forest_macro_global/audit_pierick_3d_forest_structure_source.py`、CI #43198185252 SUCCESS（6 source-blind synthetic testsも成功）、artifact ID 13933038804（SHA256 b17755a83391e8c58182b03a1cdd2c18830bf8e0e3d6d9c763c082163ce6c11a）。
- 元CSVは **2,880行×9列** の*long format*。各region×patchの **30区画、region label 2種類、各区画96組、重複組合せ0**。2880行を独立森林と数えない。原論文の30個0.25ha森林区画という記載とも一致するが、「region 2ラベル＝2つの独立研究地」という階層は別途原設計を要する。
- 各区画で直交的に保持される **気象異質性8指標 × 構造3指標 × 生物4分類群 = 96行**。温湿度因子（Horizontal_Temperature, Horizontal_VPD, Vertical_Temperature, Vertical_VPD, Temp. -6/0/15 cm, Soil moisture）、林冠・LiDAR構造（Box dimension, Canopy cover (%), Eff. number of layers）、分類群（Plants, Spiders, Diptera, Hymenoptera）。調査処理条件コード3区分。
- 元原本の値列 `climhet_val`, `structure_val`, `div` は**まだ生物効果検定をしておらず**、今回の分類はヘッダーおよび元の指標名ラベルのみで取得した。
- **先行性:** 同じデータの水平・垂直微気候と林冠/構造、植物・ハチ類・双翅目の多様性の関係は原論文で既発表。無条件に再回帰して+の相関を「新発見」と言わない。森林区画30は多地域マクロの独立n=30を意味しない。

## ベルギー Verdonck et al. 2025 — 36区画だが単森林

- 先行原研究 [Dryad 10.5061/dryad.tmpg4f5b0](https://doi.org/10.5061/dryad.tmpg4f5b0), J Appl Ecol DOI 10.1111/1365-2664.70137.
- 元36区画（Quercus 25, Fagus 11）、2022年の2 pitfall traps×plotのCarabidae/woodliceと、2022–2023年の林床15分温度、水分、林冠被覆・胸高断面積・枯死木量。CSV各ファイルの作者記載はPlotID共通。
- 2026-11-12の新規GitHub Actionsで**Dryadの公式元ファイルdownloadエンドポイントがHTTP 401**、元観測を取得できなかった（CI #43197904463、ベルギージョブFAIL）。認証を迂回せず再試行を停止し、既存で確認した源情報を保存。以後このソースを独立2森林研究としてPREDICTSと無条件プールしない。

## 米国NEON: 多数の独立観測地を優先

公式NEON 2026 data API の生物ファイルは2026年6月以降token必須。接続トークンがない状態でHTTP403/401を回避する試みは行わない。一方、既に研究者によって公開されている **neonDivData**（`daijiang.r-universe.dev/neonDivData`, current 0.3.1）は、NEONの地表甲虫 DP1.10022.001（公開掲載47 sites、831 taxa）と植物 DP1.10058.001（47 sites、7,047 taxa）を整理し、同じsiteID, plotID, observation_datetimeとサンプル努力／NLCD land-cover/検出0の指標を持つ。これは現在の公式2026配信を直接取得したわけではない**別途公開済みの派生アーカイブ**。植生構造DP1.10098.001や温湿度DP1.00002.001はこれに含まれず、植物の存在情報をLiDAR樹高の同義語としない。

`analysis/forest_macro_global/neon_divdata_multisite_source_gate.R` を新規作成、まず **2019–2023 site×year、オリジナル plotID、元森林NLCD分類、標準pitfall採集努力がどれだけ揃うか**を生物応答を開かず監査する。甲虫と植物は調査法・区画サイズが異なる。地点と年が一致しても同区画ではなく、元の全く検出されなかった標本と真の不在を混同しない。site-yearが多くても独立研究地点は最大47で、独立ecoclimatic domainはそれより少ない。

## 次の科学的ゲート

1. NEON派生データの元地点・区画・年の対応、元森林NLCDラベル・検出ゼロと努力フラグを原本的に実査する。
2. 既存のsite-level森林構造/気候指標と**同じ調査時点・同じフィールド階層**で結べる地点を選ぶ。新しい直接計測がなければ、植物組成はforest structureそのものとは明示的に区別。
3. source-only gateを通過した場合にのみ、地表甲虫・植物という**2つの異なる調査チャネルの時間的群集交代**などの群集応答を事前固定。各site/yearを独立森林として数えず、site/domain単位の検証・観測努力を考慮する。
4. 研究目的は既存PREDICTSの+0.0942を「林冠が原因」と解釈し直すことではなく、**共通する環境下でも群集交代がどこまで分類群間で再現／非同調するか**を別の独立ネットワークで検証すること。

重要：NEON派生データの中身はこれから実測。eBird、TinyFish使用なし。Structure Draft PR #469は未マージ。BALA/GEB/THERAとPREDICTSの固定済み生物効果は変更していない。
