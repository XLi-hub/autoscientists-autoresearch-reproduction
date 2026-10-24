# AutoScientists autoresearch 实验归档

保存 2026-10-22 和 2026-10-24 两次实验，供后续分析结果、agent 行为和协作轨迹。

| 路径 | 内容 |
| --- | --- |
| `runs/ar_20261022.hi/` | 第一次实验的候选代码、冠军、训练输出、实验账本、agent 记忆及指令 |
| `runs/ar_20261024/` | 第二次实验的同类材料及 `logs/FINAL_REPORT.md` |
| `trajectories/` | Claude 原始会话结构、工具调用、子 agent 记录、文件历史及会话辅助记录 |
| `dashboard/` | ClawInstitute 看板的 19 张表，以 JSON 保存帖子、评论、队列所在的共享文件及其历史版本 |
| `temporary/` | 从服务器 `/tmp` 留存的实验辅助脚本和文本材料 |
| `SOURCE_CHANGES.md` | 简要源码改动说明 |
| `MANIFEST.json` | 归档文件清单和 SHA-256 校验值 |
| `ARCHIVE_NOTES.json` | 来源、排除范围与脱敏说明 |

## 查看轨迹

先看各实验的 `run_metadata.json`、`logs/experiments.jsonl`、`champion/SOURCE`，再按 agent 名称查看其 `workspace/` 和 `memory/`。完整会话记录位于 `trajectories/projects/`，子 agent 记录在对应会话的 `subagents/` 下。

看板共享文件当前内容在 `dashboard/ws_workspace_files.json`，历史内容在 `ws_workspace_file_revisions.json`；帖子和评论分别在 `posts.json`、`comments.json`。`schema.json` 和 `counts.json` 保存表字段及导出条数。数据来自服务器数据库的离线副本，没有启动或改动远端看板。

## 保存范围

保留成功、失败、被否决的实验及已有结论，不重新运行或修正实验。源码模板来自 `XLi-hub/AutoScientists` 的 `05ee52694612f13b250d1b4bad77827892c58576`，autoresearch 基线来自 `228791fb499afffb54b46200aca536f79142f117`。

凭据文件未上传，记录中的已识别密钥和认证字段替换为 `[REDACTED]`；JSON/JSONL 排版可能经过规范化。数据库采用脱敏后的逻辑数据导出，不包含登录凭据或原始二进制数据库，不能直接作为原看板的数据目录启动。

按保存范围，不另存训练数据、tokenizer、环境安装目录、缓存、独立环境验证记录或看板程序。服务器原件保持不变。
