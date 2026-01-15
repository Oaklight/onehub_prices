# Manual Pricing 文件编写规则

本文档详细说明了 `manual_prices/` 目录下 YAML 文件的编写规范和最佳实践。

## 文件结构

### 基本格式

每个供应商的价格文件遵循以下基本结构：

```yaml
models:
  供应商名称:
    # 模型定价：[官方定价页面URL]

    模型名称:
      aliases:
        - 别名1
        - 别名2
      input: 价格 货币单位 / 单位
      output: 价格 货币单位 / 单位
      extra_ratios:
        - token类型: 价格 货币单位 / 单位
```

## 核心规则

### 1. 文件命名

- 文件名使用供应商名称，支持中英文
- 使用 `.yaml` 扩展名
- 示例：`OpenAI.yaml`、`阿里云百炼.yaml`、`字节火山.yaml`

### 2. 顶层结构

```yaml
models:
  供应商名称:
    # 必须在顶部添加官方定价页面链接作为注释
    # 模型定价：https://...
```

**要求：**

- 必须包含 `models` 根节点
- 供应商名称必须与 `ownedby.json` 中定义的名称一致
- 必须在供应商定义下方添加官方定价页面链接注释

### 3. 模型定义

#### 3.1 模型命名规则

**主模型名称（Primary Name）规范：**

1. **不应包含版本后缀**：主模型名不应包含 `latest`、时间戳、`preview`、`exp` 等后缀

   - ❌ 错误：`gpt-4o-latest`、`claude-3-5-sonnet-20241022`、`qwen-plus-2025-09-01`
   - ✅ 正确：`gpt-4o`、`claude-3-5-sonnet-v2`、`qwen-plus`
   - ⚠️ 例外：如果存在同名模型但价格不同，需要询问维护者如何命名

2. **不应包含空格**：模型名称必须使用连字符或下划线

   - ❌ 错误：`gpt 4o`、`claude sonnet`
   - ✅ 正确：`gpt-4o`、`claude-sonnet`

3. **必须可在官方文档中找到**：所有模型名称必须能在官方定价页面或文档中找到，不能臆造
   - 每个模型必须有官方来源支持
   - 如果官方文档中没有明确的模型名称，应使用最接近的官方命名

**版本标识处理：**

- 将带版本的名称放在 `aliases` 中
- 如果官方只提供带版本的名称，选择最稳定/最新的版本作为主名称

**示例：**

```yaml
# ✅ 正确示例
gpt-4o:
  aliases:
    - gpt-4o-2024-11-20
    - gpt-4o-2024-08-06
    - gpt-4o-latest
  input: 2.5 usd / M
  output: 10 usd / M

claude-3-5-sonnet-v2:
  aliases:
    - claude-3.5-sonnet-v2
    - claude-3-5-sonnet-20241022
    - claude-3-5-sonnet-latest
  input: 3 usd / M
  output: 15 usd / M

# ❌ 错误示例
gpt-4o-latest: # 不应使用 latest 作为主名称
  input: 2.5 usd / M
  output: 10 usd / M

claude 3.5 sonnet: # 不应包含空格
  input: 3 usd / M
  output: 15 usd / M

my-custom-model: # 不能臆造，必须在官方文档中存在
  input: 1 usd / M
  output: 2 usd / M
```

#### 3.2 基本价格定义

```yaml
模型名称:
  input: 价格 货币单位 / 单位
  output: 价格 货币单位 / 单位
```

**价格单位规范：**

- 货币单位：`usd`（美元）、`rmb`（人民币）
- 计量单位：
  - `M`：百万 tokens (1,000,000)
  - `K`：千 tokens (1,000)
  - `image`：按图片计费
  - `video`：按视频计费
  - `s`：按秒计费
  - `min`：按分钟计费

**示例：**

```yaml
gpt-4o:
  input: 2.5 usd / M
  output: 10 usd / M

doubao-seedream-4.5:
  output: 0.2590 rmb / image
```

#### 3.3 别名（Aliases）

用于定义模型的其他名称或版本：

```yaml
模型名称:
  aliases:
    - 别名1
    - 别名2-* # 支持通配符
```

**规则：**

- 使用 YAML 列表格式
- 支持通配符 `*` 匹配多个版本
- 别名应包含所有可能的模型名称变体

**示例：**

