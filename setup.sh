#!/bin/bash
set -e

PYTHON="${PYTHON:-python3.13}"

echo -e "\033[32m\n 项目部署开始，使用系统 Python 3.13 ... \n\033[0m"
"$PYTHON" -c 'import sys; assert sys.version_info >= (3, 13), "必须使用系统 Python 3.13 或更高版本"'

echo -e "\033[34m\n 安装poetry（如果还没有安装）... \n\033[0m"
"$PYTHON" -m pip install --user poetry

echo -e "\033[34m\n 安装所有依赖项到当前系统解释器，不创建虚拟环境 ... \n\033[0m"
POETRY_VIRTUALENVS_CREATE=false "$PYTHON" -m poetry install --no-root

echo -e "\033[34m\n 重新编译UI文件 ... \n\033[0m"
"$PYTHON" -m poetry run pyside6-rcc src/ui/PySide_src/resource.qrc -o src/ui/PySide_src/resource_rc.py
"$PYTHON" -m poetry run pyside6-uic src/ui/PySide_src/mainWindow.ui -o src/ui/PySide_src/mainWindow_ui.py
"$PYTHON" -m poetry run pyside6-uic src/ui/PySide_src/myAbout.ui -o src/ui/PySide_src/myAbout_ui.py
"$PYTHON" -m poetry run pyside6-uic src/ui/PySide_src/qrCode.ui -o src/ui/PySide_src/qrCode_ui.py

echo -e "\033[34m\n 修复UI文件中的导入问题 ... \n\033[0m"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    SED_INPLACE=(-i '')
else
    # 其他环境，假设使用 GNU sed
    SED_INPLACE=(-i)
fi

sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/mainWindow_ui.py
sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/myAbout_ui.py
sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/qrCode_ui.py


echo -e "\033[34m\n 显示当前解释器信息 ... \n\033[0m"
"$PYTHON" -c 'import sys; print(sys.executable); print(sys.version)'

echo -e "\033[32m\n 项目部署完成！使用同一系统 Python 3.13 运行 app.py。 \n\033[0m"

