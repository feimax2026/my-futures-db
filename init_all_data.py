import akshare as ak
import pandas as pd
import os
import time

DATA_DIR = "sm_research_db"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def run_init():
    # --- 1. 获取主力连续 (SM0) ---
    print("1. 正在初始化主力连续 (SM0)...")
    try:
        df_main = ak.futures_zh_daily_sina(symbol="SM0")
        if df_main is not None and not df_main.empty:
            df_main.to_csv(f"{DATA_DIR}/sm_main_sina.csv", index=False)
            print("✅ 主力连续抓取成功！")
        else:
            print("❌ 主力连续获取为空")
    except Exception as e:
        print(f"❌ 主力连续抓取失败: {e}")

    # --- 2. 穷举抓取 2017-2026 所有合约 ---
    print("\n2. 正在初始化 2017-2026 所有合约 (双重试探机制，约需 3-5 分钟)...")
    all_contracts = []
    
    for y in range(2017, 2027):
        for m in range(1, 13):
            month_str = str(m).zfill(2)
            full_id = f"SM{y}{month_str}"
            
            # 格式 1：四位数代码 (如 2025年5月 -> SM2505)
            code_4_digit = f"SM{str(y)[-2:]}{month_str}"
            # 格式 2：三位数代码 (如 2025年5月 -> SM505)
            code_3_digit = f"SM{str(y)[-1]}{month_str}"
            
            df = None
            
            # 第一步：先试新版的 4 位数代码
            try:
                df = ak.futures_zh_daily_sina(symbol=code_4_digit)
            except:
                pass
                
            # 第二步：如果 4 位数没拿到数据，立刻试旧版的 3 位数代码
            if df is None or df.empty:
                try:
                    df = ak.futures_zh_daily_sina(symbol=code_3_digit)
                except:
                    pass
            
            # 第三步：如果拿到数据，清洗并保存
            if df is not None and not df.empty:
                try:
                    df['date'] = pd.to_datetime(df['date'])
                    # 仅保留属于该合约生命周期的年份数据 (上市当年和交割当年)
                    df = df[(df['date'].dt.year >= y - 1) & (df['date'].dt.year <= y)]
                    
                    if not df.empty:
                        df['contract_id'] = full_id
                        all_contracts.append(df)
                        print(f"✅ 获取成功: {full_id} (行数: {len(df)})")
                except Exception as e:
                    print(f"⚠️ 清洗 {full_id} 时出错: {e}")
            
            # 延迟 1 秒，防止被新浪接口封禁 IP
            time.sleep(1)

    if not all_contracts:
        print("\n❌ 没有获取到任何历史合约数据，请检查网络或 API 状态。")
        return

    # 合并、去重、保存全量原始表
    print("\n正在合并全合约数据...")
    df_raw = pd.concat(all_contracts).drop_duplicates()
    df_raw.to_csv(f"{DATA_DIR}/sm_raw_all_contracts.csv", index=False)
    print("✅ 所有历史合约数据保存成功！")

# --- 3. 计算加权平均指数 (包含 OHLC) ---
    print("\n3. 正在本地计算全品种加权 OHLC 指数...")
    idx_data = []
    for date, group in df_raw.groupby('date'):
        t_hold = group['hold'].sum()
        t_vol = group['volume'].sum() # 顺便把总成交量也加总了
        
        if t_hold > 0:
            # 分别对开、高、低、收进行持仓加权
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
    print("✅ 加权 OHLC 指数计算并保存成功！")
    print("\n🎉 全部初始化完成！请检查 sm_research_db 文件夹下的 3 个 CSV 文件。")

if __name__ == "__main__":
    run_init()