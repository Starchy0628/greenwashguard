# 谛观 GreenwashGuard — 企业漂绿风险智能监测系统

基于三异构大语言模型多数投票机制的A股上市公司环境披露"漂绿"风险测算系统。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia + Naive UI + ECharts + Tailwind CSS |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Uvicorn |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| AI模型 | DeepSeek-R1 + Qwen-Max + GLM-4.7（三模型集成） |

---

## 项目结构

```
greenwash_system/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── api/             # API 路由层
│   │   │   ├── stream_analysis.py   # SSE 流式分析（核心）
│   │   │   ├── pdf_analysis.py      # PDF 上传分析
│   │   │   ├── dashboard.py         # 仪表盘接口
│   │   │   ├── companies.py         # 企业查询接口
│   │   │   └── watchlist.py         # 关注列表接口
│   │   ├── core/            # 核心配置
│   │   │   ├── config.py            # 环境变量配置
│   │   │   ├── database.py          # 数据库连接
│   │   │   ├── utils.py             # 通用工具（SSE格式化等）
│   │   │   └── logging_setup.py     # 日志系统
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 数据校验模型
│   │   └── services/        # 业务逻辑层
│   │       ├── analysis_orchestrator.py  # 🔴 分析流程编排 + SSE推送
│   │       ├── llm_client.py            # LLM客户端（限流、熔断、重试）
│   │       ├── classifier.py            # 语句分类器
│   │       ├── sentiment.py             # 情感分析器
│   │       ├── fusion.py                # 模型融合（多数投票+集成平均）
│   │       ├── calculator.py            # GW指数计算器
│   │       ├── industry_service.py      # 行业基准服务
│   │       ├── mock_service.py          # Mock模式（演示用）
│   │       ├── text_utils.py            # 文本处理工具
│   │       ├── pdf_parser.py            # PDF解析（表格转文本+指标提取）
│   │       └── cninfo_crawler.py        # 巨潮资讯年报爬虫
│   ├── scripts/             # 工具脚本
│   │   ├── init_db.py                 # 初始化数据库
│   │   ├── seed_data.py               # 导入种子企业数据
│   │   └── batch_pipeline.py          # 批量分析流水线
│   ├── tests/               # 单元测试
│   ├── requirements.txt     # Python依赖
│   └── .env.example         # 环境变量模板
│
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/             # API 请求封装
│   │   ├── components/      # Vue 组件
│   │   │   ├── HeroBanner.vue         # 首屏+搜索+结果展示
│   │   │   ├── PdfUpload.vue          # PDF上传组件
│   │   │   ├── ResultCard.vue         # 结果卡片
│   │   │   ├── Top10Grid.vue          # Top10风险企业
│   │   │   ├── ChinaMap.vue           # 中国地图可视化
│   │   │   ├── MethodSteps.vue        # 方法说明+合作伙伴Logo
│   │   │   ├── SentenceList.vue       # 语句分类列表
│   │   │   └── ...
│   │   ├── stores/          # Pinia状态管理
│   │   └── assets/          # 静态资源
│   └── package.json
│
├── docs/                    # 文档
└── 启动系统.bat             # Windows一键启动脚本
```

---

## 核心概念

| 分类标签 | 含义 |
|---------|------|
| **substantive（实质性陈述）** | 有具体数据支撑的环境信息披露，如"环保投入5000万，减排15%" |
| **descriptive（描述性陈述）** | 空泛口号式表述，如"我们高度重视绿色发展"——**漂绿主要来源** |
| **non_env（非环保语句）** | 虽含环保关键词但实际讨论其他内容 |

**GW漂绿指数** = max(0, 企业描述性语句平均语调 - 同行业年度中位数)
- 数值越高，表示企业越倾向于用空泛口号"漂绿"
- 系统自动将行业内GW指数排名后20%标记为"预警"

---

## 快速启动

### 1. 环境准备
- Python 3.10+
- Node.js 18+

### 2. 后端启动
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # 复制配置文件，按需填入API Key
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 前端启动
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 4. Windows一键启动
直接双击 `启动系统.bat`

---

## 环境变量配置

在 `backend/.env` 中配置：

| 变量 | 说明 |
|------|------|
| `APP_MODE` | `mock`（默认，无需API Key演示）或 `real`（调用真实LLM） |
| `DATABASE_URL` | 数据库连接串，默认 SQLite |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（真实模式需要） |
| `QWEN_API_KEY` | 通义千问 API Key（真实模式需要） |
| `GLM_API_KEY` | 智谱 GLM API Key（真实模式需要） |
| `MDA_ROOT` | 本地MD&A文本目录绝对路径（可选，如 E:\path\to\CMDA_ALL） |

---

## 数据流向

```
用户输入股票代码/上传PDF
        ↓
[前端] 建立SSE连接，实时接收进度
        ↓
[后端] 检查数据库缓存 → 有则直接返回
        ↓
[爬虫/PDF解析] 获取年报文本
        ↓
[文本处理] 分句 → 关键词过滤提取环境语句
        ↓
[三模型并行分类] DeepSeek + Qwen + GLM 独立判断
        ↓
[多数投票] 三模型投票决定最终分类，计算Kappa一致性
        ↓
[情感打分] 仅对描述性语句打 -1~1 情感分
        ↓
[GW指数计算] 企业语调 - 行业中位数（下限为0）
        ↓
[数据库] 保存结果 → SSE推送给前端
        ↓
[前端] 实时更新UI：进度→结果→图表
```

---

## 注意事项

- **Mock模式**无需API Key即可体验全流程，使用内置规则模拟LLM判断
- **真实模式**需要三个平台的API Key，注意控制调用量（约每句4000 tokens）
- 金融类、ST/*ST/PT公司不在分析范围内
- 本地MD&A数据目录较大，不要提交到Git（已在.gitignore中排除）
