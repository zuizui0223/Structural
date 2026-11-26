# 森林マクロ生態学：地点台帳と環境接続（2026-11-06）

## 主目標
森林区画・森林断片の内部条件と周辺景観が、節足動物群集の種数、構成、空間的独自性をどう説明するか。島は地域的な階層であり、島間救済や投稿準備はこの作業の主題ではない。これは環境接続段階の成果で、生物群集の環境応答モデルはまだ当てはめていない。

## 実行済み
BALA v1.0 と SLAM v1.7 の公開Darwin Core原本からEvent表だけを読み、種・個体数・由来のOccurrence表は読まなかった。BALA 10,379 Eventを124地点ID、SLAM 893 Eventを42地点IDへ集約。合計166の出典別地点レコード、630の地点×年×採集法レコードを作成。いずれも元の地点ID・採集年・方法・森林ラベルを保持。

BALA原本SHA256: `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2`

SLAM原本SHA256: `b86f7fad6468d2fb9aa9473849effe41ba2c4405c786357b6f50d66d9ef552a0`

[実行 #42189797069](https://github.com/zuizui0223/Structural/actions/runs/42189797069) は成功。局所テスト8件も成功。成果物 #13489460875（ZIP SHA256 `29de926616a87668674e69c1ce23196e761ea3d6a19f8222586c16a4363d2195`）に地点台帳、Eventメタデータ、地図抽出窓、環境変数、出典を保存。

## 森林研究として使える範囲

| 出典 | 地点ID数 | 森林・植生ラベル | 原本標高範囲 |
|---|---:|---|---:|
| BALA | 124 | Native forest 104、Erica 1、溶岩上Erica 8、半自然草地上Erica 7、Pittosporum 4 | 14.6–1,043.9 m |
| SLAM | 42 | Native Forest 31、Mixed Forest 9、Exotic Forest 2 | 46–937 m |

BALAのlocationRemarksは原著者のEvent作成コードでfragment_nameから作られることを確認した。元資料の27断片名を利用できる。SLAMの同項目は25地域ラベルだが、BALAと同じ断片定義と決めつけない。

BALAの枝叩き5,072 Eventには15種類の原コード（JUNI、LAUR、ILEX、VACC、ERICほか）がある。これは採集対象植物のコードを追う入口であり、15種の樹木や林分の樹種構成を示すとは限らない。ERI/ERIC等の別名照合と正式なコード辞書確認を残す。採集努力の内訳を樹木の相対被度と誤認しない。

## 実際に接続した景観変数
ESA WorldCover 2021 v200の公開COG 4タイルから、全166レコードの100 m、500 m、1,000 m円内について、樹木被覆クラス（10）、低木クラス（20）、両者の合計、水域、有効画素割合を取得した。地図欠測は全地点・全円で0。153の異なる座標に対応する切り出しGeoTIFFも保存。500 mの樹木被覆クラス面積率を153窓すべてでローカル再計算し、最大差1.12e-16以下で照合した。

周辺500 mの樹木被覆クラス面積率は全レコードで3.13–100%。ただし、これは林冠閉鎖率・樹高・在来森林率ではない。低木を含めた指標も別列として残す。水域を含む円全体に対する割合なので、水域列を併記して海岸・湖岸の影響を確認する。元の座標不確実性は一律45 mであり、500 m円の中心を45 mずらした8方向の感度幅を記録した。最大感度幅は約10.0パーセントポイント。これは信頼区間ではない。

2020/2021 WorldCoverの差はアルゴリズム差も含むため、森林変化量として単純に差し引かない。1997年の群集へ2021年の環境を同時期の値として割り当てない。

## 独立性と年代を保持
- BALAとSLAMは24地点IDを共有。該当座標の距離は76.8–971.1 m（中央値131.9 m）。同じトランセクト周辺の別採集位置・位置修正・入力差などが考えられるが原因未確定。近接だけで同一地点に統合せず、独立した再現とも数えない。
- BALA 124 IDは111の異なる座標組に対応する。T-/TY-/TB等を含む同座標IDは要照合であり、124独立森林とは主張しない。
- 2021年景観との初回横断解析候補は2019–2022年に観測のあるBALA 30 ID（7島、15断片ラベル）とSLAM 31 ID（3島、16地域ラベル）。この61レコードにも12の共通地点IDがあり、61独立地点ではない。
- 45 m座標誤差に対し10 m単一画素の分類を確定的な林冠情報としない。

## 次に実行する生態学的解析
まず年代整合した候補を使い、各採集法を別々に、固有・非固有在来・外来群の検出種数／群集組成と、周辺樹木・低木被覆、原本標高、森林タイプ、採集対象樹種コードの関連を評価する。地点・森林断片・島・反復期間を階層化し、同じ地点から複数の独立標本を作らない。相関・予測として扱い、林型と標高の独立因果効果の識別を完成条件にしない。樹高・林冠開空度・歴史的土地被覆はまだ接続していない。

## 再現用コード
- `analysis/forest_macro/forest_plot_ledger.py`
- `analysis/forest_macro/extract_environment.py`
- `analysis/forest_macro/test_ledger.py`
- `analysis/forest_macro/test_environment.py`

地方森林台帳・樹高データ・森林被覆の過去年データを追加するときは、この台帳へ出典年と解像度を付けて接続する。既存のBALA長期結果や原稿を上書きせず、新しい森林環境の研究として別ブランチで進める。

## 出典
BALA原著: https://doi.org/10.1038/s41597-024-03174-7

原著Event変換コード: https://github.com/pozsgaig/BALA_database/blob/main/Event_table_creation_G.R

BALA: https://ipt.gbif.pt/ipt/archive.do?r=bala_arthropods&v=1.0

SLAM: https://ipt.gbif.pt/ipt/archive.do?r=arthropods_slam_azores&v=1.7

ESA WorldCover 2021 v200: https://doi.org/10.5281/zenodo.7254221

取得仕様と2020/2021比較上の注意: https://esa-worldcover.org/en/data-access

地図帰属: © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.