```yaml
gpt-4o:
  aliases:
    - gpt-4o-2024-11-20
    - gpt-4o-2024-08-06
    - gpt-4o-latest

qwen-plus:
  aliases:
    - qwen-plus-latest
    - qwen-plus-2025-09*
    - qwen-plus-2025-07*
```

#### 3.4 额外计费项（Extra Ratios）

用于定义特殊 token 类型的价格：

```yaml
extra_ratios:
  - token类型: 价格 货币单位 / 单位
```

**常见 token 类型：**

- `cached_tokens`：缓存 tokens（通常为输入价格的 10-20%）
- `reasoning_tokens`：推理 tokens（思考模式输出）
- `input_audio_tokens`：音频输入 tokens
- `output_audio_tokens`：音频输出 tokens
- `input_image_tokens`：图像输入 tokens
- `output_image_tokens`：图像输出 tokens
- `input_video_tokens`：视频输入 tokens
- `output_video_tokens`：视频输出 tokens

**示例：**

```yaml
gpt-4o:
  input: 2.5 usd / M
  output: 10 usd / M
  extra_ratios:
    - cached_tokens: 1.25 usd / M

qwen-plus:
  input: 0.0008 rmb / K
  output: 0.002 rmb / K
  extra_ratios:
    - reasoning_tokens: 0.008 rmb / K
    - cached_tokens: 0.2 # 相对比例，表示输入价格的 20%

gpt-realtime-mini:
  input: 0.6 usd / M
  output: 2.4 usd / M
  extra_ratios:
    - cached_tokens: 0.06 usd / M
    - input_image_tokens: 0.8 usd / M
    - input_audio_tokens: 10 usd / M
    - output_audio_tokens: 20 usd / M
```

### 4. 阶梯定价处理

对于有阶梯定价的模型，应：

1. 在注释中说明完整的阶梯定价规则
2. 选择最常用的价格区间作为默认值
3. 明确标注选择的区间

**示例：**

```yaml
qwen3-max:
  aliases:
    - qwen3-max-*
  # 阶梯计价：0<Token≤32K: 0.0032元输入/0.0128元输出
  # 32K<Token≤128K: 0.0064元输入/0.0256元输出
  # 128K<Token≤252K: 0.0096元输入/0.0384元输出
  input: 0.0064 rmb / K # 取32～128k价格
  output: 0.0256 rmb / K
  extra_ratios:
    - cached_tokens: 0.2

doubao-seed-1.8:
  # 阶梯计价：0-32K: 0.8元/M输入，8元/M输出
  # 32K-128K: 1.2元/M输入，16元/M输出
  # 128K-256K: 2.4元/M输入，24元/M输出
  input: 1.2 rmb / M # 取32k～128k价格，最为常见
  output: 16 rmb / M
```

### 5. 模型分组与注释

使用注释对模型进行逻辑分组，提高可读性：

```yaml
models:
  OpenAI:
    # 模型价格：https://platform.openai.com/docs/pricing

    # GPT-5 系列
    gpt-5.2:
      input: 1.75 usd / M
      output: 14 usd / M

    # GPT-4o 系列
    gpt-4o:
      input: 2.5 usd / M
      output: 10 usd / M

    # Realtime 模型
    gpt-realtime:
      input: 4 usd / M
      output: 16 usd / M

    # Embedding 模型
    text-embedding-3-small:
      input: 0.02 usd / M
      output: 0
```

**分组建议：**

- 按模型系列分组（如 GPT-4、GPT-5）
- 按功能分组（如文本模型、视觉模型、音频模型）
- 按版本分组（如最新版本、旧版本）
- 使用分隔线标记重要分界（如 `# ===== 已下线 =====`）

### 6. 免费模型

对于免费模型，价格设置为 0：

```yaml
gpt-4o-mini-flash:
  input: 0
  output: 0

kat-coder-air-v1:
  input: 0 rmb / M
  output: 0 rmb / M
  extra_ratios:
    - cached_tokens: 0 rmb / M
```

### 7. 特殊模型类型

#### 7.1 仅输出计费的模型

```yaml
text-embedding-3-small:
  input: 0.02 usd / M
  output: 0

cogview-4:
  output: 0.06 rmb / image
```

#### 7.2 视频/图像生成模型

```yaml
sora-2:
  output: 0.1 usd / s

doubao-seedream-4.5:
  output: 0.2590 rmb / image

cogvideox-2:
  output: 0.5 rmb / video
```

#### 7.3 多模态模型

