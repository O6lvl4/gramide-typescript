# gramide-typescript

[gramide](https://github.com/O6lvl4/gramide) の TypeScript 言語パッケージ。JavaScript
パッケージのスキャナと文法の拡張点に型構文を差し込んだもので、どのノードが名前を
宣言するかの規則、コンパイル済みテーブル、単体のバイナリを持ち、この言語だけを参照
パーサと照合し、計測し、再生成できる。[Almide](https://github.com/almide/almide) 製。

[English](README.md)

```
gramide_typescript check   src/*.ts      パースできれば exit 0、でなければ `file:line:col: unexpected X (expected …)`
gramide_typescript outline app.ts        `L12-40 class Widget`、`  L20-24 method Widget.render`、`L50-61 interface Props`
gramide_typescript symbols app.ts        名前・所有者・行とバイト範囲のバージョン付き JSON
gramide_typescript tags    app.ts        定義と参照。リポジトリマップの入力
gramide_typescript map .   --budget 1024 --task "fix the retry"
```

配布される `gramide` コマンド([gramide-cli](https://github.com/O6lvl4/gramide-cli))は
このパッケージを他の言語と合成したもので、普通は `almide install github.com/O6lvl4/gramide-cli`
で手に入る。このリポジトリは TypeScript を定義し、その正しさを検証する場所。

## 読めるもの

`.ts` `.mts` `.cts` を TypeScript 5.9 として読む。
[gramide-javascript](https://github.com/O6lvl4/gramide-javascript) が読むものすべてに加え、
型注釈、制約・既定値・変性付きのジェネリクス、interface、型エイリアス、enum、namespace と
ambient module、`declare`、`abstract`、アクセス修飾子と `readonly`、パラメータプロパティ、
オーバーロード、インデックスシグネチャ、`import type` / `export type`、`import x = require()`、
`export =`、デコレータ、`as`、`satisfies`、`!` アサーション、`<T>x` アサーション。型の側では
union・intersection、条件型・mapped 型、`infer`、`keyof` / `typeof` / `unique symbol`、名前と
rest 付きのタプル、関数型とコンストラクタ型、テンプレートリテラル型、`import("m").T`、
型述語。JSX はまだ読まない。`.tsx` はこのパッケージのものではない。

JavaScript パッケージと同じく、TypeScript でないものは拒否するが、コンパイラが拒否する
ファイルをすべて拒否するとは約束しない。gramide が拒否したファイルはコンパイラにとっても
壊れている。それが構文ゲートが正しくなければならない向きであり、下の oracle が検証する向き。

## 検証したこと

TypeScript コンパイラの 5.9.3 タグの `src/` 配下の全 `.ts` と、コンパイラが配布する
`.d.ts` を、このパッケージとコンパイラ自身のパーサの両方に通し、答えを比較した。
ファイルがパースできるか、そして各宣言の種別・名前・所有者・行範囲・バイト範囲。

| コーパス | ファイル | バイト | 結果 |
|---|---:|---:|---|
| TypeScript 5.9.3 `src/` | 701 | 20.6 MB | 全件パース。48,691 宣言すべてが参照と一致 |
| TypeScript 5.9.3 `lib/*.d.ts` | 102 | 3.7 MB | 全件パース。26,413 宣言すべてが参照と一致 |

([証拠](docs/evidence/corpus-typescript-src.json)、
[証拠](docs/evidence/corpus-typescript-lib-dts.json))。ここでの宣言とは、JavaScript
パッケージが列挙するものすべてに加え、interface・型エイリアス・enum・namespace、メソッドと
プロパティのシグネチャ、そして namespace の中の名前を namespace で修飾したもの
(`ts.Parser.parse`)。コンパイラ `src/` へのバッチ `check` は 8 コアで約 340 MB/s。

CI が回す fixture は [ci/README.md](ci/README.md) に。

## 作り

- **`src/lexer.almd`** — JavaScript のスキャナに `>` を 1 トークンずつ読ませたもの。
  `Array<Array<T>>` が 2 つの括弧を閉じられるように。シフト演算子と比較演算子は文法が
  つなぎ直し、トークンが隣接しているかは確認しない。型構文がスキャナに強いる規則が
  あと 2 つ、同じスイッチの下で JavaScript パッケージに置いてある。オペランドの後の `>` は
  オペランドの終わり(`Promise<void>` は名前と同じように行を終える)、そして `[key: T]` や
  `(x: T)` の前の改行はオブジェクト型のメンバーを区切る(JavaScript ならインデックスや
  呼び出しと読むところ)。
- **`src/types.almd`** — 型の文法。条件型から参照まで。
- **`src/grammar.almd`** — JavaScript の拡張点をすべて埋め、分割した `>` の周りで比較と
  シフトの段を組み直し、TypeScript が足す宣言を追加する。`js.with_overrides` が各規則を
  置き換える JavaScript の名前の下に置くので、2 つの文法は 2 つのテーブルを持つ 1 つの文法。
- **`src/symbols.almd`** — JavaScript の規則に interface・型エイリアス・enum・namespace を
  加えたもの。namespace は中身を修飾し、ambient module と global 拡張は修飾しない。
- **`src/table.almd`** — `gen-table` が生成。古ければ CI が落ちる。

## 検証

`bash ci/check.sh` には Almide、Node 22、oracle のための `cd ci && npm ci` が要る。
`almide test`、テーブル検査、バイナリのスモークテスト、fixture を回す。

## ライセンス

MIT または Apache-2.0。
