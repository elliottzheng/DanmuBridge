# Release Guide

This document is for maintainers who need to build and publish `danmubridge` to PyPI.

## Update The Version

Edit `pyproject.toml` and bump the `version` field before creating a release.

## Clean Old Artifacts

PowerShell:

```powershell
Remove-Item -Recurse -Force .\dist, .\build, .\src\danmubridge.egg-info -ErrorAction SilentlyContinue
```

Bash:

```bash
rm -rf dist build src/danmubridge.egg-info
```

## Build

Install the packaging tools and build from the repository root:

```bash
python -m pip install --upgrade build twine
python -m build
```

The generated files will be placed under `dist/`.

## Upload

Upload to TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

Upload to PyPI:

```bash
python -m twine upload dist/*
```

Using an API token is recommended:

PowerShell:

```powershell
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-your-token"
python -m twine upload dist/*
```

Bash:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token
python -m twine upload dist/*
```
