# NEON森林：RELEASE-2026実測樹木構造の公開二次原本 × 甲虫・植物plot/年の前段監査（2026-11-12）

## 主線と現在地

Structuralの森林マクロの既知の実測結果はPREDICTS 20か国39原研究の森林改変とSimpson分類群置換 `Δβ=+0.0942`（Study95%CI +0.0638〜+0.1253、36/39正）および距離対応31研究の二次感度 `+0.0847`（CI +0.0527〜+0.1166）で、両方とも二次観測の陽性結果として凍結済み。NEON植物×地表甲虫の同区画・2019–2023年の年次同期は7独立森林で`R=-0.0664`（CI −0.5776〜+0.1632、p=0.536）と非有意で別endpoint、こちらも封印済。**どちらも林冠・樹高の同年同plot効果ではない。**

次の検証対象は、公式NEON `DP1.10098.001` vegetation structureの別途公開済みRELEASE-2026二次アーカイブ：[NEON Vegetation Structure Explorer](https://github.com/tgilbert14/NEON-Vegetation-Structure-Explorer)。公開研究者らの42 site bundles `data/sites/<SITE>.rds`、公開物理構造の時期とサンプル機会を持つ。元公式RELEASE-2026 DOI `10.48443/pypa-qf12`。公開アーカイブのバージョンは完成したドキュメント更新コミット**`3391e702e7be80a3f049c905782661f043be8db8`**に固定。元作者の科学契約は`NEON-VST-DP1.10098.001-v2`、構造は`list(trees, plots, opportunity_source, meta, contract)`、元のplot×event、src UID、support状態を保持。支持された真正ゼロ`sampled_absence`と測定不能`held_*`を混同しない。引用：[公式植生構造RELEASE-2026](https://data.neonscience.org/data-products/DP1.10098.001/RELEASE-2026)、[派生版科学契約](https://github.com/tgilbert14/NEON-Vegetation-Structure-Explorer/blob/3391e702e7be80a3f049c905782661f043be8db8/docs/SCIENCE-CONTRACT.md)。

## 元データ接続の不変条件

- `neonDivData` 0.3.1公開派生の2019–2023甲虫・植物（公式field site原本2026-08-05 SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`）の8 strict NLCD forest sitesだけを自動発見する。サイト候補の選択に分類群名・捕獲数・既存の非有意相関を使わない。
- 以前の元`neonDivData` site-only監査の8 forest / 7 domains / 40 site×yearsと、strict site+original plot/year/fixed 1m² plants/positive unflagged beetle effort 339 plot-yearsを維持。マッチングは**元のsiteID×plotID×暦年**。別年の構造を後から同年観測へ移し替えない。
- 新しいVST派生42サイトのうち当該8サイトの`.rds`原本だけを取得し、元`plots`の`tree_support`、真正元`area_trees>0`、元の`plotID×eventID`、元`date/year`を評価する。樹木のsource`height`、`stemDiameter`、種名、草本値、甲虫・植物の`taxon_id/value`を使った効果量は**この段階では算出しない**。`sampled_absence`は構造計測ゼロ可能性として保存し、樹高分布の計測があるとはみなさない。
- 作者の`held_sampling_impractical`, `held_opportunity_source_missing`, `held_metric_invalid`, `held_identity_conflict`をゼロ・陰性・採集努力とは扱わず、supportありのイベントと分離。VSTの一部が木本構造ではなくshrubs/saplingsのsampled areaである場合、林冠高に転用しない。**同plot×yearの測定があっても、実生物調査と完全同一季節、林冠の温度緩衝、森林面積・土壌組成の一致までは主張しない。**
- NEON 2026公式VST生ファイルはアクセス方法に独立した制限がある。今回はすでに公開されている別の二次配布データを取得し、NEON公式のトークン必須APIの認証を回避しない。元RDS・木本元行・元site/plot/個体ID・座標・原生物数値はStructuralにコミットやartifact公開をしない。

## 事前に決める科学的ゲート（新たな生物統計に関する基準）

**第1段：純粋なSourceスキーマ/被覆判定。** 公開木本42site bundleの8 forest sitesとの重複、original VST元plot+year機会の有無、その中の`tree_support in {sampled_with_records,sampled_absence}`と`area_trees>0`を持つ元site×plot×yearの数を集計。原`height`列の**存在**のみを確認。source RDSの`contract id`、exact commit、source official release一致がなければSCIENTIFIC_STOP。ソースが少なければ数値のまま報告。

**第2段：同年同plotでの生態学的連結の最小要件（第1段の数値を見る前に固定）。** サポートある木本構造元plot×yearが**6以上の独立forest sites**・**4以上のecoclimatic domains**・**40以上のoriginal plot×year**で使え、`sampled_with_records`の構造に本当に`height`の有限正値があることを、別の値の可用性ゲートで確認。条件を満たさなければ source-method SCIENTIFIC_STOPし、生物応答を再採点しない。heightの実数は生物統計の結果とは別だが、効果に有利な標本選別に使わない。**全site8は先行NEONで既に生物応答が見えているため、合格した場合でも林冠の効果解析は探索的で、独立確認的検定とは呼ばない。**

先行性：公開VST42サイトは別の研究者が2026年の樹木構造データを検査済みであり、Structuralによる元データ取得は**新しいフィールド測定ではない**。森林構造の実測に進むものの、現時点では現地同年の微気候・気候異常と共同同定できていない。

## 実装

`analysis/forest_macro_global/neon_public_vst42_original_plotyear_join.R` は元構造`plots`のsampled/held QAと、元NEON 8 forest siteの甲虫・植物採集`plotID×year`の交差のみを行う。ワークフロー`.github/workflows/forest-macro-neon-vst2026-public-structure-join.yml`で公開VST 42-site派生から8つだけ採取、元RDSを出さず匿名集計を artifact とする。PREDICTS主結果、NEON v1 STOP、NEON v2非有意結果、BALAとGEBのscorerは一切変更しない。eBird/TinyFish不使用。PR #469はDraft・未マージ。
