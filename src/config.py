"""
EveryFly 航線與查詢配置

定義追蹤的航線、查詢參數和日期範圍設定。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class Route:
    """航線定義"""
    origin: str          # 起點 IATA 代碼
    destination: str     # 終點 IATA 代碼
    name: str            # 航線名稱（顯示用）


@dataclass
class SearchConfig:
    """查詢配置"""
    adults: int = 1                    # 成人人數
    travel_class: str = "ECONOMY"      # 艙等: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
    non_stop: Optional[bool] = None    # None=不限, True=僅直飛, False=僅轉機
    max_results: int = 10              # 最多回傳結果數
    currency: str = "TWD"              # 貨幣


# ============================================================
# 追蹤航線設定
# ============================================================

ROUTES: List[Route] = [
    Route(origin="TPE", destination="NRT", name="台北-東京成田"),
    Route(origin="TPE", destination="HND", name="台北-東京羽田"),
    Route(origin="TPE", destination="KIX", name="台北-大阪關西"),
    Route(origin="TPE", destination="DPS", name="台北-峇厘島"),
    Route(origin="TPE", destination="LIS", name="台北-里斯本"),
    Route(origin="TPE", destination="BER", name="台北-柏林"),
]

# ============================================================
# 查詢日期範圍設定
# ============================================================

# 出發日期範圍（從今天算起）
DEPARTURE_DATE_RANGES = [
    (7, 14),      # 近期：7-14 天後
    (30, 45),     # 中期：30-45 天後
    (60, 90),     # 中遠期：60-90 天後
    (120, 180),   # 遠期：120-180 天後
]

# 來回票的停留天數選項
STAY_DURATIONS = [3, 5, 7, 14]  # 停留 3/5/7/14 天


# ============================================================
# 查詢類型
# ============================================================

class TripType:
    ONE_WAY = "one_way"       # 單程
    ROUND_TRIP = "round_trip" # 來回


# ============================================================
# 預設查詢配置
# ============================================================

DEFAULT_SEARCH_CONFIG = SearchConfig(
    adults=1,
    travel_class="ECONOMY",
    non_stop=None,  # 不限直飛或轉機
    max_results=5,
    currency="TWD",
)


def get_search_dates() -> List[dict]:
    """
    生成要查詢的日期組合
    
    Returns:
        包含出發日和回程日的字典列表
    """
    today = datetime.now().date()
    search_dates = []
    
    for start_offset, end_offset in DEPARTURE_DATE_RANGES:
        # 取範圍中間點作為代表日期
        mid_offset = (start_offset + end_offset) // 2
        departure_date = today + timedelta(days=mid_offset)
        
        # 單程
        search_dates.append({
            "departure_date": departure_date.isoformat(),
            "return_date": None,
            "trip_type": TripType.ONE_WAY,
            "label": f"{mid_offset}天後單程"
        })
        
        # 來回（不同停留天數）
        for stay in STAY_DURATIONS:
            return_date = departure_date + timedelta(days=stay)
            search_dates.append({
                "departure_date": departure_date.isoformat(),
                "return_date": return_date.isoformat(),
                "trip_type": TripType.ROUND_TRIP,
                "label": f"{mid_offset}天後來回{stay}天"
            })
    
    return search_dates


def get_all_search_combinations() -> List[dict]:
    """
    生成所有航線 × 日期的查詢組合
    
    Returns:
        完整的查詢組合列表
    """
    combinations = []
    search_dates = get_search_dates()
    
    for route in ROUTES:
        for date_config in search_dates:
            combinations.append({
                "route": route,
                **date_config
            })
    
    return combinations


if __name__ == "__main__":
    # 測試配置
    print("=== 追蹤航線 ===")
    for route in ROUTES:
        print(f"  {route.name}: {route.origin} → {route.destination}")
    
    print("\n=== 查詢日期組合 ===")
    dates = get_search_dates()
    print(f"  共 {len(dates)} 種日期組合")
    for d in dates[:5]:
        print(f"  - {d['label']}: {d['departure_date']}", end="")
        if d['return_date']:
            print(f" → {d['return_date']}")
        else:
            print()
    
    print("\n=== 總查詢數 ===")
    combos = get_all_search_combinations()
    print(f"  {len(ROUTES)} 航線 × {len(dates)} 日期 = {len(combos)} 次查詢")
