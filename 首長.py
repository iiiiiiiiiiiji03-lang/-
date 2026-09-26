import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁基本設定
st.set_page_config(page_title="台灣匿名版 - 無政府自由看板", layout="wide", page_icon="🇹🇼")

# 2. 全域快取：這是一上線完全空白的「雲端資料庫」
@st.cache_resource
def init_bulletin_board():
    # 這裡面完全不放任何預設貼文，留空等待網友發文
    # 每篇貼文的資料結構裡，會多一個 "replies" 的獨立清單來存全域推文
    return []

posts_db = init_bulletin_board()

# ==========================================
# 側邊欄：看板切換與發文功能
# ==========================================
st.sidebar.title("🇹🇼 台灣匿名版")
st.sidebar.write("`完全匿名 / 不記IP / 自由發言`")
st.sidebar.write("---")

# 選擇要看哪一個板
board_options = ["全部看板 📑", "全台大雜燴 ☕", "六都政治八卦 🏙️", "2026選戰預測 🗳️", "地方政策吐槽 📢"]
selected_board = st.sidebar.selectbox("🎯 選擇討論板", board_options)

st.sidebar.write("---")
st.sidebar.subheader("✍️ 匿名發表新文章")

# 發文表單
with st.sidebar.form(key="publish_form", clear_on_submit=True):
    new_board = st.selectbox("選擇要發表的看板", board_options[1:]) # 排除「全部看板」
    new_name = st.text_input("匿名暱稱", max_chars=15, placeholder="例如：中正區鄉民")
    new_title = st.text_input("文章標題", max_chars=40, placeholder="吸引人的標題...")
    new_content = st.text_area("文章內容", max_chars=500, placeholder="請暢所欲言...")
    submit_post = st.form_submit_button(label="🚀 匿名發布")

# 處理發文邏輯
if submit_post:
    if new_name.strip() == "" or new_title.strip() == "" or new_content.strip() == "":
        st.sidebar.error("欄位不能留白喔！")
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        # 把新文章塞到最前面，並預設一個空的全域推文清單 []
        posts_db.insert(0, {
            "看板": new_board,
            "暱稱": new_name.strip(),
            "時間": current_time,
            "標題": new_title.strip(),
            "content": new_content.strip(),
            "replies": []  # 核心修正：讓推文存在全域資料中
        })
        st.sidebar.success("文章已成功匿名送出！")
        st.rerun()

# ==========================================
# 主畫面：文章列表展示
# ==========================================
st.title(f"📌 目前看板：{selected_board}")
st.write("---")

# 根據選板過濾文章
if selected_board == "全部看板 📑":
    display_posts = posts_db
else:
    display_posts = [p for p in posts_db if p["看板"] == selected_board]

# 如果看板是空的
if not display_posts:
    st.info("目前這個看板還沒有人發文，快來側邊欄當第一個發文的開荒者吧！🚀")

# 展開顯示每一篇文章
for idx, post in enumerate(display_posts):
    with st.expander(f"【{post['看板']}】 {post['標題']}  —  👤 {post['暱稱']} ({post['時間']})"):
        content_text = post.get("內容") if "內容" in post else post.get("content", "")
        st.write(content_text)
        
        st.write("`— 匿名推文區 —`")
        
        # 確保舊的文章或相容性不會出錯，若無 replies 欄位則自動補上
        if "replies" not in post:
            post["replies"] = []
            
        # 核心改動：直接從全域 post["replies"] 讀取推文，所有人畫面都會同步！
        for c in post["replies"]:
            st.caption(c)
            
        # 快速推文小輸入框
        with st.form(key=f"reply_form_{idx}", clear_on_submit=True):
            reply_text = st.text_input("快速回覆這篇...", max_chars=50, key=f"input_{idx}")
            reply_sub = st.form_submit_button("推")
            if reply_sub and reply_text.strip() != "":
                # 直接塞進該篇文章的全域推文清單中
                post["replies"].append(f"💬 匿名鄉民：{reply_text.strip()}")
                st.rerun()
