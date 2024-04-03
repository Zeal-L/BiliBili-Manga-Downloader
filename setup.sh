#!/bin/bash

echo -e "\033[32m\n 项目部署开始 ... \n\033[0m"

echo -e "\033[34m\n 安装poetry（如果还没有安装）... \n\033[0m"
pip3 install poetry

echo -e "\033[34m\n 安装所有依赖项 ... \n\033[0m"
poetry install --no-root

echo -e "\033[34m\n 重新编译UI文件 ... \n\033[0m"
poetry run pyside6-rcc src/ui/PySide_src/resource.qrc -o src/ui/PySide_src/resource_rc.py
poetry run pyside6-uic src/ui/PySide_src/mainWindow.ui -o src/ui/PySide_src/mainWindow_ui.py
poetry run pyside6-uic src/ui/PySide_src/mainWindow_mac.ui -o src/ui/PySide_src/mainWindow_mac_ui.py
poetry run pyside6-uic src/ui/PySide_src/myAbout.ui -o src/ui/PySide_src/myAbout_ui.py
poetry run pyside6-uic src/ui/PySide_src/qrCode.ui -o src/ui/PySide_src/qrCode_ui.py

echo -e "\033[34m\n 修复UI文件中的导入问题 ... \n\033[0m"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    SED_INPLACE=(-i '')
else
    # 其他环境，假设使用 GNU sed
    SED_INPLACE=(-i)
fi

sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/mainWindow_ui.py
sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/mainWindow_mac_ui.py
sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/myAbout_ui.py
sed "${SED_INPLACE[@]}" 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/qrCode_ui.py


echo -e "\033[34m\n 显示虚拟环境相关信息 ... \n\033[0m"
poetry debug info

echo -e "\033[32m\n 项目部署完成！(输入 poetry shell 进入虚拟环境) \n\033[0m"

