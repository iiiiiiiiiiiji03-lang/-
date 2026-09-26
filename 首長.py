import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁基本設定 (設定為寬版，加入台灣地圖圖示)
st.set_page_config(page_title="台灣匿名版 - 無政府自由看板", layout="wide", page_icon="🇹🇼")

# 2. 全域快取：這是無政府匿名版的「雲端資料庫」
@st.cache_resource
def init_bulletin_board():
    # 預設一些好玩的匿名初始文章
    return [
        {
            "看板": "2026選戰預測 🗳️",
            "暱稱": "神算諸葛",
            "時間": "2026-09-25 14:20",
            "標題": "大家覺得年底九合一大選，哪一個縣市最激戰？",
            "內容": "感覺這次台北跟高雄都很精彩，大家有內幕消息嗎？歡迎盲猜！"
        },
        {
            "看板": "六都政治八卦 🏙️",
            "暱稱": "吃瓜群眾",
            "時間": "2026-09-26 21:05",
            "標題": "有人知道某縣市首長最近的行程嗎？",
            "內容": "純粹好奇，聽說最近都在跑基層，是不是在為連任鋪路？"
        },
        {
            "看板": "全台大雜燴 ☕",
            "暱稱": "路過的路人",
            "時間": "2026-09-27 00:15",
            "標題": "這個匿名版真的不會抓IP嗎？",
            "內容": "測試一下，如果真的不抓IP，那這裡簡直是講真話的天堂概念網頁啊哈哈哈！"
        }
    ]

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
        # 把新文章塞到最前面
        posts_db.insert(0, {
            "看板": new_board,
            "暱稱": new_name.strip(),
            "時間": current_time,
            "標題": new_title.strip(),
            "content": new_content.strip()  # 這裡先存入，後面展開顯示
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
    st.info("目前這個看板還沒有人發文，快來當第一個開荒者吧！")

# 展開顯示每一篇文章
for idx, post in enumerate(display_posts):
    # 使用 Streamlit 的 Expander（可摺疊區塊）做出像論壇點開文章的效果
    with st.expander(f"【{post['看板']}】 {post['標題']}  —  👤 {post['暱稱']} ({post['時間']})"):
        # 如果是預設文章或新發文章，確保欄位能正常讀取
        content_text = post.get("內容") if "內容" in post else post.get("content", "")
        st.write(content_text)
        
        # 幫每篇文章加上一個趣味匿名推文區 (每篇文章獨立)
        st.write("`— 匿名推文區 —`")
        comment_key = f"comment_{idx}"
        if comment_key not in st.session_state:
            st.session_state[comment_key] = ["👍 鄉民前來朝聖！"]
            
        # 顯示該文章的推文
        for c in st.session_state[comment_key]:
            st.caption(c)
            
        # 快速推文小輸入框
        with st.form(key=f"reply_form_{idx}", clear_on_submit=True):
            reply_text = st.text_input("快速回覆這篇...", max_chars=50, key=f"input_{idx}")
            reply_sub = st.form_submit_button("推")
            if reply_sub and reply_text.strip() != "":
                st.session_state[comment_key].append(f"💬 匿名鄉民：{reply_text.strip()}")
                st.rerun()
