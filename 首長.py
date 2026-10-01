import hashlib
import os
import threading
import asyncio
import requests
import streamlit as st
import discord

# 設定網頁標題與圖示
st.set_page_config(
    page_title="人事部勞工運行狀態中心", page_icon="📊", layout="centered"
)

# 隱藏 Streamlit選單與頁尾
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppHeader {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# ==============================================================================
# 【區塊 1】DISCORD API 模組 (手動發送/刪除訊息)
# ==============================================================================
class DiscordAPI:

  @staticmethod
  def send_message(bot_token: str, channel_id: str, message_text: str):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {bot_token.strip()}",
        "Content-Type": "application/json",
    }
    try:
      response = requests.post(
          url, json={"content": message_text}, headers=headers, timeout=10
      )
      if response.status_code in [200, 201]:
        msg_id = response.json().get("id", "無紀錄")
        return True, f"訊息已成功發送！ (訊息 ID: `{msg_id}`)"
      error_msg = response.json().get("message", "未知錯誤")
      return False, f"發送失敗 (HTTP {response.status_code}): {error_msg}"
    except Exception as e:
      return False, f"連線異常：{str(e)}"

  @staticmethod
  def delete_message(bot_token: str, channel_id: str, message_id: str):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id.strip()}"
    headers = {"Authorization": f"Bot {bot_token.strip()}"}
    try:
      response = requests.delete(url, headers=headers, timeout=10)
      if response.status_code == 204:
        return True, f"訊息 ID `{message_id}` 已成功刪除！"
      elif response.status_code == 404:
        return False, "刪除失敗：找不到該訊息或已被刪除。"
      elif response.status_code == 403:
        return False, "刪除失敗：Bot 缺少『管理訊息 (Manage Messages)』權限。"
      try:
        error_msg = response.json().get("message", "未知錯誤")
      except Exception:
        error_msg = response.text or "未知錯誤"
      return False, f"刪除失敗 (HTTP {response.status_code}): {error_msg}"
    except Exception as e:
      return False, f"連線異常：{str(e)}"


# ==============================================================================
# 【區塊 2】全域記憶體共享狀態與緩存 (使用 @st.cache_resource)
# ==============================================================================
class StatusManagerV3:

  def __init__(self):
    self.current_status = "🟢 上線"
    self.notice_message = ""
    self.ticker_text = (
        "🎉 歡迎來到人事部勞工運行狀態中心！系統目前正常運作中。"
    )
    self.logs = []

    # 記憶體緩存：敏感字與頻道 ID
    self.forbidden_words = ["垃圾", "詐騙", "違規"]
    self.monitored_channel_id = ""

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

  # 記憶體緩存讀寫方法
  def set_forbidden_words(self, words_list: list):
    self.forbidden_words = [w.strip() for w in words_list if w.strip()]

  def get_forbidden_words(self):
    return self.forbidden_words

  def set_monitored_channel(self, channel_id: str):
    self.monitored_channel_id = channel_id.strip()

  def get_monitored_channel(self):
    return self.monitored_channel_id


@st.cache_resource
def get_status_manager():
  return StatusManagerV3()


status_manager = get_status_manager()


# ==============================================================================
# 【區塊 3】實時 Discord 監控 Bot (背景執行緒運作，直接讀取記憶體緩存)
# ==============================================================================
class DiscordMonitorClient(discord.Client):

  async def on_ready(self):
    print(f"✅ 背景 Discord 監控機器人已啟動：{self.user}")

  async def on_message(self, message):
    if message.author.bot:
      return

    # 直接從記憶體緩存讀取最新設定
    target_channel_id = status_manager.get_monitored_channel()
    forbidden_words = status_manager.get_forbidden_words()

    if target_channel_id and str(message.channel.id) == target_channel_id:
      for word in forbidden_words:
        if word and word in message.content:
          try:
            await message.delete()
          except Exception as e:
            print(f"無法刪除訊息: {e}")

          warning_msg = (
              f"⚠️ {message.author.mention} **【違規發言警告】**\n"
              f"偵測到您的發言包含禁止字詞（`{word}`），訊息已被自動刪除！"
          )
          await message.channel.send(warning_msg)
          break


