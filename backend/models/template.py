#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
脚本模板数据模型
"""

from datetime import datetime
from backend.utils.database import get_db
from backend.utils.logger import system_logger

class Template:
    """脚本模板数据模型类"""
    
    def __init__(self, id=None, name=None, content=None, created_time=None):
        """初始化脚本模板实例
        
        Args:
            id: 模板ID
            name: 模板名称
            content: 脚本内容
            created_time: 创建时间
        """
        self.id = id
        self.name = name
        self.content = content
        self.created_time = created_time or datetime.now()
    
    @classmethod
    def create_template(cls, name, content):
        """创建新模板
        
        Args:
            name: 模板名称
            content: 脚本内容
            
        Returns:
            template: 新创建的模板实例，如果失败则返回None
        """
        if not name or not content:
            system_logger.error("创建模板失败: 名称和内容不能为空")
            return None
        
        db = get_db()
        
        # 检查名称是否已存在
        check_query = "SELECT id FROM templates WHERE name = ?"
        existing = db.fetch_one(check_query, (name,))
        if existing:
            system_logger.error(f"创建模板失败: 名称已存在: {name}")
            return None
        
        # 插入模板记录
        query = """
            INSERT INTO templates (name, content, created_time)
            VALUES (?, ?, ?)
        """
        created_time = datetime.now()
        params = (name, content, created_time)
        
        try:
            cursor = db.execute(query, params)
            template_id = cursor.lastrowid
            system_logger.info(f"创建模板成功: ID={template_id}, 名称={name}")
            
            # 返回创建的模板实例
            return cls.get_template_by_id(template_id)
        except Exception as e:
            system_logger.error(f"创建模板异常: {str(e)}")
            return None
    
    @classmethod
    def get_template_by_id(cls, template_id):
        """根据ID获取模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            template: 模板实例，如果不存在则返回None
        """
        db = get_db()
        query = "SELECT * FROM templates WHERE id = ?"
        template_data = db.fetch_one(query, (template_id,))
        
        if not template_data:
            return None
        
        # 构建模板实例
        template = cls(
            id=template_data['id'],
            name=template_data['name'],
            content=template_data['content'],
            created_time=template_data['created_time']
        )
        
        return template
    
    @classmethod
    def get_template_by_name(cls, name):
        """根据名称获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            template: 模板实例，如果不存在则返回None
        """
        db = get_db()
        query = "SELECT * FROM templates WHERE name = ?"
        template_data = db.fetch_one(query, (name,))
        
        if not template_data:
            return None
        
        # 构建模板实例
        template = cls(
            id=template_data['id'],
            name=template_data['name'],
            content=template_data['content'],
            created_time=template_data['created_time']
        )
        
        return template
    
    @classmethod
    def get_all_templates(cls):
        """获取所有模板
        
        Returns:
            list: 所有模板实例列表
        """
        db = get_db()
        query = "SELECT * FROM templates ORDER BY name"
        templates_data = db.fetch_all(query)
        
        templates = []
        for data in templates_data:
            template = cls(
                id=data['id'],
                name=data['name'],
                content=data['content'],
                created_time=data['created_time']
            )
            templates.append(template)
        
        return templates
    
    def update_template(self):
        """更新模板信息到数据库
        
        Returns:
            bool: 更新是否成功
        """
        if not self.id:
            system_logger.error("更新模板失败: 无效的模板ID")
            return False
        
        # 检查名称是否已被其他模板使用
        db = get_db()
        check_query = "SELECT id FROM templates WHERE name = ? AND id != ?"
        existing = db.fetch_one(check_query, (self.name, self.id))
        if existing:
            system_logger.error(f"更新模板失败: 名称已被其他模板使用: {self.name}")
            return False
        
        query = """
            UPDATE templates SET
                name = ?,
                content = ?
            WHERE id = ?
        """
        params = (self.name, self.content, self.id)
        
        try:
            db.execute(query, params)
            system_logger.info(f"更新模板成功: ID={self.id}, 名称={self.name}")
            return True
        except Exception as e:
            system_logger.error(f"更新模板异常: {str(e)}")
            return False
    
    def delete_template(self):
        """删除模板
        
        Returns:
            bool: 删除是否成功
        """
        if not self.id:
            system_logger.error("删除模板失败: 无效的模板ID")
            return False
        
        db = get_db()
        query = "DELETE FROM templates WHERE id = ?"
        
        try:
            db.execute(query, (self.id,))
            system_logger.info(f"删除模板成功: ID={self.id}, 名称={self.name}")
            return True
        except Exception as e:
            system_logger.error(f"删除模板异常: {str(e)}")
            return False
    
    def to_dict(self):
        """将模板转换为字典
        
        Returns:
            dict: 模板字典表示
        """
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'created_time': self.created_time
        }
