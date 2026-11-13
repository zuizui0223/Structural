# 森林マクロ生態学：全球原観測の支持範囲（2026年11月7日）

## 2026-11-14：2014–2018未利用のNEON歴史コホートも実測、元森林VST quality supportでSTOP

公開`neonDivData 0.3.1`の未利用2014–2018地表甲虫・植物sourceで**33元NEON sites・730 original forest plot×years**が同year同plotに存在し、植物初回調査日±7d、甲虫±30d、各元記録4sample/4subplot以上のsource supportを持つ**674 plot×years**を原本CIで取得。この5年は公開木本VST RELEASE-2026の収録期間に入っていた。

ところが33公開VST site bundlesをsource QAまで実際に照合すると、当該早期VST`plots`に**2,780 original plot-event contexts、うち1,889 forest source event contexts、甲虫・植物sourceと同じ森林plot×yearが227区画年**存在しても、**作者の`tree_support=sampled_with_records`かつ有効`area_trees>0`かつ同年森林plotを満たす元VSTイベントは0**。従って3資料の同年有効樹高効果を推測することは**原資料のquality supportがないため不可能**。新時期2014–2018は旧2019–23の足りない2 siteyearsに補充できず、旧22sites/73 height-readyからの10sites/10siteyears/35pairsもなお生物効果Scientific STOPのまま。これは森林構造に生物学的作用がないという帰無結果ではない。

