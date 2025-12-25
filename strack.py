"""
股票分析系统主程序
重构后使用模块化设计，主要功能已拆分到各个专门的模块中
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from stock_processor import StockDataProcessor
from stock_notification import StockNotification
from config import DEFAULT_EXCEL_FILE
from email_sender import EmailSender

# 在文件顶部添加logger配置
logger = logging.getLogger('strack')
logger.setLevel(logging.INFO)

# 创建logs目录
if not os.path.exists('logs'):
    os.makedirs('logs')

# 设置文件handler，按天轮转
# 修改文件handler部分，添加encoding参数
file_handler = TimedRotatingFileHandler(
    'logs/strack.log',
    when='midnight',
    backupCount=7,
    encoding='utf-8'  # 添加这行指定编码
)

# 同时修改控制台handler，确保控制台也能正确显示中文
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.encoding = 'utf-8'  # 添加这行
file_handler.setLevel(logging.INFO)

# 设置控制台handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加handler
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 在代码中使用logger
logger.info('初始化strack应用')

def main():
    try:
        logger.info('开始执行主函数')
        excel_file_name = DEFAULT_EXCEL_FILE
        logger.debug(f'使用Excel文件: {excel_file_name}')
        
        # 设置Excel文件路径
        excel_file_name = DEFAULT_EXCEL_FILE
        file_path = os.path.join(os.getcwd(), excel_file_name)
        
        # 创建股票数据处理器
        processor = StockDataProcessor(file_path)
        
        logger.info("开始处理股票数据...")
        
        # # 执行主要处理流程
        processor.process_stock_data(current_sheet_name="pool", target_sheet_name="watch")
        
        logger.info("开始格式化工作表...")
        
        # # 格式化工作表
        processor.format_worksheet(sheet_name="watch")
        
        logger.info("股票数据处理完成！")
        
        # 可选：执行测试功能
        # processor.test_filter_data()

        logger.info("开始获取股票通知数据...")
        notifier = StockNotification(processor.excel_handler)
        stock_notices, focus_names = notifier.get_data()
        
        logger.info("开始发送股票通知邮件...")
        email_sender = EmailSender()
        email_sender.send_email(
            to_email="llongroad@hotmail.com",
            subject="股票支撑位百分比",
            content=email_sender.generate_stock_html(stock_notices, focus_names),
            is_html=True
        )
        logger.info('strack执行完成')
    except Exception as e:
        logger.error(f'执行出错: {e}', exc_info=True)
        raise

if __name__ == "__main__":
    main()