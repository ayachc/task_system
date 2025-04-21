#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
脚本模板服务
"""

from backend.models.template import Template
from backend.utils.logger import system_logger

class TemplateService:
    """脚本模板服务类，封装模板相关业务逻辑"""
    
    def __init__(self):
        """初始化模板服务"""
        pass
    
    def create_template(self, name, content):
        """创建新脚本模板
        
        Args:
            name: 模板名称
            content: 脚本内容
            
        Returns:
            template: 新创建的模板，如果失败则返回None
        """
        # 参数验证
        if not name or not content:
            system_logger.error("创建模板失败: 名称和内容不能为空")
            return None
        
        # 检查名称是否已存在
        existing = Template.get_template_by_name(name)
        if existing:
            system_logger.error(f"创建模板失败: 名称已存在: {name}")
            return None
        
        # 创建模板
        return Template.create_template(name, content)
    
    def get_template_by_id(self, template_id):
        """根据ID获取模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            template: 模板实例，如果不存在则返回None
        """
        return Template.get_template_by_id(template_id)
    
    def get_template_by_name(self, name):
        """根据名称获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            template: 模板实例，如果不存在则返回None
        """
        return Template.get_template_by_name(name)
    
    def get_all_templates(self):
        """获取所有模板
        
        Returns:
            list: 所有模板实例列表
        """
        return Template.get_all_templates()
    
    def update_template(self, template_id, name=None, content=None):
        """更新模板
        
        Args:
            template_id: 模板ID
            name: 新模板名称，如果为None则不更新
            content: 新脚本内容，如果为None则不更新
            
        Returns:
            bool: 更新是否成功
        """
        # 获取现有模板
        template = Template.get_template_by_id(template_id)
        if not template:
            system_logger.error(f"更新模板失败: 模板不存在: ID={template_id}")
            return False
        
        # 更新字段
        if name is not None:
            template.name = name
        
        if content is not None:
            template.content = content
        
        # 保存更新
        return template.update_template()
    
    def delete_template(self, template_id):
        """删除模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            bool: 删除是否成功
        """
        # 获取模板
        template = Template.get_template_by_id(template_id)
        if not template:
            system_logger.error(f"删除模板失败: 模板不存在: ID={template_id}")
            return False
        
        # 删除模板
        return template.delete_template()
    
    def search_templates(self, keyword=None):
        """搜索模板
        
        Args:
            keyword: 搜索关键词，匹配名称或内容
            
        Returns:
            list: 匹配的模板列表
        """
        if not keyword:
            return self.get_all_templates()
        
        # 获取所有模板并过滤
        all_templates = Template.get_all_templates()
        
        # 关键词搜索
        keyword = keyword.lower()
        filtered_templates = [
            template for template in all_templates
            if keyword in template.name.lower() or keyword in template.content.lower()
        ]
        
        return filtered_templates
