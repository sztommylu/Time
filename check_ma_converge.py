import pandas as pd

def check_ma_converge(df, threshold=0.01):
    """
    判断最近一天的5日、10日、20日均线是否粘合，并分析多头排列质量
    :param df: 包含收盘价的DataFrame, 列名为 'close'
    :param threshold: 粘合阈值，默认为1%（0.01）
    :return: 字典，包含粘合状态和多头排列状态
    """
    # 计算均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()

    # 取最近一天的三条均线
    last_ma5 = df['ma5'].iloc[-1]
    last_ma10 = df['ma10'].iloc[-1]
    last_ma20 = df['ma20'].iloc[-1]
    current_price = df['close'].iloc[-1]
    
    ma_list = [last_ma5, last_ma10, last_ma20]
    max_ma = max(ma_list)
    min_ma = min(ma_list)
    
    # 粘合判断：最大最小均线的差距/均线平均值 <= 阈值
    avg_ma = sum(ma_list) / 3
    is_converge = (max_ma - min_ma) / avg_ma <= threshold
    
    # 1. 基本多头排列判断：五日线 > 十日线 > 二十日线
    is_bullish_arrangement = (last_ma5 > last_ma10) and (last_ma10 > last_ma20)
    
    # 初始化状态变量
    status = ""
    
    # 判断均线状态
    if is_converge:
        status = "粘合"
    elif is_bullish_arrangement:
        # 2. 均线斜率判断（趋势强度）- 增加分层评级
        window = 3
        ma5_slope = (df['ma5'].iloc[-1] - df['ma5'].iloc[-window]) / window
        ma10_slope = (df['ma10'].iloc[-1] - df['ma10'].iloc[-window]) / window
        ma20_slope = (df['ma20'].iloc[-1] - df['ma20'].iloc[-window]) / window
        
        # 计算平均斜率
        avg_slope = (ma5_slope + ma10_slope + ma20_slope) / 3
        
        # 多头趋势斜率分层评级
        if avg_slope > 0.03:  # 斜率大于3%
            slope_level = "强势上升"
        elif avg_slope > 0.01:  # 斜率1%-3%
            slope_level = "温和上升"
            slope_score = 2
        else: # 斜率0%-1%
            slope_level = "微弱上升"
            slope_score = 1

        status = f"多头{slope_level}"
    
    return status