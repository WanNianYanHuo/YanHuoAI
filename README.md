## 项目概览

本项目是在 Haystack 2.x 之上构建的企业内部 **RAG 知识库问答系统**，整体链路为：

- **前端 Vue 单页应用**：`frontend/src`，提供知识库选择、智能路由开关、调试模式、对话与引用展示。  
- **Python RAG 服务**：`python/api/server.py` 提供统一 HTTP 接口，封装知识库管理、RAG 推理、智能路由、进度推送等能力。

核心目标：在保证问答质量和可解释性的前提下，提供稳定、可观测的知识库问答服务，并对智能路由、CoT 推理、进度状态等高级特性做了完整封装。

## 关键模块

- **RAG API 服务**（Python / FastAPI）  
  - 入口文件：`python/api/server.py`  
  - 主要接口：  
    - `/chat/basic`、`/chat/basic/stream`：纯大模型对话（无知识库、无 CoT）。  
    - `/rag/ask`：一次性 RAG 结果（答案 + 引用 + 推理链 + timing）。  
    - `/rag/ask/stream`：RAG 流式接口（SSE），供前端实时显示答案。  
    - `/knowledge/*`：知识库的创建、删除、文档增删改查、文件导入及去重。  
    - `/config/smart-router`、`/test/smart-router`：智能路由配置与调试。  
  - 统一封装 `qa_ask`，并适配 Haystack 2.x、Pydantic v2、FAISS 持久化、去重策略等。

- **知识库管理与检索**  
  - 模块：`python/rag/kb_manager.py`、`python/rag/qa_pipeline.py`。  
  - 特性：
    - 文档内容归一化 + SHA1 生成稳定 `doc_id`，自动跳过重复内容。
    - 支持 JSON/JSONL/纯文本文件导入，自动解析题库类结构（question/options/answer）。  
    - 对接自定义 `storage.retriever` 与向量化脚本，写入 Haystack DocumentStore，并手动保存 FAISS 索引。  
    - 提供一次性去重接口 `/knowledge/dedupe`，按归一化内容清洗重复文档。

- **智能路由（Smart Router）**  
  - 模块：`python/rag/smart_router.py`、`python/rag/smart_router_simple.py`、`safe_smart_route`。  
  - 逻辑：
    - 先由智能路由判断问题复杂度、是否需要 CoT / RAG、是否仅用通识回答。  
    - 超时自动降级到简化路由（`smart_route_simple`），保证系统不会卡死。  
    - 将路由结果写入 `timing.router_info`，前端在调试模式下展示：策略、重写问题、关键词、耗时等。

- **独立进度系统（Progress API + SSE）**
  - 模块：`python/api/progress_api.py`，在 `server.py` 中以独立路由挂载到 `/api/v1/progress/*`。  
  - 能力：
    - `POST /api/v1/progress/create`：创建进度会话，返回 `session_id`。  
    - `GET /api/v1/progress/{session_id}/stream`：通过 SSE 推送实时进度。  
    - `GET /api/v1/progress/{session_id}`：查询当前阶段与状态。  
    - `DELETE /api/v1/progress/{session_id}`：删除/回收会话。  
  - RAG 流程通过 `progress_callback` 汇报阶段：如 “智能路由”、“检索中”、“重排序”、“生成答案”等。

## 前后端交互与状态显示

- **前端页面**：`frontend/src/views/Chat.vue`  
  - 核心状态：
    - 知识库选择、是否使用知识库（`useKb`）、是否启用智能路由（`useSmartRouter`）、调试模式（`debugMode`）。  
    - 历史对话 `history`（按知识库/是否使用知识库做本地分区缓存）。  
    - 进度会话与显示：`currentProgressSession`、`currentProgress`、`progressEventSource`。  
  - 发送提问时流程：
    1. 调用 `createProgressSession` 创建进度会话，获取 `session_id`。  
    2. 调用 `startProgressStreaming(session_id)` 建立 SSE 连接，展示右上角进度标签。  
    3. 调用 `/rag/ask/stream`，在请求体中附带 `progress_session_id`。  
    4. 后端 RAG 流程每到一个阶段，通过 `progress_callback` 更新进度接口，SSE 即时推送给前端。  
    5. 答案流式完成后，前端在 `finally` 中执行 `cleanupProgress()`，关闭 SSE 并删除进度会话。
  - 进度标签展示：
    - 固定在右上角，显示当前阶段 `currentProgress.stage` 与说明 `currentProgress.message`。  
    - 不再在对话区使用 “正在生成回答...” 作为统一状态，而是通过标签明确区分“智能路由/检索/重排序/生成答案/已完成/错误”等阶段。  
    - 标签有 `active` / `completed` / `error` 三种样式，并带有渐变背景与脉冲动效。

