# Codex Amazon AI 图片生产系统 V1.1
## 团队共享项目构建规范 / Build Specification

> 用途：将本文件放入 Git 仓库后，让 Codex 按本规范创建并维护一套“Amazon AI 图片生产系统”。
>
> 目标用户：几乎没有 AI 生图经验的 Amazon 运营。
>
> 核心原则：运营只描述需求、上传资料、回答必要问题、确认方案；系统负责产品分析、图片规划、Prompt、图片生成、QC 和修复。

---

# 1. 项目目标

建立一个可以由多个运营共同使用的 Codex 项目，而不是个人电脑上的本地 Skill 集合。

系统必须实现：

```text
运营输入
  ↓
Amazon Image Director（唯一入口）
  ↓
资料识别
  ↓
完整性检查
  ↓
缺失信息询问
  ↓
冲突信息确认
  ↓
产品信息锁定
  ↓
Amazon 图片方案
  ↓
运营确认
  ↓
Prompt / 图片生成
  ↓
图片 QC
  ↓
PASS → 最终图片
FAIL → 自动生成修复方案 → 再生成 → 再 QC
```

系统必须支持后续持续增加：

- Amazon 主图 Skill
- Amazon 副图 Skill
- Amazon A+ Skill
- 家居类图片 Skill
- 五金类图片 Skill
- 家具类图片 Skill
- 衣架类图片 Skill
- 其他产品类型 Skill
- Amazon 图片规则更新
- 产品知识库
- QC 规则
- Prompt 模板

---

# 2. 平台与工具范围

V1 只使用 Codex / OpenAI 能力。

明确排除：

- ComfyUI
- 即梦
- RunningHub
- Lovart
- 其他外部生图平台

不要为这些工具创建路由、Skill 或工作流。

系统应优先使用 Codex 当前可用的原生图片生成/编辑能力。

---

# 3. 模型策略

## 3.1 Agent 默认模型

整个项目默认使用：

```toml
model = "gpt-5.6"
model_reasoning_effort = "high"
```

用途：

- Amazon Image Director
- Product Analyst
- Image Planner
- Prompt Engineer
- Image QC

`gpt-5.6 + high` 是本项目的默认“高级推理”配置。

---

## 3.2 图片生成模型

必须将：

```text
Agent 推理模型
```

和：

```text
图片生成模型
```

分离。

不要在代码或 Skill 中把两者错误地写成同一个模型。

配置统一放到：

```text
config/model-policy.md
```

默认策略：

```yaml
reasoning_model: gpt-5.6
reasoning_effort: high

image_generation:
  provider: openai
  model: gpt-image-2
  quality: high
```

说明：

- `gpt-5.6 + high`：负责理解、分析、规划、Prompt、QC。
- 图片生成工具使用当前项目配置的 GPT Image 模型。
- 如果未来 Codex 原生图片工具支持新的更高规格图片模型，只修改 `model-policy.md` 和图片生成 Skill，不修改整个 Agent 架构。
- 任何模型变更必须是 Job 级或管理员配置级，不允许普通运营无意中修改全局默认值。

---

# 4. 模型切换规则

运营可以提出：

> 这次换一个模型生成。

系统不能立即切换。

必须：

1. 读取当前默认模型。
2. 告知运营当前默认模型。
3. 告知拟切换模型。
4. 判断该模型是否在当前环境可用。
5. 询问确认。
6. 只修改当前 Job 的模型配置。
7. 不修改全局默认配置。

示例：

```text
当前默认图片模型：gpt-image-2
你要求本次任务切换为：XXXX

是否仅本次任务使用 XXXX？
```

运营确认后：

```json
{
  "generation": {
    "model": "XXXX",
    "scope": "current_job"
  }
}
```

---

# 5. 团队共享原则

这是一个 Git 仓库级系统。

所有团队核心能力必须进入 Git：

```text
.agents/skills/
AGENTS.md
.codex/agents/
.codex/config.toml
schemas/
knowledge/
templates/
tests/
scripts/
config/
```

