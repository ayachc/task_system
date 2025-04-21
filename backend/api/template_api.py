#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
脚本模板管理API接口
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from backend.services.template_service import TemplateService
from backend.utils.logger import system_logger

# 创建蓝图
template_bp = Blueprint('template', __name__)

# 实例化模板服务
template_service = TemplateService()

# 日期时间转换函数
def json_serial(obj):
    """序列化日期/时间为JSON"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")

@template_bp.route('/', methods=['GET'])
def get_templates():
    """获取所有脚本模板"""
    try:
        # 解析查询参数
        keyword = request.args.get('keyword')
        
        # 搜索模板
        if keyword:
            templates = template_service.search_templates(keyword)
        else:
            templates = template_service.get_all_templates()
        
        # 转换为字典
        templates_dict = [template.to_dict() for template in templates]
        
        return jsonify({
            'success': True,
            'data': templates_dict
        }), 200
    except Exception as e:
        system_logger.error(f"获取模板列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取模板列表失败: {str(e)}"
        }), 500

@template_bp.route('/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """获取单个脚本模板"""
    try:
        template = template_service.get_template_by_id(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': f"模板不存在: ID={template_id}"
            }), 404
        
        return jsonify({
            'success': True,
            'data': template.to_dict()
        }), 200
    except Exception as e:
        system_logger.error(f"获取模板失败: ID={template_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取模板失败: {str(e)}"
        }), 500

@template_bp.route('/', methods=['POST'])
def create_template():
    """创建新脚本模板"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 检查必要字段
        required_fields = ['name', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f"缺少必要字段: {field}"
                }), 400
        
        # 创建模板
        template = template_service.create_template(
            name=data['name'],
            content=data['content']
        )
        
        if not template:
            return jsonify({
                'success': False,
                'message': "模板创建失败，可能是名称已存在"
            }), 400
        
        return jsonify({
            'success': True,
            'data': template.to_dict(),
            'message': "模板创建成功"
        }), 201
    except Exception as e:
        system_logger.error(f"创建模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"创建模板失败: {str(e)}"
        }), 500

@template_bp.route('/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """更新脚本模板"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 检查模板是否存在
        template = template_service.get_template_by_id(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': f"模板不存在: ID={template_id}"
            }), 404
        
        # 更新模板
        success = template_service.update_template(
            template_id=template_id,
            name=data.get('name'),
            content=data.get('content')
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': "模板更新失败，可能是名称已被使用"
            }), 400
        
        # 获取更新后的模板
        updated_template = template_service.get_template_by_id(template_id)
        
        return jsonify({
            'success': True,
            'data': updated_template.to_dict(),
            'message': "模板更新成功"
        }), 200
    except Exception as e:
        system_logger.error(f"更新模板失败: ID={template_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"更新模板失败: {str(e)}"
        }), 500

@template_bp.route('/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """删除脚本模板"""
    try:
        # 检查模板是否存在
        template = template_service.get_template_by_id(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': f"模板不存在: ID={template_id}"
            }), 404
        
        # 删除模板
        success = template_service.delete_template(template_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': "模板删除失败"
            }), 500
        
        return jsonify({
            'success': True,
            'message': "模板删除成功"
        }), 200
    except Exception as e:
        system_logger.error(f"删除模板失败: ID={template_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"删除模板失败: {str(e)}"
        }), 500
