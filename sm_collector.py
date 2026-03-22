import akshare as ak
import pandas as pd
import os

def update_sm_data():
    symbol = "SM0" 
    file_name = "sm_futures_data.csv"

    print(f"正在获取 {symbol} 的历史行情数据...")

    try:
        # 获取原始数据
        df = ak.futures_zh_daily_sina(symbol=symbol)
        
        # 【核心修复】：动态选择列，防止列名对不上
        cols_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume', 'hold']
        # 只保留数据中确实存在的列
        existing_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[existing_cols]
        
        if not os.path.exists(file_name):
            df.to_csv(file_name, index=False, encoding='utf-8-sig')
            print(f"首次运行：已创建 {file_name}，存入 {len(df)} 条记录。")
        else:
            old_df = pd.read_csv(file_name)
            last_date = str(old_df['date'].max())
            new_data = df[df['date'].astype(str) > last_date]
            
            if not new_data.empty:
                new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
                print(f"更新成功：追加了 {len(new_data)} 条新数据。")
            else:
                print("数据已是最新，无需更新。")

    except Exception as e:
        print(f"运行出错: {e}")

if __name__ == "__main__":
    update_sm_data()