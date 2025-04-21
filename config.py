#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统配置文件
"""

import os

class Config:
    """应用配置类"""
    # 基础配置
    DEBUG = True
    PORT = 5000
    SECRET_KEY = 'llm-task-system-secret-key'
    
    # 数据库配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'database', 'task_system.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 日志配置
    LOG_DIR = os.path.join(BASE_DIR, 'data', 'logs')
    SYSTEM_LOG_PATH = os.path.join(LOG_DIR, 'system')
    TASK_LOG_PATH = os.path.join(LOG_DIR, 'tasks')
    
    # Agent配置
    HEARTBEAT_TIMEOUT = 10  # 心跳超时时间（秒）
    MAIN_AGENT_HEARTBEAT_INTERVAL = 2  # 主Agent心跳间隔（秒）
    SUB_AGENT_HEARTBEAT_INTERVAL = 1   # 子Agent心跳间隔（秒）
    
    # API服务器地址
    SERVER_URL = 'http://localhost:5000'  # 服务器地址，Agent使用此地址连接服务器
