# 密钥守门人

> 提示词注入游戏：大模型守着一段密钥，看你怎么把它骗出来。

## 部署

```bash
cp .env.example .env   # 填入 OPENAI_API_KEY 和 GUARD_SECRET（日记加密密钥）
docker compose up -d --build
```

- 默认端口映射 `8080:80`
- 通关者姓名记录在 `data/claims.jsonl`（纯文本，一行一条）

- 修改 API key 或 GUARD_SECRET 后，重建容器生效：

```bash
docker compose up -d
```
