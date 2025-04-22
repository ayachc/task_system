#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM模型训练和脚本执行管理系统主入口
"""

import os
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import logging
from config import Config

# 导入API模块
from backend.api.task_api import task_bp
from backend.api.agent_api import agent_bp
from backend.api.template_api import template_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'system', 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """创建并配置Flask应用"""
    app = Flask(__name__, 
                static_folder='frontend/dist', 
                template_folder='frontend/dist')
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 允许CORS
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(task_bp, url_prefix='/api/tasks')
    app.register_blueprint(agent_bp, url_prefix='/api/agents')
    app.register_blueprint(template_bp, url_prefix='/api/templates')
    
    # 确保目录存在
    os.makedirs(os.path.join('data', 'logs', 'system'), exist_ok=True)
    os.makedirs(os.path.join('data', 'logs', 'tasks'), exist_ok=True)
    os.makedirs(os.path.join('data', 'database'), exist_ok=True)
    
    # 初始化数据库
    from backend.utils.database import db
    db.connect()
    db.init_tables()
    
    # 静态资源
    @app.route('/js/<path:path>')
    def send_js(path):
        return send_from_directory(os.path.join(app.static_folder, 'js'), path)
        
    @app.route('/css/<path:path>')
    def send_css(path):
        return send_from_directory(os.path.join(app.static_folder, 'css'), path)
    
    @app.route('/img/<path:path>')
    def send_img(path):
        return send_from_directory(os.path.join(app.static_folder, 'img'), path)
    
    # 前端路由 - 所有非api的GET请求都返回index.html
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        """处理前端路由"""
        if not path.startswith('api/'):
            return render_template('index.html')
        return 'Not Found', 404
    
    @app.route('/favicon.ico')
    def favicon():
        """提供网站图标"""
        return send_from_directory(app.static_folder, 'favicon.ico')
    
    logger.info("应用已启动")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