def run_bot_in_thread(token: str):
  """在背景 Thread 中跑 asyncio event loop"""
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  intents = discord.Intents.default()
  intents.message_content = True

  client = DiscordMonitorClient(intents=intents)
  try:
    loop.run_until_complete(client.start(token))
  except Exception as e:
    print(f"Discord Bot 背景運行異常: {e}")


def start_discord_bot_thread(token: str):
  if not token:
    return False, "Bot Token 不能為空！"

  # 避免重複啟動多個 Bot 執行緒
  if "bot_thread_started" not in st.session_state:
    st.session_state["bot_thread_started"] = False

  if not st.session_state["bot_thread_started"]:
    t = threading.Thread(
        target=run_bot_in_thread, args=(token,), daemon=True
    )
    t.start()
    st.session_state["bot_thread_started"] = True
    return True, "背景監控機器人已成功啟動！"
  return True, "背景監控機器人已在運行中。"


# ==============================================================================
# 【區塊 4】安全驗證與登入狀態
# ==============================================================================
def check_password(password_input):
  secret_password = st.secrets.get("ADMIN_PASSWORD") or os.environ.get(
      "ADMIN_PASSWORD", "admin"
  )
  hash_input = hashlib.sha256(password_input.encode()).hexdigest()
  hash_secret = hashlib.sha256(secret_password.encode()).hexdigest()
  return hash_input == hash_secret


if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False


# ==============================================================================
# 【區塊 5】前台展示區
# ==============================================================================
st.title("🌐 BOT運行狀態")


