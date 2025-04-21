#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主Agent实现

负责向服务器注册、发送心跳、获取任务并创建子Agent执行
"""

import os
import sys
import time
import json
import uuid
import logging
import requests
import subprocess
import threading
import socket
from datetime import datetime

# 导入资源监控工具
from agent.resource_util import get_resource_util

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到sys.path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入配置
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(ROOT_DIR, 'data', 'logs', 'system', 'main_agent.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main_agent")

class MainAgent:
    """主Agent类，负责向服务器注册、发送心跳、获取任务并创建子Agent执行"""
    
    def __init__(self, name=None, server_url=None):
        """初始化主Agent
        
        Args:
            name: Agent名称，默认使用主机名
            server_url: 服务器URL，默认使用配置中的URL
        """
        # 基本信息
        self.id = None
        self.name = name or socket.gethostname()
        self.server_url = server_url or Config.SERVER_URL
        self.running = False
        self.heartbeat_thread = None
        self.start_time = datetime.now()
        
        # 资源信息
        self.resource_util = get_resource_util()
        self.resource_info = self.get_resource_info()
        
        # 子进程管理
        self.sub_agents = {}  # 键为子Agent ID，值为子进程对象
        self.sub_agent_lock = threading.Lock()
        
        # 确保日志目录存在
        os.makedirs(os.path.join(ROOT_DIR, 'data', 'logs', 'system'), exist_ok=True)
        
        logger.info(f"主Agent初始化完成: 名称={self.name}, 服务器={self.server_url}")
        logger.info(f"资源信息: CPU核心数={self.resource_info['cpu_cores']}, GPU={self.resource_info['gpu_ids']}")
    
    def register(self):
        """向服务器注册主Agent
        
        Returns:
            bool: 注册是否成功
        """
        try:
            url = f"{self.server_url}/api/agents/main"
            data = {
                'name': self.name,
                'cpu_cores': self.resource_info['cpu_cores'],
                'gpu_ids': self.resource_info['gpu_ids']
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 201:
                result = response.json()
                if result.get('success'):
                    self.id = result['data']['id']
                    logger.info(f"主Agent注册成功: ID={self.id}")
                    return True
                else:
                    logger.error(f"主Agent注册失败: {result.get('message', '未知错误')}")
            else:
                logger.error(f"主Agent注册失败: HTTP状态码={response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"主Agent注册异常: {str(e)}")
            return False
    
    def start_heartbeat(self):
        """启动心跳线程"""
        if self.heartbeat_thread is not None and self.heartbeat_thread.is_alive():
            logger.warning("心跳线程已经在运行")
            return
        
        def heartbeat_task():
            while self.running:
                try:
                    self.send_heartbeat()
                except Exception as e:
                    logger.error(f"发送心跳异常: {str(e)}")
                
                # 等待下一次心跳
                time.sleep(Config.MAIN_AGENT_HEARTBEAT_INTERVAL)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_task, daemon=True)
        self.heartbeat_thread.start()
        logger.info("心跳线程已启动")
    
    def get_resource_info(self):
        """获取资源使用情况
        
        Returns:
            dict: 资源信息
        """
        # 获取基本资源信息
        resource_info = self.resource_util.get_resource_info()
        
        # 计算运行时间（秒）
        running_time = int((datetime.now() - self.start_time).total_seconds())
        resource_info['running_time'] = running_time
        
        return resource_info
    
    def send_heartbeat(self):
        """向服务器发送心跳并处理响应
        
        Returns:
            bool: 心跳是否成功
        """
        if not self.id:
            logger.error("发送心跳失败: Agent未注册")
            return False
        
        try:
            url = f"{self.server_url}/api/agents/{self.id}/heartbeat"
            
            # 获取最新资源信息
            resource_info = self.get_resource_info()
            
            data = {
                'resource_info': resource_info
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # 处理服务器响应
                    self.handle_heartbeat_response(result['data'])
                    return True
                else:
                    logger.error(f"心跳处理失败: {result.get('message', '未知错误')}")
            else:
                logger.error(f"心跳发送失败: HTTP状态码={response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
            return False
    
    def handle_heartbeat_response(self, response):
        """处理心跳响应
        
        Args:
            response: 服务器响应数据
                {
                    'action': 操作类型，如'continue', 'new_task', 'stop',
                    'task': 如果action='new_task'，则包含新任务信息
                }
        """
        action = response.get('action', 'continue')
        
        if action == 'new_task':
            # 获取新任务
            task = response.get('task')
            if task:
                logger.info(f"收到新任务: ID={task['id']}, 名称={task['name']}")
                
                # 创建子Agent执行任务
                threading.Thread(
                    target=self.create_sub_agent,
                    args=(task,),
                    daemon=True
                ).start()
        
        elif action == 'stop':
            # 停止Agent
            logger.info("收到停止指令，准备退出")
            self.cleanup()
    
    def create_sub_agent(self, task):
        """创建子Agent执行任务
        
        Args:
            task: 任务信息
        
        Returns:
            bool: 创建是否成功
        """
        try:
            # 确定要分配的资源
            cpu_cores = task.get('cpu_cores')
            gpu_count = task.get('gpu_count', 0)
            gpu_memory = task.get('gpu_memory', 0)
            
            # 创建子Agent名称
            task_id = task['id']
            sub_agent_name = f"sub_{self.name}_{task_id}"
            
            # 选择GPU
            selected_gpus = []
            if gpu_count > 0 and self.resource_info['gpu_ids']:
                # 简单策略：选择前N个GPU
                available_gpus = self.resource_info['gpu_ids']
                selected_gpus = available_gpus[:gpu_count]
                
                if len(selected_gpus) < gpu_count:
                    logger.error(f"GPU资源不足: 需要={gpu_count}, 可用={len(available_gpus)}")
                    return False
            
            # 准备子Agent脚本路径
            sub_agent_script = os.path.join(ROOT_DIR, 'agent', 'sub_agent.py')
            
            # 准备命令行参数
            command = [
                sys.executable,  # Python解释器
                sub_agent_script,
                '--main-id', self.id,
                '--task-id', str(task_id),
                '--name', sub_agent_name,
                '--server', self.server_url
            ]
            
            # 添加CPU核心数
            if cpu_cores:
                command.extend(['--cpu-cores', str(cpu_cores)])
            
            # 添加GPU参数
            if selected_gpus:
                gpu_str = ','.join(selected_gpus)
                command.extend(['--gpu-ids', gpu_str])
            
            # 启动子Agent进程
            logger.info(f"启动子Agent: 任务ID={task_id}, CPU核心={cpu_cores}, GPU={selected_gpus}")
            
            # 创建日志文件
            log_dir = os.path.join(ROOT_DIR, 'data', 'logs', 'system')
            log_file = os.path.join(log_dir, f"sub_agent_{task_id}.log")
            
            with open(log_file, 'w') as log_f:
                process = subprocess.Popen(
                    command,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    cwd=ROOT_DIR
                )
            
            # 记录子进程信息
            with self.sub_agent_lock:
                self.sub_agents[task_id] = process
            
            logger.info(f"子Agent启动成功: 任务ID={task_id}, PID={process.pid}")
            
            # 向服务器注册子Agent（由子Agent自己完成）
            return True
        except Exception as e:
            logger.error(f"创建子Agent失败: 任务ID={task.get('id')}, 错误={str(e)}")
            return False
    
    def cleanup(self):
        """清理资源并退出"""
        logger.info("开始清理资源...")
        
        # 停止运行标志
        self.running = False
        
        # 终止所有子进程
        with self.sub_agent_lock:
            for task_id, process in self.sub_agents.items():
                try:
                    logger.info(f"终止子Agent进程: 任务ID={task_id}, PID={process.pid}")
                    process.terminate()
                except:
                    pass
            
            # 清空子进程列表
            self.sub_agents.clear()
        
        # 等待心跳线程结束
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=3)
        
        logger.info("资源清理完成")
    
    def run(self):
        """运行主Agent"""
        logger.info("主Agent开始运行...")
        
        # 注册Agent
        if not self.register():
            logger.error("注册失败，Agent无法启动")
            return False
        
        # 设置运行标志
        self.running = True
        
        # 开始心跳
        self.start_heartbeat()
        
        try:
            # 主循环，保持进程运行
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，准备退出")
        finally:
            # 清理资源
            self.cleanup()
        
        return True


def setup_main_agent(name=None, server_url=None):
    """设置并运行主Agent
    
    Args:
        name: Agent名称
        server_url: 服务器URL
        
    Returns:
        bool: 运行是否成功
    """
    try:
        # 创建主Agent
        agent = MainAgent(name=name, server_url=server_url)
        
        # 运行主Agent
        return agent.run()
    except Exception as e:
        logger.error(f"运行主Agent失败: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="主Agent程序")
    parser.add_argument("--name", help="Agent名称")
    parser.add_argument("--server", help="服务器URL")
    
    args = parser.parse_args()
    
    # 运行主Agent
    setup_main_agent(name=args.name, server_url=args.server)
