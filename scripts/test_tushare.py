import tushare as ts
import os
from dotenv import load_dotenv

load_dotenv()

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")

ts.set_token(TUSHARE_API_KEY)

#sina数据
df = ts.realtime_quote(ts_code='600000.SH,000001.SZ,000001.SH')

print(df)

print("----")

#东财数据
df = ts.realtime_quote(ts_code='600000.SH', src='dc')

print(df)