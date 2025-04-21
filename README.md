# LLM模型训练和脚本执行管理系统

## 项目简介

本系统是一个用于管理和执行LLM模型训练和数据处理脚本的任务执行系统。系统采用Flask后端+SQLite数据库+Vue前端开发，支持任务管理、Agent监控和脚本模板管理功能。

## 系统架构

- **前端**：Vue.js + Bootstrap
- **后端**：Flask RESTful API
- **数据库**：SQLite
- **通信方式**：RESTful API + WebSocket（任务日志实时更新）

## 核心功能

1. **任务管理**：创建、查看、取消任务，查看任务日志
2. **Agent管理**：监控主Agent和子Agent状态，查看资源使用情况
3. **脚本模板**：管理和复用常用的bash脚本模板

## 项目结构

```
task_system/
│
├── app.py                  # 主入口
├── setup_master_agent.py   # 创建主agent
├── requirements.txt        # Python依赖包清单
├── README.md               # 项目说明文档
├── config.py               # 配置文件
│
├── backend/                # 后端代码
├── frontend/               # 前端代码
├── agent/                  # Agent实现
├── data/                   # 数据和日志
└── user_code/              # 用户Python代码目录
```

## 安装和使用

1. 安装依赖：
```
pip install -r requirements.txt
```

2. 启动服务：
```
python app.py
```

3. 创建主Agent：
```
python setup_master_agent.py
```

## 使用说明

访问 http://localhost:5000 打开Web界面，通过界面可以：
- 创建和管理任务
- 监控Agent状态和资源使用情况
- 管理脚本模板