禁止把核心 Skill 只放在：

```text
~/.agents/skills
```

个人目录只允许保存个人通用 Skill，不作为本项目正式版本。

---

# 6. 项目目录

请 Codex 创建以下结构：

```text
amazon-ai-image-system/
│
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── .gitignore
│
├── .codex/
│   ├── config.toml
│   └── agents/
│       ├── amazon-image-director.toml
│       ├── product-analyst.toml
│       ├── image-planner.toml
│       ├── prompt-engineer.toml
│       └── image-qc.toml
│
├── .agents/
│   └── skills/
│       ├── amazon-image-director/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-image-intake/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-product-analysis/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-image-planning/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-main-image/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-secondary-image/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-aplus-image/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       ├── amazon-prompt-engineering/
│       │   ├── SKILL.md
│       │   └── agents/
│       │       └── openai.yaml
│       │
│       └── amazon-image-qc/
│           ├── SKILL.md
│           └── agents/
│               └── openai.yaml
│
├── schemas/
│   ├── image-job.schema.json
│   ├── product.schema.json
│   ├── image-plan.schema.json
│   └── qc-result.schema.json
│
├── knowledge/
│   ├── amazon/
│   │   ├── amazon-us-image-rules.md
│   │   ├── main-image-rules.md
│   │   ├── secondary-image-rules.md
│   │   └── aplus-rules.md
│   │
│   ├── product/
│   │   ├── product-identity.md
│   │   ├── immutable-features.md
│   │   ├── claim-rules.md
│   │   └── material-rules.md
│   │
│   └── style/
│       ├── furniture.md
│       ├── hardware.md
│       ├── household.md
│       ├── beauty.md
│       └── apparel.md
│
├── config/
│   ├── model-policy.md
│   ├── question-policy.md
│   └── workflow-policy.md
│
├── templates/
│   ├── product-card.template.json
│   ├── image-job.template.json
│   ├── image-plan.template.json
│   └── qc-report.template.json
│
├── scripts/
│   ├── validate_job.py
│   ├── validate_qc.py
│   ├── validate_schema.py
│   └── run_tests.py
│
├── tests/
│   ├── missing-material.json
│   ├── conflicting-quantity.json
│   ├── conflicting-color.json
│   ├── incomplete-listing.json
│   ├── unconfirmed-generation.json
│   ├── confirmed-generation.json
│   ├── locked-product-change.json
│   ├── qc-failure.json
│   ├── qc-pass.json
│   └── model-switch.json
│
├── jobs/
│   └── README.md
│
└── outputs/
    └── README.md
```

---

# 7. AGENTS.md

请生成项目根目录 `AGENTS.md`。

它是整个项目的最高级项目规则。

必须包含：

```markdown
# Amazon AI Image System

## Project Role

This repository is a shared Amazon AI image production system.

## Mandatory Entry Point

All Amazon image creation, editing, planning, optimization, review,
and image-set requests MUST enter through:

amazon-image-director

The operator should not need to know internal Skills or Agents.

## Mandatory Workflow

1. Intake
2. Product analysis
3. Requirement validation
4. Conflict resolution
5. Product lock
6. Image planning
7. Operator confirmation
8. Prompt generation
9. Image generation
10. Image QC
11. Revision if necessary
12. Final delivery

## Hard Gates

Image generation is forbidden when:

generation.confirmed != true

Image generation is forbidden when any P0 field is missing.

Image generation is forbidden when unresolved P0 conflicts exist.

## Product Lock

After operator confirmation, lock:

- product identity
- structure
- material
- color
- quantity
- dimensions
- included accessories
- functional claims

Changing a locked field invalidates the previous confirmation.

## No Unsupported Claims

Never invent:

- material
- dimensions
- certifications
- safety claims
- performance claims
- package quantity
- included accessories
- product functions

## Operator Experience

Do not ask ordinary operators to:

- write AI prompts
- understand model parameters
- understand image-generation internals
- understand Skill names
- understand Agent names

The system should ask only necessary business questions.

## Model

Default reasoning model:

gpt-5.6

Default reasoning effort:

high

Image-generation model is controlled by:

config/model-policy.md

## QC

No image can be marked FINAL until image QC returns PASS.
```

