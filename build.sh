#!/bin/bash

echo -e "\033[32m\n 项目构建开始 ... \n\033[0m"

echo -e "\033[34m\n 显示现有的依赖包 ... \n\033[0m"
poetry show

echo -e "\033[34m\n 更新现有的依赖包 ... \n\033[0m"
poetry update

echo -e "\033[34m\n pyinstaller 封装中 ... \n\033[0m"
if [[ "$OSTYPE" == "darwin"* ]]; then
    yes | poetry run pyinstaller macos.spec
else
    yes | poetry run pyinstaller windows.spec
fi

echo -e "\033[34m\n pyinstaller 移动可执行文件到根目录 ... \n\033[0m"
cp -r dist/* ./
rm -rf dist
rm -rf build
rm -rf output

echo -e "\033[32m\n 项目构建完成 ... \n\033[0m"

