import requests
import sys
import os
import pandas as pd
import baostock as bs

################################################################################
# python .\plate.py 有色 镍 741201
# python .\plate.py 有色 铜 18258169
# python .\plate.py 有色 钼 20495569
# python .\plate.py 有色 钨 19676882
# python .\plate.py 有色 锌 21731726
# python .\plate.py 有色 锑 18963793
# python .\plate.py 有色 钛 20793881
# python .\plate.py 有色 钴 18041713
# python .\plate.py 有色 钒 19568577
# python .\plate.py 有色 铝 16819905
# python .\plate.py 有色 镁 19881630
# python .\plate.py 有色 锆 23680690
# python .\plate.py 有色 银 54724617
# python .\plate.py 有色 铁矿石 22411474
################################################################################

headers = {
    "authority": "flash-api.xuangubao.cn",
    "pragma": "no-cache",
    "cache-control": "no-cache",
    "accept": "*/*",
    "x-app-id": "rU6QIu7JHe2gOUeR",
    "sec-fetch-dest": "empty",
    "x-ivanka-token": "f7A3s3LKHkV9boIk/DLo8mlA1hmDeu4gtAgGSE6k/yhmcFg4Qg7NOrBcOxWALNZfLoVcvVTbSZW4BcXwrbDsZogRJ4QHzGhEagXvbAUWdAsS+qN5549cEsyp0tl0V30MSTObMmYM/JlXmuZ3m2E+DiWq9lh8ao6fOJPS8UmdO5/OgPHE5XIs8NhBGwPg02qkXjElKj1lVOzkKHFU1+DZg9U1zvNhrmcwV5kooYl/kQl0UWf/lLYXufqciu/CeVTCw2RVU2QUeapHmyvWrR9EtKWhRGc5XoDBN8wghMch20NrixBKaW0agmPwk2w5YAQ1vfCHEc/MYez6rjZXIzh/Zw==",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36",
    "origin": "https://xuangubao.cn",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "referer": "https://xuangubao.cn/",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8"
}

def get_data(url):
    r = requests.get(url, headers=headers)
    return r.json()["data"]

def parser_stock(stock):
    if stock.endswith('.SS'):
        stock = stock.replace('.SS', "").strip()
    
    if stock.endswith('.SZ'):
        stock = stock.replace('.SZ', "").strip()
    
    return f"A.{stock}"

def parser_plate(url):
    data = get_data(url)

    pool = []
    chains = data.get("industrial_chains")
    if chains:
        for chain in chains:
            stocks = chain['stocks']
            for stock in stocks:
                stock = parser_stock(stock)

                if stock not in pool:
                    pool.append(stock)
    else:
        stocks = data["stocks"]
        for stock_json in stocks:
            stock = parser_stock(stock_json['symbol'])

            if stock not in pool:
                pool.append(stock)

    return pool

# python .\plate.py 军工 无人机 无人机 29073617
# python .\plate.py 军工 大飞机 大飞机 18311442
# python .\plate.py 军工 航天 航天 51018737
# python .\plate.py 军工 飞行汽车 飞行汽车 89938137
# python .\plate.py 互联网 腾讯 腾讯 33504910
# python .\plate.py 互联网 阿里 阿里 33246089
# python .\plate.py 互联网 小米 小米 30370802
# python .\plate.py 互联网 字节 字节 5065425
# python .\plate.py 互联网 苹果 苹果 16793689
# python .\plate.py 有色 稀土 稀土永磁 16847921
# python .\plate.py 有色 有机硅 有机硅 19771457
# python .\plate.py AI 人工智能应用 人工智能应用 85945106
# python .\plate.py 军工 军工 军工 25513273
# python .\plate.py 机械 机械 机械 18336809
# python .\plate.py 消费 白酒 白酒 16961441
# python .\plate.py 消费 三胎 三胎 17174158
# python .\plate.py 消费 乳业 乳业 16868321
# python .\plate.py 消费 旅游 旅游 19993841
if len(sys.argv) > 2:
  excel_name = 'DayDayHappy'
  sheet_name = sys.argv[1]
  plate_name = sys.argv[2] 
  plate_id = sys.argv[3] 

  url = f"https://flash-api.xuangubao.cn/api/plate/plate_set?id={plate_id}"
  cons = parser_plate(url)

  excel_name = os.path.join(f"{excel_name}.xlsx")
  df = pd.read_excel(excel_name, sheet_name=f"{sheet_name}")

  bs.login()

  stock_name_arr = []
  for con in cons:
    items = str(con).split('.')
    con = items[1]

    if con.startswith('6'):
      exchange = 'SH'
    elif con.startswith('0') or con.startswith('3'):
      exchange = 'SZ'
    elif con.startswith('88'):
      exchange = 'BJ'
    else:
       print(con)
       print("--------------------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
       exit(1)

    new_stock_code = f"{exchange}.{con}"

    rs = bs.query_stock_basic(code=new_stock_code)
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    stock_name = data_list[0][1] if data_list else "Unknown"
    stock_name_arr.append(stock_name)

  bs.logout()

  df_new = pd.DataFrame({
     "plate": [f"{plate_name}"] * len(cons),
     "name": stock_name_arr,
     "code": cons
  })

  df_combined = pd.concat([df, df_new], ignore_index=True)
  
  with pd.ExcelWriter(excel_name, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
    df_combined.to_excel(writer, sheet_name=f"{sheet_name}", index=False)

else:
    print("参数不正确")