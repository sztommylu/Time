# -*- coding: utf-8 -*-
"""
BOLL 中轨/下轨 接近识别（Tushare 版）
- 按股票列表或指数成分抓取行情
- 计算 BOLL(20, 2)
- 输出：收盘价/下引线 是否接近 中轨/下轨（带容差）

依赖：
    pip install tushare pandas numpy
用法：
    1) 修改 TUSHARE_TOKEN
    2) 在 SYMBOLS 中填股票列表（如 ["600000.SH","000001.SZ"]）
       或设置 INDEX_CODE = "000300.SH" 使用指数成分
    3) 运行：python boll_touch_report.py
"""

import os
import time
import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta

# ====== 配置 ======
# TUSHARE_TOKEN = ''   # TODO: 改成你的 Tushare Token，或设置环境变量同名
# SYMBOLS = ["002847.SZ"]        # TODO: 手动股票列表；若为空会尝试用 INDEX_CODE
# INDEX_CODE = ""                             # TODO: 如 "000300.SH"（沪深300）自动抓成分
# LOOKBACK_DAYS = 260                         # 拉取日历天数；保证能覆盖20日均线（和更长）计算
BOLL_WIN = 20
BOLL_K = 2.0
TOL = 0.008                                 # 接近容差：0.005=0.5%，可改成 0.01=1%
# SLEEP_SEC = 0.12                            # 请求间隔，避免限流
# ==================

# def get_token():
#     token = os.getenv("TUSHARE_TOKEN", TUSHARE_TOKEN)
#     if not token or token == "YOUR_TUSHARE_TOKEN_HERE":
#         raise RuntimeError("请先配置 TUSHARE_TOKEN（脚本顶部或环境变量）。")
#     ts.set_token(token)
#     return ts.pro_api()

# def fetch_index_members(pro, index_code: str) -> list:
#     """获取指数最近一期成分股 ts_code 列表。"""
#     if not index_code:
#         return []
#     start_date = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d")
#     end_date = datetime.now().strftime("%Y%m%d")
#     df = pro.index_weight(index_code=index_code, start_date=start_date, end_date=end_date)
#     if df is None or df.empty:
#         return []
#     latest = df["trade_date"].max()
#     codes = sorted(df.loc[df["trade_date"] == latest, "con_code"].dropna().unique().tolist())
#     return codes

# def fetch_daily(pro, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
#     """抓取日线，返回按时间升序 DataFrame。"""
#     df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
#     if df is None or df.empty:
#         return pd.DataFrame()
#     df = df[["trade_date", "open", "high", "low", "close"]].sort_values("trade_date")
#     df["date"] = pd.to_datetime(df["trade_date"])
#     return df

def add_boll(g: pd.DataFrame, win=BOLL_WIN, k=BOLL_K) -> pd.DataFrame:
    """计算 BOLL(20, k)，附加 MA20/上轨/下轨/%B。"""
    g = g.copy()
    g["MA20"]  = g["close"].rolling(win).mean()
    g["STD20"] = g["close"].rolling(win).std(ddof=0)
    g["UPPER"] = g["MA20"] + k * g["STD20"]
    g["LOWER"] = g["MA20"] - k * g["STD20"]
    # %B (0=下轨, 1=上轨)；仅供参考，不用于“接近”判断（你之前的买点条件可用它）
    g["percentB"] = (g["close"] - g["LOWER"]) / (g["UPPER"] - g["LOWER"])
    return g

def pct_near(a: float, b: float, tol: float, num: int) -> bool:
    """
    判断 a 是否在 b 的 ±tol 百分比范围内，并打印差距。
    |a-b|/b <= tol
    """
    if np.isnan(a) or np.isnan(b) or b == 0:
        print(f"比较无效: a={a}, b={b}")
        return False
    
    diff_ratio = abs(a - b) / abs(b)

    if num == 1:
        title = "收盘价接近中轨"

    elif num == 2:
        title = "收盘价接近下轨"

    elif num == 3:
        title = "下引线接近中轨"

    elif num == 4:
        title = "下引线接近下轨"

    print(f"{title}: a={a:.2f}, b={b:.2f}, 差距={diff_ratio*100:.2f}%, 容差={tol*100:.2f}%")
    
    return diff_ratio <= tol

def boll_touch_signal(close: float, low: float, ma20: float, lower: float, tol: float) -> str:
    """
    输出中文提示串：
        - 收盘价接近中轨 / 收盘价接近下轨
        - 下引线接近中轨 / 下引线接近下轨
      如果都不满足，返回“未接近中轨或下轨”
    """
    msgs = []
    # 收盘价接近

    if pct_near(close, ma20, tol, 1):
        msgs.append("收盘价接近中轨")
    if pct_near(close, lower, tol, 2):
        msgs.append("收盘价接近下轨")
    # 下引线（最低价）接近
    if pct_near(low, ma20, tol, 3):
        msgs.append("下引线接近中轨")
    if pct_near(low, lower, tol, 4):
        msgs.append("下引线接近下轨")
    return "，".join(msgs) if msgs else "未接近中轨或下轨"

# def main():
#     pro = get_token()

#     # 准备股票池
#     symbols = SYMBOLS.copy()
#     if (not symbols) and INDEX_CODE:
#         symbols = fetch_index_members(pro, INDEX_CODE)
#     if not symbols:
#         print("未设置 SYMBOLS，且 INDEX_CODE 为空。请在脚本顶部配置其一。")
#         return

#     start_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y%m%d")
#     end_date   = datetime.now().strftime("%Y%m%d")

#     print("\n=== BOLL 中轨/下轨 接近识别 ===")
#     print(f"窗口=BOLL({BOLL_WIN}, {BOLL_K}), 容差={TOL*100:.1f}%")
#     for code in symbols:
#         try:
#             df = fetch_daily(pro, code, start_date, end_date)
#             if df.empty:
#                 print(f"{code}: 无数据")
#                 continue
#             g = add_boll(df).dropna(subset=["MA20"]).copy()
#             if g.empty:
#                 print(f"{code}: 数据不足（MA20 未形成）")
#                 continue

#             row = g.iloc[-1]
#             msg = boll_touch_signal(
#                 close=float(row["close"]),
#                 low=float(row["low"]),
#                 ma20=float(row["MA20"]),
#                 lower=float(row["LOWER"]),
#                 tol=TOL
#             )
#             print(f"{code} ({row['date'].date()}): {msg}")
#             time.sleep(SLEEP_SEC)
#         except Exception as e:
#             print(f"{code}: 处理出错 - {e}")

# if __name__ == "__main__":
#     main()
