"""
股票分析系统主程序
重构后使用模块化设计，主要功能已拆分到各个专门的模块中
"""

import os
from stock_processor import StockDataProcessor
from stock_notification import StockNotification
from config import DEFAULT_EXCEL_FILE
from email_sender import EmailSender

def main():
    """主函数：执行股票数据处理流程"""
    # 设置Excel文件路径
    excel_file_name = DEFAULT_EXCEL_FILE
    file_path = os.path.join(os.getcwd(), excel_file_name)
    
    # 创建股票数据处理器
    processor = StockDataProcessor(file_path)
    
    # print("开始处理股票数据...")
    
    # # 执行主要处理流程
    # processor.process_stock_data(current_sheet_name="pool", target_sheet_name="watch")
    
    # print("开始格式化工作表...")
    
    # # 格式化工作表
    # processor.format_worksheet(sheet_name="watch")
    
    # print("股票数据处理完成！")
    
    # 可选：执行测试功能
    # processor.test_filter_data()

    notifier = StockNotification(processor.excel_handler)
    stock_notices, focus_names = notifier.get_data()

    email_sender = EmailSender()
    email_sender.send_email(
        to_email="llongroad@hotmail.com",
        subject="股票支撑位百分比",
        content=email_sender.generate_stock_html(stock_notices, focus_names),
        is_html=True
    )

if __name__ == "__main__":
    main()