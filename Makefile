.PHONY: install dev server generate test lint clean help

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

help: ## 显示帮助信息
	@echo "$(CYAN)Model Forge - 3D模型生成工具$(RESET)"
	@echo ""
	@echo "$(GREEN)可用命令:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'

install: ## 安装依赖
	@echo "$(CYAN)安装依赖...$(RESET)"
	pip install -e .
	@echo "$(GREEN)✅ 安装完成$(RESET)"
	@echo ""
	@echo "$(YELLOW)请确保已配置 .env 文件:$(RESET)"
	@echo "  cp .env.example .env"
	@echo "  # 编辑 .env 填入 API Key"

install-dev: ## 安装开发依赖
	pip install -e ".[dev]"

dev: ## 开发模式启动服务 (热重载)
	@echo "$(CYAN)启动开发服务...$(RESET)"
	model-forge server --reload

server: ## 生产模式启动服务
	@echo "$(CYAN)启动服务...$(RESET)"
	model-forge server

generate: ## 交互式生成3D模型
	@echo "$(CYAN)3D模型生成向导$(RESET)"
	@echo ""
	@read -p "设备描述: " desc; \
	read -p "设备类型 (可选): " type; \
	read -p "电压等级 (可选): " voltage; \
	read -p "模型精度 [high/medium/low] (默认 medium): " quality; \
	quality=$${quality:-medium}; \
	if [ -n "$$type" ]; then type_arg="--type \"$$type\""; fi; \
	if [ -n "$$voltage" ]; then voltage_arg="--voltage \"$$voltage\""; fi; \
	model-forge generate "$$desc" $$type_arg $$voltage_arg --quality $$quality

generate-demo: ## 生成演示模型 (220kV变压器)
	@echo "$(CYAN)生成演示模型...$(RESET)"
	model-forge generate "一台220kV的油浸式电力变压器，带散热翅片和高压套管" \
		--type 变压器 \
		--voltage 220kV \
		--quality high

list: ## 列出历史任务
	model-forge list

test: ## 运行测试
	pytest tests/ -v

lint: ## 代码检查
	ruff check model_forge/
	black --check model_forge/

format: ## 代码格式化
	black model_forge/
	ruff check --fix model_forge/

clean: ## 清理输出文件
	@echo "$(YELLOW)清理输出目录...$(RESET)"
	rm -rf output/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ 清理完成$(RESET)"

check-env: ## 检查环境配置
	@echo "$(CYAN)检查环境配置...$(RESET)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✅ .env 文件存在$(RESET)"; \
		if grep -q "GEMINI_API_KEY=your-" .env 2>/dev/null; then \
			echo "$(YELLOW)⚠️  请配置 GEMINI_API_KEY$(RESET)"; \
		else \
			echo "$(GREEN)✅ GEMINI_API_KEY 已配置$(RESET)"; \
		fi; \
		if grep -q "ARK_API_KEY=your-" .env 2>/dev/null; then \
			echo "$(YELLOW)⚠️  请配置 ARK_API_KEY$(RESET)"; \
		else \
			echo "$(GREEN)✅ ARK_API_KEY 已配置$(RESET)"; \
		fi; \
	else \
		echo "$(YELLOW)⚠️  .env 文件不存在，请运行:$(RESET)"; \
		echo "    cp .env.example .env"; \
	fi

# 快捷别名
s: server
d: dev
g: generate
l: list
