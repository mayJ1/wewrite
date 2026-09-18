# WeWrite Windows Distribution

## User Package

The distributable package is:

`dist/WeWrite-Windows-x64.zip`

Users unzip it and double-click `Start-WeWrite.bat` or `WeWrite.exe`. They do not
need Python, Node.js, Git, Codex, or the original skill directory.

The first run creates a `data/` directory beside `WeWrite.exe`. This directory
contains credentials, account style, imported exemplars, uploads, and draft
history. It also stores edit-learning rules synced from user-modified WeChat
drafts. Keep `data/` when upgrading to a newer version.

## Build

Run from PowerShell:

```powershell
.\build_windows.ps1
```

The script creates an isolated `.build-venv`, installs packaging dependencies,
builds the PyInstaller onedir application, and creates the ZIP package.

Use this after the first successful dependency installation to rebuild faster:

```powershell
.\build_windows.ps1 -SkipInstall
```

## Distribution Safety

The package intentionally excludes:

- `config.yaml`
- `style.yaml`
- `output/`
- the developer exemplar library
- Node.js and `node_modules/`
- existing user credentials and draft history

The executable is currently unsigned. Windows SmartScreen may show an
"unrecognized app" warning on other computers. A commercial release should use
an Authenticode code-signing certificate.