AGENTS.md 必须保持简洁，详细规则放入 `knowledge/` 和 Skill 中。

---

# 8. Agent 架构

只建立以下 5 个自定义 Agent：

## 8.1 amazon_image_director

职责：

- 唯一入口
- 读取 Job 状态
- 控制状态机
- 调用内部 Skill
- 向运营提问
- 要求运营确认
- 触发图片生成
- 触发 QC
- 管理修复循环

默认：

```toml
model = "gpt-5.6"
model_reasoning_effort = "high"
```

---

## 8.2 product_analyst

职责：

- 分析产品图
- 分析 Listing
- 分析尺寸图
- 分析竞品图
- 提取产品事实
- 判断 immutable features
- 判断 supported claims
- 检测冲突

不得：

- 自己修改产品事实
- 自己做最终运营决策
- 直接生成图片

---

## 8.3 image_planner

职责：

- 设计 Amazon 7 图方案
- 确定每张图目的
- 避免场景重复
- 确定卖点分配
- 确定视觉层级
- 确定构图
- 确定场景
- 确定是否需要文字

不得：

- 修改已锁定产品信息
- 发明卖点

---

## 8.4 prompt_engineer

职责：

- 将已确认的 Image Plan 转换为图片生成指令
- 产品保护
- 构图
- 摄影
- 场景
- 灯光
- 材质
- 负面约束
- Amazon要求

不得：

- 改变产品结构
- 改变产品颜色
- 改变数量
- 增加未经确认的功能

---

## 8.5 image_qc

职责：

严格检查：

### 产品一致性

- 结构
- 形状
- 比例
- 数量
- 颜色
- 材质
- 配件
- 产品细节

### 使用逻辑

- 安装方式
- 人手关系
- 门/家具/墙体关系
- 物理遮挡
- 受力关系
- 光影
- 透视

### Amazon

- 主图/副图规则
- 背景
- 文字
- Logo
- 水印
- 虚假信息
- 错误产品
- 错误功能

返回：

```json
{
  "status": "PASS"
}
```

或：

```json
{
  "status": "FAIL",
  "issues": [
    {
      "severity": "critical",
      "type": "product_structure",
      "description": "...",
      "repair_instruction": "..."
    }
  ]
}
```

---

# 9. Skill 自动调用策略

这是项目最重要的调用策略。

## 唯一允许隐式调用的 Skill

```text
amazon-image-director
```

其 `agents/openai.yaml`：

```yaml
interface:
  display_name: "Amazon Image Director"
  short_description: "Amazon商品图片智能生产助手"

policy:
  allow_implicit_invocation: true
```

---

## 其他 Skill

默认：

```yaml
policy:
  allow_implicit_invocation: false
```

原因：

不能让普通运营的一句话同时触发：

- Prompt Engineer
- Image QC
- Main Image
- A+
- Product Analysis

所有内部 Skill 必须由 Amazon Image Director 按状态机调用。

---

# 10. amazon-image-director Skill

必须成为整个系统唯一入口。

description 必须覆盖以下意图：

```text
Amazon image
Amazon main image
Amazon secondary image
Amazon product image
Amazon A+
Amazon lifestyle image
Amazon feature image
Amazon size image
Amazon comparison image
Amazon image set
generate Amazon images
create Amazon images
edit Amazon images
redesign Amazon images
optimize Amazon images
review Amazon images
```

当用户说：

> 帮我做Amazon图片

也必须触发。

---

# 11. 信息状态机制

所有 Job 字段必须支持：

```text
CONFIRMED
INFERRED
MISSING
CONFLICT
LOCKED
```

