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

`.ts` `.mts` `.cts` を、そして第二の定義として `.tsx` を、TypeScript 5.9 として読む。
[gramide-javascript](https://github.com/O6lvl4/gramide-javascript) が読むものすべてに加え、
型注釈、制約・既定値・変性付きのジェネリクス、interface、型エイリアス、enum、namespace と
ambient module、`declare`、`abstract`、アクセス修飾子と `readonly`、パラメータプロパティ、
オーバーロード、インデックスシグネチャ、`import type` / `export type`、`import x = require()`、
`export =`、デコレータ、`as`、`satisfies`、`!` アサーション、`<T>x` アサーション。型の側では
union・intersection、条件型・mapped 型、`infer`、`keyof` / `typeof` / `unique symbol`、名前と
rest 付きのタプル、関数型とコンストラクタ型、テンプレートリテラル型、`import("m").T`、
型述語。`.tsx` は同じ文法で、式が立てる位置に JSX を許し `<T>x` アサーションを外して読む。
コンパイラがそうするのと同じ。タグは型引数を持てる(`<Select<string[]> multiple>`)。

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
| MUI `docs/data/{material,joy}/components/**/*.tsx`(`053c4319`) | 538 | 1.0 MB | 全件パース。1,378 宣言すべてが参照と一致 |
| Excalidraw `packages/excalidraw/**/*.tsx`(`a9186480`) | 261 | 2.6 MB | 全件パース。2,848 宣言すべてが参照と一致 |
| Excalidraw `packages/excalidraw/**/*.ts`(`a9186480`) | 187 | 3.1 MB | 全件パース。3,264 宣言すべてが参照と一致 |

同じファイルを `tags` にも通し、参照をすべて、コンパイラのパーサの上の第二の oracle
([規則](ci/reference_tags.mjs))と比較した:

| コーパス | 参照 | 結果 |
|---|---:|---|
| TypeScript 5.9.3 `src/` | 175,408 | すべて一致([証拠](docs/evidence/tags-typescript-src.json)) |
| TypeScript 5.9.3 `lib/*.d.ts` | 27,369 | すべて一致([証拠](docs/evidence/tags-typescript-lib-dts.json)) |
| MUI docs `.tsx` | 2,932 | すべて一致([証拠](docs/evidence/tags-mui-docs-tsx.json)) |
| Excalidraw `.tsx` | 29,074 | すべて一致([証拠](docs/evidence/tags-excalidraw-tsx.json)) |
| Excalidraw `.ts` | 12,175 | すべて一致([証拠](docs/evidence/tags-excalidraw-ts.json)) |

参照とは、名前の呼び出し(`f(…)`、`a.b(…)`、`new Map<K, V>(…)`、適用されたデコレータ。
non-null の `!` は無いものとして読む)と、型への言及(注釈、型引数、`as` / `satisfies` / `<T>x`、
`keyof T`、`implements` と `extends` 節、修飾名はその先頭の区切り)。意図して参照にしないもの
(キーワード型、`as const`、`typeof x`、JSX のタグ名、import)は
[ci/tags_cases.py](ci/tags_cases.py) に列挙してある。

([証拠](docs/evidence/corpus-typescript-src.json)、
[証拠](docs/evidence/corpus-typescript-lib-dts.json)、
[証拠](docs/evidence/corpus-mui-docs-tsx.json)、
[証拠](docs/evidence/corpus-excalidraw-tsx.json)、
[証拠](docs/evidence/corpus-excalidraw-ts.json))。ここでの宣言とは、JavaScript
パッケージが列挙するものすべてに加え、interface・型エイリアス・enum・namespace、メソッドと
プロパティのシグネチャ、そして namespace の中の名前を namespace で修飾したもの
(`ts.Parser.parse`)。コンパイラ `src/` へのバッチ `check` は 8 コアで約 340 MB/s。

CI が回す fixture は [ci/README.md](ci/README.md) に。

## tree-sitter との比較

tree-sitter-typescript(`75b3874`)を tree-sitter ランタイム(`1b8407d`)の上で
[bench/tree_sitter_ranges.c](bench/tree_sitter_ranges.c) から呼び、ファイルごとに新しい
プロセスで、パースの合否と宣言の一覧を、両者交互に、3 回の最小値で計測
([証拠](docs/evidence/tree-sitter-typescript-src.json)、方法は
[bench/tree_sitter.py](bench/tree_sitter.py))。

| TypeScript 5.9.3 `src/`、701 ファイル、20.6 MB | gramide | tree-sitter |
|---|---:|---:|
| パースの合否、全ファイルの合計 | 1.676 秒 | 1.837 秒 |
| 宣言の一覧、全ファイルの合計 | 1.986 秒 | 2.054 秒 |
| 200 KB 以上の 16 ファイル(7.9 MB)、合否 | 0.151 秒 | 0.305 秒 |
| その 16 ファイル、一覧 | 0.277 秒 | 0.398 秒 |
| `compiler/checker.ts`(3.1 MB)、合否 | 47 ms | 101 ms |
| 空ファイル(プロセスの床) | 1.75 ms | 1.37 ms |

合計ではほぼプロセスの床の勝負で 1 割速く、パースが費用になるファイルでは 2 倍速い。
tree-sitter はこのうち 4 ファイル(`compiler/types.ts`、`compiler/transformers/utilities.ts`、
`services/exportInfoMap.ts`、`lib/es2015.symbol.wellknown.d.ts`)に構文エラーを報告するが、
コンパイラもこのパッケージも受理する。gramide の一覧はフィールド・束縛・namespace・
全メソッドの所有者を含む(48,691 行に対して 19,300 行)ので、一覧の行は多い仕事と
少ない仕事の比較になっている。

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
- **`src/table.almd`** と **`src/table_tsx.almd`** — `gen-table` と `gen-table-tsx` が生成。
  どちらかが古ければ CI が落ちる。

## 検証

`bash ci/check.sh` には Almide、Node 22、oracle のための `cd ci && npm ci` が要る。
`almide test`、テーブル検査、バイナリのスモークテスト、fixture を回す。

## ライセンス

MIT または Apache-2.0。
