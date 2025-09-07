"""
股票分析系统主程序
重构后使用模块化设计，主要功能已拆分到各个专门的模块中
"""

import os
from stock_processor import StockDataProcessor
from config import DEFAULT_EXCEL_FILE


def main():
    """主函数：执行股票数据处理流程"""
    # 设置Excel文件路径
    excel_file_name = DEFAULT_EXCEL_FILE
    file_path = os.path.join(os.getcwd(), excel_file_name)
    
    # 创建股票数据处理器
    processor = StockDataProcessor(file_path)
    
    print("开始处理股票数据...")
    
    # 执行主要处理流程
    processor.process_stock_data(current_sheet_name="test", target_sheet_name="watch")
    
    print("开始格式化工作表...")
    
    # 格式化工作表
    processor.format_worksheet(sheet_name="watch")
    
    print("股票数据处理完成！")
    
    # 可选：执行测试功能
    # processor.test_filter_data()


if __name__ == "__main__":
    main()