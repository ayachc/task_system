#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent数据模型
"""

import uuid
from datetime import datetime
from backend.utils.database import get_db
from backend.utils.logger import system_logger

class Agent:
    """Agent数据模型类"""
    
    def __init__(self, id=None, name=None, type=None, status="online",
                 created_time=None, last_heartbeat_time=None, running_time=0,
                 cpu_cores=None, cpu_usage=0.0, memory_usage=0.0,
                 gpu_ids=None, gpu_usage=None, gpu_memory_usage=None,
                 task_id=None, main_agent_id=None,
                 available_cpu_cores=None, available_gpu_ids=None):
        """初始化Agent实例
        
        Args:
            id: Agent ID，唯一标识符
            name: Agent名称
            type: Agent类型，'main'或'sub'
            status: 状态，'online'或'offline'
            created_time: 创建时间
            last_heartbeat_time: 最后心跳时间
            running_time: 运行时长（秒）
            cpu_cores: CPU核心数
            cpu_usage: CPU使用率
            memory_usage: 内存使用率
            gpu_ids: GPU ID列表
            gpu_usage: GPU使用率字典，键为GPU ID，值为使用率
            gpu_memory_usage: GPU显存使用率字典，键为GPU ID，值为使用率
            task_id: 关联的任务ID（子Agent才有）
            main_agent_id: 主Agent ID（子Agent才有）
            available_cpu_cores: 可用CPU核心数
            available_gpu_ids: 可用GPU ID列表
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
        self.memory_usage = memory_usage
        self.gpu_ids = gpu_ids or []
        self.gpu_usage = gpu_usage or {}
        self.gpu_memory_usage = gpu_memory_usage or {}
        self.task_id = task_id
        self.main_agent_id = main_agent_id
        self.available_cpu_cores = available_cpu_cores
        self.available_gpu_ids = available_gpu_ids or []
    
    @classmethod
    def create_agent(cls, name, type, cpu_cores=None, gpu_ids=None,
                    task_id=None, main_agent_id=None):
        """创建新Agent
        
        Args:
            name: Agent名称
            type: Agent类型，'main'或'sub'
            cpu_cores: CPU核心数
            gpu_ids: GPU ID列表
            task_id: 关联任务ID
            main_agent_id: 主Agent ID
            
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
        memory_usage = 0.0
        
        # 设置可用资源
        available_cpu_cores = cpu_cores
        available_gpu_ids = gpu_ids.copy() if gpu_ids else []
        
        # 插入Agent记录
        query = """
            INSERT INTO agents (
                id, name, type, status, created_time, last_heartbeat_time,
                running_time, cpu_cores, cpu_usage, memory_usage,
                task_id, main_agent_id, available_cpu_cores
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            agent_id, name, type, status, created_time, last_heartbeat_time,
            0, cpu_cores, cpu_usage, memory_usage,
            task_id, main_agent_id, available_cpu_cores
        )
        db.execute(query, params)
        
        # 如果有GPU，插入GPU记录
        if gpu_ids:
            for gpu_id in gpu_ids:
                gpu_query = """
                    INSERT INTO agent_gpus (
                        agent_id, gpu_id, gpu_usage, gpu_memory_usage, is_available
                    ) VALUES (?, ?, ?, ?, ?)
                """
                gpu_params = (agent_id, gpu_id, 0.0, 0.0, 1)
                db.execute(gpu_query, gpu_params)
        
        system_logger.info(f"创建Agent: ID={agent_id}, 名称={name}, 类型={type}")
        
        # 返回创建的Agent实例
        return cls.get_agent_by_id(agent_id)
    
    @classmethod
    def get_agent_by_id(cls, agent_id):
        """根据ID获取Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            agent: Agent实例，如果不存在则返回None
        """
        db = get_db()
        query = "SELECT * FROM agents WHERE id = ?"
        agent_data = db.fetch_one(query, (agent_id,))
        
        if not agent_data:
            return None
        
        # 获取GPU信息
        gpu_query = "SELECT gpu_id, gpu_usage, gpu_memory_usage, is_available FROM agent_gpus WHERE agent_id = ?"
        gpu_data = db.fetch_all(gpu_query, (agent_id,))
        
        gpu_ids = []
        gpu_usage = {}
        gpu_memory_usage = {}
        available_gpu_ids = []
        
        if gpu_data:
            for gpu in gpu_data:
                gpu_id = gpu['gpu_id']
                gpu_ids.append(gpu_id)
                gpu_usage[gpu_id] = gpu['gpu_usage']
                gpu_memory_usage[gpu_id] = gpu['gpu_memory_usage']
                if gpu['is_available']:
                    available_gpu_ids.append(gpu_id)
        
        # 构建Agent实例
        agent = cls(
            id=agent_data['id'],
            name=agent_data['name'],
            type=agent_data['type'],
            status=agent_data['status'],
            created_time=agent_data['created_time'],
            last_heartbeat_time=agent_data['last_heartbeat_time'],
            running_time=agent_data['running_time'],
            cpu_cores=agent_data['cpu_cores'],
            cpu_usage=agent_data['cpu_usage'],
            memory_usage=agent_data['memory_usage'],
            gpu_ids=gpu_ids,
            gpu_usage=gpu_usage,
            gpu_memory_usage=gpu_memory_usage,
            task_id=agent_data['task_id'],
            main_agent_id=agent_data['main_agent_id'],
            available_cpu_cores=agent_data['available_cpu_cores'],
            available_gpu_ids=available_gpu_ids
        )
        
        return agent
    
    @classmethod
    def get_all_agents(cls):
        """获取所有Agent
        
        Returns:
            list: 所有Agent实例列表
        """
        db = get_db()
        query = "SELECT id FROM agents ORDER BY created_time DESC"
        agent_ids = db.fetch_all(query)
        
        agents = []
        for data in agent_ids:
            agent = cls.get_agent_by_id(data['id'])
            if agent:
                agents.append(agent)
        
        return agents
    
    def update_agent(self):
        """更新Agent信息到数据库
        
        Returns:
            bool: 更新是否成功
        """
        db = get_db()
        query = """
            UPDATE agents SET
                name = ?,
                type = ?,
                status = ?,
                last_heartbeat_time = ?,
                running_time = ?,
                cpu_cores = ?,
                cpu_usage = ?,
                memory_usage = ?,
                task_id = ?,
                main_agent_id = ?,
                available_cpu_cores = ?
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
            self.memory_usage,
            self.task_id,
            self.main_agent_id,
            self.available_cpu_cores,
            self.id
        )
        
        try:
            db.execute(query, params)
            
            # 更新GPU信息
            # 先删除所有旧记录
            db.execute("DELETE FROM agent_gpus WHERE agent_id = ?", (self.id,))
            
            # 插入新记录
            for gpu_id in self.gpu_ids:
                gpu_usage_value = self.gpu_usage.get(gpu_id, 0.0)
                gpu_memory_usage_value = self.gpu_memory_usage.get(gpu_id, 0.0)
                is_available = 1 if gpu_id in self.available_gpu_ids else 0
                
                gpu_query = """
                    INSERT INTO agent_gpus (
                        agent_id, gpu_id, gpu_usage, gpu_memory_usage, is_available
                    ) VALUES (?, ?, ?, ?, ?)
                """
                gpu_params = (self.id, gpu_id, gpu_usage_value, gpu_memory_usage_value, is_available)
                db.execute(gpu_query, gpu_params)
            
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
            # 检查可用GPU数量
            if len(self.available_gpu_ids) < gpu_count:
                return False
            
            # 如果指定了显存需求，检查每个可用GPU的显存
            if gpu_memory and gpu_memory > 0:
                # 这里简化处理，实际应该检查每个GPU的实际可用显存
                # 这部分逻辑可以在资源监控模块中实现更精确的检查
                pass
        
        return True
    
    def to_dict(self):
        """将Agent转换为字典
        
        Returns:
            dict: Agent字典表示
        """
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
            'memory_usage': self.memory_usage,
            'gpu_ids': self.gpu_ids,
            'gpu_usage': self.gpu_usage,
            'gpu_memory_usage': self.gpu_memory_usage,
            'task_id': self.task_id,
            'main_agent_id': self.main_agent_id,
            'available_cpu_cores': self.available_cpu_cores,
            'available_gpu_ids': self.available_gpu_ids
        }
