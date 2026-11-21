# NEON森林：年次群集応答のサイト内中心化・同期検証 v2（メタデータのみを見て別推定量を固定、2026-11-12）

## v1は科学的STOPのまま

[初回の事前固定仕様](FOREST_MACRO_NEON_FOREST_CROSS_TAXON_TEMPORAL_ALIGNMENT_PRESPEC_20261112.md)に基づくGitHub Actions #43207182531 は **SUCCESS/SCIENTIFIC_STOP_SAME_PLOT_EFFORT_TEMPORAL_SUPPORT**。元植物・甲虫の`taxon_id`、`taxon_rank`、`value`には**一切アクセスせず**、8森林（7domains）において追加季節・努力条件の後に306区画年、150連続区画年、3以上のplotを持つ24 site×year転換が残ると確認。しかし、**3以上の年次転換が残る森林は4サイト**で、初回の「サイトごとの相関を計算できる5以上のsite」という条件を満たさなかった。**このv1の停止を失敗や非有意な生物結果と呼ばず、条件を変更してv1のp値を追いかけない。**

## v2は元の生物応答を開く前に異なる問いとして固定

**問い**：サイトごとに異なる平均的な群集置換量を除いたあと、同じ森林の同じ年次転換で、植物と地表甲虫の観測分類群組成変動が対応するか。サイト内の年次差を問うので、各サイトで最低**2つの**年次転換があれば中心化が定義できる。n=2のサイト単独相関は定義しない。

- 元source-only cohortとデータ利用はv1と同一（neonDivData 0.3.1、公式site2026-08-05、森林8サイト・2019–2023）。`plotID`・日付・元sampling effort・NLCD Forest分類と甲虫正常フラグの厳格な基準を**一切変更しない**。植物1m²最初の調査日±7日、甲虫±30日、連続年の調査DOY差≤45日、年の間の甲虫trap-daysと植物記録済み1m²subplots数が0.5–2倍、各年の甲虫標本4以上＋植物陽性subplots4以上、各site×year転換で共通plot3以上、前回と同じ固定値。
- ソースメタデータ**だけ**でsite×year転換を定め、`>=2 year-transition`がある独立site **6以上**、独立生態気候domains **4以上**、site×year転換 **16以上**を同時に通過できないなら、`SCIENTIFIC_STOP_V2_SITE_BLOCK_SUPPORT`で生物応答未読のまま終了。先の24 transitionsからこの閾値をどう超えるかは、実際の元site→年の配列を読んで評価し、有意結果のために変えない。
- 一度だけ元派生の分類群値を開く場合はv1と同一元観測フィルタ。甲虫は`taxon_id`あり、species/subspecies/variety階級、`value>0`（ゼロ捕獲は努力には含めるがtaxon不在と解釈しない）。植物は1m²の記録がある同階級の`taxon_id`のみの観測出現。植物側でゼロ観測行が落ちているため、真の種消失ではなく**記録分類群の変化**。
- 各同一plotの連続年で植物と甲虫のSimpson replacement（β_sim）を別に計算し、同じ3以上の得点可能なplotが残るsite×year転換を単位とする。生物endpointのundefined groupsは理由と件数を保存。スコア可能なsiteが6未満・domain4未満・site-year転換16未満なら効果推測をSTOPし、閾値を事後緩和しない。
- primary v2 statistic：siteごとに年次βを平均中心化し、site内共分散・分散を**サイト等重み**で平均した`R_within_site=mean_i Cov_i(b,p) / sqrt(mean_i Var_i(b)*mean_i Var_i(p))`。各siteの転換数が2–4と不揃いなので、siteごとのn=2相関をそのまま独立の相関として平均しない。
- 元site内の**植物**βの年度対応だけを9,999回ランダムに入れ替える帰無、site block 4,000 bootstrapの区間とLeave-one-site-outを報告。統計的な独立単位は**site**（最大8）で、plot転換150やsite×year転換24を独立森林とは数えない。ゼロ分散でR undefinedならSTOP。正負、信頼区間、p値のいずれも隠さず報告。これは新規データでの完全確認でなく、2026年までに公開済みのNEON派生データの二次探索解析である。

## 科学的な主張の上限

現地林冠高やLiDAR構造を同時測定しているわけではない。NEON公式平均樹高はsite contextであり、現地同plot同年の林冠高さではない。気温・植物の送粉・捕食や森林改変の因果機構は未測定。source packageの植物1m²ゼロ行削除によりabsence比較の完全性は未確定。PREDICTSの既肯定的`+0.0942/+0.0847`、BALA、THERA、GEBを更新しない。eBird/TinyFish不使用、PR #469 Draft未マージ。v1 Source STOPは取消さない。
