# contribution-art

GitHub のコントリビューショングラフに文字を描くための空コミットを、指定した期間と時刻帯に合わせて生成する CLI

## できること

- 指定した文字列を 7 行のドット文字として配置
- `5x7` と `7x7` の文字サイズを切り替え
- 指定期間の週数に合わせて中央寄せでレイアウト
- 日ごとのコミット数をランダムに揺らして自然な見た目に調整
- コミット日時をローカル時間で指定
- `--apply` で空コミット作成
- `--push` でそのままリモートへ push

## 動作要件

- Git
- `uv`
- Python 3.12 以上

## セットアップ

```powershell
uv sync
```

## まずはプレビュー

`--apply` を付けない限り、コミットは作られない

```powershell
uv run contributionArt.py "HELLO" --start-date 2026-06-07 --end-date 2026-09-26
```

## 実際にコミットを作る

```powershell
uv run contributionArt.py "HELLO" `
  --start-date 2026-06-07 `
  --end-date 2026-09-26 `
  --apply
```

## 作成後にそのまま push する

```powershell
uv run contributionArt.py "HELLO" `
  --start-date 2026-06-07 `
  --end-date 2026-09-26 `
  --apply `
  --push `
  --remote origin `
  --branch main
```

## 主なオプション

- `--time-start 18:30`
- `--time-end 23:00`
- `--font 7x7`
- `--reset-branch-history`
- `--timezone +09:00`
- `--timezone Asia/Tokyo`
- `--min-commits 2`
- `--max-commits 5`
- `--seed 42`
- `--show-dates`

## `.env` でデフォルト値を持たせる

`.env.example` をコピーして `.env` を作ると、毎回同じオプションを打たずに済む

```env
CONTRIBUTION_ART_REMOTE=origin
CONTRIBUTION_ART_BRANCH=main
CONTRIBUTION_ART_TIMEZONE=+09:00
CONTRIBUTION_ART_TIME_START=19:30
CONTRIBUTION_ART_TIME_END=22:30
CONTRIBUTION_ART_MIN_COMMITS=3
CONTRIBUTION_ART_MAX_COMMITS=6
```

## 注意点

- GitHub 上で反映されるには、コミットメールアドレスが GitHub アカウントに紐付いている必要がある
- コミットは現在のブランチに追加される
- 誤って作業中の変更を含めないよう、`--apply` 時は作業ツリーがクリーンでないと停止する
- 期間内に収まりきらない長さの文字列はエラーになる
- `--reset-branch-history` は現在ブランチの履歴を現在ツリー 1 個のベースコミットへ作り直す
- `--reset-branch-history --push` の組み合わせでは履歴書き換えになるため force push 相当で送信される

## 例

```powershell
uv run contributionArt.py "HI" `
  --start-date 2026-06-07 `
  --end-date 2026-08-29 `
  --font 5x7 `
  --time-start 19:30 `
  --time-end 22:30 `
  --show-dates
```

## 2021年前半に `KUWA` を 28 列ぴったりで入れる例

`2021-01-03` は日曜、`2021-07-17` は土曜なので、ちょうど 7 行 x 28 列になる

```powershell
uv run contributionArt.py "KUWA" `
  --start-date 2021-01-03 `
  --end-date 2021-07-17 `
  --font 7x7 `
  --show-dates
```

実際にコミットして push する場合:

```powershell
uv run contributionArt.py "KUWA" `
  --start-date 2021-01-03 `
  --end-date 2021-07-17 `
  --font 7x7 `
  --reset-branch-history `
  --apply `
  --push
```
