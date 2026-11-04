#!/bin/bash
set -e

PYTHON="${PYTHON:-python3.13}"
export POETRY_VIRTUALENVS_CREATE=false

echo -e "\033[32m\n 项目构建开始，使用系统 Python 3.13 ... \n\033[0m"

echo -e "\033[34m\n 显示现有的依赖包 ... \n\033[0m"
"$PYTHON" -m poetry show

echo -e "\033[34m\n 更新现有的依赖包 ... \n\033[0m"
"$PYTHON" -m poetry update

echo -e "\033[34m\n pyinstaller 封装中 ... \n\033[0m"
if [[ "$OSTYPE" == "darwin"* ]]; then
    yes | "$PYTHON" -m poetry run pyinstaller macos.spec
else
    yes | "$PYTHON" -m poetry run pyinstaller windows.spec
fi

echo -e "\033[34m\n pyinstaller 移动可执行文件到根目录 ... \n\033[0m"
cp -r dist/* ./
rm -rf dist
rm -rf build
rm -rf output

echo -e "\033[32m\n 项目构建完成 ... \n\033[0m"

