#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger(name, log_file=None, level=logging.INFO):
    """设置日志器
    
    Args:
        name: 日志器名称
        log_file: 日志文件路径，如果为None则只输出到控制台
        level: 日志级别
    
    Returns:
        logger: 日志器实例
    """
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 如果已有处理器，则不重复添加
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 创建滚动文件处理器，最大5MB，保留3个备份
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_task_logger(task_id):
    """获取任务日志器
    
    Args:
        task_id: 任务ID
    
    Returns:
        logger: 任务日志器实例
    """
    log_file = os.path.join(Config.TASK_LOG_PATH, f"task_{task_id}.log")
    return setup_logger(f"task_{task_id}", log_file)

def get_system_logger():
    """获取系统日志器
    
    Returns:
        logger: 系统日志器实例
    """
    log_file = os.path.join(Config.SYSTEM_LOG_PATH, "system.log")
    return setup_logger("system", log_file)

def get_agent_logger(agent_id):
    """获取Agent日志器
    
    Args:
        agent_id: Agent ID
    
    Returns:
        logger: Agent日志器实例
    """
    log_file = os.path.join(Config.SYSTEM_LOG_PATH, f"agent_{agent_id}.log")
    return setup_logger(f"agent_{agent_id}", log_file)

# 系统主日志器
system_logger = get_system_logger()
