# WeWrite 便携桌面版

运行 `dist/portable/WeWrite.exe`，程序在独立桌面窗口中打开。
无需 BAT 或 Python 环境；Windows 需要 Microsoft Edge WebView2 Runtime。
本版未内嵌 WebView2 固定版运行时。

用户配置、素材和草稿保存在 EXE 同级的 `data` 目录。
升级时关闭程序，只替换 EXE，保留 data。旧免安装版用户可以将原有
data 文件夹复制到新 EXE 旁边。请将程序放在可写目录中。

本地模型不再内嵌。需要本地润色时，将原版 rewrite-engine 文件夹
放在 EXE 同级目录。小猫云端接口尚需单独接入和测试，目前请勿将
这个便携壳版本当作已经具备云端改写功能的商业版本。

源码启动：`.build-venv/Scripts/python.exe app/desktop.py`

构建：`./build_portable.ps1`，成功后仅需分发生成的 EXE。
首次启动会解压依赖到系统临时目录，耗时受磁盘和杀毒软件影响。
