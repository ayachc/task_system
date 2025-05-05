## 背景
在做llm模型训练和数据集处理时，总是需要人力观察脚本执行进度，然后手动执行下一个脚本，浪费时间和精力。所以我希望设计并实现一个脚本执行任务执行系统。这个项目只有我一个人开发，我希望它能结构清晰，不要有太多耦合，便于调试，适合长期维护和添加新功能与页面。项目一般是个人使用，项目的安全性和容器化都暂不用考虑。我会更关注后端实现，前端web的设计与实现都需要你来帮助完成。


## 初步设计
现在我们需要设计并实现一个方便我做科研实验的脚本任务执行系统。它需要有一个网页，网页由侧边栏可以切换几个子网页，分别是任务管理、agent管理、bash脚本模板。系统为前后端分离架构（Flask + Vue），包含数据库：SQLite，通信方式为RESTful API，核心组件是Web Server + Agents。server有公网端口，会展示web页面（包括任务队列、agent信息等）。agent有主agent和子agent，agent均没有公网端口，但是主agent可以向server发送心跳来传递任务完成情况，并根据server的回复获取新任务并创建子agent执行。


## 详细设计

### 数据库和日志
数据库：使用SQLite作为数据存储，便于部署和维护
日志系统：使用结构化日志，记录系统运行状态和错误信息


### 任务管理

#### 前端功能描述
**页面组成**：
1. 任务列表页
2. 新建任务表单
3. 任务详情浮窗

**交互逻辑**：
- **列表展示**：
  - 表格列：ID、名称、模板类型、优先级、状态（带颜色标识）、创建时间、详情和取消按钮
  - 支持多条件筛选（状态/名称/模板类型/脚本内容子串等）
  - 操作按钮：取消（二次确认）、查看详情

- **新建任务**：
  - 表单字段：
    - 必填：名称（文本输入）、模板类型（下拉选择+自定义选项）
    - 选填：优先级（1-5级滑块）、CPU/GPU资源（数字输入）、显存（下拉选择）
    - 脚本内容（代码编辑器，有代码高亮，可以根据模板自动填充）
    - 依赖任务（一个输入框，依赖任务ID由逗号分隔）
  - 提交时前端校验：名称非空、资源数值合法、依赖任务ID合法

- **任务详情**：
  - 分两部分布局：详细信息（上）、执行日志（下）
  - 错误状态时显示红色警示条，日志区域自动滚动到底部
  - 支持日志实时刷新（通过WebSocket）


#### 后端功能逻辑

**数据模型**：
```python
class Task:
    id: int # 任务ID，唯一标识符
    name: str # 任务名称
    template_type: str # 模板类型
    priority: int # 优先级(1-5, 1最高)
    depends_on: list[int] # 依赖任务ID列表
    status: str # 状态(blocked, waiting, running, completed, failed, canceled)
    created_time: datetime
    script_content: str
    cpu_cores: int
    gpu_count: int
    gpu_memory: int
    start_time: datetime
    end_time: datetime
    execution_time: int
    agent_id: str
    log_file: str
```

**task.py函数**
```python
class Task():
    __init__()
    create_task()
    get_task_by_id()
    get_task_in_range()
    get_max_id()
    get_all_tasks()
    update_task()
    cancel_task()
    to_dict()
```

**task_service.py函数**
```python
class TaskService():
    __init__()
    create_task()
    get_task_by_id()
    get_task_in_range()
    get_task_in_page()
    get_all_tasks()
    update_task()
    update_task_by_key()
    cancel_task()
    append_task_log() # 将新的日志添加到任务日志文件中
    get_task_log() # 从任务日志文件中获取日志
    find_task_for_agent() # 获取任务，按优先级排序，逐个试探agent能否执行，如果可以则返回任务
```

**额外细节**
1. 任务不支持删除，只支持取消，取消的任务依然留有记录，任务失败不会自动重试。
2. 任务的主要数据是bash脚本，并且我们只需要bash脚本的具体内容而不是一个脚本路径。
3. 定义一下模板类型：在脚本模板页面会有不同的bash脚本模板，每个模板会有一个名字。
4. 任务服务不会主动根据任务分配给agent，而是由agent服务调用find_task_for_agent函数来获取任务。






### agent管理

#### 前端功能描述
**页面组成**：
1. agent列表页

**交互逻辑**：
- **列表展示**：
  - 树形结构：主Agent为父节点，子Agent为子节点
  - agent卡片显示：id + 类型 + 名称 + 状态（在线绿色、离线灰色）+ 运行时长 + CPU使用率
  - 主Agent卡片额外显示：可使用和总CPU核心数，所有GPU的使用率和显存使用量（使用率为数字百分比，显存使用量为进度条形式，每个GPU独立显示）
  - 子Agent卡片额外显示：关联任务ID + GPU使用率和显存使用量


