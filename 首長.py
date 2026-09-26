import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="台灣縣市首長資訊圖", layout="wide")
st.title("🗺️ 全台灣縣市首長資訊圖表")

# 1. 建立縣市首長資料庫 (可自由擴充年齡、2026候選人等欄位)
data = {
    "縣市": ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"],
    "首長": ["蔣萬安", "侯友宜", "張善政", "盧秀燕", "黃偉哲", "陳其邁", "謝國樑", "高虹安", "楊文科", "鍾東錦", "王惠美", "許淑華", "張麗善", "黃敏惠", "翁章梁", "周春米", "林姿妙", "徐榛蔚", "饒慶鈴", "陳光復", "陳福海", "王忠銘"],
    "政黨": ["中國國民黨", "中國國民黨", "中國國民黨", "中國國民黨", "民主進步黨", "民主進步黨", "中國國民黨", "台灣民眾黨", "中國國民黨", "無黨籍", "中國國民黨", "中國國民黨", "中國國民黨", "中國國民黨", "民主進步黨", "民主進步黨", "中國國民黨", "中國國民黨", "中國國民黨", "民主進步黨", "無黨籍", "中國國民黨"]
}
df = pd.DataFrame(data)

# 2. 側邊欄過濾器
st.sidebar.header("篩選條件")
selected_party = st.sidebar.multiselect("選擇政黨", options=df["政黨"].unique(), default=df["政黨"].unique())
filtered_df = df[df["政黨"].isin(selected_party)]

# 3. 畫面佈局：左邊放統計圖，右邊放詳細名單表格
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("政黨席次比例")
    party_counts = filtered_df["政黨"].value_counts().reset_index()
    # 自訂台灣政黨顏色
    color_map = {"中國國民黨": "#000095", "民主進步黨": "#1B9431", "台灣民眾黨": "#28C8C8", "無黨籍": "#707070"}
    fig = px.pie(party_counts, values="count", names="政黨", color="政黨", color_discrete_map=color_map, hole=0.3)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("首長詳細名單")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
