#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent管理服务
"""

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
    
    def create_main_agent(self, name, cpu_cores, gpu_ids=None):
        """创建主Agent
        
        Args:
            name: Agent名称
            cpu_cores: CPU核心数
            gpu_ids: GPU ID列表
            
        Returns:
            agent: 新创建的主Agent
        """
        # 参数校验
        if not name:
            system_logger.error("创建主Agent失败: 缺少必要参数")
            return None
        
        # 创建主Agent
        agent = Agent.create_agent(
            name=name,
            type='main',
            cpu_cores=cpu_cores,
            gpu_ids=gpu_ids
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
        # 参数校验
        if not name or not main_agent_id or not task_id:
            system_logger.error("创建子Agent失败: 缺少必要参数")
            return None
        
        # 检查主Agent是否存在
        main_agent = Agent.get_agent_by_id(main_agent_id)
        if not main_agent or main_agent.type != 'main' or main_agent.status != 'online':
            system_logger.error(f"创建子Agent失败: 主Agent不存在或不可用: ID={main_agent_id}")
            return None
        
        # 检查任务是否存在
        task = self.task_service.get_task_by_id(task_id)
        if not task or task.status not in ['waiting', 'blocked']:
            system_logger.error(f"创建子Agent失败: 任务不存在或状态不正确: ID={task_id}")
            return None
        
        # 检查资源是否从主Agent分配
        if cpu_cores and (main_agent.available_cpu_cores is None or 
                         main_agent.available_cpu_cores < cpu_cores):
            system_logger.error(f"创建子Agent失败: 主Agent没有足够的CPU资源: 需要={cpu_cores}, 可用={main_agent.available_cpu_cores}")
            return None
        
        if gpu_ids:
            for gpu_id in gpu_ids:
                if gpu_id not in main_agent.available_gpu_ids:
                    system_logger.error(f"创建子Agent失败: GPU不可用: ID={gpu_id}")
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
        
        # 更新主Agent的可用资源
        if cpu_cores and main_agent.available_cpu_cores is not None:
            main_agent.available_cpu_cores -= cpu_cores
        
        if gpu_ids:
            for gpu_id in gpu_ids:
                if gpu_id in main_agent.available_gpu_ids:
                    main_agent.available_gpu_ids.remove(gpu_id)
        
        main_agent.update_agent()
        
        # 更新任务状态为运行中
        self.task_service.update_task_by_key(task_id, status='running', agent_id=agent.id)
        
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
    
    def get_main_agents(self, filter_status=None):
        """获取所有主Agent
        
        Args:
            filter_status: 可选的Agent状态过滤
            
        Returns:
            list: 主Agent列表
        """
        return self.get_all_agents(filter_type='main', filter_status=filter_status)
    
    def get_sub_agents(self, main_agent_id=None, filter_status=None):
        """获取子Agent
        
        Args:
            main_agent_id: 可选的主Agent ID过滤
            filter_status: 可选的Agent状态过滤
            
        Returns:
            list: 子Agent列表
        """
        agents = self.get_all_agents(filter_type='sub', filter_status=filter_status)
        
        if main_agent_id:
            agents = [agent for agent in agents if agent.main_agent_id == main_agent_id]
        
        return agents
    
    def update_agent(self, agent):
        """更新Agent
        
        Args:
            agent: Agent实例
            
        Returns:
            bool: 更新是否成功
        """
        if not agent or not agent.id:
            system_logger.error("更新Agent失败: 无效的Agent实例")
            return False
        
        # 获取原Agent信息进行比较
        original_agent = Agent.get_agent_by_id(agent.id)
        if not original_agent:
            system_logger.error(f"更新Agent失败: Agent不存在: ID={agent.id}")
            return False
        
        # 状态变更记录
        if original_agent.status != agent.status:
            logger = get_agent_logger(agent.id)
            logger.info(f"Agent状态变更: {original_agent.status} -> {agent.status}")
            
            # 如果Agent离线且正在执行任务，处理任务状态
            if agent.status == 'offline' and agent.task_id and agent.type == 'sub':
                task = self.task_service.get_task_by_id(agent.task_id)
                if task and task.status == 'running':
                    # 将任务标记为失败
                    self.task_service.update_task_by_key(
                        task.id, 
                        status='failed',
                        end_time=datetime.now()
                    )
                    logger.warning(f"Agent离线，任务标记为失败: 任务ID={agent.task_id}")
        
        # 如果是子Agent完成任务
        if agent.type == 'sub' and agent.task_id and not original_agent.task_id:
            # 将资源返还给主Agent
            if agent.main_agent_id:
                main_agent = Agent.get_agent_by_id(agent.main_agent_id)
                if main_agent:
                    # 返还CPU资源
                    if agent.cpu_cores and main_agent.available_cpu_cores is not None:
                        main_agent.available_cpu_cores += agent.cpu_cores
                    
                    # 返还GPU资源
                    for gpu_id in agent.gpu_ids:
                        if gpu_id not in main_agent.available_gpu_ids:
                            main_agent.available_gpu_ids.append(gpu_id)
                    
                    main_agent.update_agent()
        
        return agent.update_agent()
    
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
                for gpu_id in agent.gpu_ids:
                    if gpu_id not in main_agent.available_gpu_ids:
                        main_agent.available_gpu_ids.append(gpu_id)
                
                main_agent.update_agent()
        
        return agent.cancel_agent()
    
    def check_agents_status(self):
        """检查所有Agent状态，标记超时心跳的Agent为离线
        
        Returns:
            int: 标记为离线的Agent数量
        """
        # 计算心跳超时时间
        timeout = datetime.now() - timedelta(seconds=Config.HEARTBEAT_TIMEOUT)
        
        # 查询所有在线但心跳超时的Agent
        query = """
            SELECT id FROM agents 
            WHERE status = 'online' 
            AND last_heartbeat_time < ?
        """
        timeout_agents = self.db.fetch_all(query, (timeout,))
        
        count = 0
        for agent_data in timeout_agents:
            agent = Agent.get_agent_by_id(agent_data['id'])
            if agent:
                agent.status = 'offline'
                if agent.update_agent():
                    count += 1
                    system_logger.warning(f"Agent心跳超时，标记为离线: ID={agent.id}, 最后心跳时间={agent.last_heartbeat_time}")
                    
                    # 如果是子Agent且有关联任务，将任务标记为失败
                    if agent.type == 'sub' and agent.task_id:
                        task = self.task_service.get_task_by_id(agent.task_id)
                        if task and task.status == 'running':
                            self.task_service.update_task_by_key(
                                task.id, 
                                status='failed',
                                end_time=datetime.now()
                            )
                            system_logger.warning(f"Agent离线，任务标记为失败: 任务ID={agent.task_id}")
        
        return count
    
    def handle_heartbeat(self, agent_id, resource_info, task_info=None):
        """处理Agent心跳
        
        Args:
            agent_id: Agent ID
            resource_info: 资源使用信息
                {
                    'cpu_usage': CPU使用率,
                    'memory_usage': 内存使用率,
                    'gpu_usage': GPU使用率字典,
                    'gpu_memory_usage': GPU显存使用率字典,
                    'running_time': 运行时长（秒）
                }
            task_info: 可选的任务执行信息
                {
                    'status': 任务状态,
                    'log': 新增日志内容
                }
            
        Returns:
            dict: 包含Agent应执行的操作
                {
                    'action': 操作类型，如'continue', 'new_task', 'stop',
                    'task': 如果action='new_task'，则包含新任务信息
                }
        """
        agent = Agent.get_agent_by_id(agent_id)
        if not agent:
            system_logger.error(f"处理心跳失败: Agent不存在: ID={agent_id}")
            return {'action': 'stop'}
        
        # 更新Agent信息
        agent.last_heartbeat_time = datetime.now()
        agent.status = 'online'
        
        # 更新资源使用信息
        if resource_info:
            if 'cpu_usage' in resource_info:
                agent.cpu_usage = resource_info['cpu_usage']
            
            if 'memory_usage' in resource_info:
                agent.memory_usage = resource_info['memory_usage']
            
            if 'gpu_usage' in resource_info:
                agent.gpu_usage.update(resource_info['gpu_usage'])
            
            if 'gpu_memory_usage' in resource_info:
                agent.gpu_memory_usage.update(resource_info['gpu_memory_usage'])
            
            if 'running_time' in resource_info:
                agent.running_time = resource_info['running_time']
        
        # 处理任务信息
        if task_info and agent.task_id:
            task = self.task_service.get_task_by_id(agent.task_id)
            if task:
                # 处理任务状态更新
                if 'status' in task_info and task_info['status'] in ['completed', 'failed']:
                    self.task_service.update_task_by_key(
                        task.id,
                        status=task_info['status'],
                        end_time=datetime.now()
                    )
                    
                    # 子Agent完成任务后，将资源返还给主Agent
                    if agent.type == 'sub' and agent.main_agent_id:
                        main_agent = Agent.get_agent_by_id(agent.main_agent_id)
                        if main_agent:
                            # 返还CPU资源
                            if agent.cpu_cores and main_agent.available_cpu_cores is not None:
                                main_agent.available_cpu_cores += agent.cpu_cores
                            
                            # 返还GPU资源
                            for gpu_id in agent.gpu_ids:
                                if gpu_id not in main_agent.available_gpu_ids:
                                    main_agent.available_gpu_ids.append(gpu_id)
                            
                            main_agent.update_agent()
                    
                    # 清除Agent的任务ID
                    agent.task_id = None
                
                # 追加任务日志
                if 'log' in task_info and task_info['log']:
                    self.task_service.append_task_log(task.id, task_info['log'])
        
        # 保存Agent更新
        agent.update_agent()
        
        # 如果是主Agent，检查是否有新任务
        if agent.type == 'main' and not agent.task_id:
            # 检查是否有阻塞的任务可以解除
            self._check_blocked_tasks()
            
            # 查找适合该Agent的任务
            task = self.task_service.find_task_for_agent(agent)
            if task:
                return {
                    'action': 'new_task',
                    'task': task.to_dict()
                }
        
        # 默认继续当前操作
        return {'action': 'continue'}
    
    def _check_blocked_tasks(self):
        """检查被阻塞的任务，如果依赖已完成则更新状态"""
        # 获取所有被阻塞的任务
        query = "SELECT id FROM tasks WHERE status = 'blocked'"
        blocked_tasks = self.db.fetch_all(query)
        
        for task_data in blocked_tasks:
            task = self.task_service.get_task_by_id(task_data['id'])
            if not task or not task.depends_on:
                continue
            
            # 检查所有依赖任务是否已完成
            all_deps_completed = True
            for dep_id in task.depends_on:
                dep_task = self.task_service.get_task_by_id(dep_id)
                if not dep_task or dep_task.status != 'completed':
                    all_deps_completed = False
                    break
            
            # 如果所有依赖已完成，更新任务状态为等待
            if all_deps_completed:
                self.task_service.update_task_by_key(task.id, status='waiting')
                system_logger.info(f"任务依赖已满足，状态从blocked更新为waiting: ID={task.id}")
