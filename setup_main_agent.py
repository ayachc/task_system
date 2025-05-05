#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主Agent创建脚本

用于在命令行启动主Agent
"""

import os
import sys
import argparse
import logging

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加项目根目录到sys.path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入配置和Agent模块
from config import Config
from agent.main_agent import setup_main_agent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(ROOT_DIR, 'data', 'logs', 'system', 'master_agent_setup.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("setup_master_agent")

def main():
    """主函数，解析参数并启动主Agent"""
    parser = argparse.ArgumentParser(description="创建并启动主Agent")
    
    parser.add_argument("--name", help="Agent名称，默认使用主机名")
    parser.add_argument("--server", help=f"服务器URL，默认: {Config.SERVER_URL}")
    
    args = parser.parse_args()
    
    logger.info("开始创建主Agent...")
    
    success = setup_main_agent(
        name=args.name,
        server_url=args.server
    )
    
    if success:
        logger.info("主Agent运行成功")
        return 0
    else:
        logger.error("主Agent运行失败")
        return 1

if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs(os.path.join(ROOT_DIR, 'data', 'logs', 'system'), exist_ok=True)
    
    # 运行主函数
    sys.exit(main())
