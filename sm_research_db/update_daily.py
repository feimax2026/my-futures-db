import akshare as ak
import pandas as pd
from datetime import datetime
import os
import time

DATA_DIR = "sm_research_db"

def update_daily():
    print("1. 正在增量更新主力连续 (SM0)...")
    old_main = pd.read_csv(f"{DATA_DIR}/sm_main_sina.csv")
    new_main = ak.futures_zh_daily_sina(symbol="SM0")
    
    if new_main is not None and not new_main.empty:
        combined_main = pd.concat([old_main, new_main]).drop_duplicates(subset=['date'], keep='last')
        combined_main.to_csv(f"{DATA_DIR}/sm_main_sina.csv", index=False)

    print("2. 正在增量更新活跃合约 (今明两年)...")
    old_raw = pd.read_csv(f"{DATA_DIR}/sm_raw_all_contracts.csv")
    current_year = datetime.now().year
    new_contracts = []
    
    # 只抓取今年和明年的合约，采用 3位/4位 双重试探机制
    for y in [current_year, current_year + 1]:
        for m in range(1, 13):
            month_str = str(m).zfill(2)
            full_id = f"SM{y}{month_str}"
            code_4 = f"SM{str(y)[-2:]}{month_str}"
            code_3 = f"SM{str(y)[-1]}{month_str}"
            
            df = None
            try: df = ak.futures_zh_daily_sina(symbol=code_4)
            except: pass
            
            if df is None or df.empty:
                try: df = ak.futures_zh_daily_sina(symbol=code_3)
                except: pass
                
            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'].dt.year >= y - 1) & (df['date'].dt.year <= y)]
                if not df.empty:
                    df['contract_id'] = full_id
                    new_contracts.append(df)
            time.sleep(1)

    if new_contracts:
        new_raw = pd.concat(new_contracts)
        # 按照日期和合约ID双重去重，保留最新抓取的数据
        combined_raw = pd.concat([old_raw, new_raw]).drop_duplicates(subset=['date', 'contract_id'], keep='last')
        combined_raw.to_csv(f"{DATA_DIR}/sm_raw_all_contracts.csv", index=False)
    else:
        combined_raw = old_raw

    print("3. 正在重新计算加权 OHLC 指数...")
    idx_data = []
    for date, group in combined_raw.groupby('date'):
        t_hold = group['hold'].sum()
        t_vol = group['volume'].sum()
        
        if t_hold > 0:
            w_open = (group['open'] * group['hold']).sum() / t_hold
            w_high = (group['high'] * group['hold']).sum() / t_hold
            w_low = (group['low'] * group['hold']).sum() / t_hold
            w_close = (group['close'] * group['hold']).sum() / t_hold
            
            idx_data.append({
                'date': date, 
                'open': round(w_open, 2),
                'high': round(w_high, 2),
                'low': round(w_low, 2),
                'close': round(w_close, 2),
                'total_volume': t_vol,
                'total_hold': t_hold
            })
            
    df_weighted = pd.DataFrame(idx_data).sort_values('date')
    df_weighted.to_csv(f"{DATA_DIR}/sm_weighted_index.csv", index=False)
    print("🎉 每日数据更新完成！")

if __name__ == "__main__":
    update_daily()