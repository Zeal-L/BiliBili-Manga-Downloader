#!/bin/bash

echo -e "\033[32m\n 项目部署开始 ... \n\033[0m"

echo -e "\033[34m\n 安装pipenv（如果还没有安装）... \n\033[0m"
pip3 install pipenv

echo -e "\033[34m\n 安装所有依赖项 ... \n\033[0m"
pipenv install --dev

echo -e "\033[34m\n 重新编译UI文件 ... \n\033[0m"
pyside6-rcc src/ui/resource.qrc -o src/ui/resource_rc.py
pyside6-uic src/ui/mainWidget.ui -o src/ui/ui_mainWidget.py
pyside6-uic src/ui/myAbout.ui -o src/ui/ui_myAbout.py

echo -e "\033[34m\n 修复UI文件中的导入问题 ... \n\033[0m"
sed -i 's/resource_rc/src.ui.resource_rc/' src/ui/ui_mainWidget.py
sed -i 's/resource_rc/src.ui.resource_rc/' src/ui/ui_myAbout.py

echo -e "\033[34m\n 显示项目目录 ... \n\033[0m"
pipenv --where

echo -e "\033[34m\n 显示虚拟环境目录 ... \n\033[0m"
pipenv --venv

echo -e "\033[32m\n 项目部署完成！(输入 pipenv shell 进入虚拟环境) \n\033[0m"

