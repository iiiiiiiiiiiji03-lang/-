import hashlib
import os
import requests
import streamlit as st

# 設定網頁標題與圖示
st.set_page_config(
    page_title="人事部勞工運行狀態中心", page_icon="📊", layout="centered"
)


# ==========================================
# 0. Discord 訊息發送函式
# ==========================================
def send_discord_message(bot_token, channel_id, message_text):
  """透過 Discord Bot API (REST API) 發送訊息至特定頻道"""
  url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
  headers = {
      "Authorization": f"Bot {bot_token.strip()}",
      "Content-Type": "application/json",
  }
  payload = {"content": message_text}

  try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code in [200, 201]:
      return True, "訊息已成功發送至 Discord 頻道！"
    else:
      error_msg = response.json().get("message", "未知錯誤")
      return (
          False,
          f"發送失敗 (HTTP {response.status_code}): {error_msg}。請檢查 Token 與頻道 ID 是否正確，以及 Bot 是否已加入該頻道並擁有發送訊息權限。",
      )
  except Exception as e:
    return False, f"連線發生異常：{str(e)}"


# ==========================================
# 1. 全域共享狀態管理 (V3)
# ==========================================
class StatusManagerV3:

  """用來在伺服器記憶體中保存狀態與紀錄的類別"""

  def __init__(self):
    self.current_status = "🟢 上線"
    self.notice_message = ""
    self.ticker_text = (
        "🎉 歡迎來到人事部勞工運行狀態中心！系統目前正常運作中。"
    )
    self.logs = []
    self.add_log("🟢 上線", "系統初始化")

  def set_status(self, new_status, notice="", ticker=""):
    self.current_status = new_status
    self.notice_message = notice
    self.ticker_text = ticker[:60] if ticker else ""
    self.add_log(new_status, notice)

  def get_status_info(self):
    return {
        "status": self.current_status,
        "notice": self.notice_message,
        "ticker": self.ticker_text,
    }

  def add_log(self, status, notice):
    self.logs.insert(
        0, {"status": status, "notice": notice if notice else "無補充說明"}
    )
    if len(self.logs) > 20:
      self.logs.pop()

  def get_logs(self):
    return self.logs


@st.cache_resource
def get_status_manager_v3():
  return StatusManagerV3()


status_manager = get_status_manager_v3()


