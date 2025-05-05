#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务管理服务
"""

import os
from datetime import datetime
from backend.models.task import Task
from backend.utils.database import get_db
from backend.utils.logger import system_logger, get_task_logger
from config import Config

class TaskService:
    """任务管理服务类，封装任务相关业务逻辑"""
    
    def __init__(self):
        """初始化任务服务"""
        self.db = get_db()
    
    def create_task(self, name, template_type, script_content, priority=3,
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
            task: 新创建的任务
        """
        # 参数校验
        if not name or not template_type or not script_content:
            system_logger.error("创建任务失败: 缺少必要参数")
            return None
        
        # 优先级范围校验
        priority = max(1, min(5, priority))
        
        # 创建任务
        task = Task.create_task(
            name=name,
            template_type=template_type,
            script_content=script_content,
            priority=priority,
            cpu_cores=cpu_cores,
            gpu_count=gpu_count,
            gpu_memory=gpu_memory,
            depends_on=depends_on
        )
        
        # 记录任务创建日志
        if task:
            logger = get_task_logger(task.id)
            logger.info(f"任务创建成功: ID={task.id}, 名称={name}, 优先级={priority}")
            if depends_on and task.status == 'blocked':
                logger.info(f"任务已阻塞: 等待依赖任务完成: {depends_on}")
        
        return task
    
    def get_task_by_id(self, task_id):
        return Task.get_task_by_id(task_id)
    
    def get_task_in_range(self, start_id, end_id):
        return Task.get_task_in_range(start_id, end_id)
    
    def get_task_in_page(self, page=1, per_page=10, filters=None):
        """分页获取任务列表
        
        Args:
            page: 页码，从1开始
            per_page: 每页数量
            filters: 过滤条件，字典格式
                {
                    'status': 状态列表,
                    'name': 名称关键词,
                    'template_type': 模板类型,
                    'script_content': 脚本内容关键词
                }
            
        Returns:
            dict: 包含分页信息和任务列表
                {
                    'tasks': 任务实例列表,
                    'total': 总任务数,
                    'page': 当前页码,
                    'per_page': 每页数量,
                    'pages': 总页数
                }
        """
        # 构建查询条件
        conditions = []
        params = []
        
        if filters:
            if 'status' in filters and filters['status']:
                placeholders = ', '.join(['?'] * len(filters['status']))
                conditions.append(f"status IN ({placeholders})")
                params.extend(filters['status'])
            
            if 'name' in filters and filters['name']:
                conditions.append("name LIKE ?")
                params.append(f"%{filters['name']}%")
            
            if 'template_type' in filters and filters['template_type']:
                conditions.append("template_type = ?")
                params.append(filters['template_type'])
            
            if 'script_content' in filters and filters['script_content']:
                conditions.append("script_content LIKE ?")
                params.append(f"%{filters['script_content']}%")
        
        # 构建WHERE子句
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 查询总数量
        count_query = f"SELECT COUNT(*) as total FROM tasks{where_clause}"
        total_result = self.db.fetch_one(count_query, params)
        total = total_result['total'] if total_result else 0
        
        # 计算分页信息
        page = max(1, page)
        offset = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page  # 总页数，向上取整
        
        # 查询任务ID列表
        id_query = f"""
            SELECT id FROM tasks{where_clause}
            ORDER BY created_time DESC
            LIMIT ? OFFSET ?
        """
        id_params = params + [per_page, offset]
        task_ids = self.db.fetch_all(id_query, id_params)
        
        # 获取任务实例列表
        tasks = []
        for data in task_ids:
            task = Task.get_task_by_id(data['id'])
            if task:
                tasks.append(task)
        
        return {
            'tasks': tasks,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        }
    
    def get_all_tasks(self, filters=None):
        """获取所有任务（可选过滤）
        
        Args:
            filters: 过滤条件，与get_task_in_page函数相同
            
        Returns:
            list: 任务列表
        """
        # 构建查询条件
        conditions = []
        params = []
        
        if filters:
            if 'status' in filters and filters['status']:
                placeholders = ', '.join(['?'] * len(filters['status']))
                conditions.append(f"status IN ({placeholders})")
                params.extend(filters['status'])
            
            if 'name' in filters and filters['name']:
                conditions.append("name LIKE ?")
                params.append(f"%{filters['name']}%")
            
            if 'template_type' in filters and filters['template_type']:
                conditions.append("template_type = ?")
                params.append(filters['template_type'])
            
            if 'script_content' in filters and filters['script_content']:
                conditions.append("script_content LIKE ?")
                params.append(f"%{filters['script_content']}%")
        
        # 构建WHERE子句
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 查询任务ID列表
        id_query = f"SELECT id FROM tasks{where_clause} ORDER BY created_time DESC"
        task_ids = self.db.fetch_all(id_query, params)
        
        # 获取任务实例列表
        tasks = []
        for data in task_ids:
            task = Task.get_task_by_id(data['id'])
            if task:
                tasks.append(task)
        
        return tasks
    
    def update_task(self, task: Task):
        """更新任务
        
        Args:
            task: 任务实例
            
        Returns:
            bool: 更新是否成功
        """
        if not task or not task.id:
            system_logger.error("更新任务失败: 无效的任务实例")
            return False
        
        # 获取原任务信息用于比较
        original_task = Task.get_task_by_id(task.id)
        if not original_task:
            system_logger.error(f"更新任务失败: 任务不存在: ID={task.id}")
            return False
        
        # 状态变更记录
        if original_task.status != task.status:
            logger = get_task_logger(task.id)
            logger.info(f"任务状态变更: {original_task.status} -> {task.status}")
            
            # 任务开始执行时记录开始时间
            if task.status == 'running' and not task.start_time:
                task.start_time = datetime.now()
                logger.info(f"任务开始执行: 时间={task.start_time}")
            
            # 任务完成或失败时记录结束时间和执行时长
            if task.status in ['completed', 'failed'] and not task.end_time:
                task.end_time = datetime.now()
                if task.start_time:
                    duration = (task.end_time - task.start_time).total_seconds()
                    task.execution_time = int(duration)
                    logger.info(f"任务执行结束: 时间={task.end_time}, 耗时={task.execution_time}秒")
        
        return task.update_task()
    
    def update_task_by_key(self, task_id, **kwargs):
        """按键值对更新任务指定字段
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段和值
            
        Returns:
            bool: 更新是否成功
        """
        task = Task.get_task_by_id(task_id)
        if not task:
            system_logger.error(f"更新任务失败: 任务不存在: ID={task_id}")
            return False
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        return self.update_task(task)
    
    def cancel_task(self, task_id):
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 取消是否成功
        """
        print(f"取消任务: ID={task_id}")
        task = Task.get_task_by_id(task_id)
        if not task:
            system_logger.error(f"取消任务失败: 任务不存在: ID={task_id}")
            return False
        
        # 如果任务有子任务正在执行，也需要取消
        if task.status == 'running' and task.agent_id:
            # 这里暂不处理，需要在Agent模块中实现
            pass
        
        print(f"取消任务: ID={task_id}")
        # 记录取消操作日志
        logger = get_task_logger(task.id)
        logger.info(f"任务被取消")
        
        print(f"取消任务: ID={task_id}")
        return task.cancel_task()
    
    def append_task_log(self, task_id, log_content):
        """将新的日志添加到任务日志文件中
        
        Args:
            task_id: 任务ID
            log_content: 日志内容
            
        Returns:
            bool: 添加是否成功
        """
        task = Task.get_task_by_id(task_id)
        if not task or not task.log_file:
            system_logger.error(f"添加任务日志失败: 任务不存在或无日志文件: ID={task_id}")
            return False
        
        try:
            # 确保日志目录存在
            os.makedirs(os.path.dirname(task.log_file), exist_ok=True)
            
            # 追加日志内容
            with open(task.log_file, 'a', encoding='utf-8') as f:
                f.write(log_content)
                if not log_content.endswith('\n'):
                    f.write('\n')
            
            return True
        except Exception as e:
            system_logger.error(f"添加任务日志失败: ID={task_id}, 错误={str(e)}")
            return False
    
    def get_task_log(self, task_id, start_line=0, max_lines=None):
        """从任务日志文件中获取日志
        
        Args:
            task_id: 任务ID
            start_line: 起始行号，从0开始
            max_lines: 最大行数，None表示获取所有行
            
        Returns:
            dict: 包含日志内容和信息
                {
                    'content': 日志内容,
                    'total_lines': 总行数,
                    'start_line': 起始行号,
                    'end_line': 结束行号
                }
        """
        task = Task.get_task_by_id(task_id)
        if not task or not task.log_file:
            system_logger.error(f"获取任务日志失败: 任务不存在或无日志文件: ID={task_id}")
            return {
                'content': '',
                'total_lines': 0,
                'start_line': 0,
                'end_line': 0
            }
        
        try:
            # 如果日志文件不存在，返回空内容
            if not os.path.exists(task.log_file):
                return {
                    'content': '',
                    'total_lines': 0,
                    'start_line': 0,
                    'end_line': 0
                }
            
            # 读取日志文件
            with open(task.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start_line = min(start_line, total_lines - 1) if total_lines > 0 else 0
            
            if max_lines is not None:
                end_line = min(start_line + max_lines, total_lines)
                content = ''.join(lines[start_line:end_line])
            else:
                end_line = total_lines
                content = ''.join(lines[start_line:])
            
            return {
                'content': content,
                'total_lines': total_lines,
                'start_line': start_line,
                'end_line': end_line
            }
        except Exception as e:
            system_logger.error(f"获取任务日志失败: ID={task_id}, 错误={str(e)}")
            return {
                'content': f"读取日志错误: {str(e)}",
                'total_lines': 0,
                'start_line': 0,
                'end_line': 0
            }
    
    def find_task_for_agent(self, agent):
        """获取适合指定Agent执行的任务
        
        Args:
            agent: Agent实例，包含可用资源信息
            
        Returns:
            task: 可执行的任务实例，如果没有合适任务则返回None
        """
        # 查询待执行的任务，按优先级排序
        query = """
            SELECT id FROM tasks 
            WHERE status = 'waiting' 
            ORDER BY priority, created_time
        """
        waiting_tasks = self.db.fetch_all(query)
        
        if not waiting_tasks:
            return None
        
        # 检查每个任务是否满足依赖条件
        for task_data in waiting_tasks:
            task = Task.get_task_by_id(task_data['id'])
            if not task:
                continue
            
            # 检查任务依赖是否已完成
            if task.depends_on:
                # 查询依赖的任务是否都已完成
                placeholders = ', '.join(['?'] * len(task.depends_on))
                dep_query = f"""
                    SELECT COUNT(*) as count 
                    FROM tasks 
                    WHERE id IN ({placeholders}) 
                    AND status != 'completed'
                """
                result = self.db.fetch_one(dep_query, task.depends_on)
                if result and result['count'] > 0:
                    # 依赖任务未完成，更新状态为blocked并跳过
                    if task.status != 'blocked':
                        task.status = 'blocked'
                        task.update_task()
                    continue
                elif task.status == 'blocked':
                    # 依赖已完成但状态仍为blocked，更新为waiting
                    task.status = 'waiting'
                    task.update_task()
            
            # 检查资源需求是否满足
            can_execute = True
            
            # 检查CPU资源
            if task.cpu_cores and (agent.available_cpu_cores is None or 
                                  agent.available_cpu_cores < task.cpu_cores):
                can_execute = False
            
            # 检查GPU资源
            gpu_needed = task.gpu_count or 0
            if gpu_needed > 0:
                available_gpus = len(agent.available_gpu_ids) if agent.available_gpu_ids else 0
                if available_gpus < gpu_needed:
                    can_execute = False
            
            # 如果资源满足，返回该任务
            if can_execute:
                return task
        
        # 没有找到合适的任务
        return None