定义：

## CONFIRMED

来自运营明确确认或可靠产品资料。

## INFERRED

AI根据图片/Listing推断，但运营没有明确确认。

## MISSING

无法获取。

## CONFLICT

两个可靠来源不一致。

## LOCKED

运营确认后的关键产品字段。

---

# 12. 信息优先级

## P0：必须有

缺少不得生成：

- platform
- marketplace
- product identity
- product image
- product structure
- product quantity
- product color
- product material（如果影响视觉表现）
- image type
- key functional facts
- immutable product features

## P1：建议有

没有时允许AI决定：

- target customer
- visual style
- scene
- props
- lighting
- camera angle
- typography
- composition

## P2：AI直接决定

- 摄影镜头
- 光源位置
- 小道具
- 装饰
- 构图细节
- 背景细节

---

# 13. 提问规则

AI必须遵守：

## 原则1

能从上传图片、Listing、尺寸图读取，就不要问运营。

## 原则2

能由AI合理决定，就不要问运营。

## 原则3

会影响产品准确性、Amazon合规或图片功能表达，就必须问。

## 原则4

一次尽量只问最必要的问题。

## 原则5

不要一次问运营10个问题。

错误：

```text
请告诉我材质、颜色、场景、灯光、角度、人物、
卖点、目标人群、构图、字体……
```

正确：

```text
我还缺一个会影响产品真实性的信息：

这个产品实际销售数量是1个还是2个？
```

---

# 14. 冲突处理

如果发现：

```text
Listing：
1 Pack

图片：
2个
```

必须询问：

```text
我发现数量存在冲突：

Listing：1 Pack
产品图片：显示2个

请确认最终销售数量：
1个 / 2个
```

不能自行选择。

---

# 15. 确认闸门

在生成前必须展示：

```text
【Amazon图片生产确认】

平台：
Amazon US

产品：
XXXX

图片：
7张

产品不可改变：
- XXXX
- XXXX
- XXXX

核心卖点：
- XXXX
- XXXX

图片方案：
1. 主图
2. 功能图
3. 使用场景
4. 尺寸图
5. 细节图
6. 对比图
7. 场景图

默认模型：
gpt-image-2

是否确认生成？
```

只有以下明确确认才可以继续：

```text
确认
确认生成
开始生成
可以生成
```

---

# 16. 产品锁定

确认后：

```json
{
  "product": {
    "structure": {
      "status": "LOCKED"
    },
    "color": {
      "status": "LOCKED"
    },
    "material": {
      "status": "LOCKED"
    },
    "quantity": {
      "status": "LOCKED"
    }
  }
}
```

如果运营随后说：

> 改成灰色。

系统必须停止当前生成流程：

```text
当前产品颜色已经锁定为米白色。

如果要修改为灰色，需要解除产品锁定并重新确认。

是否修改？
```

---

# 17. 图片方案 Skill

至少建立：

```text
amazon-main-image
amazon-secondary-image
amazon-aplus-image
```

以后继续增加：

```text
amazon-lifestyle-image
amazon-feature-image
amazon-size-image
amazon-comparison-image
```

每个 Skill 必须包含：

```text
用途
适用场景
输入
输出
Amazon规则
构图规则
产品保护规则
Prompt结构
禁止事项
QC要求
```

---

# 18. Amazon Main Image Skill

必须包含：

- 主图目的
- 白底规则
- 产品主体要求
- 产品占画面比例建议
- 禁止文字
- 禁止水印
- 禁止不相关装饰
- 产品真实一致性
- 阴影规则
- 材质表现
- 产品摆放
- 构图规范

不要把“具体像素值”永久写死。

应该：

```text
以当前Amazon官方规则知识库为准
```

并在：

```text
knowledge/amazon/main-image-rules.md
```

维护。

---

# 19. Product Knowledge Card

每个产品可以建立：

```text
jobs/
  YYYY/
    MM/
      SKU/
        product-card.json
        image-job.json
        image-plan.json
        prompts/
        qc/
        outputs/
```

Product Card：

```json
{
  "product_identity": {},
  "immutable_features": [],
  "materials": [],
  "colors": [],
  "dimensions": [],
  "quantity": null,
  "accessories": [],
  "supported_claims": [],
  "forbidden_changes": [],
  "reference_images": []
}
```

---

# 20. Schema

必须使用 JSON Schema 管理：

```text
schemas/image-job.schema.json
schemas/product.schema.json
schemas/image-plan.schema.json
schemas/qc-result.schema.json
```

不要把复杂状态只存在 Agent 的自然语言记忆里。

---

# 21. Validator

必须建立：

```text
scripts/validate_job.py
```

负责：

- P0完整性
- P0冲突
- confirmation状态
- product lock
- schema
- model policy
- image type
- generation permission

示例：

```python
if not job["generation"]["confirmed"]:
    raise ValidationError(
        "Generation blocked: operator confirmation required."
    )
```

---

# 22. QC Validator

建立：

```text
scripts/validate_qc.py
```

规则：

```text
PASS → 可以进入FINAL
FAIL → 必须进入REVISION
```

禁止：

```text
FAIL → 直接交付
```

---

# 23. 状态机

Job 必须支持：

```text
INIT
COLLECTING
ANALYZING
VALIDATING
WAITING_FOR_CONFIRMATION
LOCKED
PLANNING
PROMPT_READY
GENERATING
QC
REVISION
FINAL
CANCELLED
```

状态不能随意跳跃。

核心流程：

```text
INIT
 ↓
COLLECTING
 ↓
ANALYZING
 ↓
VALIDATING
 ↓
WAITING_FOR_CONFIRMATION
 ↓
LOCKED
 ↓
PLANNING
 ↓
PROMPT_READY
 ↓
GENERATING
 ↓
QC
 ├── PASS → FINAL
 └── FAIL → REVISION → GENERATING
```

---

# 24. 图片生成策略

图片生成必须：

1. 读取 Product Card
2. 读取 Image Plan
3. 读取 Amazon Rules
4. 读取 Prompt Skill
5. 生成 Prompt
6. 调用当前可用的 OpenAI 图片生成能力
7. 保存结果
8. 进入 QC

不要允许生成模型自己重新解释产品。

---

# 25. 多轮图片修改

支持：

```text
第一版
 ↓
QC
 ↓
问题：
衣架数量错误
 ↓
修复Prompt
 ↓
第二版
 ↓
QC
 ↓
PASS
```

修复时必须保留：

```text
产品锁定信息
```

只允许修改 QC 指出的区域。

---

# 26. 测试体系

必须创建至少10个测试：

### 1 missing-material

材质缺失。

预期：

```text
BLOCKED
询问运营
```

### 2 conflicting-quantity

Listing和图片数量冲突。

预期：

```text
CONFLICT
询问运营
```

### 3 conflicting-color

颜色冲突。

预期：

```text
CONFLICT
询问运营
```

### 4 incomplete-listing

缺少Listing。

预期：

```text
要求上传/提供Listing
```

### 5 unconfirmed-generation

运营要求直接生成但没有确认。

预期：

```text
BLOCKED
```

### 6 confirmed-generation

资料完整且运营确认。

预期：

```text
ALLOW
```

### 7 locked-product-change

产品已锁定后修改颜色。

预期：

```text
INVALIDATE CONFIRMATION
```

### 8 qc-failure

QC失败。

预期：

```text
REVISION
```

### 9 qc-pass

QC通过。

预期：

```text
FINAL
```

### 10 model-switch

运营要求更换图片模型。

预期：

```text
只修改当前Job
不修改全局默认
```

---

# 27. 自动调用测试

必须测试以下自然语言：

```text
帮我做一个Amazon主图
```

```text
帮我做这个产品的Amazon七张图
```

```text
这个产品图片重新设计一下
```

```text
帮我优化Amazon副图
```

```text
帮我做A+
```

这些都必须进入：

```text
amazon-image-director
```

而不能绕过总入口直接调用内部 Skill。

---

# 28. 系统自检命令

建立：

```text
scripts/system_diagnostic.py
```

或者提供一个 Skill：

```text
system-diagnostic
```

当运营/管理员输入：

```text
检查当前Amazon AI图片系统
```

必须输出：

```text
项目根目录
AGENTS.md状态
Skill列表
Agent列表
唯一入口
隐式调用Skill
默认推理模型
默认推理强度
默认图片模型
当前知识库版本
Schema状态
Validator状态
测试数量
测试结果
```

---

# 29. Git协作规则

README必须写明：

## 管理员

负责：

- Skill
- Agent
- Amazon规则
- QC
- Schema
- Prompt
- 测试

## 普通运营

负责：

- 使用系统
- 提供产品资料
- 回答问题
- 确认方案
- 提出修改

普通运营不要直接修改：

```text
AGENTS.md
.codex/
.agents/skills/
schemas/
knowledge/
scripts/
```

---

# 30. Skill修改规则

新增 Skill 必须：

1. 创建独立目录
2. 创建 SKILL.md
3. 写清楚 description
4. 明确触发条件
5. 明确不应该触发的场景
6. 添加 references
7. 添加测试
8. 更新 README
9. 检查是否与现有 Skill 冲突

---

# 31. Amazon规则维护

不要把所有Amazon规则永久硬编码到 Agent。

规则放：

```text
knowledge/amazon/
```

Skill只负责读取。

例如：

```text
knowledge/amazon/main-image-rules.md
```

以后Amazon规则变化：

只修改知识文件。

不要重写 Agent。

---

# 32. Prompt维护

Prompt不要全部写死在 Agent。

放：

```text
templates/
knowledge/
skills/
```

分成：

```text
产品保护模板
主图模板
场景模板
功能模板
尺寸模板
A+模板
QC修复模板
```

---

# 33. 运营体验要求

运营不应该看到：

```text
Skill
Agent
Schema
Validator
JSON
TOML
Prompt engineering
```

除非管理员进入系统诊断模式。

普通运营看到：

```text
我需要先确认几个产品信息。
```

而不是：

```text
image-job.schema validation failed.
```

---

# 34. 输出标准

最终每个图片任务至少产生：

```text
image-job.json
product-card.json
image-plan.json
prompt/
qc/
outputs/
```

最终图片：

```text
01-main.png
02-feature.png
03-lifestyle.png
04-size.png
05-detail.png
06-comparison.png
07-scene.png
```

文件名可根据实际方案动态调整。

---

# 35. 管理员命令

README中提供以下管理员操作示例：

```text
检查当前系统
```

```text
检查所有Skill
```

```text
检查Skill冲突
```

```text
检查图片生成流程
```

```text
运行全部测试
```

```text
新增一个衣架产品图片Skill
```

```text
更新Amazon主图规则
```

```text
更新QC规则
```

```text
检查默认模型
```

---

# 36. Codex实施顺序

当本文件被提供给 Codex 后：

## 第一阶段

先检查当前仓库。

不要直接覆盖已有文件。

输出：

```text
当前项目结构
现有Skill
现有Agent
现有AGENTS
现有Schema
现有测试
冲突项
```

## 第二阶段

提出迁移计划。

## 第三阶段

用户确认后：

- 创建目录
- 创建AGENTS.md
- 创建Agent
- 创建Skill
- 创建Schema
- 创建Validator
- 创建测试
- 创建README

## 第四阶段

运行系统自检。

## 第五阶段

运行10个测试。

## 第六阶段

输出：

```text
PASS / FAIL
```

---

# 37. 禁止Codex做的事情

禁止：

1. 删除现有业务文件
2. 覆盖用户已有Skill而不备份
3. 修改全局Codex配置
4. 修改用户目录中的Skill
5. 把项目规则放进个人目录
6. 默认使用ComfyUI
7. 默认使用即梦
8. 要求运营手写Prompt
9. 未确认直接生成
10. 未通过QC直接交付
11. 自动修改产品事实
12. 自动接受冲突数据
13. 自动修改全局模型
14. 把Agent模型和图片生成模型混为一谈

---

# 38. 验收标准

系统只有满足以下条件才算 V1 完成：

### A. 团队共享

```text
Skill在 .agents/skills
Agent在 .codex/agents
规则在 AGENTS.md
```

### B. 自动入口

普通运营说：

```text
帮我做Amazon图片
```

可以进入：

```text
amazon-image-director
```

### C. 缺失询问

资料缺失时不会直接生成。

### D. 冲突确认

产品资料冲突时不会自行决定。

### E. 确认闸门

没有明确确认不能生成。

### F. 产品锁定

确认后产品关键属性被锁定。

### G. QC

生成后必须QC。

### H. 修复

QC失败后必须进入修复流程。

### I. 模型

默认：

```text
gpt-5.6
high
```

图片模型单独管理。

### J. 测试

10个核心测试全部通过。

---

# 39. V1之后的扩展方向

完成V1后再考虑：

```text
V1.1
更多产品类别Skill

V1.2
Amazon Listing → 图片自动规划

V1.3
SKU产品知识库

V1.4
历史图片复用

V1.5
图片版本管理

V1.6
运营数据反馈 → 图片策略优化

V2
Amazon + Walmart + Coupang统一视觉Agent
```

---

# 40. 最终目标

最终普通运营只需要：

```text
上传产品资料
        ↓
说：
“帮我做Amazon七图”
        ↓
AI自动分析
        ↓
AI只问必要问题
        ↓
AI输出方案
        ↓
运营确认
        ↓
AI生成
        ↓
AI检查
        ↓
AI修复
        ↓
最终图片
```

运营不需要学习：

- Prompt
- Skill
- Agent
- JSON
- ComfyUI
- 工作流节点
- 图片模型参数

管理员只需要维护：

```text
Skill
Knowledge
Schema
Validator
QC
Model Policy
```

---

# 41. 官方能力对应原则

本项目采用以下 Codex 原生机制：

- `AGENTS.md`：项目长期规则
- `.agents/skills`：团队共享 Skill
- `.codex/agents`：项目级子智能体
- `SKILL.md`：可复用工作流
- `agents/openai.yaml`：Skill调用策略与UI元数据
- `schemas/`：结构化数据约束
- `scripts/`：硬性验证
- `tests/`：回归测试

不要使用自创的、无法被当前 Codex识别的配置机制替代这些目录和文件。

---

# 42. 给Codex的最终执行指令

当你把本文件加入仓库后，对 Codex 发送：

> 请完整读取 `CODEX_PROJECT_BUILD_SPEC.md`。
>
> 先检查当前仓库，不要立即修改。
>
> 按文档要求输出：
>
> 1. 当前仓库结构
> 2. 当前已有的 Codex Skill
> 3. 当前已有的 Agent
> 4. 当前 AGENTS.md
> 5. 当前配置
> 6. 与本规范的差异
> 7. 需要新增的文件
> 8. 需要修改的文件
> 9. 潜在冲突
> 10. 实施计划
>
> 等我确认后再正式创建/修改。
>
> 不允许删除已有业务文件。
>
> 不允许修改用户级 Codex 配置。
>
> 本项目必须最终成为一个可以提交 Git、供团队其他成员 clone 后直接使用的项目级 Amazon AI 图片生产系统。

---

# 43. 版本

```text
System Version: V1.1
Platform: Codex
Primary Model: gpt-5.6
Reasoning: high
Image Generation: OpenAI GPT Image capability
External Image Tools: disabled
Architecture: Director + Specialist Agents + Skills + Schema + Validator + QC
Sharing: Git repository
```