# ==========================================
# 2. 安全驗證與登入狀態
# ==========================================
def check_password(password_input):
  if "ADMIN_PASSWORD" in st.secrets:
    secret_password = st.secrets["ADMIN_PASSWORD"]
  elif "ADMIN_PASSWORD" in os.environ:
    secret_password = os.environ["ADMIN_PASSWORD"]
  else:
    secret_password = "admin"

  hash_input = hashlib.sha256(password_input.encode()).hexdigest()
  hash_secret = hashlib.sha256(secret_password.encode()).hexdigest()
  return hash_input == hash_secret


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

  if ticker:
    st.markdown(
        f"""
            <style>
            .ticker-box {{
                width: 100%;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-left: 5px solid #ff4b4b;
                border-radius: 8px;
                padding: 12px 0;
                margin-bottom: 20px;
                overflow: hidden;
                position: relative;
            }}
            .ticker-text {{
                display: inline-block;
                white-space: nowrap;
                animation: marquee 16s linear infinite;
                font-size: 15px;
                font-weight: 600;
                line-height: 1.5;
            }}
            @keyframes marquee {{
                0%   {{ transform: translateX(100%); }}
                100% {{ transform: translateX(-100%); }}
            }}
            </style>
            <div class="ticker-box">
                <div class="ticker-text">📢 {ticker}</div>
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

  if notice:
    st.info(f"📌 **詳細說明：** {notice}")

  st.caption("🔄 狀態每 5 秒自動同步更新中...")


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
  st.info("🔓 您已成功登入，可以變更網站狀態或以 Discord Bot 身份發送訊息。")

  # 分頁選單：1. 狀態控制 / 2. Discord Bot 連動發言
  tab1, tab2 = st.tabs(["📊 網站狀態與跑馬燈", "🤖 Discord Bot 發言"])

  # --- Tab 1: 網站狀態更新 ---
  with tab1:
    current_info = status_manager.get_status_info()
    status_options = ["🟢 上線", "🟡 維修中", "🔴 故障"]
    current_index = status_options.index(current_info["status"])

    with st.form("update_status_form"):
      new_status = st.radio(
          "請選擇欲變更的網站狀態：",
          options=status_options,
          index=current_index,
      )
      ticker_input = st.text_input(
          "跑馬燈公告內容（上限 60 字，留空則隱藏）：",
          value=current_info["ticker"],
          max_chars=60,
      )
      notice_input = st.text_area(
          "自訂補充公告 / 預計恢復時間（可留空）：",
          value=current_info["notice"],
      )

      # 勾選框：更新狀態時是否同步推播至 Discord
      sync_discord = st.checkbox("📢 同步將狀態變更發送至 Discord")

      submit_update = st.form_submit_button("更新設定", type="primary")

      if submit_update:
        status_manager.set_status(new_status, notice_input, ticker_input)
        st.success("網站設定已成功更新！")

        # 若勾選同步推播
        if sync_discord:
          discord_token = st.session_state.get("dc_bot_token", "")
          discord_channel = st.session_state.get("dc_channel_id", "")

          if discord_token and discord_channel:
            msg = f"**【系統狀態更新公告】**\n目前狀態：{new_status}\n"
            if ticker_input:
              msg += f"跑馬燈：{ticker_input}\n"
            if notice_input:
              msg += f"詳細說明：{notice_input}"

            ok, res_msg = send_discord_message(
                discord_token, discord_channel, msg
            )
            if ok:
              st.success(f"Discord 同步推播成功：{res_msg}")
            else:
              st.error(f"Discord 同步推播失敗：{res_msg}")
          else:
            st.warning(
                "請先至「🤖 Discord Bot 發言」分頁設定 Bot Token 與頻道 ID！"
            )

        st.rerun()

  # --- Tab 2: Discord Bot 連動發言控制 ---
  with tab2:
    st.markdown("#### ⚙️ Discord 設定 (SESSION 暫存)")

    # 允許管理員輸入 Bot Token 與 頻道 ID
    saved_token = st.secrets.get("DISCORD_BOT_TOKEN", "")
    dc_bot_token = st.text_input(
        "Discord Bot Token：",
        value=st.session_state.get("dc_bot_token", saved_token),
        type="password",
        help="輸入您在 Discord Developer Portal 取得的 Bot Token",
    )

    dc_channel_id = st.text_input(
        "目標頻道 ID (Channel ID)：",
        value=st.session_state.get("dc_channel_id", ""),
        placeholder="例如：123456789012345678",
        help="在 Discord 開啟開發者模式後，右鍵點擊頻道名稱即可複製頻道 ID",
    )

    # 將輸入寫入 Session State
    st.session_state["dc_bot_token"] = dc_bot_token
    st.session_state["dc_channel_id"] = dc_channel_id

    st.markdown("---")
    st.markdown("#### 💬 發送廣播訊息")

    with st.form("discord_message_form"):
      dc_message = st.text_area(
          "發送至 Discord 頻道的訊息內容：",
          placeholder="請輸入要讓機器人發送的公告文字...",
      )
      send_btn = st.form_submit_button("🚀 以 Bot 身份發送訊息", type="primary")

      if send_btn:
        if not dc_bot_token or not dc_channel_id:
          st.error("請先填寫 Discord Bot Token 與 頻道 ID！")
        elif not dc_message.strip():
          st.warning("訊息內容不可空白！")
        else:
          success, msg = send_discord_message(
              dc_bot_token, dc_channel_id, dc_message
          )
          if success:
            st.success(msg)
          else:
            st.error(msg)

  # 歷史紀錄與登出
  st.markdown("---")
  with st.expander("📜 查看狀態變更歷史紀錄"):
    st.table(status_manager.get_logs())

  if st.button("登出後台"):
    st.session_state["logged_in"] = False
    st.success("已成功登出。")
    st.rerun()