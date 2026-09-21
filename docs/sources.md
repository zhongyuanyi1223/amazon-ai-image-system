# 来源与设计决议

核验日期：2026-09-20。原始用户规范见 CODEX_PROJECT_BUILD_SPEC.md。
落地歧义决议在 config/workflow-policy.md，能力边界在 config/model-policy.md。

- Codex 项目 Agent（name / description / developer_instructions、模型配置）：
  https://learn.chatgpt.com/docs/agent-configuration/subagents
- Skill 的 SKILL.md、UI 元数据及隐式调用策略：
  https://learn.chatgpt.com/docs/build-skills
- GPT Image 2 模型存在性（不等于当前账号权限）：
  https://developers.openai.com/api/docs/models/gpt-image-2
- Amazon 主图公开员工说明：
  https://sellercentral.amazon.com/seller-forums/discussions/t/86af5299720a1cd2cb752c2e3b4f88bd
- Amazon A+ 官方设计指南：
  https://sell.amazon.com/blog/a-plus-content-design-guide
- Amazon A+ 产品说明：
  https://sell.amazon.com/tools/a-content
- 完整图片规则入口（本次重定向登录，未读取完整正文）：
  https://sellercentral.amazon.com/help/hub/reference/G1881

未复制用户级 Skill 或配置；项目内容独立编写。技能工作流参考了当前可用的
skill-creator 与 rongjie-amazon-design 方法，项目运行不依赖这两份个人技能。
