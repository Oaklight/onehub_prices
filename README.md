# onehub_prices 🚀

[![Stars](https://img.shields.io/github/stars/Oaklight/onehub_prices?color=green)](https://github.com/Oaklight/onehub_prices/stargazers)
[![Last Commit](https://img.shields.io/github/last-commit/Oaklight/onehub_prices?color=green)](https://github.com/Oaklight/onehub_prices/commits/master)
[![License](https://img.shields.io/github/license/Oaklight/onehub_prices?color=green)](LICENSE)

## 🌟 新功能上线

**GitHub Pages 现已支持价格展示与搜索功能！访问 [https://oaklight.github.io/onehub_prices/](https://oaklight.github.io/onehub_prices/) 体验直观的价格对比和搜索** 🔍

## 📜 项目简介

本项目管理多个 AI 供应商的价格信息，支持自动获取和手动维护多种来源的价格数据。包含以下价格表：

1. **oneapi_prices.json**: 适用于 one-hub 的完整价格表，包含所有供应商
2. **onehub_only_prices.json**: 仅包含供应商 id <= 1000 的核心供应商价格表
3. **siliconflow_prices.json**: 来自 siliconflow 官方的原始价格数据
4. **openrouter_prices.json**: 来自 openrouter 官方的原始价格数据

所有价格数据每 6 小时自动更新，确保信息及时准确。为了保持整洁，目前的 JSON 格式的价格和 ownedby 更新结果均已迁移至 prices 分支。请关注价格表最末尾的更新时间提示图标。

项目维护者：[Oaklight](https://github.com/Oaklight)

## 目录

1. [主要文件说明](#主要文件说明)
2. [价格同步指导](#价格同步指导)
   - [通过 OneHub 运营界面更新](#通过-onehub-运营界面更新)
   - [通过 OneHub API 脚本更新](#通过-onehub-api-脚本更新-推荐)
3. [手工定价文件要求](#手工定价文件要求)

## 主要文件说明

**重要提示**：

- 价格表与供应商 JSON 结果均已迁移至**prices 分支**，使用前请注意更新 url 路径
- 使用任何价格表前，请务必检查[ownedby.json](https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/ownedby.json) ([jsDelivr CDN](https://cdn.jsdelivr.net/gh/Oaklight/onehub_prices@prices/ownedby.json)，[jsDelivr Mirror](https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@prices/ownedby.json)) 以确保供应商 ID 与本项目版本一致
- 如需使用除了 onehub 默认定义的供应商之外的价格，请确保你的`模型归属`页面与 ownedby.json 中的定义一致

根据不同的使用场景选择相应的价格表：

1. **完整价格表** (oneapi_prices.json)

   - 包含所有供应商的价格信息
   - 适用于需要完整价格数据的场景
   - 地址:
     - GitHub Raw: <https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/oneapi_prices.json>
     - jsDelivr CDN: <https://cdn.jsdelivr.net/gh/Oaklight/onehub_prices@prices/oneapi_prices.json>
     - jsDelivr Mirror: <https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@prices/oneapi_prices.json>

2. **核心供应商价格表** (onehub_only_prices.json)

   - 仅包含供应商 id <= 1000 的核心供应商
   - 适用于只需要核心供应商价格的场景
   - 地址:
     - GitHub Raw: <https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/onehub_only_prices.json>
     - jsDelivr CDN: <https://cdn.jsdelivr.net/gh/Oaklight/onehub_prices@prices/onehub_only_prices.json>
     - jsDelivr Mirror: <https://cdn.jsdmirror.com/npm/onehub_prices@prices/onehub_only_prices.json>

3. **Siliconflow 原始价格表** (siliconflow_prices.json)

   - 来自 Siliconflow 官方的原始价格数据
   - 适用于需要原始价格数据的场景
   - 地址:
     - GitHub Raw: <https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/siliconflow_prices.json>
     - jsDelivr CDN: <https://cdn.jsdelivr.net/gh/Oaklight/onehub_prices@prices/siliconflow_prices.json>
     - jsDelivr Mirror: <https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@prices/siliconflow_prices.json>

4. **OpenRouter 原始价格表** (openrouter_prices.json)
   - 来自 OpenRouter 官方的原始价格数据
   - 适用于需要原始价格数据的场景
   - 地址:
     - GitHub Raw: <https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/openrouter_prices.json>
     - jsDelivr CDN: <https://cdn.jsdelivr.net/gh/Oaklight/onehub_prices@prices/openrouter_prices.json>
     - jsDelivr Mirror: <https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@prices/openrouter_prices.json>

### 价格同步指导

#### 通过 OneHub 运营界面更新

**核对模型归属**：

1. 进入`运营 -> 模型归属`
2. 对比`ownedby.json`文件，手工增删查改模型归属信息

**更新模型价格**：

1. 进入`运营 -> 模型价格 -> 更新价格`
2. 根据需求选择上述价格表地址填入
3. 点击`获取数据`
4. 按需选择`覆盖数据`或`仅添加新增`

#### 通过 OneHub API 脚本更新 (推荐)

[`sync_pricing.py`](src/sync_pricing.py) 是一个用于同步价格数据的脚本。可选择 json 文件或 url 地址作为数据源。

#### 使用步骤

1. 确保已安装依赖项：

   ```bash
   pip install -r requirements.txt
   ```

2. 运行脚本以同步 ownedby 数据：

   ```bash
   python src/sync_ownedby.py [--source_json SOURCE_JSON] [--source_url SOURCE_URL] [--manual_json MANUAL_JSON] [--manual_url MANUAL_URL]
   ```

   示例：

   ```bash
   python src/sync_ownedby.py --source_json=ownedby.json --manual_url=https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@master/ownedby_manual.json
   ```

   如果未指定 `--json_file` 或 `--json_url` 参数，脚本将默认加载 `./ownedby.json`。

3. 检查生成的 ownedby 表文件是否更新成功。

4. 运行脚本以同步价格数据：

   ```bash
   python src/sync_pricing.py [--json_file JSON_FILE] [--json_url JSON_URL]
   ```

   示例：

   ```bash
   python src/sync_pricing.py --json_url=https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@prices/oneapi_prices.json
   ```

   如果未指定 `--json_file` 或 `--json_url` 参数，脚本将默认加载 `./oneapi_prices.json`。

5. 检查生成的价格表文件是否更新成功。

#### 注意事项

- 请确保网络连接正常，以便脚本能够访问外部 API。
- 如果需要手动调整价格数据，请编辑 `manual_prices/` 目录中的 YAML 文件。
- `sync_pricing.py` 脚本支持通过以下环境变量进行配置，并支持以下参数：
  - `--json_file`: 指定 JSON 文件路径
  - `--json_url`: 指定 JSON 数据的 URL
  - 优先使用 url，其次使用文件
  - `ONEHUB_URL`: API 基础 URL
  - `ONEHUB_ADMIN_TOKEN`: 管理员认证令牌
  - `SYNC_PRICE_OVERWRITE`: 是否覆盖现有价格（默认为 `True`）

例如

```bash
export ONEHUB_URL="https://onehub.your.link" # 仅基础url,不要附带api subpath
export ONEHUB_ADMIN_TOKEN="your_admin_token" # 网页管理后台获得
export SYNC_PRICE_OVERWRITE=True # 是否覆盖现有价格

python src/sync_pricing.py [--json_file=./oneapi_prices.json] [--json_url=https://cdn.jsdmirror.com/gh/Oaklight/onehub_prices@prices/oneapi_prices.json]
```

## 手工定价文件要求

如果需要添加或更新供应商的手工定价文件，请遵循以下规范：

### 📋 编写规则

详细的 YAML 文件编写规范请查看：[**Manual Pricing 编写规则文档**](docs/manual_pricing_rules.md)

**核心要求：**
- ✅ 主模型名称不应包含 `latest`、时间戳、`preview`、`exp` 等后缀
- ✅ 模型名称不应包含空格
- ✅ 所有模型必须能在官方定价页面中找到，不能臆造
- ✅ 必须添加官方定价页面链接
- ✅ 价格单位格式正确（如 `2.5 usd / M`）

### 📁 文件位置

- [`manual_prices/`](manual_prices/) - 手动维护的供应商价格 YAML 文件
- [`docs/manual_pricing_rules.md`](docs/manual_pricing_rules.md) - 完整的编写规则文档
- [`src/`](src/) - 价格处理和同步脚本

## 更新说明

近期主要更新包括：

1. **增添 CDN 链接**:
   - 添加 jsdelivr 链接
   - 添加 jsdmirror 链接
2. **自动刷新间隔调整为每 6 小时**：github action 的运行时间从原来的每天一次改为每 6 小时一次。
3. **新增供应商支持**：添加了 Coreshub, Pollinations.AI, OpenRouter, Moonshot 等新供应商的价格支持
4. **脚本改进**：
   - 新增 `get_ownedby.py` 用于获取供应商归属信息
   - 改进 `get_siliconflow_prices.py` 的模型排序逻辑
   - 优化 `merge_prices.py` 生成 `onehub_only_prices.json`
   - 新增 `sync_pricing.py` 用于同步价格数据，支持通过 JSON 文件或 URL 数据源
   - 新增 `sync_ownedby.py` 用于同步 ownedby 数据，支持通过 JSON 文件或 URL 数据源
5. **价格表维护**：
   - 新增多个供应商的手动价格配置
   - 优化价格合并逻辑，确保数据一致性
6. **自动化流程**：
   - 每日自动更新价格数据
   - 自动生成核心供应商价格表
   - 自动验证数据完整性
