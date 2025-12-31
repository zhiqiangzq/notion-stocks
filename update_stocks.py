import os
import re
from datetime import datetime, timezone

import yfinance as yf
from notion_client import Client
NOTION_TOKEN = os.environ["NOTION_TOKEN"]

# 这里放你 Notion 数据库(数据源) ID。你当前是 [华润系股票行情](https://www.notion.so/44ee4ae984ab81ffbb2d000302eb5600/ds/76fadc188de949aa875d051f4a1f6cf1?db=5334cda0444943b196bee4bcd430fe81&pvs=21)

NOTION_DATA_SOURCE_URL = os.environ["NOTION_DATA_SOURCE_URL"]

def hk_to_yahoo(ticker: str) -> str:

def a_to_yahoo(ticker: str) -> str:

def to_yahoo(ticker: str) -> str:

def today_date_str_local() -> str:

def query_all_pages(notion: Client, database_id: str):

def get_text_prop(page, prop_name: str) -> str:

def update_page(

):

def main():

if **name** == "**main**":
