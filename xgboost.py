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
            analysis_df = analysis_df.sort_values('得分', ascending=False)
            self.excel_handler.save_data_to_sheet(analysis_df, target_sheet_name, mode='a')

            print(f"技术分析完成，共分析 {len(analysis_df)} 只股票")
        
        return analysis_df
    
    def analyze_stock_status(self, df, symbol_name="未知股票"):
        """
        优化后股票状态得分评价体系（不含量能维度）
        总分范围：0-100 分（分值越高，多头趋势越强）
        评分逻辑：基础分 + 加分项分层评分，避免离散化非黑即白
        维度权重：阶段新高(25%) + 均线结构(45%) + 底部形态(30%)
        
        Args:
            df: 包含 'date', 'close' 的 DataFrame，建议至少包含 180 天以上数据
            symbol_name: 股票名称
            
        Returns:
            dict: 包含分析结果的字典
        """
        # 检查数据是否足够（至少需要60个交易日数据）
        if len(df) < 60:
            return {
                "股票名": symbol_name,
                "得分": 0,
                "状态": "【数据不足】",
                "核心逻辑": "数据不足60天，无法进行完整分析",
                "操作建议": "请获取更多历史数据"
            }
        
        # 计算所需的均线
        df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['MA10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()
        
        # 获取最新数据
        latest = df.iloc[-1]
        close = latest['close']
        ma5 = latest['MA5']
        ma10 = latest['MA10']
        ma20 = latest['MA20']
        
        total_score = 0
        reasons = []
        
        # --- 1. 阶段新高评分（25分） ---
        stage_high_score = 0
        # 获取过去180个交易日的最高价（如果数据不足180天则使用所有数据）
        lookback_period = min(180, len(df))
        high_180 = df['close'].tail(lookback_period).max()
        
        if abs(close - high_180) / high_180 <= 0.005:  # 完美新高（允许0.5%误差）
            stage_high_score = 25
            reasons.append("阶段新高：完美新高（180日）")
        elif close >= high_180 * 0.95:  # 接近新高（≥95%）
            stage_high_score = 12
            reasons.append("阶段新高：接近新高（180日）")
        else:  # 普通状态
            stage_high_score = 0
            reasons.append("阶段新高：普通状态")
        
        total_score += stage_high_score
        
        # --- 2. 均线结构评分（45分 = 基础分25分 + 加分项20分） ---
        ma_structure_score = 0
        ma_basic_score = 0
        ma_bonus_score = 0
        is_strong_bull = False
        
        # 基础分（25分）
        if ma5 > ma10 > ma20 and close > ma5 and close > ma10 and close > ma20:
            ma_basic_score = 25
            is_strong_bull = True
            reasons.append("均线结构：强势多头排列")
        elif abs(ma5 - ma10) / ma10 < 0.01 and abs(ma10 - ma20) / ma20 < 0.01 and abs(ma5 - ma20) / ma20 < 0.01:
            ma_basic_score = 10
            reasons.append("均线结构：中性缠绕")
        elif ma20 > ma10 > ma5:
            ma_basic_score = 0
            reasons.append("均线结构：弱势空头排列")
        else:
            ma_basic_score = 5
            reasons.append("均线结构：非标准排列")
        
        # 加分项（20分，仅强势多头状态可参与加分）
        if is_strong_bull:
            # 多头发散度（0-12分）
            divergence_score = 0
            if len(df) >= 30:  # 需要至少30天数据计算10天前的均线
                # 计算10天前的均线值
                ma5_10d_ago = df.iloc[-11]['MA5']
                ma10_10d_ago = df.iloc[-11]['MA10']
                ma20_10d_ago = df.iloc[-11]['MA20']
                
                # 计算斜率
                slope_ma5 = (ma5 - ma5_10d_ago) / ma5_10d_ago if ma5_10d_ago != 0 else 0
                slope_ma10 = (ma10 - ma10_10d_ago) / ma10_10d_ago if ma10_10d_ago != 0 else 0
                slope_ma20 = (ma20 - ma20_10d_ago) / ma20_10d_ago if ma20_10d_ago != 0 else 0
                
                if slope_ma5 > slope_ma10 > slope_ma20 > 0:
                    slope_diff = slope_ma5 - slope_ma20
                    if slope_diff >= 0.01:
                        divergence_score = 12
                        reasons.append("均线强度：多头发散度强")
                    elif slope_diff >= 0.005:
                        divergence_score = 6
                        reasons.append("均线强度：多头发散度中等")
                    else:
                        divergence_score = 0
                        reasons.append("均线强度：多头发散度弱")
            
            # 收盘价站均线强度（0-8分）
            close_strength_score = 0
            if close > ma5 * 1.03:
                close_strength_score += 3
            if close > ma10 * 1.03:
                close_strength_score += 3
            if close > ma20 * 1.03:
                close_strength_score += 2
            
            if close_strength_score > 0:
                reasons.append(f"均线强度：收盘价站均线强度得{close_strength_score}分")
            else:
                reasons.append("均线强度：收盘价站均线强度不足")
            
            ma_bonus_score = divergence_score + close_strength_score
        
        ma_structure_score = ma_basic_score + ma_bonus_score
        total_score += ma_structure_score
        
        # --- 3. 底部形态评分（30分，可叠加） ---
        bottom_pattern_score = 0
        
        # 获取最近60个交易日的数据
        recent_df = df.tail(60).copy()
        recent_df.reset_index(drop=True, inplace=True)
        
        # V型底（10分）：存在1个明显低点，低点后收盘价反弹幅度≥5%，且反弹时间≤10个交易日
        v_bottom_score = 0
        if len(recent_df) >= 20:  # 需要足够数据判断V型底
            # 找出最近60天的最低价
            min_idx = recent_df['close'].idxmin()
            min_price = recent_df['close'].min()
            
            # 检查低点后10个交易日内是否有≥5%的反弹
            if min_idx < len(recent_df) - 1:  # 确保低点不是最后一天
                days_after_low = len(recent_df) - 1 - min_idx
                if days_after_low <= 10:  # 反弹时间≤10个交易日
                    max_after_low = recent_df.iloc[min_idx:]['close'].max()
                    rebound_pct = (max_after_low - min_price) / min_price
                    if rebound_pct >= 0.05:  # 反弹幅度≥5%
                        v_bottom_score = 10
                        reasons.append("底部形态：V型底")
        
        # W底（10分）：存在2个明显低点，两点收盘价差值＜2%；第二个低点＞第一个低点；第二个低点后收盘价突破两低点之间的高点
        w_bottom_score = 0
        if len(recent_df) >= 30:  # 需要足够数据判断W型底
            # 找出前半段和后半段的低点
            mid_idx = len(recent_df) // 2
            first_half = recent_df.iloc[:mid_idx]['close']
            second_half = recent_df.iloc[mid_idx:]['close']
            
            if not first_half.empty and not second_half.empty:
                # 直接使用位置索引
                first_half_min_pos = first_half.argmin()
                second_half_min_pos = second_half.argmin()
                
                # 转换为在recent_df中的绝对位置
                first_low_pos = first_half_min_pos
                second_low_pos = mid_idx + second_half_min_pos
                
                first_low = recent_df.iloc[first_low_pos]['close']
                second_low = recent_df.iloc[second_low_pos]['close']
                
                # 检查两个低点的条件
                if abs(first_low - second_low) / first_low < 0.02 and second_low > first_low:
                    # 找出两低点之间的高点
                    between_high = recent_df.iloc[first_low_pos:second_low_pos]['close'].max()
                    # 检查第二个低点后是否突破两低点之间的高点
                    after_second_low_max = recent_df.iloc[second_low_pos:]['close'].max()
                    if after_second_low_max > between_high:
                        w_bottom_score = 10
                        reasons.append("底部形态：W型底")
        
        # 圆弧底（10分）：存在至少3个逐步抬升的低点，相邻低点收盘价差值＜3%；整体形态无明显尖峰，低点出现时间跨度≥20个交易日
        arc_bottom_score = 0
        if len(recent_df) >= 40:  # 需要足够数据判断圆弧底
            # 使用滑动窗口找低点
            window = 5
            lows = []
            
            for i in range(window, len(recent_df) - window):
                if recent_df.iloc[i]['close'] == recent_df.iloc[i-window:i+window]['close'].min():
                    lows.append((i, recent_df.iloc[i]['close']))
            
            # 检查是否有至少3个逐步抬升的低点
            if len(lows) >= 3:
                # 检查低点是否逐步抬升且相邻差值＜3%
                ascending = True
                valid_lows = True
                for j in range(1, len(lows)):
                    if lows[j][1] <= lows[j-1][1] or abs(lows[j][1] - lows[j-1][1]) / lows[j-1][1] >= 0.03:
                        ascending = False
                        valid_lows = False
                        break
                
                # 检查低点出现时间跨度是否≥20个交易日
                if valid_lows and (lows[-1][0] - lows[0][0]) >= 20:
                    arc_bottom_score = 10
                    reasons.append("底部形态：圆弧底")
        
        bottom_pattern_score = v_bottom_score + w_bottom_score + arc_bottom_score
        total_score += bottom_pattern_score
        
        # --- 评分结果解读 ---
        if total_score >= 80:
            status = "【极强多头】"
            advice = "符合核心选股标准，可重点跟踪布局"
        elif total_score >= 60:
            status = "【中度多头】"
            advice = "趋势明确但强度一般，需等待回调确认支撑"
        elif total_score >= 40:
            status = "【震荡整理】"
            advice = "多空力量均衡，无明确趋势，建议观望"
        elif total_score >= 20:
            status = "【中度空头】"
            advice = "空头占优，避免主动买入"
        else:
            status = "【极强空头】"
            advice = "趋势走弱，需规避风险"
        
        return {
            "股票名": symbol_name,
            "得分": total_score,
            "状态": status,
            "核心逻辑": " | ".join(reasons) if reasons else "暂无明确信号",
            "操作建议": advice,
            "阶段新高得分": stage_high_score,
            "均线结构得分": ma_structure_score,
            "底部形态得分": bottom_pattern_score
        }

def test_stock_analysis():
    """测试股票状态分析功能"""
    import pandas as pd
    import numpy as np
    
    # 创建模拟股票数据
    dates = pd.date_range(start='2023-01-01', periods=200, freq='B')
    
    # 创建一个强势上涨的股票
    close_prices = np.zeros(200)
    close_prices[0] = 10
    for i in range(1, 200):
        # 模拟上涨趋势，带有随机波动
        close_prices[i] = close_prices[i-1] * (1 + 0.003 + np.random.normal(0, 0.02))
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices
    })
    
    # 创建 StockDataManager 实例
    manager = StockDataManager(file_path="DayDayHappy.xlsx")
    
    # 测试分析功能
    result = manager.analyze_stock_status(df, symbol_name="测试股票")
    
    print("股票状态分析测试结果：")
    print(f"股票名：{result['股票名']}")
    print(f"得分：{result['得分']}")
    print(f"状态：{result['状态']}")
    print(f"核心逻辑：{result['核心逻辑']}")
    print(f"操作建议：{result['操作建议']}")
    print(f"阶段新高得分：{result['阶段新高得分']}")
    print(f"均线结构得分：{result['均线结构得分']}")
    print(f"底部形态得分：{result['底部形态得分']}")

if __name__ == "__main__":
    # 创建 StockDataManager 实例
    manager = StockDataManager(file_path="DayDayHappy.xlsx")

    # 根据命令行参数决定执行流程
    if len(sys.argv) > 1:
        param = sys.argv[1]
        if param == "process":
            manager.process_stock_data_to_json(sheet_name="pool")
        elif param == "test":
            test_stock_analysis()
        else:
            print("参数错误，支持：process（处理数据）或 test（测试分析功能）")
    else:
        # 默认仅执行特征提取
        manager.extract_features()  







