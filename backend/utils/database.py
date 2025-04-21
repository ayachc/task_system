#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库工具模块
"""

import os
import sqlite3
import logging
from config import Config

logger = logging.getLogger(__name__)

class Database:
    """数据库操作类"""
    
    def __init__(self, db_path=None):
        """初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        if db_path is None:
            db_path = Config.DATABASE_PATH
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 设置返回结果为字典格式
            logger.info(f"连接到数据库: {self.db_path}")
            return self.conn
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    def execute(self, query, params=None):
        """执行SQL语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            cursor: 执行结果游标
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
            return cursor
        except Exception as e:
            self.conn.rollback()
            logger.error(f"SQL执行错误: {str(e)}, 查询: {query}, 参数: {params}")
            raise
    
    def fetch_all(self, query, params=None):
        """执行查询并返回所有结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            list: 查询结果列表
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        """执行查询并返回单个结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            dict: 查询结果
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def init_tables(self):
        """初始化数据库表结构"""
        # 任务表
        self.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            template_type TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 3,
            status TEXT NOT NULL DEFAULT 'waiting',
            created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            script_content TEXT NOT NULL,
            cpu_cores INTEGER,
            gpu_count INTEGER,
            gpu_memory INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            execution_time INTEGER,
            agent_id TEXT,
            log_file TEXT
        )
        ''')
        
        # 任务依赖表
        self.execute('''
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            depends_on_id INTEGER NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (depends_on_id) REFERENCES tasks (id)
        )
        ''')
        
        # Agent表
        self.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'online',
            created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_heartbeat_time TIMESTAMP,
            running_time INTEGER DEFAULT 0,
            cpu_cores INTEGER,
            cpu_usage REAL DEFAULT 0,
            memory_usage REAL DEFAULT 0,
            task_id INTEGER,
            main_agent_id TEXT,
            available_cpu_cores INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
        ''')
        
        # Agent GPU表
        self.execute('''
        CREATE TABLE IF NOT EXISTS agent_gpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            gpu_id TEXT NOT NULL,
            gpu_usage REAL DEFAULT 0,
            gpu_memory_usage REAL DEFAULT 0,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
        ''')
        
        # 脚本模板表
        self.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        logger.info("数据库表结构初始化完成")

# 创建全局数据库实例
db = Database()

def get_db():
    """获取数据库实例"""
    if not db.conn:
        db.connect()
    return db
