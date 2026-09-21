# Job 工作区

目录：YYYY/MM/SKU/job-id/，每次任务使用不同 job-id；同一 Job 由一个 Director 写入。
Job 包含 image-job.json、product-card.json、image-plan.json、inputs/、prompts/、qc/、outputs/、history/。
实际商品资料默认不进入 Git。团队需要共享时用受控存储同步完整 Job；不要提交密钥和客户资料。
image-job.json 是主记录；侧文件为导出副本。更新用 workflow update，不直接改写已锁定数据。
