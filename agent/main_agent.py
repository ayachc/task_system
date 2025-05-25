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
import logging
import requests
import subprocess
import threading
import socket
from datetime import datetime

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 添加项目根目录到 Python 路径
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入资源监控工具
from agent.resource_util import get_resource_util

# 导入配置
from config import Config

# 配置日志
# 确保日志目录存在
log_dir = os.path.join(ROOT_DIR, 'data', 'logs', 'system')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'main_agent.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main_agent")

class MainAgent:
    """主Agent类，负责向服务器注册、发送心跳、获取任务并创建子Agent执行"""
    
    def __init__(self, name=None, server_url=None, reject_new_task=False):
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
        self.reject_new_task = reject_new_task
        
        # 资源信息
        self.resource_util = get_resource_util()
        self.resource_info = self.resource_util.get_resource_info(os.getpid())
        self.locked_cpu_cores = 0
        self.locked_gpu_ids = []
        
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
    
    def send_heartbeat(self):
        """向服务器发送心跳并处理响应
        
        Returns:
            bool: 心跳是否成功
        """
        
        try:
            url = f"{self.server_url}/api/agents/{self.id}/heartbeat"

            # 检查子Agent进程
            for task_id, [process, cpu_cores, gpu_ids] in list(self.sub_agents.items()):
                if process.poll() is not None:
                    logger.info(f"子Agent进程已结束: 任务ID={task_id}, PID={process.pid}")
                    with self.sub_agent_lock:
                        del self.sub_agents[task_id]
                        self.locked_cpu_cores -= cpu_cores
                        self.locked_gpu_ids = [gid for gid in self.locked_gpu_ids if gid not in gpu_ids]
            
            # 获取最新资源信息
            resource_info = self.resource_util.get_resource_info(os.getpid())
            resource_info["available_cpu_cores"] = resource_info["cpu_cores"] - self.locked_cpu_cores
            for gpu_unit in resource_info["gpu_info"]:
                if gpu_unit["gpu_id"] in self.locked_gpu_ids:
                    gpu_unit["is_available"] = False
            resource_info["reject_new_task"] = self.reject_new_task

            data = {
                'resource_info': resource_info
            }
            
            response = requests.post(url, json=data)
            logger.info(f"{'='*10} 心跳发送完成 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'='*10}")
            
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
                    'action': 操作类型，如'continue', 'new_task', 'reject_new_task', 'accept_new_task', 'quit'
                    'task': 如果action='new_task'，则包含新任务信息
                }
        """
        action = response.get('action', 'continue')
        print(response)
        
        if action == 'new_task':
            # 获取新任务
            task = response.get('task')
            logger.info(f"收到新任务: ID={task['id']}, 名称={task['name']}")
            
            # 创建子Agent执行任务
            self.create_sub_agent(task)
        
        elif action == 'reject_new_task':
            logger.info("收到指令:拒绝新任务")
            self.reject_new_task = True
        
        elif action == 'accept_new_task':
            logger.info("收到指令:接受新任务")
            self.reject_new_task = False
        
        elif action == 'quit':
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
            cpu_cores = task.get('cpu_cores', 0)
            gpu_ids = task.get('gpu_ids', [])
            self.locked_cpu_cores += cpu_cores
            self.locked_gpu_ids += gpu_ids
            
            # 准备子Agent脚本路径
            sub_agent_script = os.path.join(ROOT_DIR, 'agent', 'sub_agent.py')
            
            # 准备命令行参数
            command = [
                sys.executable,  # Python解释器
                sub_agent_script,
                '--main-id', self.id,
                '--task', json.dumps(task),
                '--server', self.server_url
            ]
            
            # 启动子Agent进程
            logger.info(f"启动子Agent: 任务ID={task['id']}, CPU核心={cpu_cores}, GPU={gpu_ids}")
            process = subprocess.Popen(
                command,
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL,
                stdout=sys.stdout,
                stderr=sys.stderr,
                cwd=ROOT_DIR
            )
            
            # 记录子进程信息
            with self.sub_agent_lock:
                self.sub_agents[task['id']] = [process, cpu_cores, gpu_ids]
            
            logger.info(f"子Agent启动成功: 任务ID={task['id']}, PID={process.pid}")
            
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
            for task_id, [process, cpu_cores, gpu_ids] in self.sub_agents.items():
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
        try:
            while self.running:
                try:
                    self.send_heartbeat()
                except Exception as e:
                    logger.error(f"心跳异常: {str(e)}")
                
                # 等待下一次心跳
                time.sleep(Config.MAIN_AGENT_HEARTBEAT_INTERVAL)
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
    parser.add_argument("--name", help="Agent名称", default="main_agent")
    parser.add_argument("--server", help="服务器URL", default="http://localhost:5050")
    
    args = parser.parse_args()
    
    # 运行主Agent
    setup_main_agent(name=args.name, server_url=args.server)
