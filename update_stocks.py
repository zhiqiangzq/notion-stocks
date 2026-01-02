import os
import re
from datetime import datetime, timezone

import yfinance as yf
from notion_client import Client

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
print("TOKEN_LEN =", len(NOTION_TOKEN))

def hk_to_yahoo(ticker: str) -> str:
    """00291.HK -> 0291.HK（yfinance 常用格式）"""
    m = re.fullmatch(r"(\d{4,5})\.HK", ticker.upper())
    if not m:
        return ticker.upper()
    num = m.group(1)
    return f"{int(num):04d}.HK"


def a_to_yahoo(ticker: str) -> str:
    """上交所 .SH -> yfinance 的 .SS；深交所 .SZ 保持不变"""
    t = ticker.upper()
    if t.endswith(".SH"):
        return t[:-3] + ".SS"
    return t


def to_yahoo(ticker: str) -> str:
    t = ticker.strip().upper()
    if t.endswith(".HK"):
        return hk_to_yahoo(t)
    if t.endswith(".SH") or t.endswith(".SZ"):
        return a_to_yahoo(t)
    return t


def today_date_str_local() -> str:
    return datetime.now(timezone.utc).astimezone().date().isoformat()

def query_all_pages(notion: Client, database_id: str):
    pages = []
    cursor = None
    while True:
        if cursor:
            resp = notion.databases.query(
                database_id=database_id,
                start_cursor=cursor,
                page_size=100,
            )
        else:
            resp = notion.databases.query(
                database_id=database_id,
                page_size=100,
            )
    
        pages.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return pages


def get_text_prop(page, prop_name: str) -> str:
    prop = page["properties"].get(prop_name)
    if not prop:
        return ""

    if prop["type"] == "rich_text":
        return "".join(x["plain_text"] for x in prop["rich_text"]).strip()

    if prop["type"] == "title":
        return "".join(x["plain_text"] for x in prop["title"]).strip()

    return ""
def update_page(notion: Client, page_id: str, last_price, change, change_pct, date_str: str):
    notion.pages.update(
        page_id=page_id,
        properties={
            "最新价": {"number": None if last_price is None else float(last_price)},
            "涨跌额": {"number": None if change is None else float(change)},
            "涨跌幅%": {"number": None if change_pct is None else float(change_pct)},
            "更新日期": {"date": {"start": date_str}},
        },
    )


def main():
    notion = Client(auth=NOTION_TOKEN)
    database_id = NOTION_DATABASE_ID

    pages = query_all_pages(notion, database_id)

    rows = []
    for p in pages:
        code = get_text_prop(p, "代码")
        if code:
            rows.append((p["id"], code))

    if not rows:
        print("No tickers found in Notion.")
        return

    yahoo_map = {code: to_yahoo(code) for _, code in rows}
    yahoo_list = sorted(set(yahoo_map.values()))

    data = yf.download(
        tickers=" ".join(yahoo_list),
        period="5d",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    date_str = today_date_str_local()
    for page_id, code in rows:
        y = yahoo_map[code]
        try:
            if "Close" in getattr(data, "columns", []):
                df = data
            else:
                if y not in data.columns.get_level_values(0):
                    print(f"Skip {code} ({y}) not in data")
                    continue
                df = data[y]

            df = df.dropna()
            if df.empty:
                print(f"Skip {code} ({y}) empty")
                continue

            last_close = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else None

            change = (last_close - prev_close) if prev_close is not None else None
            change_pct = ((change / prev_close) * 100.0) if (change is not None and prev_close) else None

            update_page(notion, page_id, last_close, change, change_pct, date_str)
            print(f"Updated {code} ({y}) price={last_close}")
        except Exception as e:
            print(f"Failed {code} ({y}): {e}")


if __name__ == "__main__":
    main()    







