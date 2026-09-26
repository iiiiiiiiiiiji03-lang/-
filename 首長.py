import streamlit as st
import hashlib
import os

# 設定網頁標題與圖示
st.set_page_config(page_title="網站運行狀態中心", page_icon="📊", layout="centered")

# ==========================================
# 0. 全域共享狀態管理（解決 F5 與 跨電腦同步 問題）
# ==========================================
class StatusManager:
    """用來在伺服器記憶體中保存狀態的類別"""
    def __init__(self):
        self.current_status = "🟢 上線"
    
    def set_status(self, new_status):
        self.current_status = new_status
        
    def get_status(self):
        return self.current_status

@st.cache_resource
def get_status_manager():
    """利用 Streamlit 快取機制，讓所有使用者、所有分頁共享同一個物件執行個體"""
    return StatusManager()

# 取得全域唯一的狀態管理器
status_manager = get_status_manager()

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
        st.error("❌ 系統錯誤：未設定管理員密碼。請確認您已在 Streamlit 後台的「秘密」欄位中填寫 ADMIN_PASSWORD。")
        return False
        
    hash_input = hashlib.sha256(password_input.encode()).hexdigest()
    hash_secret = hashlib.sha256(secret_password.encode()).hexdigest()
    return hash_input == hash_secret

# ==========================================
# 2. 初始化登入狀態 (登入狀態仍保持每個人獨立)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ==========================================
# 3. 前台：使用者查看狀態介面
# ==========================================
st.title("🌐 網站運行狀態中心")
st.subheader("目前服務狀態")

# 從全域管理器取得當前狀態
current_status = status_manager.get_status()

if current_status == "🟢 上線":
    st.success("### 🟢 系統正常運行中 (Online)\n目前所有服務皆可正常存取，請安心使用。")
elif current_status == "🟡 維修中":
    st.warning("### 🟡 系統定期維修中 (Maintenance)\n我們正在進行例行性維護以提升服務品質，預計不久後恢復，造成不便敬請見諒。")
elif current_status == "🔴 故障":
    st.error("### 🔴 系統突發故障 (Down)\n核心服務目前遭遇異常，技術團隊已收到通知並正全力搶修中，請稍後再試。")

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
    st.info("🔓 您已成功登入，可以自由切換網站狀態。")
    
    status_options = ["🟢 上線", "🟡 維修中", "🔴 故障"]
    current_index = status_options.index(status_manager.get_status())
    
    new_status = st.radio(
        "請選擇欲變更的網站狀態：",
        options=status_options,
        index=current_index
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("更新網站狀態", type="primary"):
            # 將新狀態寫入全域管理器（所有人和 F5 都會同步更新）
            status_manager.set_status(new_status)
            st.success(f"狀態已成功更新為：{new_status}")
            st.rerun()
            
    with col2:
        if st.button("登出後台"):
            st.session_state["logged_in"] = False
            st.success("已成功登出。")
            st.rerun()
