#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务数据模型
"""

import os
from datetime import datetime
from backend.utils.database import get_db
from backend.utils.logger import system_logger
from config import Config

class Task:
    """任务数据模型类"""
    
    def __init__(self, id=None, name=None, template_type=None, priority=3,
                 status="waiting", created_time=None, script_content=None,
                 cpu_cores=None, gpu_count=None, gpu_memory=None,
                 start_time=None, end_time=None, execution_time=None,
                 agent_id=None, log_file=None, depends_on=None):
        """初始化任务实例
        
        Args:
            id: 任务ID
            name: 任务名称
            template_type: 模板类型
            priority: 优先级(1-5, 1最高)
            status: 状态(blocked, waiting, running, completed, failed, canceled)
            created_time: 创建时间
            script_content: 脚本内容
            cpu_cores: CPU核心数
            gpu_count: GPU数量
            gpu_memory: GPU显存需求(MB)
            start_time: 开始时间
            end_time: 结束时间
            execution_time: 执行时间(秒)
            agent_id: 执行该任务的Agent ID
            log_file: 日志文件路径
            depends_on: 依赖任务ID列表
        """
        self.id = id
        self.name = name
        self.template_type = template_type
        self.priority = priority
        self.status = status
        self.created_time = created_time or datetime.now()
        self.script_content = script_content
        self.cpu_cores = cpu_cores
        self.gpu_count = gpu_count
        self.gpu_memory = gpu_memory
        self.start_time = start_time
        self.end_time = end_time
        self.execution_time = execution_time
        self.agent_id = agent_id
        self.log_file = log_file
        self.depends_on = depends_on or []
    
    @classmethod
    def create_task(cls, name, template_type, script_content, priority=3,
                   cpu_cores=None, gpu_count=None, gpu_memory=None,
                   depends_on=None):
        """创建新任务
        
        Args:
            name: 任务名称
            template_type: 模板类型
            script_content: 脚本内容
            priority: 优先级(1-5, 1最高)
            cpu_cores: CPU核心数
            gpu_count: GPU数量
            gpu_memory: GPU显存需求(MB)
            depends_on: 依赖任务ID列表
            
        Returns:
            task: 新创建的任务实例
        """
        db = get_db()
        
        # 处理依赖任务，先查看是否有依赖任务未完成，若有则将状态设置为blocked
        depends_on = depends_on or []
        status = "waiting"
        if depends_on:
            # 查询依赖的任务是否都已完成
            placeholders = ', '.join(['?'] * len(depends_on))
            query = f"""
                SELECT COUNT(*) as count 
                FROM tasks 
                WHERE id IN ({placeholders}) 
                AND status != 'completed'
            """
            result = db.fetch_one(query, depends_on)
            if result and result['count'] > 0:
                status = "blocked"
        
        # 创建日志文件路径
        log_dir = Config.TASK_LOG_PATH
        os.makedirs(log_dir, exist_ok=True)
        
        # 插入任务记录
        query = """
            INSERT INTO tasks (
                name, template_type, priority, status, script_content,
                cpu_cores, gpu_count, gpu_memory, created_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        created_time = datetime.now()
        params = (
            name, template_type, priority, status, script_content,
            cpu_cores, gpu_count, gpu_memory, created_time
        )
        cursor = db.execute(query, params)
        task_id = cursor.lastrowid
        
        # 创建日志文件
        log_file = os.path.join(log_dir, f"task_{task_id}.log")
        
        # 更新日志文件路径
        db.execute(
            "UPDATE tasks SET log_file = ? WHERE id = ?",
            (log_file, task_id)
        )
        
        # 如果有依赖任务，插入依赖关系
        if depends_on:
            for dep_id in depends_on:
                db.execute(
                    "INSERT INTO task_dependencies (task_id, depends_on_id) VALUES (?, ?)",
                    (task_id, dep_id)
                )
        
        system_logger.info(f"创建任务: ID={task_id}, 名称={name}, 状态={status}")
        
        # 返回创建的任务实例
        return cls.get_task_by_id(task_id)
    
    @classmethod
    def get_task_by_id(cls, task_id):
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            task: 任务实例，如果不存在则返回None
        """
        db = get_db()
        query = "SELECT * FROM tasks WHERE id = ?"
        task_data = db.fetch_one(query, (task_id,))
        
        if not task_data:
            return None
        
        # 获取依赖任务ID
        dep_query = "SELECT depends_on_id FROM task_dependencies WHERE task_id = ?"
        deps = db.fetch_all(dep_query, (task_id,))
        depends_on = [dep['depends_on_id'] for dep in deps] if deps else []
        
        # 构建任务实例
        task = cls(
            depends_on=depends_on,
            **task_data
        )
        return task
    
    @classmethod
    def get_task_in_range(cls, start_id, end_id):
        """获取指定ID范围内的任务
        
        Args:
            start_id: 起始ID
            end_id: 结束ID
            
        Returns:
            list: 任务实例列表
        """
        db = get_db()
        query = "SELECT id FROM tasks WHERE id >= ? AND id <= ? ORDER BY id"
        task_ids = db.fetch_all(query, (start_id, end_id))
        
        tasks = []
        for data in task_ids:
            task = cls.get_task_by_id(data['id'])
            if task:
                tasks.append(task)
        
        return tasks
    
    @classmethod
    def get_max_id(cls):
        """获取当前最大任务ID
        
        Returns:
            int: 最大任务ID，如果无任务则返回0
        """
        db = get_db()
        query = "SELECT MAX(id) as max_id FROM tasks"
        result = db.fetch_one(query)
        
        return result['max_id'] if result and result['max_id'] else 0
    
    @classmethod
    def get_all_tasks(cls):
        """获取所有任务
        
        Returns:
            list: 所有任务实例列表
        """
        db = get_db()
        query = "SELECT id FROM tasks ORDER BY id"
        task_ids = db.fetch_all(query)
        
        tasks = []
        for data in task_ids:
            task = cls.get_task_by_id(data['id'])
            if task:
                tasks.append(task)
        
        return tasks
    
    def update_task(self):
        """更新任务信息到数据库
        
        Returns:
            bool: 更新是否成功
        """
        db = get_db()
        query = """
            UPDATE tasks SET
                name = ?,
                template_type = ?,
                priority = ?,
                status = ?,
                script_content = ?,
                cpu_cores = ?,
                gpu_count = ?,
                gpu_memory = ?,
                start_time = ?,
                end_time = ?,
                execution_time = ?,
                agent_id = ?,
                log_file = ?
            WHERE id = ?
        """
        params = (
            self.name,
            self.template_type,
            self.priority,
            self.status,
            self.script_content,
            self.cpu_cores,
            self.gpu_count,
            self.gpu_memory,
            self.start_time,
            self.end_time,
            self.execution_time,
            self.agent_id,
            self.log_file,
            self.id
        )
        
        try:
            db.execute(query, params)
            system_logger.info(f"更新任务: ID={self.id}, 状态={self.status}")
            return True
        except Exception as e:
            system_logger.error(f"更新任务失败: ID={self.id}, 错误={str(e)}")
            return False
    
    def cancel_task(self):
        """取消任务
        
        Returns:
            bool: 取消是否成功
        """
        if self.status in ['completed', 'failed', 'canceled']:
            system_logger.warning(f"无法取消任务: ID={self.id}, 当前状态={self.status}")
            return False
        
        self.status = 'canceled'
        result = self.update_task()
        
        if result:
            system_logger.info(f"取消任务: ID={self.id}")
        
        return result
    
    def to_dict(self):
        """将任务转换为字典
        
        Returns:
            dict: 任务字典表示
        """
        return {
            'id': self.id,
            'name': self.name,
            'template_type': self.template_type,
            'priority': self.priority,
            'status': self.status,
            'created_time': self.created_time,
            'script_content': self.script_content,
            'cpu_cores': self.cpu_cores,
            'gpu_count': self.gpu_count,
            'gpu_memory': self.gpu_memory,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'execution_time': self.execution_time,
            'agent_id': self.agent_id,
            'log_file': self.log_file,
            'depends_on': self.depends_on
        }
