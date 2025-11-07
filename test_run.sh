#!/bin/bash

# 定义红色文本输出函数
print_red() {
    echo -e "\033[31m$1\033[0m"
}

# 定义检查命令执行结果的函数
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo "执行: $description"
    $cmd
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        print_red "错误: $description 执行失败 (退出码: $exit_code)"
        exit $exit_code
    fi
    echo "$description 执行成功"
    echo "----------------------------------------"
}

# 运行 get_ownedby.py
run_command "python src/get_ownedby.py" "获取 ownedby 价格数据"

# 运行 sync_ownedby.py
run_command "python src/sync_ownedby.py --source_json ownedby.json --manual_json ownedby_manual.json" "同步 ownedby 数据"

# 运行 get_siliconflow_prices.py
run_command "python src/get_siliconflow_prices.py" "获取 Siliconflow 价格数据"

# 运行 get_openrouter_prices.py
run_command "python src/get_openrouter_prices.py" "获取 OpenRouter 价格数据"

# 运行 merge_prices.py
run_command "python src/merge_prices.py" "合并价格数据"

# 运行 sync_pricing.py
run_command "python src/sync_pricing.py" "同步定价数据"

echo "所有步骤执行完成！"