成功CI [#43459879574](https://github.com/zuizui0223/Structural/actions/runs/43459879574)・匿名artifact #14054839489。完全な[2014–2018の元森林tree-QA attrition](FOREST_MACRO_NEON_HISTORICAL_2014_2018_VST_ORIGINAL_QA_ATTRITION_RESULT_20261114.md)。これ以上同じ観測を閾値調整して結果探索しない。新しい独立の木本原資料または本当に同年同plotのリモートセンシング高さを、別の証拠とデザインとして検討する。先に凍結したPREDICTSの+0.0942/+0.0847とNEON年次の−0.0664(p=.536)は全く変更していない。

## 2026-11-13：NEON実測樹高73区画年の季節・採集努力Source QAを完了、10森林・35組の比較機会

固定したNEON mixed-landscape森林パッチ22sites・13domains・73樹高有効元plot×yearに対し、甲虫正常trap採集（植物最初の調査±30d、元sample数≥4）、植物1m²（最初の調査日±7d、記録済みsubplot≥4）、木本元event日（植物日±90d）、元forest `plotID×year`を**分類群生物応答未読で**再検証。**73→36 plot×yearsが時期・最低努力条件を満たす**。同一site×yearに2以上のplotがあるのは10 siteyears、41組のplot対が候補。甲虫努力量比0.5–2.0は39、植物記録済みsubplot比0.5–2.0は41、植物初回調査日の差30d以内は36、**3条件を同じplot対で全て満たすのは35組／10独立NEON sites／8 domains／10 siteyears**。事前固定した許可基準は10 sites/6 domains/**12 siteyears**で、後者のみ未達。**構造と群集組成の生物効果検定はSTOP（未実行）**。

**誤判定訂正：** 初回Source QA CI #43338037317の「0比較組」は、存在しない植物努力量フィールド名`plant_recorded_1m2_subplots`を参照したコードの人工物だった。生物データは未開封のまま合成テストにより発見し、`recorded_one_m2_plant_subplots`へ修正・欠落フィールドを明示STOPする防御を追加した。後続の原本CI [#43340430135](https://github.com/zuizui0223/Structural/actions/runs/43340430135) **SUCCESS** が**35区画対**を確認。以前の0/FAILの値は**研究証拠として無効**。脱落理由は樹木日±90d超25、正常甲虫日±30dなし3、植物/甲虫最低採集数不足9。区画対に3条件を揃えると35/41が一致するので「データがほとんど対応しない」と一般化しない。

完全な修正後source数値：[FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_SEASON_EFFORT_ORIGINAL_RESULT_20261113.md](FOREST_MACRO_NEON_VST2026_73_HEIGHT_PATCH_SEASON_EFFORT_ORIGINAL_RESULT_20261113.md)。既存PREDICTS 39研究`+0.0942`／距離対応31研究`+0.0847`、NEON7森林の植物甲虫年次同期`−0.0664,p=.536`は元結果を一切変更していない。独立森林間で樹高が群集種組成を決める因果機構はまだ検証できていない。

## 2026-11-12 NEW：NEON実測樹高×甲虫×植物の同year同original plot原本接続（22 sites・13 domains）

NEON植物・地表甲虫の公開派生`neonDivData` 0.3.1と、別の研究者が公開したNEON木本構造`DP1.10098.001 RELEASE-2026`のsite別RDS（公開commit `3391e702e7be80a3f049c905782661f043be8db8`）を、**同じsource original siteID×plotID×year**と、甲虫/植物/VST各3資料で独立にforest NLCD区画と認定する方法で照合した。サイト全体がstrict forestのみの当初8サイトでは**7 sites・7 domains・26 plot×years**で事前固定最小40に届かずSource-only STOP（先行結果を保持）。

次に**別母集団**「混在景観のforest patches」に限った場合、甲虫・植物の元森林plotが同年存在するのは35 sites・952 plot×years、元VSTの林内木本sampling opportunityもQA支持されたのは**22 sites・13 domains・75 plot×years**、うち74は真正の木本measurement recordsを持っていた。2026-11-12に**生物taxon値を開かず**当該74を元plot×eventと個体ID・source QAで結合したところ、**73 plot×yearsで3以上の別個体 live single/multi bole trees DBH≥10cm 有効height**を取得可（有効樹木数の元plot×year中央値13）。**16 sitesで17同site×yearに2以上のheight有効plot**。構造source-only minimum（6 sites/4 domains/40 plotyears）は22/13/73で通過。原生物値を再スコアして得た生態学的陽性効果ではなく、森林構造と生物組成を同年同plotで検定できる**独立地域の観測機会を実測で確保したこと**が主な進展。

元原本：[strict8 QA](FOREST_MACRO_NEON_VST2026_STRICT_FOREST_ORIGINAL_PLOTYEAR_RESULT_20261112.md)、[mixedforest triple-source QA](FOREST_MACRO_NEON_VST2026_FOREST_PATCH_TRIPLE_SOURCE_RESULT_20261112.md)、[height QA](FOREST_MACRO_NEON_VST2026_FORESTPATCH_HEIGHT_QA_RESULT_20261112.md)。Source-only GitHub Actions [#43238833529](https://github.com/zuizui0223/Structural/actions/runs/43238833529)、[#43240643741](https://github.com/zuizui0223/Structural/actions/runs/43240643741)、[#43242197939](https://github.com/zuizui0223/Structural/actions/runs/43242197939) すべてSUCCESS。

このコホートはNEONの22 sitesが13domainsにネストされるもので、73反復区画年や15,556元全source individual rowsを独立森林数に換算しない。樹高と分類群構成の回帰、同時期の微気候、林冠の垂直虫相や森林改変による因果機構は**未検証**。次のprimary lineは同year同source original plotでの`trappingDays`/trap flagsと植物1m²/調査季節を揃えた比較可能性のsource-only判定。あらかじめ**10 sites、6 domains、12 site×yearsで同year ≥2 plots**を残すことを次段の生物モデル許可要件とし、効果に応じてしきい値を変更しない。

## 2026-11-12 NEON 7森林での年次同期結果：有意な共変動は検出されず（独立の時系列比較）

**一次設計v1は採集努力と季節を揃えると5以上のサイト内相関が作れずSCIENTIFIC STOP**。v1停止を解除せず、生物応答を開く前に別のv2推定対象「サイト内年次群集置換の等サイト重み共分散／分散比」を固定し、一度だけNEON公開派生`neonDivData`0.3.1（2019–2023）を実解析。森林8サイト・7domainsの元区画母集団で、方法／時期等の固定条件を満たした**24 site×year transitions**のうち、元分類群βが両群で定義された**20 transitions**、113元plot転換（非独立）、**7森林・6domains**で推定できた。

**植物×地表甲虫の年次Simpson群集置換のサイト内中心化相関 = −0.0664**、サイトblock-bootstrap 95%区間 **[−0.5776,+0.1632]**、元site内植物年次ラベル9,999置換の両側 **p=0.536**。site共分散は正2/負5、leave-one-site-outは−0.1858〜+0.0217。各分類群の平均年次置換成分は甲虫0.1845、植物0.1592。**正の年次同期が検出されない結果で、完全な非同期の証明ではない**。植物1m²ゼロ記録が派生データから除去されていること、甲虫pitfallの検出過程、気候の変動、site単位の林冠高が採集plot同年の測定ではないことに注意。

実行 [GitHub Actions #43216964523](https://github.com/zuizui0223/Structural/actions/runs/43216964523) SUCCESS、元結果 artifact #13943484010。**生物解析とv1科学的STOPの両ジョブは自動再採点しないよう封印済**。全数値と独立単位：[FOREST_MACRO_NEON_8FOREST_CROSS_TAXON_TEMPORAL_V2_ORIGINAL_RESULT_20261112.md](FOREST_MACRO_NEON_8FOREST_CROSS_TAXON_TEMPORAL_V2_ORIGINAL_RESULT_20261112.md)。

**PREDICTSで正に支持された歴史的・空間的な改変林と参照林の群集置換パターンと、NEONで有意でなかった植物×地表甲虫の時間的同期は、異なる推定対象である。** 一方を他方の確認・反証としない。両研究を同じ因果的「林冠メカニズム」の結果へ統合しない。森林構造・微気候の同plot同年かつ独立複数森林での検証を次の主線とする。

## 2026-11-12 NEW: 20か国・39原研究で参照林を超える群集置換を実測（PREDICTS）

前回のTHERA 20区画・地理2森林で探索を止め、独立した多研究の森林マクロ生態学へ主線を移行した。事前固定したPREDICTS厳格森林1,145地点／39 original Study×method×target taxon／20か国について、公式NHM 2016+2022 full diversityから**242,677分類群×地点測定記録を実際に使用**した。各研究の改変林–参照林Simpson置換成分から参照林–参照林の基準置換成分を引いた結果、**研究等重みΔβ_sim=+0.0942、Study 4,000-bootstrap95%区間[+0.0638,+0.1253]、36/39研究正方向、9,999 Study符号反転p=0.0001**。39 original Studiesが各1 groupで、1,145地点や数万ペアを独立森林として計数していない。**群集構成に関する新しい肯定的な二次解析結果**であり、独立の新野外実験ではない。

気候帯別記述では湿潤熱帯34群の31群正・平均+0.1028、温帯広葉樹5群の5群正・平均+0.0361。ただし森林バイオーム間差の確認的相互作用検定や森林内部の実測高さ・群落層の比較ではない。

原本実行 [GitHub Actions #43164680231](https://github.com/zuizui0223/Structural/actions/runs/43164680231) 二ジョブ成功、原生物集計artifact #13919791026。仕様[FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_PRESPEC_20261112.md](FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_PRESPEC_20261112.md)、結果[FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_ORIGINAL_RESULT_20261112.md](FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_ORIGINAL_RESULT_20261112.md)。再実行で結果を探さないよう元の生物学的一次jobは一回成功後自動SEALED済み。

**ただし地理距離による交絡が確認された。** 同じ39研究のsite-only原座標で改変–参照群の平均水平距離の方が参照–参照より遠い研究が22、近い15、同値2。studyごとの平均距離の中央値は各7.9313 km、4.0613 km。したがって観測された置換差すべてを人為土地利用の因果的な環境フィルタと呼べない。距離支援の原本CI [#43165483599](https://github.com/zuizui0223/Structural/actions/runs/43165483599) は生物応答0件開封。次段として原座標だけで凍結した距離比1.5x以内のeligible Studiesは**33/39**（CI #43166027360）、生物学的な二次感度は初回得点とは独立した後付け探索として実行。実際の森林構造／樹高との結合は**未検証**であり、これをすでに検証済みとは呼ばない。

**追加入手できた結果（2026-11-12）**：距離比1.5倍以内・元参照3地点以上等の事前固定した地点座標だけの条件を満たしたのは**33/39研究**。元の分類群データを一回だけ再参照した二次感度では、2研究がβ未定義でSTOPし、**31研究の距離対応Simpson置換差=+0.0847、Study bootstrap95%区間[+0.0527,+0.1166]、25/31正、9,999符号反転の記述的p=0.0001**。本採点は最初の+0.0942・39研究から**異なるサブ母集団と距離重み**に基づく後付け探索であり、数値差を距離因果の効果量とは呼ばない。元RR/ARの距離0と記載された地点対各64もあり、座標精度は未確証。詳しい元解析・限界は[FOREST_MACRO_PREDICTS_DISTANCE_MATCHED_SECONDARY_RESULT_20261112.md](FOREST_MACRO_PREDICTS_DISTANCE_MATCHED_SECONDARY_RESULT_20261112.md)、[成功CI #43166669584](https://github.com/zuizui0223/Structural/actions/runs/43166669584)。二次生物スコアも一回完走した後は自動再実行を封印した。

文献上の新規性の上限：PREDICTSの森林土地利用×βは既存論文の主題。2026-11-10 Nature Ecology & Evolution DOI 10.1038/s41559-026-03205-z は同じPREDICTS母集団の184研究38,010地点対でBray-Curtis類似度と外挿精度を検討済。今回の推定量は同一研究内の**Simpson入れ替わり成分と参照林相互の基準差の比較**。自然林が多いから必ず保護効果がある、島のメタ個体群救済と同じ機構という飛躍はしない。

## 2026-11-12 現在地：THERA地理階層の実確認と独立マクロ検証への切替

DATASAPROXのTHERA（EFNO）は厳格な2上層＋2下層の同法・同時期比較が**55 plot×month、20原区画、220イベント**。原座標の欠測・矛盾はゼロ。ただし5kmおよび20km連結成分は**2群**であり、20の独立森林とはいえない。Balvay et al. (2026, DOI 10.1016/j.foreco.2026.124001) は同じくフランスの2森林・20区画でLindgren垂直甲虫群集差と衰退による均質化を公表済みで、THERAとのフィールド系列重複の可能性が高い。標本IDの直接照合までは未完了であるため「確定的な重複」も「独立再現」も主張しない。

実測論文の既発表結果を新たなStructuralの発見として数えず、THERA原本の地理・方法監査は完了とする。**次の主線は異なる地域／森林タイプで同じ群集組成endpointが推定可能な独立採集系の取得**。既存のNardi 13景観・8か国の「都市化差と甲虫種交代」の探索的肯定結果は維持するが、縦層効果の独立再現と混同しない。PREDICTS/sPlotOpenの大きな母集団は生物応答・現場階層・採集方法の完全な同時比較母数が少ないため、数字をそのまま有効標本数とは扱わない。

原本地理・論文先行性の数値監査と終了条件：[`FOREST_MACRO_THERA_GEOGRAPHY_PRIOR_ART_DECISION_20261112.md`](FOREST_MACRO_THERA_GEOGRAPHY_PRIOR_ART_DECISION_20261112.md)。[GitHub Actions #43126599073](https://github.com/zuizui0223/Structural/actions/runs/43126599073) SUCCESS。THERA・BALA・GEBのspecies outcome/holdoutは無変更、eBird不使用、PR Draft。

## 主目標
BALA・SLAMを単なる地域事例として保持し、全球森林の環境母集団を独自に構築して、森林量・林冠内部構造・気候／土壌・森林連続性が群集構成とどう対応するかを比較する。公表された個別論文の結果を横に並べることをマクロ解析とは呼ばない。

## 公開原観測から今回実際に数えた支持範囲

英Natural History Museumの公開2016/2022年版PREDICTSの地点要約原本を公式Rアクセスパッケージから取得した。[CI #42320392359](https://github.com/zuizui0223/Structural/actions/runs/42320392359)は成功。元の約431万種測定レコードの再解析ではなく、地点・研究・森林分類・採集法・調査年の適格性を監査した。

| 観測範囲 | 地点ID | 原研究・比較群 | 国 |
|---|---:|---:|---:|
| PREDICTS公開全地点 | 35,738 | 817原研究ID | 101 |
| 森林Biomes＋森林性土地利用（広義上限） | 12,687 | 522 | 82 |
| **現地Habitatに森林明記＋森林性土地利用＋森林Biome** | **4,920** | **315** | **64** |
| 一次植生・低攪乱候補 | 3,032 | 250 | 57 |
| **同じ原研究・方法・分類群で参照森林2地点、改変森林2地点以上** | **1,145** | **39比較群** | **20** |
| 2019年以降採集の厳格森林地点 | **0** | 0 | 0 |

森林地点4,920は7森林バイオームと7生物地理Realmに分布するが、熱帯・亜熱帯湿潤広葉樹林3,001（61.0%）、温帯広葉樹・混交林1,116（22.7%）で計83.7%を占める。さらに原研究内比較が可能な39比較群は、**湿潤熱帯広葉樹林34と温帯広葉樹林5に限られる**。亜寒帯林、地中海性森林、乾燥林、各種針葉樹林には同じ条件の比較群がない。全球森林のすべてへ外挿しない。

全地点35,738は緯度経度の数値を持つが、原著・著者由来の座標34,187と地理参照した座標1,551で、実際の10 m精度が保証されるわけではない。調査時期は2020年より古いため、2020年樹冠高を当時の樹冠構造として割り当てない。元データの利用条件は非商用・原著帰属であり、元地点の行は成果物に再配布していない。

## 個別論文ではなく、多地域の共通観測ネットワークを自前で構築

[GBIF世界の標準化採集ソースの目録](https://github.com/zuizui0223/Structural/actions/runs/42320079634)を世界森林関連の固定10検索語で照合した結果、重複を除く448データセット、うちタイトル／説明文の森林関係語がある356件を発見。356件には海中のケルプ林や出版社名からの偽一致もあるため、**陸上森林の独立地点数ではない**。eBirdは除外。

森林現地モニタリング関連の18データセットを生物結果を見る前に固定し、[GBIF近年原本索引監査 #42320818293](https://github.com/zuizui0223/Structural/actions/runs/42320818293)で実際の2019〜2026年観測記録を照合した。**7データセットが近年の記録を持つ**。記録国はスウェーデン、日本、タイ、米国、ノルウェー、リベリアの6か国。候補にはスウェーデン森林インベントリ、日本列島45地点森林モニタリング、タイ林冠・下層昆虫（甲虫・膜翅目）、米国森林ハチ、ノルウェー森林植生、リベリア森林植生・炭素モニタリングが含まれる。インデックス上の出現記録数は森林区画数でも独立サンプル数でもない。

## 7つの近年ネットワークの実際の採集Eventメタデータを監査

[GBIF最新7ネットワークのEvent／座標／方法監査 #42321146344](https://github.com/zuizui0223/Structural/actions/runs/42321146344)は**SUCCESS**。先に固定した7データセットについて、各データセットの2019〜2026年索引から**最初の200 Occurrenceレコードだけ**を取得し、そのうちEventID・場所・採集法・habitat・座標・位置不確実性の列を検証した。**合計1,400件のOccurenceレコードはメタデータ確認用に取得したが、種名・個体数は抽出／採点／保存していない。** BALA/SLAMの既存生物学的採点は再実行していない。

| 既存の多地域候補 | 現地記録国 | 最初の200レコードにEventID | 採集法記載 | habitat記載 | 座標の不確実性記載 |
|---|---|---|---|---|---|
| Swedish NFI植生 | Sweden | 200 | 200 | 0 | 200 |
| 日本45森林区画モニタリング | Japan | 200 | 200 | 0 | 0 |
| SE-Asia林冠・下層甲虫 | Thailand | 200 | 200 | 0 | 0 |
| SE-Asia林冠・下層膜翅目 | Thailand | 200 | 200 | 0 | 0 |
| 北米森林ハチ | United States | 200 | 200 | 200 | 200 |
| ノルウェー森林植生 | Norway | 200 | 0 | 200 | 0 |
| リベリア上部ギニア森林植生 | Liberia | 200 | 200 | 200 | 0 |

**7/7ソースでEventIDと座標の数値は見つかったが、採集法6/7、habitat3/7、座標不確実性の明示2/7。** これは**最初の200索引レコード**のフィールド充足率であり、全データの欠測率や、独立森林区画数の推定ではない。Swedenでは最初の200記録が1 Event ID、Japanでは2 Event IDだった。これを1区画／2区画という結論にしない。Thailandの甲虫・膜翅目は同じ調査ネットワークの分類群別分割である可能性があり、別々の生物地理的な独立再現としない。

この監査によって、**研究ごとの森林現地定義・実座標の精度・原Eventと原地点との一対多関係を確認しない限り、林冠高画素に接続した全球マクロ回帰を始めない**という具体的な判定基準が得られた。今後必要なのは、出典原本のEvent表／野外プロトコルと、ForestGEOや国別森林インベントリの区画識別方法の照合であり、200行の検索結果をサイト全数と誤認しないこと。

## 森林生態学の検証をどう成立させるか

主仮説：**森林量と気候が同じ程度でも、森林内部構造の差によって群集構成・森林専門群の残存・森林間の独自性が異なる。その環境相関は、絶対樹冠高より地域の参照森林からの構造偏差で強く説明されるか。**

空間森林画素は説明側で、現地採集の原Event・森林区画が応答側。元の調査努力、分類群、採集年、採集法、区画階層を保持する。地図の樹冠高の表面ばらつきと、実際の林内鉛直構造は別々に定義する。地域または森林帯を丸ごと学習から外した評価で追加予測力を判定し、既知の研究地点だけの有意差を成功条件にしない。

**未完了：** 7件の近年モニタリングの実際の独立Event／区画／habitat／方法・座標精度、2020年森林構造への時点適合、全球森林母集団、群集行列の統合と環境効果推定。現在は原観測の地理的・設計的支持範囲を確認した段階。Global GEB哺乳類本体のScientific HOLDを維持する。

## 資料とコード
- NHM PREDICTS 2016＋2022公式データ取得: https://biodiversity-futures-lab.github.io/predictsr/
- GBIF sampling-event Registry API: https://techdocs.gbif.org/en/openapi/v1/registry
- 全球樹冠高2020: https://doi.org/10.1038/s41559-023-02206-6
- 森林構造と気候の既知の関係: https://doi.org/10.1038/s41467-020-20767-z
- 原データ取得・集計コードは analysis/forest_macro_global/ を参照。
