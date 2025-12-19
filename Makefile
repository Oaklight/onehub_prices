# OneHub Prices Makefile

.PHONY: help new-provider test clean

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  make new-provider \"Provider Name\" [SERIES=1000|2000]  - 创建新的provider"
	@echo "    SERIES=1000: 公开provider (商业AI服务商)"
	@echo "    SERIES=2000: 私人/小众provider (自建或小众服务)"
	@echo "  make test                                              - 运行测试"
	@echo "  make clean                                             - 清理临时文件"

# 创建新provider
# 用法: make new-provider "Provider Name" [SERIES=1000|2000]
new-provider:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "错误: 请提供provider名称"; \
		echo "用法: make new-provider \"Provider Name\" [SERIES=1000|2000]"; \
		echo "示例: make new-provider \"新的AI提供商\""; \
		echo "示例: make new-provider \"新的AI提供商\" SERIES=1000"; \
		exit 1; \
	fi
	@if [ -n "$(SERIES)" ]; then \
		python3 scripts/new_provider.py "$(filter-out $@,$(MAKECMDGOALS))" --series $(SERIES); \
	else \
		python3 scripts/new_provider.py "$(filter-out $@,$(MAKECMDGOALS))"; \
	fi

# 运行测试
test:
	@echo "运行测试..."
	@if [ -f test_run.sh ]; then \
		bash test_run.sh; \
	else \
		echo "未找到test_run.sh文件"; \
	fi

# 清理临时文件
clean:
	@echo "清理临时文件..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "清理完成"

# 防止make将参数当作目标
%:
	@: