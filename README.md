# Amazon AI 图片生产系统

项目版本 **1.1.0**。运营在 Codex 中上传资料并描述需求，由项目入口完成事实整理、
方案确认、原生生图、图片 QC 与修复。核心能力随 Git 分发，不依赖创建者的个人 Skill。

## 团队首次使用

需要 Git、Python 3.11+、支持项目 Skill/自定义 Agent 的当前 Codex 客户端，以及成员自己的
登录账号和原生 OpenAI 图片能力。Git clone 不会复制账号权限、模型额度或个人配置。
本项目没有第三方生图平台、后台服务或必填 API Key。

1. 克隆仓库后，在 Codex 中打开**包含本 README 和 AGENTS.md 的项目根目录**。
2. 按客户端提示信任项目。项目配置是否加载、模型和图片工具是否可用，需要本机核验。
3. 安装本地验证器依赖；以下命令中的 `python` 可按机器环境改为 `python3`。

Windows PowerShell：
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/system_diagnostic.py --run-tests
```

macOS / Linux：
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/system_diagnostic.py --run-tests
```

后续命令里的 `python` 指上述虚拟环境解释器，或激活虚拟环境后的 python。
自检 PASS 表示文件、配置和本地测试通过，不代表账号模型、生图或 Amazon 发布审核通过。

## 运营使用

上传真实产品图、Listing 或产品说明，然后说：

> 帮我做这个产品的 Amazon 七张图，销售站点是美国。

系统先整理事实，遇到数量/颜色/材质冲突时询问，再展示方案。你确认后才生成。
需要修改锁定产品时会重新确认。图片检查失败会修复；所有图片通过后交付。
不需要自己写 Prompt，也不需要知道内部角色名称。

首次运行请管理员确认自动进入 `amazon-image-director`。若未自动触发，可以显式输入
`$amazon-image-director`，但必须把自动触发验收记录为未通过并检查客户端加载/技能冲突。

## 项目结构

```text
.agents/skills/     9 个项目技能（仅 Director 隐式调用）
.codex/agents/      5 个自定义 Agent
.codex/config.toml 项目推理配置
AGENTS.md          项目规则
config/            模型、提问和状态流程策略
knowledge/         Amazon、产品、风格知识
schemas/           4 个 JSON Schema
templates/         数据与 Prompt 模板
scripts/           校验、Job 生命周期、自检与测试入口
tests/             10 个核心场景、边界回归、5 个入口验收案例
docs/              执行手册、验收说明与来源
jobs/              本地生产任务（实际资料不跟踪）
outputs/           本地汇总交付（不跟踪）
```

## 管理员与运营分工

管理员维护 Skill、Agent、平台规则、QC、Schema、Prompt 和测试。
普通运营负责资料、回答问题、确认方案和提出修改，不直接编辑
AGENTS.md、.codex/、.agents/skills/、schemas/、knowledge/、scripts/。
Git 本身不提供角色权限隔离；团队可用分支保护和代码审查落实此分工。

管理员可对 Codex 说：
- 检查当前系统 / 检查当前Amazon AI图片系统
- 检查所有Skill / 检查Skill冲突
- 检查图片生成流程 / 运行全部测试
- 新增一个衣架产品图片Skill
- 更新Amazon主图规则 / 更新QC规则
- 检查默认模型

对应检查：`python scripts/system_diagnostic.py --run-tests`。
新增 Skill 需独立目录、frontmatter、触发/排除范围、references、测试和 README 更新；
默认作为内部显式技能，保持唯一入口。知识更新记录来源日期与适用站点。

## 模型与运行边界

推理默认 `gpt-5.6` + `high`，生图意向 `gpt-image-2` + `high`，由 config/model-policy.md 管理。
原生工具不一定开放 model/quality 参数。必须披露无法指定/核验实际模型的情况，得到运营接受；
不能写了配置就声称工具使用该模型。显式换模型需验证工具支持，并仅影响当前 Job。
无原生工具时停止，不自动改用外部平台或付费 API。

本项目为 **Codex 原生工具协作系统**，不是独立调用生图 API 的无人值守服务。
CLI 负责本地状态和校验；Director 负责原生工具调用、文件保存和视觉检查。
CLI 不会拦截其他任意工具调用，也无法验证操作者是否伪造确认或视觉审查结果。

## 测试与验收

```bash
python scripts/run_tests.py
python scripts/system_diagnostic.py --run-tests
python scripts/validate_schema.py image-job templates/image-job.template.json
```

详细执行见 [执行手册](docs/operator-workflow.md)，线上验收见
[验收说明](docs/acceptance.md)。测试素材为临时合成文件，不是商品图或真实生图结果。
Amazon 完整后台规则本次有登录限制；管理员上线前按站点与类目复核。

## 提交到 Git

ZIP 解压后在项目根目录执行（替换你的仓库地址）：
```bash
git init -b main
git add .
git status
git commit -m "Add Amazon AI image system v1.1"
git remote add origin <你的Git仓库地址>
git push -u origin main
```

若放入已有仓库，先检查同名文件并合并，不要覆盖已有业务规则。打包文件包含隐藏目录
`.agents`、`.codex`、`.github`，提交时须保留。不要把 ZIP 自身再次放入项目仓库。
实际 Job、产品素材和图片默认被 .gitignore 排除；需要团队同步时使用受控共享存储。
