# Model policy / 管理员维护

以下 YAML 是机器读取的唯一模型策略块；修改后运行系统自检。

```yaml
reasoning_model: gpt-5.6
reasoning_effort: high
image_generation:
  provider: openai
  model: gpt-image-2
  quality: high
```

推理与生图分离。项目 TOML 是推理默认值的必要镜像，自检检查其一致性。
不允许普通运营改变默认值。模型切换必须先展示当前值/目标值，验证环境可用性，
取得明确确认，只写当前 Job。切换使原方案确认失效，需要重新展示完整确认摘要。

原生工具不提供 model 或 quality 参数时，不伪造参数，不承诺高质量选项已执行。
Director 检查当前工具签名，将证据写入 Job capability；可用模型列表只能来自
实际环境证据，不能从网上模型目录推断账号权限。
默认模型不可核验时，向运营披露：工具可用，但实际模型和质量档位由工具管理。
只有运营接受该限制并明确确认，才允许以原生默认能力执行；实际模型记录 null
直到工具返回可靠标识。显式切换必须具备可选模型能力，不能借此路径绕过。
工具不可用时停在确认之前，不用第三方平台，不自动改用付费 API。

官方依据（2026-09-20核验）：
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://developers.openai.com/api/docs/models/gpt-image-2
