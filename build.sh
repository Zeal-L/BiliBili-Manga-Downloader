#!/bin/bash

echo -e "\033[32m\n 项目构建开始 ... \n\033[0m"

echo -e "\033[34m\n 显示现有的依赖包 ... \n\033[0m"
pipenv run pipenv graph

echo -e "\033[34m\n 检查PyUp Safety的安全漏洞 ... \n\033[0m"
pipenv run pipenv check

echo -e "\033[34m\n 是否继续？(y/n) \n\033[0m"
read -r isContinue
if [ "$isContinue" != "y" ]; then
    exit 0
fi

echo -e "\033[34m\n 验证Pipfile.lock中的哈希值是最新的 ... \n\033[0m"
pipenv run pipenv verify

echo -e "\033[34m\n 更新lock文件锁定的依赖版本 ... \n\033[0m"
pipenv run pipenv update

echo -e "\033[34m\n pyinstaller 封装中 ... \n\033[0m"
pipenv run pyinstaller app.spec

echo -e "\033[34m\n pyinstaller 移动可执行文件到根目录 ... \n\033[0m"
cp -r dist/* ./
rm -rf dist
rm -rf build

echo -e "\033[32m\n 项目构建完成 ... \n\033[0m"

