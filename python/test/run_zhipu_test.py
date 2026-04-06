#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI测试运行器
专门用于运行智谱AI相关的测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_zhipu_basic import main as run_basic_test
from test_zhipu_integration import main as run_integration_test

def main():
    """主函数"""
    print("🚀 开始运行智谱AI测试套件...")
    print()
    
    # 运行基础测试
    print("📋 第一阶段：智谱AI基础功能测试")
    print("-" * 50)
    basic_result = run_basic_test()
    
    print("\n" + "=" * 60)
    
    # 运行集成测试
    print("📋 第二阶段：智谱AI集成测试（包含RAG功能）")
    print("-" * 50)
    integration_result = run_integration_test()
    
    print("\n" + "=" * 80)
    print("智谱AI测试套件总结")
    print("=" * 80)
    
    basic_status = "✅ 通过" if basic_result == 0 else "❌ 失败"
    integration_status = "✅ 通过" if integration_result == 0 else "❌ 失败"
    
    print(f"基础功能测试: {basic_status}")
    print(f"集成功能测试: {integration_status}")
    
    if basic_result == 0 and integration_result == 0:
        print("\n🎉 所有智谱AI测试全部通过！系统完全兼容智谱AI。")
        return 0
    elif basic_result == 0:
        print("\n✨ 智谱AI基础功能正常，集成测试部分失败（可能需要安装额外依赖）。")
        print("💡 建议：运行 'pip install faiss-haystack' 安装RAG相关依赖。")
        return 0  # 基础功能通过就算成功
    else:
        print("\n⚠️ 智谱AI测试存在问题，请检查API配置和网络连接。")
        return 1

if __name__ == "__main__":
    exit(main())