#### 后端功能逻辑
**数据模型**：
```python
class Agent:
    id: str
    name: str
    type: str # "main" or "sub"
    status: str # "online" or "offline"
    created_time: datetime
    last_heartbeat_time: datetime
    running_time: int
    cpu_cores: int
    cpu_usage: float
    memory_usage: float
    gpu_info: list[dict[str, float]]
    task_id: str
    main_agent_id: str
    available_cpu_cores: int
    monitor_file: str
```

**agent.py函数**
```python
class AgentService():
    __init__()
    create_agent()
    get_agent_by_id()
    get_all_agents()
    update_agent()
    cancel_agent()
    has_available_resources()
    to_dict()
```

**agent_service.py函数**
```python
class AgentService():
    __init__()
    create_main_agent()
    create_sub_agent()
    get_agent_by_id()
    get_all_agents()
    update_agent()
    cancel_agent()
    check_agents_status()
    handle_heartbeat()
```

#### agent执行端功能

**main_agent.py**
```python
class MainAgent():
    __init__()
    register()
    start_heartbeat()
    get_resource_info()
    send_heartbeat()
    handle_heartbeat_response()
    create_sub_agent()
    cleanup()
    run()

setup_main_agent()
```

**sub_agent.py**
```python
class SubAgent():
    __init__()
    register()
    start_heartbeat()
    get_resource_info()
    send_heartbeat()
    start_task()
    read_task_output()
    cleanup()
    run()

setup_sub_agent()
```

**resource_util.py**
```python
class ResourceUtil():
    __init__()
    get_gpu_info() # 使用pynvml获取所有gpu的id、使用率、显存使用量
    get_cpu_core_count() # 优先考虑cgroups限制，失败后使用psutil获取可使用cpu核心数
    get_cpu_usage() # 使用psutil获取当前进程及其所有子进程的cpu使用率总和
    get_memory_usage() # 使用psutil获取当前进程及其所有子进程的内存使用情况
    
```

**额外细节**
1. agent分为两类：主agent和子agent。主agent负责记录资源总量和可分配量，创建子agent执行任务，一个子agent只会执行一个任务，执行完任务后子agent会自动退出。
2. 主agent一般由用户手动创建，不执行任务，每2秒向server发送一次心跳，传递主agent资源使用情况并从server的回复中获取任务，然后根据任务的资源需求来更新资源并创建子agent执行该任务。
3. 子agent每1秒向server发送一次心跳，发送子agent资源使用情况以及任务新产生的stdout、stderr。

我们继续修改agent服务，现在我们来修改前端部分：
请逐步分析现在agent服务的前端部分，当前有一个agent列表显示页面，agent列表我希望是不分页的，然后每个主agent和他的子agent在一块（子agent能显示在主agent下面，每两个主agent间有间隔）。每个agent都会显示id、名字、类型、状态、创建时间、上次心跳时间、正在使用的cpu核心数，总核心数，cpu使用率（百分比），内存使用率，gpu信息。子aget额外显示一个正在运行的任务id。每个agent的信息显示，如果一行只显示一个，右边会很空。请自行判断一行显示多少种信息，其中每个gpu都显示，显存用类似进度条可视化。请你逐步分析，需要修改或者重构哪些文件，并做出修改。

### 脚本模板
请简洁的实现
脚本模板页面会显示所有脚本模板，模板包含名称和一个字符串形式的bash脚本内容。会有一个添加脚本模板的接口。





task_system/
│
├── app.py                  # 主入口
├── setup_master_agent.py   # 创建主agent
├── requirements.txt        # Python依赖包清单
├── README.md               # 项目说明文档
├── config.py               # 配置文件，在类中
│
├── backend/
│   ├── models/                 # 数据模型
│   │   ├── task.py             # 任务模型
│   │   ├── agent.py            # Agent模型
│   │   └── template.py         # 脚本模板模型
│   ├── services/               # 业务服务
│   │   ├── task_service.py     # 任务调度服务
│   │   ├── agent_service.py    # Agent管理服务
│   │   └── template_service.py # 脚本模板服务
│   ├── api/                    # API接口
│   │   ├── task_api.py         # 任务管理接口
│   │   ├── agent_api.py        # Agent管理接口
│   │   └── template_api.py     # 脚本模板管理接口
│   └── utils/
│       ├── logger.py           # 日志系统
│       └── database.py         # 数据库操作
│
├── frontend/                   # Vue前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── Tasks.vue       # 任务管理
│   │   │   └── Agents.vue      # Agent监控
│   │   ├── components/         # 通用组件
│   │   ├── router/             # 前端路由
│   │   └── store/              # Vuex状态管理
│   └── public/                 # 静态资源
│
├── agent/
│   ├── master_agent.py         # 主Agent实现
│   ├── worker_agent.py         # 子Agent实现
│   └── resource_util.py        # 资源监控工具
│
├── data/
│   ├── database/               # SQLite数据库文件
│   └── logs/
│       ├── tasks/              # 按任务ID存储日志
│       └── system/             # 系统运行日志
│
└── user_code/                  # 用户Python代码目录
    ├── test/                   # 测试相关Python脚本
    └── utils/                  # 用户自定义工具函数脚本

