"""
股票数据获取模块
负责获取股票历史数据和交易日期
"""

import pandas as pd
import akshare as ak
import tushare as ts
import traceback
from datetime import datetime
from config import TUSHARE_TOKEN

class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self):
        """初始化股票数据获取器"""
        ts.set_token(TUSHARE_TOKEN)
        self.pro = ts.pro_api()
    
    def get_stock_date(self):
        """
        获取交易日期范围
        返回: (start_date, end_date) 格式为 YYYYMMDD
        """
        print("获取股票交易日期")
        
        try:
            trade_df = ak.tool_trade_date_hist_sina()
            # 确保日期列是字符串格式
            trade_dates = pd.to_datetime(trade_df['trade_date']).dt.strftime('%Y%m%d').tolist()
            current_date = datetime.now().strftime('%Y%m%d')
            
            latest_date = max(d for d in trade_dates if d <= current_date)
            idx = trade_dates.index(latest_date)
            start_date = trade_dates[max(0, idx-99)]
            return start_date, latest_date
            
        except Exception as e:
            print(f"获取交易日错误: {e}")
            # 默认返回最近100天的日期范围
            return "20230101", "20231231"
    
    def get_stock_history(self, stock_code, start_date, end_date):
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码，格式如 'SH.600000'
            start_date: 开始日期，格式 YYYYMMDD
            end_date: 结束日期，格式 YYYYMMDD
            
        Returns:
            DataFrame: 股票历史数据，包含日期、开高低收、成交量等信息
        """
        print(f"获取股票历史数据 {stock_code} {start_date} {end_date}")
        

            # 解析股票代码
        items = str(stock_code).split('.')
        code = items[1]
        
        # 确定交易所
        exchange = ""
        if code.startswith('6'):
            exchange = 'SH'
        elif code.startswith('0') or code.startswith('3'):
            exchange = 'SZ'
        elif code.startswith('88'):
            exchange = 'BJ'
        
        new_stock_code = f"{code}.{exchange}"
        
        # 获取历史数据
        history_df = self.pro.daily(
            ts_code=new_stock_code, 
            start_date=start_date, 
            end_date=end_date
        )
        
        if history_df is None or history_df.empty:
            raise Exception((f"{code} 出现异常: {str(e)}"))

        try:
            history_df = history_df[["trade_date", "open", "high", "low", "close", "pct_chg"]].sort_values("trade_date")
            history_df["date"] = pd.to_datetime(history_df["trade_date"])

            print(f"成功获取 {new_stock_code} 从 {start_date} 到 {end_date} 的历史数据")
            return history_df
            
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"获取股票历史数据错误 {stock_code}: {e}")

    def parse_stock_code(self, stock_code):
        """
        解析股票代码，确定交易所
        
        Args:
            stock_code: 原始股票代码
            
        Returns:
            tuple: (代码, 交易所)
        """
        items = str(stock_code).split('.')
        code = items[1] if len(items) > 1 else items[0]
        
        if code.startswith('6'):
            exchange = 'SH'
        elif code.startswith('0') or code.startswith('3'):
            exchange = 'SZ'
        elif code.startswith('88'):
            exchange = 'BJ'
        else:
            exchange = 'SH'  # 默认
            
        return code, exchange