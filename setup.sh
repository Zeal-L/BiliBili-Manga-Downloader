#!/bin/bash

echo -e "\033[32m\n 项目部署开始 ... \n\033[0m"

echo -e "\033[34m\n 安装pipenv（如果还没有安装）... \n\033[0m"
pip3 install pipenv

echo -e "\033[34m\n 安装所有依赖项 ... \n\033[0m"
pipenv run pipenv install --dev

echo -e "\033[34m\n 重新编译UI文件 ... \n\033[0m"
pipenv run pyside6-rcc src/ui/PySide_src/resource.qrc -o src/ui/PySide_src/resource_rc.py
pipenv run pyside6-uic src/ui/PySide_src/mainWindow.ui -o src/ui/PySide_src/mainWindow_ui.py
pipenv run pyside6-uic src/ui/PySide_src/myAbout.ui -o src/ui/PySide_src/myAbout_ui.py

echo -e "\033[34m\n 修复UI文件中的导入问题 ... \n\033[0m"
sed -i 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/mainWindow_ui.py
sed -i 's/resource_rc/src.ui.PySide_src.resource_rc/' src/ui/PySide_src/myAbout_ui.py

echo -e "\033[34m\n 显示项目目录 ... \n\033[0m"
pipenv run pipenv --where

echo -e "\033[34m\n 显示虚拟环境目录 ... \n\033[0m"
pipenv run pipenv --venv

echo -e "\033[32m\n 项目部署完成！(输入 pipenv shell 进入虚拟环境) \n\033[0m"

