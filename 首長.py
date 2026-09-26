import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定 (設定為寬版，使用台灣國旗圖示)
st.set_page_config(page_title="台灣匿名版 - 無政府自由看板", layout="wide", page_icon="🇹🇼")

# 核心設定：網頁每隔 5 秒 (5000毫秒) 在背景自動重整，即時同步全台最新貼文
st_autorefresh(interval=5000, key="taiwan_board_counter")

# 2. 全域快取：這是一上線完全空白的「雲端資料庫」
@st.cache_resource
def init_bulletin_board():
    return []

posts_db = init_bulletin_board()

# ==========================================
# 側邊欄：純發文功能區
# ==========================================
st.sidebar.title("🇹🇼 台灣匿名版")
st.sidebar.write("`完全匿名 / 不記IP / 自由發文`")
st.sidebar.write("*(網頁每 5 秒會自動重新整理)*")
st.sidebar.write("---")

st.sidebar.subheader("✍️ 匿名發表新貼文")

# 發文表單 (這裡拿掉了選擇看板的功能)
with st.sidebar.form(key="publish_form", clear_on_submit=True):
    new_name = st.text_input("匿名暱稱", max_chars=15, placeholder="例如：中正區鄉民")
    new_title = st.text_input("貼文標題", max_chars=40, placeholder="輸入貼文標題...")
    new_content = st.text_area("貼文內容", max_chars=500, placeholder="請暢所欲言...")
    submit_post = st.form_submit_button(label="🚀 匿名發布")

# 處理發文邏輯
if submit_post:
    if new_name.strip() == "" or new_title.strip() == "" or new_content.strip() == "":
        st.sidebar.error("欄位不能留白喔！")
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        # 把新文章塞到全域清單的最前面
        posts_db.insert(0, {
            "暱稱": new_name.strip(),
            "時間": current_time,
            "標題": new_title.strip(),
            "content": new_content.strip()
        })
        st.sidebar.success("貼文已成功匿名送出！")
        st.rerun()

# ==========================================
# 主畫面：唯一的台灣版貼文列表展示
# ==========================================
st.title("📌 目前看板：台灣版 🇹🇼")
st.write("---")

# 如果目前沒有任何貼文
if not posts_db:
    st.info("目前台灣版還沒有人發文，快來側邊欄當第一個發文的開荒者吧！🚀")

# 展開顯示每一篇歷史貼文
for idx, post in enumerate(posts_db):
    # 使用可折疊區塊，標題直接呈現：標題、作者、發文時間
    with st.expander(f"📝 {post['標題']}  —  👤 {post['暱稱']} ({post['時間']})"):
        # 顯示純文字貼文內容 (這裡已經徹底移除下方的留言與回覆框)
        content_text = post.get("內容") if "內容" in post else post.get("content", "")
        st.write(content_text)