```yaml
qwen3-omni-flash:
  input: 0.0018 rmb / K
  output: 0.0069 rmb / K
  extra_ratios:
    - input_audio_tokens: 0.0158 rmb / K
    - input_image_tokens: 0.0033 rmb / K
    - output_audio_tokens: 0.0626 rmb / K
```

### 8. 版本管理

#### 8.1 最新版本

使用 `latest` 或通配符标记最新版本：

```yaml
claude-3-5-sonnet-v2:
  aliases:
    - claude-3.5-sonnet-v2
    - claude-3-5-sonnet-20241022
    - claude-3-5-sonnet-latest
```

#### 8.2 已下线模型

使用注释明确标记：

```yaml
# =========================== 已下线 ===========================
kat-coder:
  aliases:
    - kat-coder-256k
  input: 6 rmb / M
  output: 24 rmb / M
```

#### 8.3 陈旧版本

```yaml
#  =================================== 陈旧aliases ===================================

qwen-max: # 仍旧为qwen2.5
  aliases: qwen-max-latest
  input: 0.0024 rmb / K
  output: 0.0096 rmb / K
```

## 最佳实践

### 1. 注释规范

- 必须在供应商定义下添加官方定价页面链接
- 对阶梯定价进行详细说明
- 标注价格选择的理由
- 对特殊模型添加说明性注释

### 2. 价格精度

- 保持与官方定价一致的精度
- 人民币通常保留 2-4 位小数
- 美元通常保留 2-3 位小数

### 3. 单位一致性

- 同一供应商内尽量使用统一的计量单位
- 优先使用 `M`（百万）作为 token 计量单位
- 特殊情况下可使用 `K`（千）

### 4. 相对价格

对于 `cached_tokens`，可以使用相对比例：

```yaml
extra_ratios:
  - cached_tokens: 0.2 # 表示输入价格的 20%
```

### 5. 文件组织

- 按模型系列分组
- 最新模型放在前面
- 已下线模型放在最后
- 使用空行分隔不同组

## 常见错误

### ❌ 错误示例

```yaml
# 1. 缺少官方链接
models:
  OpenAI:
    gpt-4o:
      input: 2.5 usd / M

# 2. 主模型名包含版本后缀
gpt-4o-latest:  # 应使用 gpt-4o 作为主名称
  input: 2.5 usd / M

# 3. 模型名包含空格
gpt 4o:  # 应使用 gpt-4o
  input: 2.5 usd / M

# 4. 臆造的模型名
my-awesome-model:  # 必须在官方文档中存在
  input: 1 usd / M

# 5. 单位不规范
gpt-4o:
  input: 2.5 USD/M  # 应使用小写 usd / M

# 6. 别名格式错误
gpt-4o:
  aliases: gpt-4o-latest  # 应使用列表格式

# 7. 缺少计量单位
gpt-4o:
  input: 2.5  # 缺少单位
```

### ✅ 正确示例

```yaml
models:
  OpenAI:
    # 模型价格：https://platform.openai.com/docs/pricing

    gpt-4o:
      aliases:
        - gpt-4o-latest
      input: 2.5 usd / M
      output: 10 usd / M
      extra_ratios:
        - cached_tokens: 1.25 usd / M
```

## 验证清单

在提交新的价格文件前，请确认：

- [ ] 已添加官方定价页面链接
- [ ] 主模型名称不包含 `latest`、时间戳、`preview`、`exp` 等后缀
- [ ] 模型名称不包含空格
- [ ] 所有模型都能在官方文档中找到（不能臆造）
- [ ] 价格单位格式正确（`货币 / 单位`）
- [ ] 别名使用列表格式
- [ ] 版本标识已放入 aliases
- [ ] 阶梯定价已注释说明
- [ ] 特殊 token 类型已定义
- [ ] 模型已合理分组
- [ ] 已标记已下线或陈旧模型
- [ ] YAML 语法正确（可使用在线验证工具）

## 参考示例

完整的供应商价格文件示例请参考：

- [`manual_prices/OpenAI.yaml`](../manual_prices/OpenAI.yaml)
- [`manual_prices/阿里云百炼.yaml`](../manual_prices/阿里云百炼.yaml)
- [`manual_prices/Anthropic.yaml`](../manual_prices/Anthropic.yaml)
- [`manual_prices/Deepseek.yaml`](../manual_prices/Deepseek.yaml)
