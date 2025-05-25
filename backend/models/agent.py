#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent数据模型
"""

import uuid
import json
from datetime import datetime
from backend.utils.database import get_db
from backend.utils.logger import system_logger

class Agent:
    """Agent数据模型类"""
    
    def __init__(self, id=None, name=None, type=None, status="online",
                 created_time=None, last_heartbeat_time=None, running_time=0,
                 cpu_cores=None, cpu_usage=0.0, memory_used=0, memory_total=0,
                 gpu_info=None, task_id=None, main_agent_id=None,
                 available_cpu_cores=None, monitor_file=None):
        """初始化Agent实例
        
        Args:
            id: Agent ID，唯一标识符
            name: Agent名称
            type: Agent类型，'main'或'sub'
            status: 状态，'online'或'offline'或'end'
            created_time: 创建时间
            last_heartbeat_time: 最后心跳时间
            running_time: 运行时长（秒）
            cpu_cores: CPU核心数
            cpu_usage: CPU使用率（百分比，可能超过100%）
            memory_used: 内存使用量（字节）
            memory_total: 内存总量（字节）
            gpu_info: GPU信息列表，每个元素为包含GPU信息的字典
            task_id: 关联的任务ID（子Agent才有）
            main_agent_id: 主Agent ID（子Agent才有）
            available_cpu_cores: 可用CPU核心数
            monitor_file: 监控文件路径
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.type = type
        self.status = status
        self.created_time = created_time or datetime.now()
        self.last_heartbeat_time = last_heartbeat_time
        self.running_time = running_time
        self.cpu_cores = cpu_cores
        self.cpu_usage = cpu_usage
        self.memory_used = memory_used
        self.memory_total = memory_total
        self.gpu_info = gpu_info or []
        self.task_id = task_id
        self.main_agent_id = main_agent_id
        self.available_cpu_cores = available_cpu_cores
        self.monitor_file = monitor_file
    
    @classmethod
    def create_agent(cls, name, type, cpu_cores=0, gpu_ids=None,
                    task_id=None, main_agent_id=None, monitor_file=None):
        """创建新Agent
        
        Args:
            name: Agent名称
            type: Agent类型，'main'或'sub'
            cpu_cores: CPU核心数
            gpu_ids: GPU ID列表
            task_id: 关联任务ID
            main_agent_id: 主Agent ID
            monitor_file: 监控文件路径
            
        Returns:
            agent: 新创建的Agent实例
        """
        db = get_db()
        
        # 生成唯一ID
        agent_id = str(uuid.uuid4())
        
        # 设置初始状态和时间
        status = "online"
        created_time = datetime.now()
        last_heartbeat_time = created_time
        
        # 初始化资源使用情况
        cpu_usage = 0.0
        memory_used = 0
        memory_total = 1
        
        # 设置可用资源
        available_cpu_cores = cpu_cores
        
        # 初始化GPU信息
        gpu_info = []
        if gpu_ids:
            for gpu_id in gpu_ids:
                gpu_info.append({
                    'gpu_id': gpu_id,
                    'usage': 0.0,
                    'memory_used': 0,
                    'memory_total': 1,
                    'is_available': True
                })
        
        # 将GPU信息转换为JSON字符串
        gpu_info_json = json.dumps(gpu_info)
        
        # 插入Agent记录
        query = """
            INSERT INTO agents (
                id, name, type, status, created_time, last_heartbeat_time,
                running_time, cpu_cores, cpu_usage, memory_used, memory_total, gpu_info,
                task_id, main_agent_id, available_cpu_cores, monitor_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            agent_id, name, type, status, created_time, last_heartbeat_time,
            0, cpu_cores, cpu_usage, memory_used, memory_total, gpu_info_json,
            task_id, main_agent_id, available_cpu_cores, monitor_file
        )
        
        try:
            db.execute(query, params)
            system_logger.info(f"Agent创建成功: ID={agent_id}, 名称={name}, 类型={type}")
            
            # 返回新创建的Agent实例
            return cls.get_agent_by_id(agent_id)
        except Exception as e:
            system_logger.error(f"Agent创建失败: {str(e)}")
            return None
    
    @classmethod
    def get_agent_by_id(cls, agent_id):
        """根据ID获取Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            agent: Agent实例，如果不存在则返回None
        """
        if not agent_id:
            return None
        
        db = get_db()
        
        # 查询Agent基本信息
        query = "SELECT * FROM agents WHERE id = ?"
        row = db.fetch_one(query, (agent_id,))
        
        if not row:
            return None
        
        # 解析JSON格式的GPU信息
        gpu_info = []
        if row['gpu_info']:
            try:
                gpu_info = json.loads(row['gpu_info'])
            except Exception as e:
                system_logger.error(f"解析GPU信息失败: {str(e)}")
        
        # 创建Agent实例
        agent = cls(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            status=row['status'],
            created_time=row['created_time'],
            last_heartbeat_time=row['last_heartbeat_time'],
            running_time=row['running_time'],
            cpu_cores=row['cpu_cores'],
            cpu_usage=row['cpu_usage'],
            memory_used=row['memory_used'],
            memory_total=row['memory_total'],
            gpu_info=gpu_info,
            task_id=row['task_id'],
            main_agent_id=row['main_agent_id'],
            available_cpu_cores=row['available_cpu_cores'],
            monitor_file=row['monitor_file']
        )
        
        return agent
    
    @classmethod
    def get_all_agents(cls):
        """获取所有Agent
        
        Returns:
            list: 所有Agent实例列表
        """
        db = get_db()
        
        query = "SELECT * FROM agents"
        rows = db.fetch_all(query)
        
        agents = []
        for row in rows:
            # 解析JSON格式的GPU信息
            gpu_info = []
            if row['gpu_info']:
                try:
                    gpu_info = json.loads(row['gpu_info'])
                except Exception as e:
                    system_logger.error(f"解析GPU信息失败: {str(e)}")
            
            agent = cls(
                id=row['id'],
                name=row['name'],
                type=row['type'],
                status=row['status'],
                created_time=row['created_time'],
                last_heartbeat_time=row['last_heartbeat_time'],
                running_time=row['running_time'],
                cpu_cores=row['cpu_cores'],
                cpu_usage=row['cpu_usage'],
                memory_used=row['memory_used'],
                memory_total=row['memory_total'],
                gpu_info=gpu_info,
                task_id=row['task_id'],
                main_agent_id=row['main_agent_id'],
                available_cpu_cores=row['available_cpu_cores'],
                monitor_file=row['monitor_file']
            )
            agents.append(agent)
        
        return agents
    
    def update_agent(self):
        """更新Agent信息到数据库
        
        Returns:
            bool: 更新是否成功
        """
        db = get_db()
        
        # 将GPU信息转换为JSON字符串
        gpu_info_json = json.dumps(self.gpu_info)
        
        # 更新Agent记录
        query = """
            UPDATE agents SET
                name = ?,
                type = ?,
                status = ?,
                last_heartbeat_time = ?,
                running_time = ?,
                cpu_cores = ?,
                cpu_usage = ?,
                memory_used = ?,
                memory_total = ?,
                gpu_info = ?,
                task_id = ?,
                main_agent_id = ?,
                available_cpu_cores = ?,
                monitor_file = ?
            WHERE id = ?
        """
        params = (
            self.name,
            self.type,
            self.status,
            self.last_heartbeat_time,
            self.running_time,
            self.cpu_cores,
            self.cpu_usage,
            self.memory_used,
            self.memory_total,
            gpu_info_json,
            self.task_id,
            self.main_agent_id,
            self.available_cpu_cores,
            self.monitor_file,
            self.id
        )
        
        try:
            db.execute(query, params)
            system_logger.info(f"更新Agent: ID={self.id}, 状态={self.status}")
            return True
        except Exception as e:
            system_logger.error(f"更新Agent失败: ID={self.id}, 错误={str(e)}")
            return False
    
    def cancel_agent(self):
        """取消Agent（设置为离线状态）
        
        Returns:
            bool: 取消是否成功
        """
        if self.status == 'offline':
            system_logger.warning(f"Agent已经处于离线状态: ID={self.id}")
            return True
        
        self.status = 'offline'
        result = self.update_agent()
        
        if result:
            system_logger.info(f"Agent已设置为离线: ID={self.id}")
        
        return result
    
    def has_available_resources(self, cpu_cores=None, gpu_count=None, gpu_memory=None):
        """检查Agent是否有足够的可用资源
        
        Args:
            cpu_cores: 所需CPU核心数
            gpu_count: 所需GPU数量
            gpu_memory: 每个GPU所需显存(MB)
            
        Returns:
            bool: 是否有足够资源
        """
        # 检查Agent是否在线
        if self.status != 'online':
            return False
        
        # 检查CPU资源
        if cpu_cores and (self.available_cpu_cores is None or 
                         self.available_cpu_cores < cpu_cores):
            return False
        
        # 检查GPU资源
        if gpu_count and gpu_count > 0:
            # 计算可用GPU数量
            available_gpus = [gpu for gpu in self.gpu_info if gpu.get('is_available', False)]
            if len(available_gpus) < gpu_count:
                return False
            
            # 如果指定了显存需求，检查每个可用GPU的显存
            if gpu_memory and gpu_memory > 0:
                # 这里简化处理，实际应该检查每个GPU的实际可用显存
                # 这部分逻辑可以在资源监控模块中实现更精确的检查
                pass
        
        return True
    
    def to_dict(self):
        """将Agent实例转换为字典，便于JSON序列化"""
            
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'created_time': self.created_time,
            'last_heartbeat_time': self.last_heartbeat_time,
            'running_time': self.running_time,
            'cpu_cores': self.cpu_cores,
            'cpu_usage': self.cpu_usage,
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'gpu_info': self.gpu_info,
            'task_id': self.task_id,
            'main_agent_id': self.main_agent_id,
            'available_cpu_cores': self.available_cpu_cores,
            'monitor_file': self.monitor_file
        }
