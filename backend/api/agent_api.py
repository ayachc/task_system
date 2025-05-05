#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent管理API接口
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from backend.services.agent_service import AgentService
from backend.utils.logger import system_logger

# 创建蓝图
agent_bp = Blueprint('agent', __name__)

# 实例化Agent服务
agent_service = AgentService()

# 日期时间转换函数
def json_serial(obj):
    """序列化日期/时间为JSON"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")

@agent_bp.route('/', methods=['GET'])
def get_agents():
    """获取Agent列表"""
    try:
        # 解析过滤参数
        agent_type = request.args.get('type')
        status = request.args.get('status')
        
        agents = agent_service.get_all_agents(filter_type=agent_type, filter_status=status)
        
        # 转换Agent为字典
        agents_dict = [agent.to_dict() for agent in agents]

        if 2333:
            print(agents_dict)
        
        return jsonify({
            'success': True,
            'data': agents_dict
        }), 200
    except Exception as e:
        system_logger.error(f"获取Agent列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取Agent列表失败: {str(e)}"
        }), 500

@agent_bp.route('/<string:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """获取单个Agent详情"""
    try:
        agent = agent_service.get_agent_by_id(agent_id)
        if not agent:
            return jsonify({
                'success': False,
                'message': f"Agent不存在: ID={agent_id}"
            }), 404
        
        return jsonify({
            'success': True,
            'data': agent.to_dict()
        }), 200
    except Exception as e:
        system_logger.error(f"获取Agent详情失败: ID={agent_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取Agent详情失败: {str(e)}"
        }), 500

@agent_bp.route('/main', methods=['POST'])
def create_main_agent():
    """创建主Agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 检查必要字段
        required_fields = ['name', 'cpu_cores']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f"缺少必要字段: {field}"
                }), 400
        
        # 创建主Agent
        agent = agent_service.create_main_agent(
            name=data['name'],
            cpu_cores=data['cpu_cores'],
            gpu_ids=data.get('gpu_ids', [])
        )
        
        if not agent:
            return jsonify({
                'success': False,
                'message': "主Agent创建失败"
            }), 500
        
        return jsonify({
            'success': True,
            'data': agent.to_dict(),
            'message': "主Agent创建成功"
        }), 201
    except Exception as e:
        system_logger.error(f"创建主Agent失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"创建主Agent失败: {str(e)}"
        }), 500

@agent_bp.route('/sub', methods=['POST'])
def create_sub_agent():
    """创建子Agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 检查必要字段
        required_fields = ['name', 'main_agent_id', 'task_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f"缺少必要字段: {field}"
                }), 400
        
        # 创建子Agent
        agent = agent_service.create_sub_agent(
            name=data['name'],
            main_agent_id=data['main_agent_id'],
            task_id=data['task_id'],
            cpu_cores=data.get('cpu_cores'),
            gpu_ids=data.get('gpu_ids', [])
        )
        
        if not agent:
            return jsonify({
                'success': False,
                'message': "子Agent创建失败"
            }), 500
        
        return jsonify({
            'success': True,
            'data': agent.to_dict(),
            'message': "子Agent创建成功"
        }), 201
    except Exception as e:
        system_logger.error(f"创建子Agent失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"创建子Agent失败: {str(e)}"
        }), 500

@agent_bp.route('/<string:agent_id>/cancel', methods=['POST'])
def cancel_agent(agent_id):
    """取消Agent"""
    try:
        success = agent_service.cancel_agent(agent_id)
        if not success:
            return jsonify({
                'success': False,
                'message': "Agent取消失败"
            }), 500
        
        return jsonify({
            'success': True,
            'message': "Agent已取消"
        }), 200
    except Exception as e:
        system_logger.error(f"取消Agent失败: ID={agent_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"取消Agent失败: {str(e)}"
        }), 500

@agent_bp.route('/<string:agent_id>/heartbeat', methods=['POST'])
def handle_heartbeat(agent_id):
    """处理Agent心跳"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效，需要JSON格式"
            }), 400
        
        # 提取资源信息
        resource_info = data.get('resource_info', {})
        task_info = data.get('task_info')
        
        # 处理心跳
        response = agent_service.handle_heartbeat(agent_id, resource_info, task_info)
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
    except Exception as e:
        system_logger.error(f"处理Agent心跳失败: ID={agent_id}, 错误={str(e)}")
        return jsonify({
            'success': False,
            'message': f"处理Agent心跳失败: {str(e)}"
        }), 500

@agent_bp.route('/check-status', methods=['POST'])
def check_agents_status():
    """检查所有Agent状态"""
    try:
        count = agent_service.check_agents_status()
        
        return jsonify({
            'success': True,
            'data': {
                'offline_count': count
            },
            'message': f"已检查Agent状态，{count}个Agent被标记为离线"
        }), 200
    except Exception as e:
        system_logger.error(f"检查Agent状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"检查Agent状态失败: {str(e)}"
        }), 500
