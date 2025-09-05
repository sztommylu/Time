"""
主处理器模块
整合所有功能模块，提供完整的股票数据处理流程
"""

import time
import numpy as np
import traceback
from collections import defaultdict

from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from excel_handler import ExcelHandler
from config import API_LIMIT_COUNT, API_SLEEP_TIME
import support_buy_scanner


class StockDataProcessor:
    """股票数据处理器 - 整合所有功能的主处理类"""
    
    def __init__(self, file_path):
        """
        初始化股票数据处理器
        
        Args:
            file_path: Excel文件路径
        """
        self.file_path = file_path
        self.data_fetcher = StockDataFetcher()
        self.technical_analyzer = TechnicalAnalyzer()
        self.excel_handler = ExcelHandler(file_path)
    
    def read_data_from_sheet(self, sheet_name):
        """
        从工作表读取数据
        
        Args:
            sheet_name: 工作表名称
            
        Returns:
            DataFrame: 读取的数据
        """
        return self.excel_handler.read_data_from_sheet(sheet_name)
    
    def get_stock_date(self):
        """
        获取股票交易日期范围
        
        Returns:
            tuple: (开始日期, 结束日期)
        """
        return self.data_fetcher.get_stock_date()
    
    def get_stock_history(self, stock_code, start_date, current_date):
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            current_date: 结束日期
            
        Returns:
            DataFrame: 股票历史数据
        """
        return self.data_fetcher.get_stock_history(stock_code, start_date, current_date)
    
    def analyze_trend(self, df, window=20, bandwidth_thresh=0.1):
        """
        分析股票趋势
        
        Args:
            df: 股票历史数据
            window: 分析窗口期
            bandwidth_thresh: 带宽阈值
            
        Returns:
            dict: 趋势分析结果
        """
        return self.technical_analyzer.analyze_trend(df, window, bandwidth_thresh)
    
    def _calculate_trend_signal(self, history_df):
        """
        使用 support_buy_scanner 计算趋势信号
        
        Args:
            history_df: 股票历史数据
            
        Returns:
            str: 趋势信号字符串
        """
        try:
            if history_df is None or history_df.empty:
                return "无数据"
            
            # 添加布林带计算
            df_with_boll = support_buy_scanner.add_boll(history_df.copy())
            
            if df_with_boll.empty:
                return "数据不足"
            
            # 获取最新数据
            latest_row = df_with_boll.iloc[-1]
            
            # 调用趋势信号函数
            trend_signal = support_buy_scanner.boll_touch_signal(
                close=float(latest_row["close"]),
                low=float(latest_row["low"]),
                ma20=float(latest_row["MA20"]),
                lower=float(latest_row["LOWER"]),
                tol=support_buy_scanner.TOL
            )
            
            return trend_signal
            
        except Exception as e:
            print(f"计算趋势信号错误: {e}")
            return "计算错误"
    
    def append_data_to_sheet(self, data, target_sheet_name):
        """
        将数据追加到工作表
        
        Args:
            data: 要写入的数据
            target_sheet_name: 目标工作表名称
        """
        self.excel_handler.append_data_to_sheet(data, target_sheet_name)
    
    def process_stock_data(self, current_sheet_name, target_sheet_name):
        """
        处理股票数据的主要流程
        从源工作表读取股票列表，获取历史数据，计算指标，写入目标工作表
        
        Args:
            current_sheet_name: 源工作表名称
            target_sheet_name: 目标工作表名称
        """
        # 读取源 Sheet 数据
        source_data = self.read_data_from_sheet(current_sheet_name)
        if source_data is None:
            print("无法读取源数据，处理中止")
            return
        
        # 使用 defaultdict 存储合并后的数据
        merged_data = defaultdict(list)
        
        try:
            start_date, current_date = self.get_stock_date()
            print(f"交易日期范围: {start_date} 到 {current_date}")
            
            count = 0
            
            for index, row in source_data.iterrows():
                # API调用频率控制
                if count >= API_LIMIT_COUNT:
                    print(f"已处理 {count} 只股票，等待 {API_SLEEP_TIME} 秒...")
                    time.sleep(API_SLEEP_TIME)
                    count = 0
                
                count += 1
                print(f"============================{count}============================")
                
                # 获取股票基本信息
                stock_code = row["代码"]   
                stock_name = row["名称"]   
                stock_plate = row["板块"]  
                
                print(f"处理股票: {stock_code} - {stock_name} ({stock_plate})")
                
                # 获取股票历史数据
                history_df = self.get_stock_history(stock_code, start_date, current_date)
                
                # 添加股票基本信息（即使没有历史数据也要添加）
                merged_data["代码"].append(stock_code)
                merged_data["名称"].append(stock_name)
                merged_data["板块"].append(stock_plate)
                
                # 初始化默认值
                five_pct_sum = np.nan
                ten_pct_sum = np.nan
                twenty_pct_sum = np.nan
                trend = ""
                
                if history_df is not None:
                    # 计算各项指标
                    five_pct_sum = round(history_df["pct_chg"].head(5).sum(), 2)
                    ten_pct_sum = round(history_df["pct_chg"].head(10).sum(), 2)
                    twenty_pct_sum = round(history_df["pct_chg"].head(20).sum(), 2)
                    
                    # 调用 support_buy_scanner 计算趋势
                    trend = self._calculate_trend_signal(history_df)
                    
                    print(f"计算指标 - 5天: {five_pct_sum}, 10天: {ten_pct_sum}, 20天: {twenty_pct_sum}, 趋势: {trend}")
                
                # 添加指标数据
                merged_data["5天求和"].append(five_pct_sum)
                merged_data["10天求和"].append(ten_pct_sum)
                merged_data["20天求和"].append(twenty_pct_sum)
                merged_data["trend"].append(trend)
                
                # 添加历史数据（确保所有股票都有相同数量的日期列）
                if history_df is not None:
                    for _, record in history_df.head(20).iterrows():
                        date = record["trade_date"]
                        pct_change = round(record["pct_chg"], 2)
                        merged_data[date].append(pct_change)
                else:
                    # 如果没有历史数据，为每个已存在的日期列添加NaN
                    for col_name in merged_data.keys():
                        if col_name not in ["代码", "名称", "板块", "5天求和", "10天求和", "20天求和", "trend"]:
                            merged_data[col_name].append(np.nan)
                
                # 确保所有列长度一致
                max_len = max(len(v) for v in merged_data.values())
                for key in merged_data:
                    if len(merged_data[key]) < max_len:
                        merged_data[key].extend([np.nan] * (max_len - len(merged_data[key])))
            
            # 将处理结果写入目标工作表
            if merged_data:
                import pandas as pd
                result_df = pd.DataFrame(merged_data)
                self.append_data_to_sheet(result_df, target_sheet_name)
                print(f"数据处理完成，共处理 {len(source_data)} 只股票")
            else:
                print("没有数据需要写入")
                
        except Exception as e:
            print(f"处理股票数据错误: {e}")
            traceback.print_exc()
            raise
    
    def apply_color_coding(self, sheet_name):
        """
        为工作表应用颜色编码
        
        Args:
            sheet_name: 工作表名称
        """
        self.excel_handler.apply_color_coding(sheet_name)
    
    def add_hyperlinks(self, sheet_name):
        """
        为工作表添加超链接
        
        Args:
            sheet_name: 工作表名称
        """
        self.excel_handler.add_hyperlinks(sheet_name)
    
    def set_column_widths(self, sheet_name):
        """
        设置工作表列宽
        
        Args:
            sheet_name: 工作表名称
        """
        self.excel_handler.set_column_widths(sheet_name)
    
    def format_worksheet(self, sheet_name):
        """
        对工作表进行完整的格式化处理
        
        Args:
            sheet_name: 工作表名称
        """
        self.excel_handler.format_worksheet(sheet_name)
    
    def test_filter_data(self):
        """
        测试数据过滤功能
        """
        filter_func = lambda df: (df.iloc[:, 3] > 5) | (df.iloc[:, 6] > 6)
        result_list = self.excel_handler.read_filtered_data("watch", filter_func)
        print("过滤结果:", result_list)
        return result_list