@st.fragment(run_every=5)
def render_status_display():
  info = status_manager.get_status_info()
  current_status, notice, ticker = (
      info["status"],
      info["notice"],
      info["ticker"],
  )

  if ticker:
    st.markdown(
        f"""
            <style>
            .ticker-box {{
                width: 100%; background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-left: 5px solid #ff4b4b; border-radius: 8px;
                padding: 12px 0; margin-bottom: 20px;
                overflow: hidden; position: relative;
            }}
            .ticker-text {{
                display: inline-block; white-space: nowrap;
                animation: marquee 16s linear infinite;
                font-size: 15px; font-weight: 600; line-height: 1.5;
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
        "### 🟢 系統正常運行中 (Online)\n目前所有服務皆可正常存取。"
    )
  elif current_status == "🟡 維修中":
    st.warning(
        "### 🟡 系統定期維修中 (Maintenance)\n正在進行例行維護以提升服務品質，造成不便請見諒。"
    )
  elif current_status == "🔴 故障":
    st.error(
        "### 🔴 系統突發故障 (Down)\n服務目前遭遇異常，工程師已收到通知並正搶修中。"
    )

  if notice:
    st.info(f"📌 **詳細說明：** {notice}")

  st.caption("🔄 狀態每 5 秒自動同步更新中...")


render_status_display()
st.divider()


# ==============================================================================
# 【區塊 6】後台介面分頁元件
# ==============================================================================
def render_tab_status():
  """分頁 1：網站狀態與跑馬燈管理"""
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

    if st.form_submit_button("更新設定", type="primary"):
      status_manager.set_status(new_status, notice_input, ticker_input)
      st.success("網站設定已成功更新！")
      st.rerun()


def render_tab_discord():
  """分頁 2：Discord Bot 廣播與刪除"""
  st.markdown("#### ⚙️ Discord 連線設定")

  saved_token = st.secrets.get("DISCORD_BOT_TOKEN", "")
  dc_bot_token = st.text_input(
      "Discord Bot Token：",
      value=st.session_state.get("dc_bot_token", saved_token),
      type="password",
  )
  dc_channel_id = st.text_input(
      "預設頻道 ID (Channel ID)：",
      value=st.session_state.get("dc_channel_id", ""),
      placeholder="例如：123456789012345678",
  )

  st.session_state["dc_bot_token"] = dc_bot_token
  st.session_state["dc_channel_id"] = dc_channel_id

  st.markdown("---")

  st.markdown("#### 💬 發送廣播訊息")
  with st.form("discord_message_form"):
    dc_message = st.text_area(
        "發送內容：", placeholder="請輸入要讓機器人發送的公告文字..."
    )
    if st.form_submit_button("🚀 發送訊息", type="primary"):
      if not dc_bot_token or not dc_channel_id:
        st.error("請先填寫 Token 與頻道 ID！")
      elif not dc_message.strip():
        st.warning("訊息內容不可空白！")
      else:
        ok, msg = DiscordAPI.send_message(
            dc_bot_token, dc_channel_id, dc_message
        )
        if ok:
          st.success(msg)
        else:
          st.error(msg)

  st.markdown("---")

  st.markdown("#### 🗑️ 刪除指定訊息")
  with st.form("discord_delete_form"):
    delete_msg_id = st.text_input(
        "要刪除的訊息 ID：", placeholder="例如：1234567890123456789"
    )
    if st.form_submit_button("🗑️ 刪除訊息"):
      if not dc_bot_token or not dc_channel_id:
        st.error("請先填寫 Token 與頻道 ID！")
      elif not delete_msg_id.strip():
        st.warning("請輸入欲刪除的訊息 ID！")
      else:
        ok, msg = DiscordAPI.delete_message(
            dc_bot_token, dc_channel_id, delete_msg_id
        )
        if ok:
          st.success(msg)
        else:
          st.error(msg)


def render_tab_moderation():
  """分頁 3：禁止字詞與受監控頻道設定（純緩存，無文字檔）"""
  st.markdown("#### 🛡️ Discord 頻道敏感詞監控設定")
  st.info(
      "💡 設定會直接存放在**記憶體緩存**中，完全不需要建立任何外部檔案。"
  )

  current_monitored_channel = status_manager.get_monitored_channel()
  current_words_str = ", ".join(status_manager.get_forbidden_words())

  with st.form("moderation_config_form"):
    monitored_channel_input = st.text_input(
        "受監控頻道 ID (Monitored Channel ID)：",
        value=current_monitored_channel,
        placeholder="例如：123456789012345678",
    )
    words_input = st.text_area(
        "禁止字詞庫（請用英文逗點 `,` 分隔）：",
        value=current_words_str,
        help="例如：垃圾, 詐騙, 廣告, 違規文字",
    )

    if st.form_submit_button("💾 儲存並更新緩存", type="primary"):
      words_list = [w.strip() for w in words_input.split(",") if w.strip()]
      status_manager.set_forbidden_words(words_list)
      status_manager.set_monitored_channel(monitored_channel_input)
      st.success("✅ 設定已成功更新至記憶體緩存！")

  st.markdown("---")
  st.markdown("#### 🚀 啟動背景實時監控 Bot")

  bot_token = st.session_state.get("dc_bot_token", "")
  if st.button("▶️ 啟動背景監控機器人"):
    if not bot_token:
      st.error("請先至『🤖 Discord Bot 管理』頁籤填寫 Bot Token！")
    else:
      ok, msg = start_discord_bot_thread(bot_token)
      if ok:
        st.success(f"✅ {msg}")
      else:
        st.error(f"❌ {msg}")


# ==============================================================================
# 【區塊 7】後台主流程 (3個頁籤)
# ==============================================================================
st.subheader("🔒 管理員控制台")

if not st.session_state["logged_in"]:
  with st.form("login_form"):
    password_input = st.text_input("請輸入管理員密碼：", type="password")
    if st.form_submit_button("登入後台"):
      if check_password(password_input):
        st.session_state["logged_in"] = True
        st.success("登入成功！")
        st.rerun()
      else:
        st.error("密碼錯誤，請再試一次。")
else:
  st.info("🔓 您已成功登入管理後台。")

  tab1, tab2, tab3 = st.tabs([
      "📊 網站狀態與跑馬燈",
      "🤖 Discord Bot 管理",
      "🛡️ 敏感詞與頻道監控",
  ])
  with tab1:
    render_tab_status()
  with tab2:
    render_tab_discord()
  with tab3:
    render_tab_moderation()

  st.markdown("---")
  with st.expander("📜 查看狀態變更歷史紀錄"):
    st.table(status_manager.get_logs())

  if st.button("登出後台"):
    st.session_state["logged_in"] = False
    st.success("已成功登出。")
    st.rerun()