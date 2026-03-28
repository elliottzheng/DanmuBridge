# 发布说明

这个文档面向维护者，用于构建并发布 `danmubridge` 到 PyPI。

## 更新版本号

发布前先修改 `pyproject.toml` 中的 `version` 字段。

## 清理旧产物

PowerShell：

```powershell
Remove-Item -Recurse -Force .\dist, .\build, .\src\danmubridge.egg-info -ErrorAction SilentlyContinue
```

Bash：

```bash
rm -rf dist build src/danmubridge.egg-info
```

## 构建

在仓库根目录安装打包工具并执行构建：

```bash
python -m pip install --upgrade build twine
python -m build
```

生成的分发文件会放在 `dist/` 目录下。

## 上传

上传到 TestPyPI：

```bash
python -m twine upload --repository testpypi dist/*
```

上传到正式 PyPI：

```bash
python -m twine upload dist/*
```

推荐使用 API Token。

PowerShell：

```powershell
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-你的token"
python -m twine upload dist/*
```

Bash：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-你的token
python -m twine upload dist/*
```
