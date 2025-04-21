#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务管理API接口
"""

from flask import Blueprint, request, jsonify, current_app
import json
from datetime import datetime
from backend.services.task_service import TaskService
from backend.utils.logger import system_logger

# 创建蓝图
task_bp = Blueprint('task', __name__)

# 实例化任务服务
task_service = TaskService()

# 日期时间转换函数
def json_serial(obj):
    """序列化日期/时间为JSON"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")

@task_bp.route('/', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        # 解析分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 解析过滤参数
        filters = {}
        if 'status' in request.args:
            status_str = request.args.get('status')
            filters['status'] = status_str.split(',') if status_str else []
        
        if 'name' in request.args:
            filters['name'] = request.args.get('name')
        
        if 'template_type' in request.args:
            filters['template_type'] = request.args.get('template_type')
        
        if 'script_content' in request.args:
            filters['script_content'] = request.args.get('script_content')
        
        # 获取任务分页数据
        result = task_service.get_task_in_page(page, per_page, filters)
        
        # 转换任务实例为字典
        tasks_dict = [task.to_dict() for task in result['tasks']]
        
        # 返回响应
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks_dict,
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages']
            }
        }), 200
    except Exception as e:
        system_logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取任务列表失败: {str(e)}"
        }), 500

@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取单个任务详情"""
    try:
        task = task_service.get_task_by_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': f"任务不存在: ID={task_id}"
            }), 404
        
        return jsonify({
            'success': True,
            'data': task.to_dict()
        }), 200
    except Exception as e:
        system_logger.error(f"获取任务详情失败: ID={task_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取任务详情失败: {str(e)}"
        }), 500

@task_bp.route('/', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 检查必要字段
        required_fields = ['name', 'template_type', 'script_content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f"缺少必要字段: {field}"
                }), 400
        
        # 创建任务
        task = task_service.create_task(
            name=data['name'],
            template_type=data['template_type'],
            script_content=data['script_content'],
            priority=data.get('priority', 3),
            cpu_cores=data.get('cpu_cores'),
            gpu_count=data.get('gpu_count'),
            gpu_memory=data.get('gpu_memory'),
            depends_on=data.get('depends_on', [])
        )
        
        if not task:
            return jsonify({
                'success': False,
                'message': "任务创建失败"
            }), 500
        
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': "任务创建成功"
        }), 201
    except Exception as e:
        system_logger.error(f"创建任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"创建任务失败: {str(e)}"
        }), 500

@task_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 获取现有任务
        task = task_service.get_task_by_id(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': f"任务不存在: ID={task_id}"
            }), 404
        
        # 更新任务字段
        update_fields = {}
        for key, value in data.items():
            if hasattr(task, key) and key != 'id':
                update_fields[key] = value
        
        if not update_fields:
            return jsonify({
                'success': False,
                'message': "没有提供有效的更新字段"
            }), 400
        
        # 执行更新
        success = task_service.update_task_by_key(task_id, **update_fields)
        if not success:
            return jsonify({
                'success': False,
                'message': "任务更新失败"
            }), 500
        
        # 获取更新后的任务
        updated_task = task_service.get_task_by_id(task_id)
        
        return jsonify({
            'success': True,
            'data': updated_task.to_dict(),
            'message': "任务更新成功"
        }), 200
    except Exception as e:
        system_logger.error(f"更新任务失败: ID={task_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"更新任务失败: {str(e)}"
        }), 500

@task_bp.route('/<int:task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    try:
        success = task_service.cancel_task(task_id)
        if not success:
            return jsonify({
                'success': False,
                'message': "任务取消失败"
            }), 500
        
        return jsonify({
            'success': True,
            'message': "任务已取消"
        }), 200
    except Exception as e:
        system_logger.error(f"取消任务失败: ID={task_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"取消任务失败: {str(e)}"
        }), 500

@task_bp.route('/<int:task_id>/log', methods=['GET'])
def get_task_log(task_id):
    """获取任务日志"""
    try:
        # 解析参数
        start_line = request.args.get('start_line', 0, type=int)
        max_lines = request.args.get('max_lines', type=int)
        
        # 获取日志
        log_data = task_service.get_task_log(task_id, start_line, max_lines)
        
        return jsonify({
            'success': True,
            'data': log_data
        }), 200
    except Exception as e:
        system_logger.error(f"获取任务日志失败: ID={task_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取任务日志失败: {str(e)}"
        }), 500

@task_bp.route('/<int:task_id>/log', methods=['POST'])
def append_task_log(task_id):
    """添加任务日志"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式且包含content字段"
            }), 400
        
        # 添加日志
        success = task_service.append_task_log(task_id, data['content'])
        if not success:
            return jsonify({
                'success': False,
                'message': "添加任务日志失败"
            }), 500
        
        return jsonify({
            'success': True,
            'message': "日志添加成功"
        }), 200
    except Exception as e:
        system_logger.error(f"添加任务日志失败: ID={task_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"添加任务日志失败: {str(e)}"
        }), 500
