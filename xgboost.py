import pandas as pd
from datetime import datetime, timedelta
from stock_data import StockDataFetcher
from excel_handler import ExcelHandler
from config import API_LIMIT_COUNT, API_SLEEP_TIME
import json
import sys
import time

class StockDataManager:
    """股票数据管理器"""
    
    def __init__(self, file_path):
        """初始化数据管理器"""
        self.data_fetcher = StockDataFetcher()
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
        return self.data_fetcher.get_stock_date(start=0, end=179)

    def process_stock_data_to_json(self, sheet_name="pool"):
        """
        处理股票数据并保存为JSON格式
        
        Args:
            current_sheet_name: 当前工作表名称
        """
        source_data = self.read_data_from_sheet(sheet_name)
        if source_data is None:
            print("无法读取源数据，处理中止")
            return
        
        start_date, current_date = self.get_stock_date()
        print(f"交易日期范围: {start_date} 到 {current_date}")
        
        count = 0
        
        all_data = {}
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
            try:
                history_df = self.data_fetcher.get_stock_history2(stock_code, start_date, current_date)
                records = {
                    stock_name: {
                        "plate": stock_plate,
                        "history": history_df.to_dict(orient='records')
                    }
                }
                all_data.update(records)
            except Exception as e:
                print(f"获取股票 {stock_code} 历史数据失败: {e}")
                continue
        
        with open('stocks_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)

    def extract_features(self, target_sheet_name="trend"):
        """
        从JSON数据中提取特征并进行股票技术分析
        
        Returns:
            DataFrame: 包含技术分析结果的数据
        """
        # 读取 Excel 中的目标工作表数据
        with open('stocks_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis_results = []
        for stock_name, stock_data in data.items():
            if len(stock_data) < 60:  # 需要至少60天数据进行分析
                print(f"股票 {stock_name} 数据不足，跳过分析")
                continue

            # 转换为DataFrame
            df = pd.DataFrame(stock_data)

            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date', ascending=True)

            # 进行技术分析
            result = self.analyze_stock_status(df, stock_name)
            analysis_results.append(result)

        analysis_df = pd.DataFrame(analysis_results)

        if not analysis_df.empty:
            #analysis_df = analysis_df.sort_values('得分', ascending=False)

            self.excel_handler.save_data_to_sheet(analysis_df, target_sheet_name, mode='a')

            print(f"技术分析完成，共分析 {len(analysis_df)} 只股票")
        
        return analysis_df
    
    def analyze_stock_status(self, df, symbol_name="未知股票"):
        """
        基于 5/10/20 日均线的量化评分系统
        
        Args:
            df: 包含 'date', 'close' 的 DataFrame，建议至少包含 60 天以上数据
            symbol_name: 股票名称
            
        Returns:
            dict: 包含分析结果的字典
        """
        # 1. 计算均线指标
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        # 获取最新数据和前一日数据
        now = df.iloc[-1]
        prev = df.iloc[-2]
        close = now['close']
        
        print("----------------------------")
        print(f"{now}")
        print("**************")
        print(f"{prev}")
        print("**************")
        print(f"{close}")
        print("----------------------------")

        score = 0
        reasons = []

        # --- 维度一：价格位置 (满分 30) ---
        p_score = 0
        if close > now['MA5']: p_score += 10
        if close > now['MA10']: p_score += 10
        if close > now['MA20']: p_score += 10
        score += p_score
        if p_score == 30: reasons.append("价格站稳所有短期均线")

        # --- 维度二：均线形态 (满分 40) ---
        # 多头排列 (5 > 10 > 20)
        if now['MA5'] > now['MA10'] > now['MA20']:
            score += 40
            reasons.append("均线多头排列（趋势极强）")
        # 5日线拐头向上
        elif now['MA5'] > prev['MA5']:
            score += 15
            reasons.append("MA5 拐头向上（短线转强）")

        # --- 维度三：动能与金叉 (满分 30) ---
        # 5日线上穿10日线（金叉）
        if prev['MA5'] <= prev['MA10'] and now['MA5'] > now['MA10']:
            score += 30
            reasons.append("捕捉到 5/10 日线金叉（起涨信号）")
        # 5日线运行在10日线上方（持续动能）
        elif now['MA5'] > now['MA10']:
            score += 15
            reasons.append("短线动能保持活跃")

        # --- 维度四：风险预警 (扣分项) ---
        # 计算 5 日偏离度 (Bias)
        bias_5 = (close - now['MA5']) / now['MA5']
        if bias_5 > 0.05:
            reasons.append("警告：乖离率过大（短线追高风险）")
            
        if close < now['MA20']:
            score -= 10
            reasons.append("警告：已跌破 20 日生命线")

        # --- 最终状态判断 ---
        if score >= 80:
            status = "【强势持股】"
            advice = "趋势非常完美，建议继续持有，让利润奔跑。"
        elif score >= 60:
            status = "【稳健持有】"
            advice = "趋势尚可，但爆发力不足，可继续观察支撑位。"
        elif score >= 40:
            status = "【震荡观望】"
            advice = "多空胶着，不建议重仓，等待方向明确。"
        else:
            status = "【弱势清仓】"
            advice = "技术指标走坏，建议逢高减仓，规避风险。"

        return {
            "股票名": symbol_name,
            "得分": score,
            "状态": status,
            "核心逻辑": " | ".join(reasons),
            "操作建议": advice
        }

if __name__ == "__main__":
    # 创建 StockDataManager 实例
    manager = StockDataManager(file_path="DayDayHappy.xlsx")

    # 根据命令行参数决定执行流程
    if len(sys.argv) > 1:
        param = sys.argv[1]
        if param == "process":
            manager.process_stock_data_to_json(sheet_name="pool")
        else:
            print("参数错误，支持：all（处理并分析）或 json（仅处理）")
    else:
        # 默认仅执行特征提取
        manager.extract_features()  
