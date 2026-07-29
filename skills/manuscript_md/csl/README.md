# Bundled citation styles (CSL)

論文 docx ビルドで使う citation style を同梱しています。`task paper:docx` または pandoc の `--csl` / `PAPER_CSL` で指定します。

| ファイル | 用途（目安） |
|----------|----------------|
| `vancouver.csl` | 数字引用（既定） |
| `vancouver-superscript.csl` | Vancouver 上付き |
| `bmj.csl` | BMJ |
| `gie.csl` | GIE |
| `clinical-gastroenterology-and-hepatology.csl` | CGH（Clinical Gastroenterology and Hepatology） |
| `endoscopy.csl` | Endoscopy |
| `den.csl` | DEN |
| `jg.csl` | Journal of Gastroenterology |
| `thieme-german.csl` | Thieme（ドイツ語） |

## 指定方法

```bash
task paper:docx PAPER_DIR=/path/to/paper PAPER_CSL=vancouver.csl

# 絶対パスも可
task paper:docx PAPER_DIR=/path/to/paper PAPER_CSL=/path/to/custom.csl

# 論文フォルダに同名 CSL を置くと bundled CSL より優先
cp /Users/mizuy/lab/manuscript_md/csl/vancouver.csl /path/to/paper/
```

一覧: `uv --directory /Users/mizuy/lab/manuscript_md run lab-paper resolve-csl --list`
