#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
子Agent实现

负责执行单个任务，上报执行状态和资源使用情况
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
import tempfile
import traceback
from datetime import datetime

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到sys.path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入资源监控工具
from agent.resource_util import get_resource_util

# 导入配置
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(ROOT_DIR, 'data', 'logs', 'system', 'sub_agent.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sub_agent")

class SubAgent:
    """子Agent类，负责执行单个任务并上报状态"""
    
    def __init__(self, main_agent_id, task_id, name=None, server_url=None, 
                 cpu_cores=None, gpu_ids=None):
        """初始化子Agent
        
        Args:
            main_agent_id: 主Agent ID
            task_id: 任务ID
            name: Agent名称，默认为"sub_agent_{task_id}"
            server_url: 服务器URL，默认使用配置中的URL
            cpu_cores: 分配的CPU核心数
            gpu_ids: 分配的GPU ID列表
        """
        # 基本信息
        self.id = None
        self.main_agent_id = main_agent_id
        self.task_id = task_id
        self.name = name or f"sub_agent_{task_id}"
        self.server_url = server_url or Config.SERVER_URL
        self.running = False
        self.heartbeat_thread = None
        self.start_time = datetime.now()
        
        # 资源信息
        self.cpu_cores = cpu_cores
        self.gpu_ids = gpu_ids.split(',') if isinstance(gpu_ids, str) and gpu_ids else \
                     (gpu_ids or [])
        self.resource_util = get_resource_util()
        
        # 任务执行
        self.task_process = None
        self.task_output_thread = None
        self.task_output_buffer = []
        self.task_status = "waiting"  # waiting, running, completed, failed
        self.task_start_time = None
        self.task_script_file = None
        
        # 确保日志目录存在
        os.makedirs(os.path.join(ROOT_DIR, 'data', 'logs', 'system'), exist_ok=True)
        
        logger.info(f"子Agent初始化完成: 名称={self.name}, 主Agent={self.main_agent_id}, 任务={self.task_id}")
        logger.info(f"资源分配: CPU核心数={self.cpu_cores}, GPU={self.gpu_ids}")
    
    def register(self):
        """向服务器注册子Agent
        
        Returns:
            bool: 注册是否成功
        """
        try:
            url = f"{self.server_url}/api/agents/sub"
            data = {
                'name': self.name,
                'main_agent_id': self.main_agent_id,
                'task_id': self.task_id,
                'cpu_cores': self.cpu_cores,
                'gpu_ids': self.gpu_ids
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 201:
                result = response.json()
                if result.get('success'):
                    self.id = result['data']['id']
                    logger.info(f"子Agent注册成功: ID={self.id}")
                    return True
                else:
                    logger.error(f"子Agent注册失败: {result.get('message', '未知错误')}")
            else:
                logger.error(f"子Agent注册失败: HTTP状态码={response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"子Agent注册异常: {str(e)}")
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
                time.sleep(Config.SUB_AGENT_HEARTBEAT_INTERVAL)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_task, daemon=True)
        self.heartbeat_thread.start()
        logger.info("心跳线程已启动")
    
    def get_resource_info(self):
        """获取资源使用情况
        
        Returns:
            dict: 资源信息
        """
        # 获取当前进程ID
        pid = os.getpid()
        
        # 如果任务进程在运行，使用任务进程ID
        if self.task_process and self.task_process.poll() is None:
            pid = self.task_process.pid
        
        # 获取资源信息
        resource_info = self.resource_util.get_resource_info(pid)
        
        # 计算运行时间（秒）
        running_time = int((datetime.now() - self.start_time).total_seconds())
        resource_info['running_time'] = running_time
        
        return resource_info
    
    def send_heartbeat(self):
        """向服务器发送心跳
        
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
            
            # 准备任务信息
            task_info = {
                'status': self.task_status
            }
            
            # 添加任务输出
            if self.task_output_buffer:
                # 获取并清空缓冲区
                with threading.Lock():
                    output = ''.join(self.task_output_buffer)
                    self.task_output_buffer = []
                
                if output:
                    task_info['log'] = output
            
            data = {
                'resource_info': resource_info,
                'task_info': task_info
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # 处理服务器响应
                    action = result['data'].get('action', 'continue')
                    if action == 'stop':
                        logger.info("收到停止指令，准备退出")
                        self.running = False
                    
                    return True
                else:
                    logger.error(f"心跳处理失败: {result.get('message', '未知错误')}")
            else:
                logger.error(f"心跳发送失败: HTTP状态码={response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
            return False
    
    def start_task(self):
        """启动任务执行
        
        Returns:
            bool: 启动是否成功
        """
        try:
            # 获取任务信息
            url = f"{self.server_url}/api/tasks/{self.task_id}"
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.error(f"获取任务信息失败: HTTP状态码={response.status_code}")
                return False
            
            result = response.json()
            if not result.get('success'):
                logger.error(f"获取任务信息失败: {result.get('message', '未知错误')}")
                return False
            
            task = result['data']
            script_content = task.get('script_content')
            
            if not script_content:
                logger.error("任务脚本内容为空")
                return False
            
            # 创建临时脚本文件
            with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as temp:
                self.task_script_file = temp.name
                temp.write(script_content.encode('utf-8'))
            
            # 修改脚本文件权限
            os.chmod(self.task_script_file, 0o755)
            
            # 准备环境变量
            env = os.environ.copy()
            
            # 设置GPU环境变量
            if self.gpu_ids:
                env['CUDA_VISIBLE_DEVICES'] = ','.join(self.gpu_ids)
            
            # 启动任务进程
            logger.info(f"启动任务执行: 脚本文件={self.task_script_file}")
            self.task_status = "running"
            self.task_start_time = datetime.now()
            
            # 添加任务开始标记到日志
            self.task_output_buffer.append(f"=================== 任务开始执行: {self.task_start_time} ===================\n")
            
            # 启动进程
            self.task_process = subprocess.Popen(
                ['/bin/bash', self.task_script_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1  # 行缓冲
            )
            
            # 启动输出读取线程
            self.task_output_thread = threading.Thread(
                target=self.read_task_output,
                daemon=True
            )
            self.task_output_thread.start()
            
            logger.info(f"任务进程已启动: PID={self.task_process.pid}")
            return True
        except Exception as e:
            logger.error(f"启动任务执行失败: {str(e)}")
            self.task_status = "failed"
            self.task_output_buffer.append(f"启动任务执行失败: {str(e)}\n{traceback.format_exc()}\n")
            return False
    
    def read_task_output(self):
        """读取任务输出"""
        try:
            for line in iter(self.task_process.stdout.readline, ''):
                if not line:
                    break
                
                # 将输出添加到缓冲区
                with threading.Lock():
                    self.task_output_buffer.append(line)
            
            # 等待进程结束
            exit_code = self.task_process.wait()
            
            # 进程结束，记录状态
            end_time = datetime.now()
            duration = (end_time - self.task_start_time).total_seconds() if self.task_start_time else 0
            
            # 添加任务结束标记到日志
            end_message = f"=================== 任务执行结束: {end_time}, 耗时: {duration:.2f}秒, 退出码: {exit_code} ===================\n"
            with threading.Lock():
                self.task_output_buffer.append(end_message)
            
            # 根据退出码设置任务状态
            if exit_code == 0:
                self.task_status = "completed"
                logger.info(f"任务执行成功: 退出码={exit_code}, 耗时={duration:.2f}秒")
            else:
                self.task_status = "failed"
                logger.error(f"任务执行失败: 退出码={exit_code}, 耗时={duration:.2f}秒")
            
            # 发送最后一次心跳
            self.send_heartbeat()
            
            # 任务完成，可以退出
            self.running = False
        except Exception as e:
            logger.error(f"读取任务输出失败: {str(e)}")
            self.task_status = "failed"
            
            with threading.Lock():
                self.task_output_buffer.append(f"读取任务输出失败: {str(e)}\n{traceback.format_exc()}\n")
            
            # 发送最后一次心跳
            self.send_heartbeat()
            
            # 任务失败，可以退出
            self.running = False
    
    def cleanup(self):
        """清理资源并退出"""
        logger.info("开始清理资源...")
        
        # 停止运行标志
        self.running = False
        
        # 终止任务进程
        if self.task_process and self.task_process.poll() is None:
            try:
                logger.info(f"终止任务进程: PID={self.task_process.pid}")
                self.task_process.terminate()
                self.task_process.wait(timeout=5)
            except:
                try:
                    self.task_process.kill()
                except:
                    pass
        
        # 删除临时脚本文件
        if self.task_script_file and os.path.exists(self.task_script_file):
            try:
                os.unlink(self.task_script_file)
                logger.info(f"已删除临时脚本文件: {self.task_script_file}")
            except:
                pass
        
        # 等待任务输出线程结束
        if self.task_output_thread and self.task_output_thread.is_alive():
            self.task_output_thread.join(timeout=3)
        
        # 等待心跳线程结束
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=3)
        
        logger.info("资源清理完成")
    
    def run(self):
        """运行子Agent"""
        logger.info("子Agent开始运行...")
        
        # 注册Agent
        if not self.register():
            logger.error("注册失败，Agent无法启动")
            return False
        
        # 设置运行标志
        self.running = True
        
        # 开始心跳
        self.start_heartbeat()
        
        # 启动任务执行
        if not self.start_task():
            logger.error("任务启动失败")
            self.running = False
            return False
        
        try:
            # 主循环，等待任务完成
            while self.running:
                time.sleep(1)
                
                # 检查任务进程是否仍在运行
                if self.task_process and self.task_process.poll() is not None:
                    # 任务进程已结束，等待一会以确保输出线程完成处理
                    time.sleep(2)
                    break
        except KeyboardInterrupt:
            logger.info("收到中断信号，准备退出")
            self.task_status = "failed"
        finally:
            # 清理资源
            self.cleanup()
        
        return self.task_status == "completed"


def setup_sub_agent(main_agent_id, task_id, name=None, server_url=None,
                   cpu_cores=None, gpu_ids=None):
    """设置并运行子Agent
    
    Args:
        main_agent_id: 主Agent ID
        task_id: 任务ID
        name: Agent名称
        server_url: 服务器URL
        cpu_cores: CPU核心数
        gpu_ids: GPU ID列表或逗号分隔的字符串
        
    Returns:
        bool: 运行是否成功
    """
    try:
        # 创建子Agent
        agent = SubAgent(
            main_agent_id=main_agent_id,
            task_id=task_id,
            name=name,
            server_url=server_url,
            cpu_cores=cpu_cores,
            gpu_ids=gpu_ids
        )
        
        # 运行子Agent
        return agent.run()
    except Exception as e:
        logger.error(f"运行子Agent失败: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="子Agent程序")
    parser.add_argument("--main-id", required=True, help="主Agent ID")
    parser.add_argument("--task-id", required=True, help="任务ID")
    parser.add_argument("--name", help="Agent名称")
    parser.add_argument("--server", help="服务器URL")
    parser.add_argument("--cpu-cores", type=int, help="CPU核心数")
    parser.add_argument("--gpu-ids", help="GPU IDs，逗号分隔")
    
    args = parser.parse_args()
    
    # 运行子Agent
    success = setup_sub_agent(
        main_agent_id=args.main_id,
        task_id=args.task_id,
        name=args.name,
        server_url=args.server,
        cpu_cores=args.cpu_cores,
        gpu_ids=args.gpu_ids
    )
    
    # 设置退出码
    sys.exit(0 if success else 1)
