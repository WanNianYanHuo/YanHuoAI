# Haystack RAG 项目文档（整合版）

本文档由项目内原有 Markdown 文件整合而成，便于统一查阅。

---

## 一、快速开始（原 QUICK_START.md）

### 系统已配置完成 ✅

- **Embedding 模型**: BAAI/bge-small-zh (512维)
- **向量数据库**: FAISS
- **文档切分**: 500字符/块，50字符重叠
- **检索参数**: Top-K = 3
- **Prompt**: 医学专家问答格式

### 三步开始使用

1. **准备医学文档**：将 TXT 放入 `python/demo/txt_data/`（支持 UTF-8, GBK, GB2312, Latin1）。
2. **构建知识库**：`cd python/demo` 后执行 `python import_txt_faiss.py`（会读 txt_data、切分、向量化、写入 FAISS 并去重）。
3. **启动服务并测试**：
   - 后端：`cd python` 后执行 `python run.py` 或 `python scripts/run/run_backend.py`，服务在 http://127.0.0.1:8000
   - 前端：`cd frontend` → `npm install` → `npm run dev`，前端在 http://localhost:5173
   - 在聊天页输入问题测试（如「什么是气虚证？」）。

### 启动入口汇总

- **后端**：在 `python` 目录下执行 `python run.py`，或执行 `scripts/run/run_backend.bat`（Windows）。
- **前端**：在 `frontend` 目录下执行 `npm run dev`。

---

## 二、RAG 使用指南（原 RAG_USAGE_GUIDE.md）

### 技术栈

- Embedding: BAAI/bge-small-zh (512维)
- 向量库: FAISS + SQLite
- 切分: 500字符/块，50字符重叠
- Top-K: 3
- LLM: Ollama / ZhipuAI

### 核心模块

- **知识库构建**：`python/demo/import_txt_faiss.py`（读文档、切分、bge-small-zh 向量化、写入 FAISS、去重）。
- **向量检索**：`python/storage/retriever.py`（问题向量化、FAISS Top-3、可重排序）。
- **RAG 问答**：`python/rag/qa_pipeline.py`（检索 → 重排序 → 上下文评估 → Prompt 构建 → LLM 流式输出）。

### 配置与 API

- 配置文件：`python/config/settings.py`（EMBEDDING_*、TOP_K、CHUNK_*、LLM_BACKEND 等）。
- 流式问答：`POST /rag/ask/stream`，请求体可含 `question`、`kb_id`、`use_kb`、`llm_backend`、`use_cot`；响应为 SSE 流。

### 多知识库

- 数据目录：`python/knowledge_bases/`，每库一子目录（如 kb_0001），内含 docs.db、faiss 等；`_mapping.json` 为展示名与存储 key 映射。

---

## 三、测试套件（原 test/README.md + TEST_SUMMARY.md）

### 测试目录与运行方式

所有测试与测试工具统一放在 **python/test/** 下：

- `run_all_tests.py`：运行全部测试并生成报告。
- `run_zhipu_test.py`：智谱相关测试。
- `test_*.py`：各模块单测（基础功能、知识库管理、文件导入、API、错误处理、性能、集成、智谱等）。
- `db_and_backend_test_tool.py`：数据库与后端图形测试工具（原 scripts 内，已迁入 test/）。

运行示例（均在 `python` 目录下）：

```bash
python test/run_all_tests.py
python test/run_all_tests.py --tests test_basic_functionality
python -m unittest test.test_basic_functionality
```

智谱测试需在 `config/settings.py` 中配置 `ZHIPU_API_KEY`。

### 测试总结要点

- 覆盖：Haystack 2.x 迁移、知识库 CRUD、文件导入、API、智谱集成、性能与健壮性。
- 关键修复：FAISSDocumentStore 迁移、write_documents 参数、JSONL 支持、文档持久化与 embedding 生成等。

---

## 四、脚本说明（原 scripts/README.md）

- **run/run_backend.py**：启动 RAG 后端（需在 python 目录下执行）。
- **run/run_backend.bat**：Windows 下一键启动后端。
- **pull_ollama_model.py**：从本地 Ollama 拉取模型（如 deepseek-v3.1:671b-cloud）。
- **kb_validate_and_repair.py**：知识库校验与修复（status/repair），建议启动前在 `python/` 下执行一次。
- 数据库与后端图形测试工具：见 **test/db_and_backend_test_tool.py**。

---

## 五、评估系统（原 evaluation/README.md）

- 评估模块：`evaluation/`（metrics、evaluation_dataset、evaluator、visualizer）。
- 数据集格式：JSONL，每行含 `question`、`ground_truth` 等。
- 运行示例：`python scripts/evaluate.py --dataset data/evaluation_dataset_sample.jsonl --output-dir evaluation_results --verbose`。
- 输出：results.jsonl、report.txt、report.md、report.json。

---

## 六、评估报告摘要（evaluation_results / evaluation_results_test）

- **evaluation_results/report.md**（10 样本）：平均响应约 29.24s，平均检索文档约 4.5，F1 约 30.32%，无错误。
- **evaluation_results_test/report.md**（30 样本）：平均响应约 29.26s，平均检索文档 5，F1 约 20.52%，recall 约 57.42%，无错误。

详细表格见各自目录下的 report.md / report.json。

---

## 七、常见问题

- **添加文档**：放入 `demo/txt_data/` 后重新运行 `demo/import_txt_faiss.py`（会去重）。
- **切换 LLM**：修改 `config/settings.py` 的 `LLM_BACKEND` 或在 API 中传 `llm_backend`。
- **调整检索数量**：修改 `config/settings.py` 的 `TOP_K`。
- **知识库路径**：已固定为 `python/knowledge_bases`，与运行时的当前目录无关。

---

*文档整合日期：2026-03-15。原分散的 QUICK_START.md、RAG_USAGE_GUIDE.md、test/README.md、test/TEST_SUMMARY.md、scripts/README.md、evaluation/README.md 及评估 report 已合并入本文档，原文件可保留作备份或删除以避免重复。*
