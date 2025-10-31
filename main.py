import requests
from bs4 import BeautifulSoup

# --- Target 1: PTT (Japan_Travel, Korea_Travel, Aviation) ---
# PTT 需要 cookies 來繞過 "我已滿18歲" 的檢查
def scrape_ptt(board_name):
    print(f"--- 正在爬取 PTT {board_name} 版 ---")
    url = f"https://www.ptt.cc/bbs/{board_name}/index.html"
    headers = {
        'Cookie': 'over18=1'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # 如果出錯，拋出異常
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找所有文章標題
        titles = soup.find_all('div', class_='title')
        for title in titles:
            if title.a: # 確保標題存在 (避免被刪除的文章)
                print(f"[標題] {title.a.text}")
                # print(f"[連結] https://www.ptt.cc{title.a['href']}")

    except requests.exceptions.RequestException as e:
        print(f"爬取 PTT {board_name} 失敗: {e}")

# --- Target 2: FlyData (機票促銷資訊) ---
def scrape_flydata():
    print(f"\n--- 正在爬取 FlyData 網站 ---")
    url = "https://flydata.com.tw/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找促銷文章的標題 (h2 class='entry-title')
        titles = soup.find_all('h2', class_='entry-title')
        for title in titles:
            if title.a:
                print(f"[標題] {title.a.text}")
                # print(f"[連結] {title.a['href']}")

    except requests.exceptions.RequestException as e:
        print(f"爬取 FlyData 失敗: {e}")

# --- 其他可能的目標 (結構類似) ---
# https://traveggo.com/
# https://www.tripplus.cc/ (偏向點數卡)

if __name__ == "__main__":
    # 執行爬蟲
    scrape_ptt("Japan_Travel")
    scrape_ptt("Korea_Travel")
    scrape_flydata()