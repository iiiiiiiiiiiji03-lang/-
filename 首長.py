import hashlib
import os
import streamlit as st

# 設定網頁標題與圖示
st.set_page_config(
    page_title="人事部勞工運行狀態中心", page_icon="📊", layout="centered"
)


# ==========================================
# 0. 全域共享狀態管理（跨電腦同步）
# ==========================================
class StatusManager:

  """用來在伺服器記憶體中保存狀態與紀錄的類別"""

  def __init__(self):
    self.current_status = "🟢 上線"
    self.notice_message = ""  # 管理員自訂公告
    self.ticker_text = (
        "🎉 歡迎來到人事部勞工運行狀態中心！系統目前正常運作中。"  # 跑馬燈預設內容
    )
    self.logs = []

    self.add_log("🟢 上線", "系統初始化")

  def set_status(self, new_status, notice="", ticker=""):
    self.current_status = new_status
    self.notice_message = notice

    # 嚴格限制跑馬燈最大長度為 50 字
    if ticker:
      self.ticker_text = ticker[:50]
    else:
      self.ticker_text = ""

    self.add_log(new_status, notice)

  def get_status_info(self):
    return {
        "status": self.current_status,
        "notice": self.notice_message,
        "ticker": self.ticker_text,
    }

  def add_log(self, status, notice):
    self.logs.insert(
        0,
        {
            "status": status,
            "notice": notice if notice else "無補充說明",
        },
    )
    if len(self.logs) > 50:
      self.logs.pop()

  def get_logs(self):
    return self.logs


@st.cache_resource
def get_status_manager():
  """利用 Streamlit 快取機制，讓所有使用者共享同一個物件"""
  return StatusManager()


# 取得全域唯一的狀態管理器
status_manager = get_status_manager()

# 【自動相容防錯機制】如果快取中是舊版物件，自動清除快取並重新載入
if not hasattr(status_manager, "get_status_info"):
  st.cache_resource.clear()
  st.rerun()


# ==========================================
# 1. 從後台 Secrets 安全讀取密碼並驗證
# ==========================================
def check_password(password_input):
  """從 Streamlit 後台的 Secrets 欄位安全讀取密碼"""
  if "ADMIN_PASSWORD" in st.secrets:
    secret_password = st.secrets["ADMIN_PASSWORD"]
  elif "ADMIN_PASSWORD" in os.environ:
    secret_password = os.environ["ADMIN_PASSWORD"]
  else:
    secret_password = "admin"  # 本地測試備用密碼

  hash_input = hashlib.sha256(password_input.encode()).hexdigest()
  hash_secret = hashlib.sha256(secret_password.encode()).hexdigest()
  return hash_input == hash_secret


# ==========================================
# 2. 初始化登入狀態
# ==========================================
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

# ==========================================
# 3. 前台：每 5 秒自動更新的狀態與跑馬燈展示區
# ==========================================
st.title("🌐 BOT運行狀態")


@st.fragment(run_every=5)
def render_status_display():
  info = status_manager.get_status_info()
  current_status = info["status"]
  notice = info["notice"]
  ticker = info["ticker"]

  # 跑馬燈區塊 (若管理員有輸入內容才顯示)
  if ticker:
    st.markdown(
        f"""
            <div style="
                background-color: #f0f2f6; 
                padding: 8px 12px; 
                border-radius: 8px; 
                margin-bottom: 15px;
                border-left: 5px solid #ff4b4b;
                overflow: hidden;
            ">
                <marquee behavior="scroll" direction="left" scrollamount="6" style="font-weight: bold; color: #31333F;">
                    📢 {ticker}
                </marquee>
            </div>
            """,
        unsafe_allow_html=True,
    )

  st.subheader("目前服務狀態")

  if current_status == "🟢 上線":
    st.success(
        "### 🟢 系統正常運行中 (Online)\n目前所有服務皆可正常存取，請安心使用。"
    )
  elif current_status == "🟡 維修中":
    st.warning(
        "### 🟡 系統定期維修中 (Maintenance)\n正在進行例行維護以提升服務品質，造成不便請見諒。"
    )
  elif current_status == "🔴 故障":
    st.error(
        "### 🔴 系統突發故障 (Down)\n核心服務目前遭遇異常，工程師已收到通知並正全力搶修中。"
    )

  # 詳細補充公告
  if notice:
    st.info(f"📌 **詳細說明：** {notice}")

  # 完全移除時間，僅保留狀態同步提示
  st.caption("🔄 狀態每 5 秒自動同步更新中...")


# 執行前台狀態區
render_status_display()

st.divider()

# ==========================================
# 4. 後台：密碼保護的管理控制台
# ==========================================
st.subheader("🔒 管理員控制台")

if not st.session_state["logged_in"]:
  with st.form("login_form"):
    password_input = st.text_input("請輸入管理員密碼：", type="password")
    submit_button = st.form_submit_button("登入後台")

    if submit_button:
      if check_password(password_input):
        st.session_state["logged_in"] = True
        st.success("密碼正確！已成功登入管理後台。")
        st.rerun()
      else:
        st.error("密碼錯誤，請再試一次。")
else:
  st.info("🔓 您已成功登入，可以自由切換網站狀態與跑馬燈。")

  current_info = status_manager.get_status_info()
  status_options = ["🟢 上線", "🟡 維修中", "🔴 故障"]
  current_index = status_options.index(current_info["status"])

  # 狀態與跑馬燈變更表單
  with st.form("update_status_form"):
    new_status = st.radio(
        "請選擇欲變更的網站狀態：", options=status_options, index=current_index
    )

    # 跑馬燈文字輸入框（上限 20 字）
    ticker_input = st.text_input(
        "跑馬燈公告內容（上限 20 字，留空則隱藏）：",
        value=current_info["ticker"],
        max_chars=20,
        help="限制最多輸入 20 個字元，會在前台最上方滾動顯示。",
    )

    notice_input = st.text_area(
        "自訂補充公告 / 預計恢復時間（可留空）：",
        value=current_info["notice"],
        placeholder="例如：預計今日 14:00 恢復服務...",
    )

    submit_update = st.form_submit_button("更新設定", type="primary")

    if submit_update:
      status_manager.set_status(new_status, notice_input, ticker_input)
      st.success("設定已成功更新！")
      st.rerun()

  # 顯示歷史紀錄 Tab
  with st.expander("📜 查看狀態變更歷史紀錄"):
    logs = status_manager.get_logs()
    st.table(logs)

  # 登出按鈕
  if st.button("登出後台"):
    st.session_state["logged_in"] = False
    st.success("已成功登出。")
    st.rerun()
