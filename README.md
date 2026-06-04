# PageIndex Web 可视化RAG系统使用说明

## 📖 目录

- [系统概述](#系统概述)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速启动](#快速启动)
- [功能说明](#功能说明)
- [支持的文件格式](#支持的文件格式)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 系统概述

**PageIndex Web** 是基于 PageIndex 开源项目构建的 **Web 可视化RAG系统**，提供了完整的文档处理、树结构可视化和智能问答功能。

### 什么是 PageIndex？

PageIndex 是由 [Vectify AI](https://vectify.ai) 开源的**无向量化、基于推理的 RAG（检索增强生成）系统**。与传统基于向量数据库的 RAG 不同，PageIndex 通过构建文档的**层级树状索引**，利用 LLM 进行**推理式检索**，模拟人类专家阅读文档的方式。

github: https://github.com/VectifyAI/PageIndex

### 本系统的特点

- 🌐 **Web 可视化界面**：基于 Vue3 + Vite 构建的现代化前端
- 📁 **多格式支持**：支持 PDF、Markdown、TXT、JSON、CSV、Word 等多种格式
- 🌲 **树结构可视化**：交互式文档层级树展示，支持搜索、展开/折叠
- 💬 **智能问答**：基于树结构的推理式检索，实时流式输出答案
- 🔧 **LLM 配置**：支持切换不同的 LLM 服务（已配置 DeepSeek API）
- 📊 **实时进度**：文档处理进度实时推送（SSE）

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **无向量数据库** | 不需要向量数据库，使用文档结构 + LLM 推理进行检索 |
| **无分块** | 文档按自然章节组织，而非人为切块 |
| **类人检索** | 模拟人类专家浏览文档、提取知识的方式 |
| **可解释性强** | 检索基于推理过程，可追踪、可解释，附带页码和章节引用 |
| **多格式支持** | 自动将 TXT/JSON/CSV/Word 转换为 Markdown 再处理 |

### 工作原理（两阶段）

1. **生成树状索引**：将文档转换为语义化的层级树结构（类似增强版目录）
2. **推理式检索**：通过 LLM 在树结构上进行推理搜索，找到最相关的章节并生成答案

---

## 系统架构

```
PageIndex-main/
├── server/                    # FastAPI 后端
│   ├── main.py                # 应用入口
│   ├── routers/               # API 路由
│   │   ├── documents.py       # 文档上传、列表、树结构 API
│   │   ├── chat.py            # 问答 SSE 流式 API
│   │   └── config.py          # LLM 配置 API
│   └── services/              # 业务逻辑
│       ├── document_service.py    # 文档处理编排
│       ├── tree_service.py        # 树结构操作
│       ├── chat_service.py        # RAG 问答管道
│       └── converter_service.py   # 格式转换（TXT/JSON/CSV/Word → Markdown）
│
├── web/                       # Vue3 前端
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── Home.vue       # 首页（上传）
│   │   │   └── DocumentView.vue   # 文档详情（树+问答）
│   │   ├── components/        # UI 组件
│   │   │   ├── document/      # 文档相关组件
│   │   │   ├── tree/          # 树可视化组件
│   │   │   └── chat/          # 问答组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── api/               # API 调用封装
│   │   └── composables/       # 可复用逻辑（SSE）
│   └── vite.config.js         # Vite 配置（代理到后端 8001 端口）
│
├── pageindex/                 # 核心 PageIndex 包
│   ├── page_index.py          # PDF 处理核心
│   ├── page_index_md.py       # Markdown 处理
│   └── utils.py               # 工具函数（已适配 DeepSeek API）
│
├── uploads/                   # 上传文件存储目录
├── results/                   # 生成的树结构 JSON 存储目录
├── .env                       # 环境变量（API Key 配置）
└── start.bat                  # Windows 一键启动脚本
```

---

## 快速启动

### 前置要求

- **Python 3.10+**（推荐使用 Miniconda）
- **Node.js 18+**（前端开发）
- **DeepSeek API Key**（或其他 OpenAI 兼容 API）

### 第 1 步：安装 Python 依赖

```bash
cd PageIndex-main
pip install --upgrade -r requirements.txt
pip install python-docx  # Word 文件支持
```

### 第 2 步：配置环境变量

在项目根目录创建 `.env` 文件：

```env
CHATGPT_API_KEY=sk-你的DeepSeek_API_Key
API_BASE_URL=https://api.deepseek.com
```

> **注意**：如果使用 OpenAI，则 `API_BASE_URL` 留空或删除该行。

### 第 3 步：安装前端依赖

```bash
cd web
npm install
```

> **重要**：如果遇到 Vite 7 与 Node.js 版本不兼容的问题，降级 Vite：
> ```bash
> npm install vite@5 @vitejs/plugin-vue@5
> ```

### 第 4 步：启动系统

#### 方式一：使用启动脚本（推荐）

在项目根目录双击运行 `start.bat`，或在命令行执行：

```bash
start.bat
```

这会自动启动：
- **后端服务**：http://localhost:8001
- **前端服务**：http://localhost:3000

#### 方式二：手动启动

**启动后端**（在项目根目录）：
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8001
```

**启动前端**（在 `web/` 目录）：
```bash
npm run dev
```

### 第 5 步：访问系统

在浏览器打开：**http://localhost:3000**

---

## 功能说明

### 1. 文档上传

**支持的格式**：PDF、Markdown (.md)、TXT、JSON、CSV、Word (.docx/.doc)

**操作步骤**：
1. 在首页点击"Upload Document"区域或拖拽文件
2. 系统自动开始处理（提取文本 → 分析结构 → 生成树 → 生成摘要）
3. 处理完成后自动跳转到文档详情页

**处理时间**：
- 小文件（<10页）：约 30-60 秒
- 中等文件（10-50页）：约 1-3 分钟
- 大文件（>50页）：约 3-10 分钟

> 处理时间取决于文档复杂度和 LLM API 响应速度。

### 2. 树结构可视化

**功能特性**：
- 📂 **层级展示**：按文档章节层级显示树结构
- 🔍 **搜索过滤**：实时搜索节点标题
- 🎨 **深度着色**：不同层级用不同颜色边框标识
- ✨ **高亮同步**：问答时自动高亮相关节点
- 🔄 **展开/折叠**：一键展开或折叠所有节点

**节点信息**：
- 标题
- 节点 ID
- 页码范围（PDF）或行号（Markdown）
- 内容摘要

### 3. 智能问答

**RAG 流程**：
1. **树搜索阶段**：
   - 将完整树骨架（不含原文）+ 用户问题发送给 LLM
   - LLM 推理出最相关的节点列表
   - 显示"思考过程"和"找到的节点"

2. **答案生成阶段**：
   - 提取相关节点的原文内容
   - 结合问题生成答案
   - 实时流式输出（SSE）

**特色功能**：
- 💭 **思考过程可见**：展示 LLM 的推理逻辑
- 🎯 **节点引用**：答案中标注引用的节点，点击可跳转
- 🔗 **树同步高亮**：左侧树自动高亮相关节点
- 📜 **对话历史**：保留完整对话上下文

### 4. LLM 配置

**可配置项**：
- API Key
- API Base URL（支持 OpenAI 兼容接口）
- 模型名称（如 `deepseek-chat`、`gpt-4o` 等）

**操作步骤**：
1. 点击右上角"Settings"图标
2. 修改配置
3. 点击"Test Connection"验证连接
4. 保存配置

---

## 支持的文件格式

### 1. PDF
- **处理方式**：提取文本 → 检测目录 → 构建树结构 → 生成摘要
- **适用场景**：学术论文、技术手册、财务报告、法律文件

### 2. Markdown (.md)
- **处理方式**：按 `#` 标题层级解析 → 构建树结构 → 生成摘要
- **适用场景**：技术文档、博客文章、项目说明

### 3. TXT
- **转换策略**：
  - 自动检测中文章节标题（第X章、第X节）
  - 检测英文标题（全大写、编号标题）
  - 如无明显标题，按固定行数分段
- **适用场景**：纯文本文档、小说、日志

### 4. JSON
- **转换策略**：
  - 嵌套对象 → Markdown 标题层级
  - 对象数组 → 表格 + 详情章节
  - 基本类型数组 → 列表
- **适用场景**：API 响应、配置文件、结构化数据

### 5. CSV
- **转换策略**：
  - 自动检测分隔符（`,` `;` `\t` `|`）
  - 生成数据概览表格
  - 每行数据生成详情章节
- **适用场景**：数据表格、统计报表、导出数据

### 6. Word (.docx)
- **转换策略**：
  - 提取 Heading 样式 → Markdown 标题
  - 保留加粗、斜体格式
  - 表格转换为 Markdown 表格
- **适用场景**：商务文档、报告、合同

> **转换原理**：所有非 PDF/Markdown 格式都会先转换为 Markdown，再走统一的 `md_to_tree` 处理管道。

---

## 配置说明

### 后端配置

**环境变量** (`.env`)：
```env
CHATGPT_API_KEY=your_api_key_here
API_BASE_URL=https://api.deepseek.com  # 可选，OpenAI 兼容接口
```

**LLM 配置** (`pageindex/config.yaml`)：
```yaml
model: "deepseek-chat"           # 模型名称
toc_check_page_num: 20            # 检查目录的页数（PDF）
max_page_num_each_node: 10        # 每个节点最大页数（PDF）
max_token_num_each_node: 20000    # 每个节点最大 token 数
if_add_node_id: "yes"             # 是否添加节点 ID
if_add_node_summary: "yes"        # 是否添加节点摘要
if_add_doc_description: "no"      # 是否添加文档描述
if_add_node_text: "no"            # 是否添加节点原文
```

### 前端配置

**Vite 代理** (`web/vite.config.js`)：
```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',  // 后端地址
        changeOrigin: true,
      },
    },
  },
})
```

---

## 常见问题

### Q1: 文档一直显示"Processing..."怎么办？

**原因**：后端进程可能已停止，但元数据状态未更新。

**解决方案**：
1. 刷新页面，系统会自动重新触发处理
2. 检查后端日志是否有错误
3. 确认 API Key 配置正确且有效

### Q2: 上传文件后报错"Unsupported file type"

**原因**：文件扩展名不在支持列表中。

**解决方案**：
- 确认文件扩展名为：`.pdf` `.md` `.markdown` `.txt` `.json` `.csv` `.docx` `.doc`
- 检查文件名是否包含特殊字符

### Q3: 问答时没有返回结果

**可能原因**：
1. LLM API 配置错误
2. 树结构未正确生成
3. 网络连接问题

**排查步骤**：
1. 在"Settings"中测试 API 连接
2. 检查文档是否处理完成（状态为"completed"）
3. 查看浏览器控制台和后端日志

### Q4: 如何切换到 OpenAI API？

修改 `.env` 文件：
```env
CHATGPT_API_KEY=sk-你的OpenAI_API_Key
API_BASE_URL=  # 留空或删除此行
```

修改 `pageindex/config.yaml`：
```yaml
model: "gpt-4o-2024-11-20"  # 或其他 OpenAI 模型
```

重启后端服务。

### Q5: 前端启动报错"crypto.hash is not a function"

**原因**：Vite 7 与 Node.js 21.6.2 不兼容。

**解决方案**：
```bash
cd web
npm install vite@5 @vitejs/plugin-vue@5
```

### Q6: 后端启动报错"ModuleNotFoundError: No module named 'PyPDF2'"

**原因**：依赖未正确安装到当前 Python 环境。

**解决方案**：
```bash
python -m pip install --upgrade -r requirements.txt
python -m pip install python-docx
```

### Q7: 如何查看处理日志？

**后端日志**：
- 如果用 `start.bat` 启动，日志在启动的命令行窗口
- 如果手动启动，日志在当前终端

**前端日志**：
- 打开浏览器开发者工具（F12）→ Console 标签

### Q8: 文件上传大小限制是多少？

**当前限制**：50MB

**修改方法**：编辑 `server/routers/documents.py`：
```python
if len(content) > 50 * 1024 * 1024:  # 改为你需要的大小
    raise HTTPException(400, "File too large. Maximum size is 50MB.")
```

---

## 技术栈

### 后端
- **FastAPI**：现代化 Python Web 框架
- **Pydantic**：数据验证
- **asyncio**：异步处理
- **python-docx**：Word 文件解析
- **PyPDF2 / pymupdf**：PDF 解析

### 前端
- **Vue 3**：渐进式 JavaScript 框架
- **Vite**：下一代前端构建工具
- **Pinia**：Vue 状态管理
- **Vue Router**：路由管理
- **markdown-it**：Markdown 渲染

### LLM 集成
- **DeepSeek API**（默认）：OpenAI 兼容接口
- **OpenAI API**：可切换
- **自定义 API**：支持任何 OpenAI 兼容接口

---

## 开发说明

### 后端开发

启动开发服务器（自动重载）：
```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8001
```

### 前端开发

启动开发服务器（热更新）：
```bash
cd web
npm run dev
```

构建生产版本：
```bash
cd web
npm run build
```

构建产物会输出到 `server/static/`，可直接由后端静态文件服务提供。

---

## 许可证

MIT License - Copyright (c) 2025 Vectify AI

---

## 联系方式

- 🌐 官网：https://vectify.ai
- 📧 邮箱：通过 [Contact Form](https://ii2abc2jejf.typeform.com/to/tK3AXl8T) 联系
- 💬 Discord：https://discord.com/invite/VuXuf29EUj
- 🐦 Twitter：https://x.com/PageIndexAI

---

**祝使用愉快！如有问题，欢迎提交 Issue 或加入 Discord 社区交流。**
