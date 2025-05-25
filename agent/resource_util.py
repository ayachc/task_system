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
    
    def get_available_gpu_ids(self):
        """获取可用的GPU ID列表
        
        优先使用CUDA相关环境变量，如果不存在则返回所有GPU
        
        Returns:
            list: 可用GPU ID列表
        """
        gpu_ids = []
        
        # 首先从环境变量获取CUDA_VISIBLE_DEVICES
        cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
        if cuda_devices is not None and cuda_devices != "":
            # CUDA_VISIBLE_DEVICES可能是逗号分隔的ID列表，如"0,1,2"
            try:
                # 处理可能的情况，如"0,1,2"或"0"
                gpu_ids = [dev.strip() for dev in cuda_devices.split(',') if dev.strip()]
                return gpu_ids
            except Exception as e:
                logger.warning(f"解析CUDA_VISIBLE_DEVICES环境变量失败: {str(e)}")
        
        # 如果没有环境变量或解析失败，尝试获取所有GPU
        if not self.has_gpu:
            return gpu_ids
        
        try:
            # 获取GPU设备数量
            device_count = self.pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                gpu_ids.append(str(i))
        except Exception as e:
            logger.error(f"获取可用GPU ID失败: {str(e)}")
        
        return gpu_ids

    def get_gpu_info(self):
        """获取指定GPU的ID、使用率、显存使用量
        
        只返回get_available_gpu_ids返回的GPU列表中包含的GPU信息
        
        Returns:
            list: GPU信息列表，每个元素为包含单个GPU信息的字典
                [
                    {
                        'gpu_id': GPU ID,
                        'usage': GPU使用率,
                        'memory_used': 已用显存(字节),
                        'memory_total': 总显存(字节),
                        'memory_usage': 显存使用率,
                        'is_available': 是否可用
                    },
                    ...
                ]
        """
        result = []
        
        if not self.has_gpu:
            return result
        
        # 获取可用的GPU ID列表
        available_gpu_ids = self.get_available_gpu_ids()
        if not available_gpu_ids:
            return result
        
        try:
            # 获取GPU设备数量
            device_count = self.pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                gpu_id = str(i)
                
                # 只处理可用GPU列表中包含的GPU
                if gpu_id not in available_gpu_ids:
                    continue
                
                # 获取GPU句柄
                handle = self.pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # 初始化GPU信息字典
                gpu_info = {
                    'gpu_id': gpu_id,
                    'usage': 0.0,
                    'memory_used': 0,
                    'memory_total': 0,
                    'memory_usage': 0.0,
                    'is_available': True  # 默认可用
                }
                
                # 获取GPU使用率
                try:
                    utilization = self.pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_info['usage'] = utilization.gpu / 100.0
                except:
                    pass
                
                # 获取显存信息
                try:
                    mem_info = self.pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_info['memory_total'] = mem_info.total
                    gpu_info['memory_used'] = mem_info.used
                    gpu_info['memory_usage'] = mem_info.used / mem_info.total if mem_info.total > 0 else 0.0
                except:
                    pass
                
                # 添加到结果列表
                result.append(gpu_info)
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

    def get_memory_total(self):
        """获取系统可用的总内存量
        
        优先从cgroup获取，然后使用psutil获取系统总内存
        
        Returns:
            int: 内存总量(字节)
        """
        # 首先尝试从cgroups获取限制（适用于容器环境）
        try:
            # 检查cgroup v2
            if os.path.exists('/sys/fs/cgroup/memory.max'):
                with open('/sys/fs/cgroup/memory.max', 'r') as f:
                    content = f.read().strip()
                    if content != 'max':
                        return int(content)
            
            # 检查cgroup v1
            elif os.path.exists('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
                with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                    limit = int(f.read().strip())
                    # 非无限制的值（不等于 2^64-1）
                    if limit < 2**63:
                        return limit
        except Exception as e:
            logger.warning(f"获取cgroups内存限制失败: {str(e)}")
        
        # 如果无法从cgroups获取，使用psutil获取系统总内存
        return psutil.virtual_memory().total

    def get_cpu_usage(self, pid=None, interval=0.1):
        """获取CPU使用率
        
        获取系统或者指定进程（含递归子进程）的CPU使用率总和（可超过100%）
        
        Args:
            pid: 进程ID，None表示获取系统总体使用率
            interval: 采样间隔（秒）
            
        Returns:
            float: 总CPU使用率（百分比，可超过100%）
        """
        if pid is None:
            # 获取系统CPU使用率
            return psutil.cpu_percent(interval=interval)
        
        try:
            # 获取指定进程
            process = psutil.Process(pid)
            
            # 获取进程列表（包括所有子进程）
            processes = [process] + process.children(recursive=True)
            
            # 预热采样，不使用第一次结果
            for p in processes:
                try:
                    p.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # 等待采样间隔
            time.sleep(interval)
            
            # 获取所有进程的CPU使用率总和
            total_cpu_percent = 0
            processes = [process] + process.children(recursive=True)
            # 第二次采样，获取实际结果
            for p in processes:
                try:
                    cpu_percent = p.cpu_percent()
                    total_cpu_percent += cpu_percent
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return total_cpu_percent
        except Exception as e:
            logger.error(f"获取进程CPU使用率失败: PID={pid}, 错误={str(e)}")
            return 0.0
    
    def get_memory_usage(self, pid=None):
        """获取内存使用量（不是百分比）
        
        获取指定进程（含递归子进程）的内存使用量总和(字节)
        
        Args:
            pid: 进程ID，None表示获取系统总体内存使用量
            
        Returns:
            int: 内存使用量(字节)
        """
        if pid is None:
            # 获取系统内存使用量
            return psutil.virtual_memory().used
        
        try:
            # 获取指定进程
            process = psutil.Process(pid)
            
            # 获取进程列表（包括所有子进程）
            processes = [process] + process.children(recursive=True)
            
            # 计算总内存使用量
            total_memory = 0
            for p in processes:
                try:
                    # 使用RSS（Resident Set Size）作为内存使用量
                    memory_info = p.memory_info()
                    total_memory += memory_info.rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return total_memory
        except Exception as e:
            logger.error(f"获取进程内存使用量失败: PID={pid}, 错误={str(e)}")
            return 0

    def get_resource_info(self, pid=None):
        """获取资源信息汇总
        
        Args:
            pid: 进程ID，None表示获取系统总体资源
            
        Returns:
            dict: 资源信息
                {
                    'cpu_cores': CPU核心数,
                    'cpu_usage': CPU使用率(百分比，可能超过100%),
                    'memory_total': 系统总内存(字节),
                    'memory_total_usage': 系统总内存使用量(字节),
                    'memory_usage': 内存使用量(字节),
                    'gpu_info': GPU信息列表,
                    'gpu_ids': 可用GPU ID列表
                }
        """
        result = {
            'cpu_cores': self.get_cpu_core_count(),
            'cpu_usage': self.get_cpu_usage(pid),
            'memory_total': self.get_memory_total(),
            'memory_total_usage': self.get_memory_usage(),
            'memory_usage': self.get_memory_usage(pid),
            'gpu_info': self.get_gpu_info(),
            'gpu_ids': self.get_available_gpu_ids()
        }
        
        return result


def get_resource_util():
    """获取资源工具实例"""
    resource_util = ResourceUtil()
    return resource_util
