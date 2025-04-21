#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
资源监控工具

用于获取系统资源信息，包括CPU、内存和GPU
"""

import os
import time
import logging
import psutil
import subprocess
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("resource_util")

class ResourceUtil:
    """资源监控工具类，提供获取系统资源信息的方法"""
    
    def __init__(self):
        """初始化资源监控工具"""
        # 尝试导入pynvml，如果失败则记录警告
        try:
            import pynvml
            self.pynvml = pynvml
            self.has_gpu = True
            self.pynvml.nvmlInit()
        except ImportError:
            logger.warning("pynvml模块未安装，无法获取GPU信息")
            self.has_gpu = False
        except Exception as e:
            logger.warning(f"初始化NVML失败: {str(e)}")
            self.has_gpu = False
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'has_gpu') and self.has_gpu:
            try:
                self.pynvml.nvmlShutdown()
            except:
                pass
    
    def get_gpu_info(self):
        """获取所有GPU的ID、使用率、显存使用量
        
        Returns:
            dict: GPU信息
                {
                    'gpu_ids': GPU ID列表,
                    'gpu_usage': GPU使用率字典，键为GPU ID，值为使用率,
                    'gpu_memory_usage': GPU显存使用率字典，键为GPU ID，值为使用率,
                    'gpu_memory_total': GPU总显存字典，键为GPU ID，值为显存大小(MB)
                }
        """
        result = {
            'gpu_ids': [],
            'gpu_usage': {},
            'gpu_memory_usage': {},
            'gpu_memory_total': {}
        }
        
        if not self.has_gpu:
            return result
        
        try:
            # 获取GPU设备数量
            device_count = self.pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                # 获取GPU句柄
                handle = self.pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # 获取GPU ID（使用索引作为ID）
                gpu_id = str(i)
                result['gpu_ids'].append(gpu_id)
                
                # 获取GPU使用率
                try:
                    utilization = self.pynvml.nvmlDeviceGetUtilizationRates(handle)
                    result['gpu_usage'][gpu_id] = utilization.gpu / 100.0
                except:
                    result['gpu_usage'][gpu_id] = 0.0
                
                # 获取显存信息
                try:
                    mem_info = self.pynvml.nvmlDeviceGetMemoryInfo(handle)
                    total_memory = mem_info.total / (1024 * 1024)  # 转换为MB
                    used_memory = mem_info.used / (1024 * 1024)    # 转换为MB
                    
                    result['gpu_memory_total'][gpu_id] = total_memory
                    result['gpu_memory_usage'][gpu_id] = used_memory / total_memory if total_memory > 0 else 0.0
                except:
                    result['gpu_memory_total'][gpu_id] = 0
                    result['gpu_memory_usage'][gpu_id] = 0.0
        except Exception as e:
            logger.error(f"获取GPU信息失败: {str(e)}")
        
        return result
    
    def get_cpu_core_count(self):
        """获取可用CPU核心数
        
        优先考虑cgroups限制，失败后使用psutil获取
        
        Returns:
            int: CPU核心数
        """
        # 首先尝试从cgroups获取限制（适用于容器环境）
        try:
            # 检查cgroup v2
            if os.path.exists('/sys/fs/cgroup/cpu.max'):
                with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                    content = f.read().strip()
                    if content != 'max':
                        quota, period = map(int, content.split())
                        if quota > 0 and period > 0:
                            return max(1, quota // period)
            
            # 检查cgroup v1
            elif os.path.exists('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') and \
                 os.path.exists('/sys/fs/cgroup/cpu/cpu.cfs_period_us'):
                with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
                    quota = int(f.read().strip())
                with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us', 'r') as f:
                    period = int(f.read().strip())
                if quota > 0 and period > 0:
                    return max(1, quota // period)
        except Exception as e:
            logger.warning(f"获取cgroups CPU限制失败: {str(e)}")
        
        # 如果cgroups方法失败，使用psutil获取
        return psutil.cpu_count()
    
    def get_cpu_usage(self, pid=None, interval=0.1):
        """获取CPU使用率
        
        如果指定了pid，获取指定进程及其所有子进程的CPU使用率总和
        否则获取系统总体CPU使用率
        
        Args:
            pid: 进程ID，None表示获取系统总体使用率
            interval: 采样间隔（秒）
            
        Returns:
            float: CPU使用率（0.0-1.0）
        """
        if pid is None:
            # 获取系统总体CPU使用率
            return psutil.cpu_percent(interval=interval) / 100.0
        
        try:
            # 获取指定进程
            process = psutil.Process(pid)
            
            # 获取进程列表（包括所有子进程）
            processes = [process]
            processes.extend(process.children(recursive=True))
            
            # 第一次采样
            cpu_times_1 = defaultdict(float)
            for p in processes:
                try:
                    cpu_times_1[p.pid] = sum(p.cpu_times())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 等待采样间隔
            time.sleep(interval)
            
            # 第二次采样
            cpu_times_2 = defaultdict(float)
            for p in processes:
                try:
                    cpu_times_2[p.pid] = sum(p.cpu_times())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 计算时间差
            cpu_time_diff = sum(cpu_times_2[pid] - cpu_times_1[pid] for pid in cpu_times_1.keys())
            
            # 计算使用率
            cpu_count = self.get_cpu_core_count()
            usage = cpu_time_diff / (interval * cpu_count)
            
            return min(usage, 1.0)  # 确保不超过100%
        except Exception as e:
            logger.error(f"获取进程CPU使用率失败: PID={pid}, 错误={str(e)}")
            return 0.0
    
    def get_memory_usage(self, pid=None):
        """获取内存使用情况
        
        如果指定了pid，获取指定进程及其所有子进程的内存使用率总和
        否则获取系统总体内存使用率
        
        Args:
            pid: 进程ID，None表示获取系统总体使用率
            
        Returns:
            float: 内存使用率（0.0-1.0）
        """
        if pid is None:
            # 获取系统内存使用率
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        
        try:
            # 获取指定进程
            process = psutil.Process(pid)
            
            # 获取进程列表（包括所有子进程）
            processes = [process]
            processes.extend(process.children(recursive=True))
            
            # 计算总内存使用量
            total_memory = 0
            for p in processes:
                try:
                    # 使用RSS（Resident Set Size）作为内存使用量
                    memory_info = p.memory_info()
                    total_memory += memory_info.rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 计算系统总内存
            system_memory = psutil.virtual_memory().total
            
            # 计算使用率
            usage = total_memory / system_memory
            
            return min(usage, 1.0)  # 确保不超过100%
        except Exception as e:
            logger.error(f"获取进程内存使用率失败: PID={pid}, 错误={str(e)}")
            return 0.0
    
    def get_resource_info(self, pid=None):
        """获取资源信息汇总
        
        Args:
            pid: 进程ID，None表示获取系统总体资源
            
        Returns:
            dict: 资源信息
                {
                    'cpu_cores': CPU核心数,
                    'cpu_usage': CPU使用率,
                    'memory_usage': 内存使用率,
                    'gpu_ids': GPU ID列表,
                    'gpu_usage': GPU使用率字典,
                    'gpu_memory_usage': GPU显存使用率字典,
                    'gpu_memory_total': GPU总显存字典
                }
        """
        result = {
            'cpu_cores': self.get_cpu_core_count(),
            'cpu_usage': self.get_cpu_usage(pid),
            'memory_usage': self.get_memory_usage(pid),
        }
        
        # 获取GPU信息
        gpu_info = self.get_gpu_info()
        result.update(gpu_info)
        
        return result


# 单例模式
resource_util = ResourceUtil()

def get_resource_util():
    """获取资源工具实例"""
    return resource_util
