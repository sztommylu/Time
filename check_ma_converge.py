import pandas as pd

def check_ma_converge(df, threshold=0.01):
    """
    判断最近一天的5日、10日、20日均线是否粘合
    :param df: 包含收盘价的DataFrame, 列名为 'close'
    :param threshold: 粘合阈值，默认为1%（0.01）
    :return: True or False
    """
    # 计算均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()

    # 取最近一天的三条均线
    last_ma5 = df['ma5'].iloc[-1]
    last_ma10 = df['ma10'].iloc[-1]
    last_ma20 = df['ma20'].iloc[-1]
    
    ma_list = [last_ma5, last_ma10, last_ma20]
    max_ma = max(ma_list)
    min_ma = min(ma_list)
    
    # 粘合判断：最大最小均线的差距/均线平均值 <= 阈值
    avg_ma = sum(ma_list) / 3
    if (max_ma - min_ma) / avg_ma <= threshold:
        return True
    else:
        return False

# 假设你已经有df（DataFrame），里面有 'close' 列
# 例如: df = pd.read_csv('your_kline.csv')
# result = check_ma_converge(df, threshold=0.01)  # 1%以内算粘合
# print("粘合" if result else "不粘合")
