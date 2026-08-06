# Local Tool Manager

自作のPythonスクリプト、exe、bat/cmd、PATH上の任意コマンド、ブラウザURLを登録し、一覧から起動・停止するWindows向けGUIアプリです。ツールごとに実行ディレクトリ、引数、カテゴリ、説明、多重起動可否などを管理できます。

## 必要環境

- Windows 10/11
- Python 3.12以上

## インストールと起動

PowerShellで次を実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
local-tool-manager
```

モジュールとして起動する場合は次のコマンドも使用できます。

```powershell
python -m local_tool_manager.main
```

## Windows実行ファイルのビルド

Pythonをインストールしていない環境でも起動できる単一のGUI実行ファイルを、
PyInstallerで生成できます。

```powershell
python -m pip install -e ".[build]"
.\scripts\build_windows.ps1
```

生成先は次のとおりです。

```text
dist\LocalToolManager.exe
```

ビルド後、デスクトップへショートカットを作成できます。

```powershell
.\scripts\create_shortcut.ps1
```

ショートカットはリポジトリ内の `dist\LocalToolManager.exe` を参照します。
リポジトリを移動した場合は、上記スクリプトを再実行してください。

## 登録例

### Pythonツール

- 種類: `コマンド`
- 実行ディレクトリ: `C:\tools\sample`
- 実行コマンド: `C:\tools\sample\main.py`
- 引数: `--input "C:\input files\data.json"`

`.py`を直接指定すると、Local Tool Managerを実行しているPython環境で起動します。固有の仮想環境を使う場合は、実行コマンドにその環境の `python.exe`、引数に `main.py` 以降を指定してください。

実行ディレクトリを登録している場合、実行コマンドにはそのディレクトリを
基準とした相対パスも指定できます。

```text
実行ディレクトリ: C:\tools\sample
実行コマンド: scripts\main.py
```

### exe

- 種類: `コマンド`
- 実行ディレクトリ: `C:\tools\converter`
- 実行コマンド: `C:\tools\converter\converter.exe`
- 引数: `--format json`

### URL

- 種類: `URL`
- URL: `https://example.com/dashboard`

パラメータ付きURLでは `https://www.google.com/search?q={keyword}` のように登録します。実行時に表示される入力欄へ値を入れると、URLエンコードして既定ブラウザで開きます。複数パラメータや同じパラメータの複数箇所での利用にも対応します。

## 主な操作

- 実行タブ上部で、名前・説明・カテゴリの部分一致検索、カテゴリ・状態による絞り込みができます。
- 行のダブルクリック、または右クリックメニューから起動します。
- 行を選択して「編集」を押すと、登録内容を設定タブで編集できます。
- 検索・絞り込みを解除した状態では、行をドラッグして表示順を変更できます。
- コマンドは右クリックメニューから子プロセスを含めて停止できます。
- 編集と複製は設定タブへ内容を読み込みます。複製は保存するまでDBへ追加されません。
- 設定タブの「既存からコピー」では、登録済みツールを選んで未保存の新規データとして編集できます。
- 実行中のツールは削除できません。
- 設定フォームは種類に応じて、コマンド用またはURL用の入力欄だけを表示します。
- 未保存の変更がある状態で新規入力、入力クリア、別ツールの編集、タブ移動、
  またはアプリ終了を行うと、変更を破棄するか確認します。
- 設定タブの「実行チェック」では、保存前のコマンドを非同期で試行できます。
- 実行チェックの標準出力、標準エラー、終了コードは画面下部のターミナルへ表示します。

## 多重起動制御

「多重起動を許可」がオフの場合、このアプリから起動した最新プロセスのPIDとプロセス作成時刻を照合します。同じプロセスが実行中なら再起動しません。アプリ再起動後もPIDの存在と作成時刻を検証するため、終了済みPIDや再利用されたPIDを実行中とは扱いません。

停止時は子プロセスを含めて通常終了を要求し、一定時間後も残るプロセスだけを強制終了します。Local Tool Manager自体の終了時には起動済みツールを終了しません。

## データ保存先

DBとローテーションログは次へ保存します。ソースディレクトリには保存しません。

```text
%LOCALAPPDATA%\local_tool_manager\
├─ local_tool_manager.db
└─ local_tool_manager.log
```

## テスト

```powershell
pytest
```

## 現時点の制限事項

- URL起動後のブラウザプロセスは管理しません。
- 管理者権限が必要なプロセスの起動・停止には対応しません。
- スケジュール、ワークフロー、前後処理、タスクトレイ、ホットキー、インポート/エクスポートはMVP対象外です。
- 外部で起動された同じツールは多重起動判定の対象外です。
