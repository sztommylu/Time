#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试核心股票高亮功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from excel_handler import ExcelHandler

def test_highlight_core_stocks():
    """测试高亮核心股票功能"""
    # 请替换为你的Excel文件路径
    excel_file = "d:\\up\\DayDayHappy.xlsx"  # 请修改为实际文件路径
    
    if not os.path.exists(excel_file):
        print(f"Excel文件不存在: {excel_file}")
        return
    
    # 创建Excel处理器
    excel_handler = ExcelHandler(excel_file)
    
    # 调用高亮核心股票功能
    # 假设核心列在pool工作表中，需要高亮watch工作表中的对应股票名称
    excel_handler.highlight_core_stocks('test', 'watch')
    
    print("核心股票高亮测试完成")

if __name__ == "__main__":
    test_highlight_core_stocks()