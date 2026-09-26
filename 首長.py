import threading
import asyncio
import streamlit as st
import discord
from discord.ext import commands

# 設定網頁標題與圖示
st.set_page_config(page_title="Discord 機器人狀態面板", layout="centered", page_icon="🤖")
st.title("🤖 Discord 機器人狀態面板")

# 1. 使用 Streamlit 快取機制，確保機器人在背景「只會啟動一次」，不會因為網頁刷新而重複啟動
@st.cache_resource
def start_discord_bot():
    intents = discord.Intents.default()
    # 如果你的機器人需要讀取成員名單或訊息，請在下方開啟對應的 intents
    # intents.members = True
    # intents.message_content = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    # 為背景線程建立專屬的事件循環 (Event Loop)
    loop = asyncio.new_event_loop()
    
    # 用來跨線程共享的狀態字典
    status_data = {
        "bot": bot,
        "is_ready": False
    }

    @bot.event
    async def on_ready():
        status_data["is_ready"] = True
        print(f"【系統通知】機器人已成功上線：{bot.user}")

    def run_bot():
        asyncio.set_event_loop(loop)
        try:
            # 從 Streamlit 後台的 Secrets 安全地讀取 Token
            TOKEN = st.secrets["DISCORD_TOKEN"]
            loop.run_until_complete(bot.start(TOKEN))
        except Exception as e:
            print(f"【錯誤】機器人啟動失敗: {e}")

    # 建立多線程 (Multi-threading) 讓機器人在背景跑，不卡住網頁
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    return status_data

# 呼叫啟動函式（如果已經啟動過，會直接回傳現有的狀態）
bot_status = start_discord_bot()
bot = bot_status["bot"]

# 2. 製作 Streamlit 前端網頁畫面
st.subheader("即時連線數據")

# 判斷機器人是否已經成功與 Discord 連線
if bot_status["is_ready"] and bot.user:
    st.success("🟢 機器人目前在線中 (Online)")
    
    # 建立三個漂亮的數據方塊
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🤖 機器人名稱", value=str(bot.user).split('#')[0])
    with col2:
        # 計算延遲時間 (微秒轉毫秒)
        ping = round(bot.latency * 1000) if bot.latency and not float('inf') else 0
        st.metric(label="⚡ 延遲 (Ping)", value=f"{ping} ms")
    with col3:
        st.metric(label="🏠 伺服器總數", value=f"{len(bot.guilds)} 個")
        
else:
    st.warning("🔴 機器人正在聯絡 Discord 伺服器中，或處於離線狀態...")
    st.info("提示：如果等待過久，請檢查 Streamlit 後台的 Secrets 是否有正確填入 `DISCORD_TOKEN`，或查看右下角的 Manage app 紀錄。")

st.divider()

# 手動重新整理按鈕
if st.button("🔄 重新整理網頁狀態"):
    st.author = "Streamlit"
    st.rerun()
