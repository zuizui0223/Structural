# NEON森林パッチ：樹高73区画年と甲虫・植物調査の同区画・同季節・同努力の資格検査（2026-11-13、原応答値未使用時に固定）

## 現在地

先行Source-only監査で、公開NEON VST2026の品質管理済み木本実測と、公開`neonDivData`甲虫・植物が元`siteID×plotID×year`で重なるのは、混在景観内forest plotを含む **22独立NEON sites・13 ecoclimatic domains・75 source-eligible plot-years**。元`sampled_with_records`と有効な木本高さは74区画年、そのうち**73区画年**で元`individualID`の重複を除いた生存木・DBH≥10cm・source`size_height_ok`・有限正`height`が各3個体以上ある。原本成功CI #43242197939。値による樹高の傾向・有意性は未計算。

既存の森林生物応答は独立に封印：PREDICTS 39 original studies `+0.0942`（36/39正、Study 95%CI +0.0638～+0.1253）、距離対応31研究の探索的感度`+0.0847`、NEON森林7サイトの植物×甲虫時間的同期`R=−0.0664` (p=.536)。本Source-only検査で上記の生物結果を再開封・得点しない。

## 応答を見る前に固定した採集資格の条件

元7資料や他バイオームへの横流しはしない。厳格森林サイト8での26区画年Science STOPは別母集団として保持。

- 対象は新母集団の**固定73元plot×2019–2023年**のみ。構造sourceは公開VSTのRELEASE-2026派生RDS（exact commit `3391e702e7be80a3f049c905782661f043be8db8`）、`trees`測定実数は扱わず元`plots`の支持された`sampled_with_records`・正`area_trees`・`nlcdClass`森林・元event `date`を使用。元`sampled_absence`を高さ0としない。
- 甲虫・植物sourceは独立公開`neonDivData` **0.3.1**。種名、`taxon_id`、捕獲数`value`、植物被度や解析済みβを**一切参照せず**、元`plotID`、`siteID`、採集日、採集努力、subplot、元NLCD forestのみを参照。
- 各plot×year内で植物1m²の有効なsource `unique_sample_id` と `subplotID`を持つ元記録の**最初の調査日**を固定する。植物は同日±**7日**の調査だけを候補にする。正常`trapConditionFlag`が空、`trappingDays>0`、固有`unique_sample_id`と`trapID`がある甲虫採集は植物の最初の調査日±**30日**の記録だけを候補にする。同一sampleIDに矛盾する元trap-daysがあればSTOP。
- 生物効果に必要な努力を源のみで揃えるため、各plot×yearで甲虫正常source sampleIDを最低**4**、植物1m²の記録済み元subplotを最低**4**保持する。植物のゼロ記録が派生パッケージから落ちているため、これは全植物調査の真の努力量ではないことを明記。
- 同plot×yearの元VST樹木測定`date`が、固定した植物最初の調査日から**90日以内**であること。VSTの`year`しかなく`date`が欠測の場合は同季節であると補完せず、そのplotを不適格とする。
- 同元site×同年に最低2森林plotが残り、plot間で正常甲虫`trappingDays`総和と植物1m²の記録済み`subplotID`数がそれぞれ**0.5–2.0倍**、固定植物最初の調査日の差が**30日以内**となるplot対が最低1組あること。plot対は非独立、独立nは元NEON siteである。
- **唯一の次段生物効果モデルへの原資料許可要件**は、先に固定した**10独立NEON sites、6 domains、12 original site×year paired-plot groups**を全て満たすこと。達しなければ`SCIENTIFIC_STOP_ORIGINAL_SAMEPLOT_SEASON_EFFORT_REPLICATION_INSUFFICIENT`。効果に都合のよい90日・4採集・0.5–2.0倍を事後変更せず、停止自体を論文の非有意結果と呼ばない。

## 科学上の主張上限

原source QAは森林区画の観測機会であって、林冠の立体異質性・温度緩衝・甲虫の送粉/捕食機能の機構を証明しない。地表甲虫pitfallと植物1m²で測定チャンネルが異なり、元site/plotが同じでも林内サンプリング地点は必ずしも完全に一致しない。VSTの`height`は森林構造の**1次元**であり温度計やLiDAR体積ではない。元sourceの木本測定年が合うからといって改変林vs参照林という土地利用操作を設計したことにはならない。

採集適格性が通過してから初めて、同site同yearの異なるplot間で高さの90%分位差（同plot元event、生木DBH≥10cm、元個体ID単位）と記録分類群組成差（taxon階級・検出努力）について、研究内比較・site単位で探索する別事前固定仕様を作る。**現時点で構造効果、係数、有意差を算出した事実はない。**

実装 `analysis/forest_macro_global/neon_vst2026_forestpatch_species_source_season_effort_gate.R`、ランナー内にのみ元plotkeyを保存する`neon_public_vst2026_forestpatch_height_quality_gate.R`、CI `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`。元個体/plot/種名/座標の原行はGitHub成果物に再配布しない。PR #469 Draft未マージ、eBird/TinyFish不使用。
