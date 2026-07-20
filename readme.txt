============================================================
谛观 GreenwashGuard - 企业漂绿风险智能监测系统
============================================================

【文件夹作用】
项目根目录，包含整个参赛作品的所有文件。

【文件/子文件夹说明】
- backend/             后端服务代码（FastAPI）
- frontend/            前端界面代码（Vue 3，已预构建dist）
- 系统启动运行.py       Windows一键启动脚本（无日志版本）
- README.md            项目说明文档（快速启动指南）
- 技术文档.md           详细技术设计文档
- 数据来源说明.txt      CNRDS数据来源版权声明
- .gitignore/.gitattributes  Git版本控制配置

【启动方式】
Windows环境下双击运行 "系统启动运行.py" 即可一键启动前后端服务。

启动流程：
  1. 自动检查并安装Python依赖（首次启动）
  2. 自动创建.env配置文件（首次启动）
  3. 后台静默启动uvicorn服务（无控制台窗口）
  4. 等待服务就绪后自动打开浏览器
  5. 访问地址：http://localhost:8000

也可手动启动：
  1. 后端：cd backend && pip install -r requirements.txt && python -m uvicorn app.main:app --port 8000
  2. 浏览器访问：http://localhost:8000

【停止服务】
在任务管理器中结束 pythonw.exe / python.exe 进程。

【注意事项】
- 默认使用Mock模式，无需API Key即可体验完整功能
- 真实模式需要配置DeepSeek、Qwen、GLM三个大模型的API Key
- 前端已预构建，普通使用无需安装Node.js
