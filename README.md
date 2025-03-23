# onehub_prices

本项目最初为 onehub 提供 siliconflow 价格数据，现已扩展为管理多个 AI 供应商的价格信息。所有价格数据每日自动更新，确保信息及时准确。

项目维护者：[Oaklight](https://github.com/Oaklight)

管理多个 AI 供应商的价格信息，支持自动获取和手动维护多种来源的价格数据。

```bash
SILICONFLOW_API_KEY="sk-xxxxx" python get_prices.py
python merge_prices.py
```

## 主要文件说明

- `siliconflow_models.json`: 来自 siliconflow 官方的原始模型数据
- `oneapi_prices.json`: 适用于 one-hub 的最终价格表
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

对于 one-hub 使用：

1. 进入`运营 -> 模型价格 -> 更新价格`
2. 填入 [`https://oaklight.github.io/onehub_prices/oneapi_prices.json`](https://oaklight.github.io/onehub_prices/oneapi_prices.json)
3. 点击`获取数据`
4. 按需选择`覆盖数据`或`仅添加新增`

**注意**：如需使用除了onehub默认定义的供应商之外的价格，则需关注你的`模型归属`页面，确保与自定义的供应商id与本项目的版本一致：见[ownedby.json](https://oaklight.github.io/onehub_prices/ownedby.json)


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
