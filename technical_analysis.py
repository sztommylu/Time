"""
技术分析模块
包含布林带等技术指标的计算和趋势分析
"""

import pandas as pd
import numpy as np
from config import BOLLINGER_WINDOW, BOLLINGER_STD_DEV, BANDWIDTH_THRESHOLD


class TechnicalAnalyzer:
    """技术分析器"""
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, window: int = BOLLINGER_WINDOW, std_dev: int = BOLLINGER_STD_DEV):
        """
        计算布林带指标
        
        Args:
            df: 包含收盘价的DataFrame
            window: 移动平均线窗口期，默认20
            std_dev: 标准差倍数，默认2
            
        Returns:
            DataFrame: 添加了布林带指标的DataFrame
        """
        df_copy = df.copy()
        df_copy['BBM'] = df_copy['close'].rolling(window=window).mean()  # 中轨
        std = df_copy['close'].rolling(window=window).std()
        df_copy['BBU'] = df_copy['BBM'] + (std * std_dev)  # 上轨
        df_copy['BBL'] = df_copy['BBM'] - (std * std_dev)  # 下轨
        df_copy['BBB'] = (df_copy['BBU'] - df_copy['BBL']) / df_copy['BBM']  # 带宽
        return df_copy
    
    def analyze_trend(self, df, window=BOLLINGER_WINDOW, bandwidth_thresh=BANDWIDTH_THRESHOLD):
        """
        基于布林带分析股票趋势
        
        Args:
            df: 股票历史数据DataFrame
            window: 分析窗口期
            bandwidth_thresh: 带宽阈值，用于判断震荡行情
            
        Returns:
            dict: 包含趋势分析结果的字典
        """
        if df is None or len(df) < window:
            return {
                'trend': None,
                'action': '数据不足无法分析',
                'desc': '数据量不足20天',
                'trend_name': '',
                'touch_lower': False,
                'touch_upper': False,
                'touch_middle': False
            }
        
        # 数据预处理
        new_df = df.copy()
        new_df = new_df.sort_values('trade_date').reset_index(drop=True)
        
        # 计算布林带
        df_with_bb = self.calculate_bollinger_bands(df=new_df, window=window)
        latest = df_with_bb.iloc[-1]
        prev_bbm = df_with_bb['BBM'].iloc[-2]  # 前一日中轨值
        
        # 检测轨道接触（加入1%的容差）
        touch_lower = latest['low'] <= latest['BBL'] * 1.01
        touch_upper = latest['high'] >= latest['BBU'] * 0.99
        touch_middle = (latest['low'] <= latest['BBM'] * 1.01) and (latest['high'] >= latest['BBM'] * 0.99)
        
        # 初始化返回结果
        result = {
            'trend': 10000,
            'action': '',
            'desc': '',
            'trend_name': '',
            'touch_lower': touch_lower,
            'touch_upper': touch_upper,
            'touch_middle': touch_middle
        }
        
        # 获取关键指标
        close = latest['close']
        bbu = latest['BBU'] 
        bbm = latest['BBM']
        bbl = latest['BBL']
        bbb = latest['BBB']
        
        # 趋势判断逻辑
        result = self._determine_trend(result, close, bbu, bbm, bbl, bbb, prev_bbm, bandwidth_thresh)
        
        # 特殊情况处理
        result = self._handle_special_cases(result, touch_lower, touch_middle)
        
        return result
    
    def _determine_trend(self, result, close, bbu, bbm, bbl, bbb, prev_bbm, bandwidth_thresh):
        """
        确定趋势类型
        
        Args:
            result: 结果字典
            close, bbu, bbm, bbl, bbb: 布林带相关指标
            prev_bbm: 前一日中轨值
            bandwidth_thresh: 带宽阈值
            
        Returns:
            dict: 更新后的结果字典
        """
        # 1. 优先判断震荡行情
        if bbb < bandwidth_thresh:
            result.update({
                'trend': 0,
                'action': '观望',
                'desc': '布林带收窄，震荡行情',
                'trend_name': "<->震荡"
            })
        
        # 2. 判断趋势行情
        # 强势上涨
        elif close > bbu and bbm > prev_bbm:
            result.update({
                'trend': 4,
                'action': '强势买入',
                'desc': '价格突破上轨且中轨向上，强势上涨',
                'trend_name': '📈强势上涨'
            })
        # 普通上涨
        elif close > bbm and bbm > prev_bbm:
            result.update({
                'trend': 3,
                'action': '买入',
                'desc': '价格在中轨上方且中轨向上，上涨趋势',
                'trend_name': '↑上涨'
            })
        # 强势下跌
        elif close < bbl and bbm < prev_bbm:
            result.update({
                'trend': 2,
                'action': '立即卖出',
                'desc': '价格跌破下轨且中轨向下，强势下跌',
                'trend_name': '📉强势下跌'
            })
        # 普通下跌
        elif close < bbm and bbm < prev_bbm:
            result.update({
                'trend': 1,
                'action': '卖出',
                'desc': '价格在中轨下方且中轨向下，下跌趋势',
                'trend_name': '↓下跌'
            })
        
        return result
    
    def _handle_special_cases(self, result, touch_lower, touch_middle):
        """
        处理特殊情况（触及轨道）
        
        Args:
            result: 结果字典
            touch_lower: 是否触及下轨
            touch_middle: 是否触及中轨
            
        Returns:
            dict: 更新后的结果字典
        """
        # 处理触及下轨的情况
        if touch_lower:
            if result['trend'] == 0:  # 震荡行情
                result.update({
                    'action': '考虑入场',
                    'desc': result['desc'] + '，震荡股价触及下轨',
                    'trend_name': 'B'
                })
            elif result['trend'] in [1, 2]:  # 下跌趋势
                result.update({
                    'action': '考虑入场',
                    'desc': result['desc'] + '，下行股价触及下轨',
                    'trend_name': 'B'
                })
        
        # 处理触及中轨的情况
        if touch_middle:
            if result['trend'] in [3, 4]:
                result.update({
                    'action': '考虑入场',
                    'desc': result['desc'] + '，上行股价触及中轨',
                    'trend_name': 'B'
                })
        
        # 调整强势下跌时触及下轨的动作
        if touch_lower and result['trend'] == 2:
            result['action'] = '反弹减仓'
        elif touch_lower and result['trend'] == 1:
            result['action'] = '谨慎持有'
        
        return result
    
    def calculate_ma_indicators(self, df, periods=[5, 10, 20]):
        """
        计算移动平均线指标
        
        Args:
            df: 股票数据DataFrame
            periods: 移动平均线周期列表
            
        Returns:
            DataFrame: 添加了移动平均线的DataFrame
        """
        df_copy = df.copy()
        for period in periods:
            df_copy[f'MA{period}'] = df_copy['close'].rolling(window=period).mean()
        return df_copy