#!/bin/bash

# 文件名: rpmbuild.sh
# 作者: wanghongwei
# 日期: 2025年3月22日
# 版本: 1.0
# 描述: 使用 rpmbuild 编译 rpm 包一键式脚本
# 使用方式:./rpmbuild.sh <仓库URL> <分支名称>, 如:./rpmbuild.sh https://github.com/wanghongwei-dev/example.git main

set -e

# 一次性初始化
# yum install -y git rpm-build rpmdevtools yum-utils dnf-plugins-core
# rpmdev-setuptree

# 检查参数数量
if [ $# -lt 2 ]; then
    echo "错误：需要传入两个参数，分别为仓库URL和分支名称"
    echo "用法：$0 <仓库URL> <分支名称>"
    exit 1
fi

# 获取命令行参数
REPO_URL="$1"          # 仓库URL（参数1）
BRANCH_NAME="$2"       # 分支名称（参数2）
SPEC_PATTERN="*.spec"  # spec文件匹配模式

# 定义目录路径
WORK_DIR=$(mktemp -d)                       # 创建临时工作目录
RPMBUILD_HOME="$HOME/rpmbuild"              # rpmbuild工作目录
RPMBUILD_SPECS="$RPMBUILD_HOME/SPECS/"      # spec文件目录
RPMBUILD_SOURCES="$RPMBUILD_HOME/SOURCES/"  # source文件目录
RPMBUILD_RPMS="$RPMBUILD_HOME/RPMS/"        # rpm文件目录

# 1. 克隆代码仓库
echo "开始克隆代码仓库... 仓库URL: $REPO_URL, 分支: $BRANCH_NAME"
git clone -b "$BRANCH_NAME" "$REPO_URL" "$WORK_DIR" || {
    echo "错误：代码克隆失败"
    exit 1
}
echo "代码仓库克隆完成，存储在临时目录：$WORK_DIR"
cd "$WORK_DIR"

# 2. 查找spec文件
echo "查找spec文件... 匹配模式：$SPEC_PATTERN"
SPEC_FILE=$(find . -type f -name "$SPEC_PATTERN" | head -n 1)
if [ -z "$SPEC_FILE" ]; then
    echo "错误：未找到匹配的spec文件（$SPEC_PATTERN）"
    exit 1
fi
echo "找到spec文件：$SPEC_FILE"

# 3. 使用spectool下载源文件
echo "开始使用spectool下载源文件..."
spectool -g "$SPEC_FILE" || {
    echo "错误：spectool下载源文件失败"
    exit 1
}

# 4. 复制文件到RPM构建目录
echo "开始复制spec文件到 $RPMBUILD_SPECS 目录"
cp "$SPEC_FILE" "$RPMBUILD_SPECS" || {
    echo "错误：spec文件复制失败"
    exit 1
}

echo "开始复制源码文件到 $RPMBUILD_SOURCES 目录"
find . -type f ! -name "$(basename "$SPEC_FILE")" -exec cp {} "$RPMBUILD_SOURCES" \; || {
    echo "错误：源码文件复制失败"
    exit 1
}

# 5. 安装依赖
echo "安装构建依赖..."
SPEC_PATH="$RPMBUILD_SPECS/$(basename "$SPEC_FILE")"
yum-builddep -y "$SPEC_PATH" || {
    echo "错误：依赖安装失败"
    exit 1
}

# 6. 编译生成RPM包
echo "开始编译RPM包..."
rpmbuild -bb "$SPEC_PATH" || {
    echo "错误：RPM编译失败"
    exit 1
}
echo "RPM构建完成，结果位于 $RPMBUILD_RPMS"

# 7. 清理临时目录
rpmbuild --clean "$SPEC_PATH"
rm -rf "$WORK_DIR"
