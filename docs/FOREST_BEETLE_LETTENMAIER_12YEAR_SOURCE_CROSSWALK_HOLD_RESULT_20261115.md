# 2026-11-15 長期枯死木甲虫：元原本の `plot/log/tree/year` と群集525行の対応は未認証 — SOURCE IDENTITY HOLD

## 現在の判定（原生物値を開封していない）

元著者の長期観測（Lettenmaier et al., *Journal of Animal Ecology*, DOI [10.1111/1365-2656.70183](https://doi.org/10.1111/1365-2656.70183)、原本 [Zenodo 10.5281/zenodo.17337484](https://doi.org/10.5281/zenodo.17337484)）について、2026-11-15の**原source-only**監査は以下を確定した。

- 元 `Beetle_Data` 7,738 long metadata行：完全な作者列 `plot, log, year, tree` を照合。42 `plot`ラベル、52 `plot×log` 候補、**522 `plot×log×year`**候補、52/52反復、最大11年、`tree` の同丸太内矛盾0。これは独立した42森林、52森林、522実験ではない。
- 元 `Beetle_Community` 行列：**525**異なる先頭列ID、種別応答候補297列。IDはすべて**4要素・末尾に年**の形状。
- 著者Rコード `GAM.R`（724行）・`NMDS.R`（371行）を原本MD5検証したが、今回の**狭いコード検出器**では `paste(plot,log,year,sep=...)` といった一意の作者定義join式は見つからなかった。この検出結果は「作者が実際に他の形のjoinをしていない」ことの証明ではない。
- 元 `Trait_Table`には `host_tree` ヘッダーがあるが、trait値・種名・同定対応は未読。国別Burnerの3段階 `Host_tree` と同じ測定とは未確認。

## 追加した6通りの原メタデータ完全列挙 — 主線の失敗箇所と原因

[**実行 CI #43697804270**](https://github.com/zuizui0223/Structural/actions/runs/43697804270) は SUCCESS、原本MD5・ソース契約・全6 permutationの記録を完了。これは**計算プログラムの成功**であり、研究仮説の支持を意味しない。元出典を明示した[6候補固定プロトコル](FOREST_BEETLE_LETTENMAIER_12Y_FOURTOKEN_IDENTITY_PRESPEC_20261115.md)は生物値を開く前に登録した。元の `plot,log,tree` を先頭3 tokenへ **3!=6** 通りの順列で完全一致させ、年は最後のまま固定、文字の切り詰め・別名推定・曖昧一致は一切していない。

| 元 `Beetle_Community` の先頭3要素に対応させた元フィールド順 | long 522組と完全一致した数 | long-only | community-only |
|---|---:|---:|---:|
| **plot – log – tree** | **359/522** | **163** | **166** |
| plot – tree – log | 0 | 522 | 525 |
| log – plot – tree | 0 | 522 | 525 |
| log – tree – plot | 0 | 522 | 525 |
| tree – plot – log | 0 | 522 | 525 |
| tree – log – plot | 0 | 522 | 525 |

全候補で元 `plot×log×year`からの変換時のID衝突は0。**6通りのうち522/522完全一致する候補は0**。最も一致する `plot – log – tree – year` さえ359組で、**163組の long-only と166行の community-only が残る**。表面的な「525行−522組＝3行」だけで説明できる不一致ではない。両者の差が3でも、非一致の規模は大きい。原因候補（由来コードの命名規則差、フィールドの別表記、群集CSVの編集・測定機会差など）は現時点で**未判定**。

**決定：`SOURCE_CROSSWALK_NOT_UNIQUELY_IDENTIFIABLE_NO_SPECIES_SCORING`**。元著者が明示した正確な群集IDの生成・対応規則を確認できるまでは、この525行を522元 `plot×log×year`に割り当てない。359一致した群だけを「生物的に有利なサブセット」として暫定採点しない。166 community-only を未捕獲や消失に、163 long-only を欠測・無昆虫に置き換えない。

## CIおよび再現性

- 元観測メタデータ長期階層：[Actions #43696912095](https://github.com/zuizui0223/Structural/actions/runs/43696912095) SUCCESS、匿名artifact #14154582676、SHA256 `b2b7760894c3093b4e9fed99ecca0374e51a8c7fd0d62ca98ad7c9ac32c22472`。
- 著者Rコードの方法監査：[Actions #43697279162](https://github.com/zuizui0223/Structural/actions/runs/43697279162) SUCCESS、artifact #14154548910 SHA256 `bf317ec71e7756b9bcafc17d72ecaa24330cab0e640e4fbc2d8c845e90dfc0a5`。コード解析は一意の元join式を認証できなかった。
- 固定6通りの完全一致検査：[Actions #43697804270](https://github.com/zuizui0223/Structural/actions/runs/43697804270) SUCCESS、匿名artifact #**14154724062**、ZIP SHA256 `92937a5d1a716aed02bcd12fce691bd370ad3c098239248af189f84094cf7fe4`。
- 実装 `analysis/forest_macro_global/lettenmaier_12year_4token_source_identity_gate.py`、CI `.github/workflows/forest-macro-lettenmaier12y-4token-source-crosswalk.yml`。
- ソースの元研究に対する甲虫種別出現・個体数、木材資源、腐朽指標、機能形質の効果係数は**0件しか新規に推定していない**。元の種ラベル・丸太ID・環境値・著者Rコード本文をGitHubへ再配布していない。

## 生態学的な次工程（条件付き）

同じ論文の通常の前処理・補助方法、あるいは著者が公開した source codebook から、両表の**元physical log×sampling-year×host**のID生成規則と同じ調査努力が確定できた場合のみ、新しい**事前固定・別の探索的推定量**へ進む。既刊JAE論文の木材樹種別・腐朽年数別の群集変化を新発見としない。問いの候補は「丸太の長期腐朽に伴い種組成が交代しても、同じ宿主資源の機能的チャネル構成が保たれる条件は何か」だが、現時点は**元sourceの同一性が未確定なので未検定**。

旧フィンランド142地点の枯死木量による小幅の地理外予測改善 `+0.00024237`、機能ギルドの事後感度 `D=+.035237`、Burner 3か国、PREDICTS、NEON、BALA、GEBの既存スコアは**すべて凍結・未変更**。eBird/TinyFish不使用、PR #469はDraft／未マージ。
