# onehub_prices

本项目管理多个 AI 供应商的价格信息，支持自动获取和手动维护多种来源的价格数据。包含以下价格表：

1. **oneapi_prices.json**: 适用于 one-hub 的完整价格表，包含所有供应商
2. **siliconflow_prices.json**: 来自 siliconflow 官方的原始价格数据
3. **onehub_only_prices.json**: 仅包含供应商 id <= 1000 的核心供应商价格表

所有价格数据每日自动更新，确保信息及时准确。

项目维护者：[Oaklight](https://github.com/Oaklight)

```bash
SILICONFLOW_API_KEY="sk-xxxxx" python get_prices.py
python merge_prices.py
```

## 主要文件说明

- `siliconflow_models.json`: 来自 siliconflow 官方的原始模型数据
- `oneapi_prices.json`: 适用于 one-hub 的完整价格表
- `siliconflow_prices.json`: 来自 siliconflow 官方的原始价格数据
- `onehub_only_prices.json`: 仅包含供应商 id <= 1000 的核心供应商价格表
- `manual_prices.yaml`: 手工维护的价格表
- `manual_prices/`目录: 包含各供应商的独立价格文件，包括：
  - 阿里云百炼
  - 零一万物
  - 字节火山引擎
  - Baidu
  - Deepseek
  - Google Gemini
  - MiniMax
  - Moonshot
  - OpenRouter
  - Pollinations.AI
  - Zhipu
  - 等

## 使用说明

根据不同的使用场景选择相应的价格表：

1. **完整价格表** (oneapi_prices.json)
   - 包含所有供应商的价格信息
   - 适用于需要完整价格数据的场景
   - 地址: 
     - GitHub Pages: [`https://oaklight.github.io/onehub_prices/oneapi_prices.json`](https://oaklight.github.io/onehub_prices/oneapi_prices.json)
     - Raw GitHub: [`https://raw.githubusercontent.com/Oaklight/onehub_prices/main/oneapi_prices.json`](https://raw.githubusercontent.com/Oaklight/onehub_prices/main/oneapi_prices.json)

2. **核心供应商价格表** (onehub_only_prices.json)
   - 仅包含供应商 id <= 1000 的核心供应商
   - 适用于只需要核心供应商价格的场景
   - 地址:
     - GitHub Pages: [`https://oaklight.github.io/onehub_prices/onehub_only_prices.json`](https://oaklight.github.io/onehub_prices/onehub_only_prices.json)
     - Raw GitHub: [`https://raw.githubusercontent.com/Oaklight/onehub_prices/main/onehub_only_prices.json`](https://raw.githubusercontent.com/Oaklight/onehub_prices/main/onehub_only_prices.json)

3. **Siliconflow 原始价格表** (siliconflow_prices.json)
   - 来自 Siliconflow 官方的原始价格数据
   - 适用于需要原始价格数据的场景
   - 地址:
     - GitHub Pages: [`https://oaklight.github.io/onehub_prices/siliconflow_prices.json`](https://oaklight.github.io/onehub_prices/siliconflow_prices.json)
     - Raw GitHub: [`https://raw.githubusercontent.com/Oaklight/onehub_prices/main/siliconflow_prices.json`](https://raw.githubusercontent.com/Oaklight/onehub_prices/main/siliconflow_prices.json)

**使用步骤**：
1. 进入`运营 -> 模型价格 -> 更新价格`
2. 根据需求选择上述价格表地址填入
3. 点击`获取数据`
4. 按需选择`覆盖数据`或`仅添加新增`

**重要提示**：
- 使用任何价格表前，请务必检查[ownedby.json](https://oaklight.github.io/onehub_prices/ownedby.json)以确保供应商 ID 与本项目版本一致
- 如需使用除了 onehub 默认定义的供应商之外的价格，请确保你的`模型归属`页面与 ownedby.json 中的定义一致

## 更新说明

从提交 6bcde110295e7d0a4bca69a0ec6c9381318f1e0d 之后的更新包括：

1. **手工设置的价格表**：新增了一个手工设置的价格表 `manual_prices.yaml`，其中包含多个供应商的手动设置价格。
2. **合并价格表**：新增了 `merge_prices.py` 脚本，用于合并上游的价格表。合并逻辑如下：
   - 以 siliconflow 自动查询的价格为更新
   - 手工价格作为主要价格（出现冲突时以手工表为准）
3. **GitHub Workflow**：配置了 GitHub Action `.github/workflows/run_get_prices.yml`，内容如下：
   - 每天 UTC 时间 00:00 执行，或者在 master 分支有推送时触发。
   - 运行 `get_prices.py` 和 `merge_prices.py` 脚本。
   - 自动提交并推送更新后的价格文件。