- **答案与引用显示**：
  - 答案：
    - 流式阶段使用纯文本实时拼接；完成后再调用 `marked.parse` 渲染为 Markdown HTML。  
    - 对于智能路由选择 CoT 模式的回答，会额外解析出结构化的“推理步骤（CoT Steps）”并以卡片形式展示。  
  - 引用与调试信息：
    - `refs`：真正参与生成答案的引用文档。  
    - `allRefs`：后端 `timing.all_docs` 返回的全量检索结果（仅在调试模式下完全展开）。  
    - 调试模式下展示检索时间、重排序时间、生成时间、路由时间与总时间，以及知识库是否参与。

## 已完成的清理与简化

- **删除的 Python 调试脚本 / 零散测试**（保留 `python/test` 下规范化测试）：  
  - 根目录下与进度、流式、服务器启动调试相关的 `test_*.py`、`*progress*.py`、`*server*.py` 等一次性调试脚本已清理，避免混淆主入口。  
  - 这些脚本的主要用途（验证 SSE、验证流式、验证 RAG 组合）已经被稳定功能与前端集成替代。

- **删除的历史修复说明类 Markdown**：  
  - 如 `SERVER_UPGRADE_COMPLETE.md`、`PROGRESS_PUSH_INTEGRATION.md`、`INDEPENDENT_PROGRESS_SYSTEM.md`、`PROGRESS_DISPLAY_FIX_REPORT.md`、`COT_FORMAT_AND_STREAMING_FIXES.md`、`KB_PERSISTENCE_FIX_REPORT.md`、`COT_STRUCTURE_UPDATE.md` 以及 `python/SMART_ROUTER_SOLUTION.md` 等。  
  - 这些文件记录了中间迭代过程与 Bug 修复过程，目前关键设计与最终形态已经在本 `PROJECT_SUMMARY.md` 及 `docs/` 中沉淀，不再需要保留零散历史说明。

## 当前已知行为与注意事项

- **进度显示**：
  - 后端所有带 `progress_session_id` 的 RAG 流程都会通过进度系统汇报阶段。  
  - 前端现在对所有问答统一创建进度会话，不再仅限智能路由模式，因此用户始终能看到从“准备中 → 检索/重排序/生成 → 已完成”的完整进度。

- **错误处理**：
  - 若 RAG 流程出现异常，后端会通过进度接口标记“错误”阶段，并在 SSE 中返回 `error` 字段；前端进度标签会切换到“错误”样式，并在对话区提示“本次请求失败”。  
  - 进度会话在完成/错误后会被前端主动清理，避免后台堆积。

- **知识库使用开关**：
  - `useKb` 关闭时不会创建检索器，问答完全依赖大模型通识；开启时则会根据 `kb_id` 动态选择文档库和向量索引。  
  - CoT 与智能路由功能在是否使用知识库两种场景下均可工作，但调试信息和引用展示会有差异。

## 如何快速上手

1. **启动 Python RAG 服务**  
   - 进入 `python` 目录，执行 `python run_rag_server.py`（或从项目根运行 `start_server.bat` / `python\start_rag_server.bat`）。  
2. **启动前端**  
   - 进入 `frontend` 目录，执行 `npm install`（首次）然后 `npm run dev`。  
3. **浏览器访问**  
   - 打开前端地址（默认 `http://localhost:5173` 或 Vite 显示的端口），登录后进入“知识库问答”页面。  
   - 选择知识库与问答模式，输入问题即可看到：  
     - 聊天区的问答与 Markdown 格式答案；  
     - 右上角的进度状态标签；  
     - （可选）调试模式下的路由信息、检索/重排序/生成耗时与全量检索结果。

本文件作为项目的最终总览与结构说明，后续如有架构级变更，建议在此处同步更新，以替代新增零散的修复说明文档。

