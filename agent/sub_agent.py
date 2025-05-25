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
    
    def __init__(self, main_agent_id, task, server_url=None):
        """初始化子Agent
        
        Args:
            main_agent_id: 主Agent ID
            task: 任务
            server_url: 服务器URL
            cpu_cores: 分配的CPU核心数
            gpu_ids: 分配的GPU ID列表
        """
        # 基本信息
        self.id = None
        self.main_agent_id = main_agent_id
        self.task = task
        self.task_id = task['id']
        self.name = f"sub_agent_for_task_{task['id']}"
        self.server_url = server_url
        self.running = False
        self.heartbeat_thread = None
        self.start_time = datetime.now()
        
        # 资源信息
        self.cpu_cores = task['cpu_cores']
        self.gpu_ids = task['gpu_ids']
        self.resource_util = get_resource_util()
        
        # 任务执行
        self.task_process = None
        self.task_output_thread = None
        self.task_output_buffer = []
        self.task_status = "waiting"  # blocked, waiting, running, completed, failed, canceled
        self.task_start_time = None
        self.task_script_file = None
        
        # 创建日志目录
        self.log_dir = os.path.join(ROOT_DIR, 'data', 'logs', 'agents')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 设置子Agent的日志输出到文件
        file_handler = logging.FileHandler(os.path.join(self.log_dir, f"{self.name}.log"))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
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
            
        except Exception as e:
            logger.error(f"子Agent注册异常: {str(e)}")
    
    def start_heartbeat(self):
        """启动心跳线程"""
        
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
            resource_info = self.resource_util.get_resource_info(os.getpid())
            resource_info["available_cpu_cores"] = self.cpu_cores
            resource_info["gpu_info"] = [gpu for gpu in resource_info["gpu_info"] if gpu["gpu_id"] in self.gpu_ids]
            
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
                    if action == 'quit':
                        logger.info("收到停止指令，准备退出")
                        self.close()
                    
                    return True
                else:
                    logger.error(f"心跳处理失败: {result.get('message', '未知错误')}")
            else:
                logger.error(f"心跳发送失败: HTTP状态码={response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
            return False
    
    def run_task(self):
        """启动任务执行
        
        Returns:
            bool: 启动是否成功
        """
        try:
            task = self.task
            script_content = task.get('script_content')
            
            if not script_content:
                logger.error("任务脚本内容为空")
                return False
            
            # 检测操作系统类型
            is_windows = sys.platform.startswith('win')
            
            # 创建临时脚本文件，Windows 使用 .bat 后缀，其他系统使用 .sh
            suffix = '.bat' if is_windows else '.sh'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='wb') as temp:
                self.task_script_file = temp.name
                # 对于 Windows，确保使用 CRLF 行尾
                if is_windows:
                    script_content = script_content.replace('\n', '\r\n')
                temp.write(script_content.encode('utf-8'))
            
            # 在非 Windows 系统上设置执行权限
            if not is_windows:
                os.chmod(self.task_script_file, 0o755)
            
            # 准备环境变量
            env = os.environ.copy()
            
            # 设置GPU环境变量
            if self.gpu_ids:
                env['CUDA_VISIBLE_DEVICES'] = ','.join(self.gpu_ids)
            
            # 启动任务进程，将输出重定向到文件
            logger.info(f"启动任务执行: 脚本文件={self.task_script_file}")
            self.task_status = "running"
            self.task_start_time = datetime.now()
            
            # 添加任务开始标记到日志
            self.task_output_buffer.append(f"=================== start: {self.task_start_time} ===================\n")
            
            # 设置任务日志文件
            self.task_log_file = os.path.join(self.log_dir, f"task_{self.task_id}.log")
            
            # 启动进程
            with open(self.task_log_file, 'w', buffering=1) as log_file:  # 使用行缓冲
                # 根据操作系统类型选择不同的启动方式
                if sys.platform.startswith('win'):
                    # Windows 上直接执行脚本文件
                    self.task_process = subprocess.Popen(
                        self.task_script_file,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        env=env,
                        shell=True,  # Windows 上需要 shell=True 来执行批处理文件
                        text=True,
                        bufsize=1    # 使用行缓冲
                    )
                else:
                    # Linux/macOS 上使用 bash 执行
                    self.task_process = subprocess.Popen(
                        ['/bin/bash', self.task_script_file],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        env=env,
                        text=True,
                        bufsize=1    # 使用行缓冲
                    )
            logger.info(f"任务进程已启动: PID={self.task_process.pid}")
            
            # 确保日志文件存在
            while not os.path.exists(self.task_log_file) and self.running:
                time.sleep(0.1)

            # 使用单独的文件句柄读取日志    
            with open(self.task_log_file, 'r') as f:
                # 跳到文件末尾
                f.seek(0, 2)
                
                # 循环直到进程结束
                while True:
                    line = f.readline()
                    if line:
                        # 将输出添加到缓冲区
                        with threading.Lock():
                            self.task_output_buffer.append(line)
                    else:
                        if self.task_process.poll() is not None:
                            break
                        # 没有新内容，短暂等待
                        time.sleep(0.1)

            # 获取退出码 - 现在只需获取一次，因为poll()已经检测到进程结束
            exit_code = self.task_process.returncode
            
            # 进程结束，记录状态
            end_time = datetime.now()
            duration = (end_time - self.task_start_time).total_seconds() if self.task_start_time else 0
            
            # 添加任务结束标记到日志
            end_message = f"=================== end: {end_time}, time: {duration:.2f}s, exit_code: {exit_code} ===================\n"
            with threading.Lock():
                self.task_output_buffer.append(end_message)
            
            # 根据退出码设置任务状态
            if exit_code == 0:
                self.task_status = "completed"
                logger.info(f"任务执行成功: 退出码={exit_code}, 耗时={duration:.2f}秒")
            else:
                self.task_status = "failed"
                logger.error(f"任务执行失败: 退出码={exit_code}, 耗时={duration:.2f}秒")
            
            # 任务完成，可以退出
            self.running = False

            # 发送最后一次心跳
            self.send_heartbeat()

            return True
        except Exception as e:
            logger.error(f"启动任务执行失败: {str(e)}")
            self.task_status = "failed"
            self.task_output_buffer.append(f"failed: {str(e)}\n{traceback.format_exc()}\n")
            return False
    
    def close(self):
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
        self.register()
        
        # 设置运行标志
        self.running = True
        
        # 开始心跳
        self.start_heartbeat()

        # 启动任务
        self.run_task()

        # 结束agent
        self.close()



if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="子Agent程序")
    parser.add_argument("--main-id", required=True, help="主Agent ID")
    parser.add_argument("--task", required=True, help="任务")
    parser.add_argument("--server", help="服务器URL")
    
    args = parser.parse_args()
    
    try:
        # 创建子Agent
        agent = SubAgent(
            main_agent_id=args.main_id,
            task=json.loads(args.task),
            server_url=args.server,
        )
        agent.run()
    except Exception as e:
        logger.error(f"运行子Agent失败: {str(e)}")
