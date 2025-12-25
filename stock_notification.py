import pandas as pd

class StockNotification:
    def __init__(self, excel_handler):
        self.excel_handler = excel_handler
    
    def get_data(self):
        """
        从pool sheet获取名称和支撑价位，与watch sheet的close价格比较
        """
        try:
            # 从pool sheet获取名称和支撑价位，过滤空值
            pool_df = self.excel_handler.read_data_from_sheet('pool')
            support_data = {
                row['名称']: row['支撑价位'] 
                for _, row in pool_df.iterrows() 
                if pd.notna(row['支撑价位'])
            }
            
            # 从pool sheet获取重点关注列，过滤掉非YES的行，然后转成数组
            focus_rows = pool_df[pool_df['重点关注'] == 'YES']
            focus_names = focus_rows['名称'].tolist()

            # 从watch sheet获取名称和close价格
            watch_df = self.excel_handler.read_data_from_sheet('watch')
            
            # 比较支撑位和close价格
            stock_notices = []
            for _, row in watch_df.iterrows():
                name = row['名称']
                close = row['close']
                
                if name in support_data:
                    support = support_data[name]
                    change_percent = ((close - support) / support) * 100  # 计算价格变化百分比，负值表示下跌，正值表示上涨
                    
                    if support > close:
                        stock_notices.append(f"{name}下跌了{abs(change_percent):.2f}%")
                    else:
                        stock_notices.append(f"{name}上涨了{abs(change_percent):.2f}%")
            
            return stock_notices, focus_names
            
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return []