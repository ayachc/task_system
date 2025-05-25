#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent管理服务
"""

import json
from datetime import datetime, timedelta
from backend.models.agent import Agent
from backend.utils.database import get_db
from backend.utils.logger import system_logger, get_agent_logger
from backend.services.task_service import TaskService
from config import Config

class AgentService:
    """Agent管理服务类，封装Agent相关业务逻辑"""
    
    def __init__(self):
        """初始化Agent服务"""
        self.db = get_db()
        self.task_service = TaskService()
    
    def create_main_agent(self, name, cpu_cores, gpu_ids=None, monitor_file=None):
        """创建主Agent
        
        Args:
            name: Agent名称
            cpu_cores: CPU核心数
            gpu_ids: GPU ID列表
            monitor_file: 监控文件路径
            
        Returns:
            agent: 新创建的主Agent
        """
        
        # 创建主Agent
        agent = Agent.create_agent(
            name=name,
            type='main',
            cpu_cores=cpu_cores,
            gpu_ids=gpu_ids,
            monitor_file=monitor_file
        )
        
        # 记录Agent创建日志
        if agent:
            logger = get_agent_logger(agent.id)
            logger.info(f"主Agent创建成功: ID={agent.id}, 名称={name}")
            logger.info(f"资源配置: CPU核心数={cpu_cores}, GPU IDs={gpu_ids}")
        
        return agent
    
    def create_sub_agent(self, name, main_agent_id, task_id, cpu_cores=None, gpu_ids=None):
        """创建子Agent
        
        Args:
            name: Agent名称
            main_agent_id: 主Agent ID
            task_id: 关联的任务ID
            cpu_cores: 分配的CPU核心数
            gpu_ids: 分配的GPU ID列表
            
        Returns:
            agent: 新创建的子Agent
        """
        
        # 检查主Agent是否存在
        main_agent = Agent.get_agent_by_id(main_agent_id)
        if not main_agent or main_agent.type != 'main' or main_agent.status != 'online':
            system_logger.error(f"创建子Agent失败: 主Agent不存在或不可用: ID={main_agent_id}")
            return None
        
        # 创建子Agent
        agent = Agent.create_agent(
            name=name,
            type='sub',
            cpu_cores=cpu_cores,
            gpu_ids=gpu_ids,
            task_id=task_id,
            main_agent_id=main_agent_id
        )
        
        if not agent:
            return None
        
        # 记录日志
        logger = get_agent_logger(agent.id)
        logger.info(f"子Agent创建成功: ID={agent.id}, 名称={name}, 任务ID={task_id}")
        logger.info(f"资源配置: CPU核心数={cpu_cores}, GPU IDs={gpu_ids}")
        
        return agent
    
    def get_agent_by_id(self, agent_id):
        """根据ID获取Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            agent: Agent实例
        """
        return Agent.get_agent_by_id(agent_id)
    
    def get_all_agents(self, filter_type=None, filter_status=None):
        """获取所有Agent（可选过滤）
        
        Args:
            filter_type: 可选的Agent类型过滤
            filter_status: 可选的Agent状态过滤
            
        Returns:
            list: Agent列表
        """
        agents = Agent.get_all_agents()
        
        # 应用过滤
        if filter_type:
            agents = [agent for agent in agents if agent.type == filter_type]
        
        if filter_status:
            agents = [agent for agent in agents if agent.status == filter_status]
        
        return agents
    
    def cancel_agent(self, agent_id):
        """取消Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            bool: 取消是否成功
        """
        agent = Agent.get_agent_by_id(agent_id)
        if not agent:
            system_logger.error(f"取消Agent失败: Agent不存在: ID={agent_id}")
            return False
        
        # 如果是主Agent，先取消所有子Agent
        if agent.type == 'main':
            sub_agents = self.get_sub_agents(main_agent_id=agent_id, filter_status='online')
            for sub_agent in sub_agents:
                self.cancel_agent(sub_agent.id)
        
        # 如果是子Agent且有关联任务，标记任务为失败
        if agent.type == 'sub' and agent.task_id:
            task = self.task_service.get_task_by_id(agent.task_id)
            if task and task.status == 'running':
                self.task_service.update_task_by_key(
                    task.id, 
                    status='failed',
                    end_time=datetime.now()
                )
                logger = get_agent_logger(agent.id)
                logger.warning(f"Agent被取消，任务标记为失败: 任务ID={agent.task_id}")
        
        # 如果是子Agent，返还资源给主Agent
        if agent.type == 'sub' and agent.main_agent_id:
            main_agent = Agent.get_agent_by_id(agent.main_agent_id)
            if main_agent:
                # 返还CPU资源
                if agent.cpu_cores and main_agent.available_cpu_cores is not None:
                    main_agent.available_cpu_cores += agent.cpu_cores
                
                # 返还GPU资源
                for gpu in agent.gpu_info:
                    gpu_id = gpu.get('gpu_id')
                    for main_gpu in main_agent.gpu_info:
                        if main_gpu.get('gpu_id') == gpu_id:
                            main_gpu['is_available'] = True
                            break
                
                main_agent.update_agent()
        
        return agent.cancel_agent()
    
    def handle_heartbeat(self, agent_id, data):
        """处理Agent心跳
        
        Args:
            agent_id: Agent ID
            data: agent传来的信息
                {
                    'resource_info': {
                        'cpu_cores': CPU核心数,
                        'cpu_usage': CPU使用率(百分比，可能超过100%),
                        'memory_total': 系统总内存(字节),
                        'memory_total_usage': 系统总内存使用量(字节),
                        'memory_used': 内存使用量(字节),
                        'gpu_info': GPU信息列表,
                        'gpu_ids': 可用GPU ID列表
                    }
                    'task_info': { # 仅子agent提供
                        'status': 任务状态, 
                        'log': 新日志内容
                    }
                }
                
        Returns:
            dict: 包含Agent应执行的操作
                {
                    'action': 操作类型，如'continue', 'new_task', 'stop',
                    'task': 如果action='new_task'，则包含新任务信息
                }
        """
        agent = Agent.get_agent_by_id(agent_id)
        if not agent or agent.status == "end":
            system_logger.error(f"处理心跳失败: Agent不存在: ID={agent_id}")
            return {'action': 'stop'}
        
        # 从data中提取信息
        resource_info = data.get('resource_info', {})
        task_info = data.get('task_info', {})
        
        # 更新Agent信息
        agent.last_heartbeat_time = datetime.now()
        agent.status = 'online'
        
        # 更新资源使用信息
        if resource_info:
            if 'cpu_usage' in resource_info:
                agent.cpu_usage = resource_info['cpu_usage']
            
            if 'memory_usage' in resource_info:
                agent.memory_used = resource_info['memory_usage']
                
            if 'memory_total' in resource_info:
                agent.memory_total = resource_info['memory_total']
            
            if 'gpu_info' in resource_info:
                # 更新GPU信息
                agent.gpu_info = json.dumps(resource_info['gpu_info'])
            
            # 确保 created_time 是 datetime 对象
            if isinstance(agent.created_time, str):
                try:
                    agent.created_time = datetime.fromisoformat(agent.created_time.replace('Z', '+00:00'))
                except ValueError:
                    # 如果无法解析，使用当前时间
                    agent.created_time = datetime.now()
                    
            agent.running_time = (datetime.now() - agent.created_time).total_seconds()
            agent.last_heartbeat_time = datetime.now()

        
        # 处理任务信息，主要针对子Agent
        if task_info and agent.task_id and agent.type == 'sub':
            task = self.task_service.get_task_by_id(agent.task_id)
            if task:
                # 处理任务状态更新
                if 'status' in task_info and task_info['status'] in ['completed', 'failed']:
                    self.task_service.update_task_by_key(
                        task.id,
                        status=task_info['status'],
                        end_time=datetime.now()
                    )
                    # 子agent生命终结
                    agent.status = "end"
                
                # 追加任务日志
                if 'log' in task_info and task_info['log']:
                    self.task_service.append_task_log(task.id, task_info['log'])
        
        # 保存Agent更新
        agent.update_agent()
        
        # 如果是主Agent，检查是否有新任务
        if agent.type == 'main':
            # 查找适合该Agent的任务
            
            task, gpu_dis = self.task_service.find_task_for_agent(agent)
            if task:
                # 立即将任务状态更新为running，防止被其他Agent获取
                success = self.task_service.update_task_by_key(
                    task.id,
                    status='running',
                    agent_id=agent_id,
                    start_time=datetime.now()
                )
                
                if success:
                    system_logger.info(f"为主Agent分配任务: Agent ID={agent_id}, Task ID={task.id}")
                    task = task.to_dict()
                    task.update({'gpu_ids': gpu_dis})
                    return {
                        'action': 'new_task',
                        'task': task,
                    }
                    
                    

        
        # 默认继续当前操作
        return {'action': 'continue'}
