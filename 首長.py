import streamlit as st
import hashlib

# 設定網頁標題與圖示
st.set_page_config(page_title="網站運行狀態中心", page_icon="📊", layout="centered")

# ==========================================
# 1. 密碼驗證安全機制
# ==========================================
# 預設的管理密碼雜湊值（明文為: admin123）
# 您可以使用相同的 SHA-256 演算法更換此處的雜湊值來更換密碼
DEFAULT_PASSWORD_HASH = "240982635b8e9744434302316e83815e79602e1a3bc86f0113f848fd86e88a08"

def check_password(password):
    """驗證輸入的密碼是否與預設雜湊值相符"""
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    return input_hash == DEFAULT_PASSWORD_HASH

# ==========================================
# 2. 初始化 Session State (狀態保持)
# ==========================================
# 預設狀態為「上線」
if "site_status" not in st.session_state:
    st.session_state["site_status"] = "🟢 上線"

# 預設登入狀態為「未登入」
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ==========================================
# 3. 前台：使用者查看狀態介面
# ==========================================
st.title("🌐 網站運行狀態中心")
st.subheader("目前服務狀態")

current_status = st.session_state["site_status"]

# 根據不同狀態顯示不同的視覺提示
if current_status == "🟢 上線":
    st.success("### 🟢 系統正常運行中 (Online)\n目前所有服務皆可正常存取，請安心使用。")
elif current_status == "🟡 維修中":
    st.warning("### 🟡 系統定期維修中 (Maintenance)\n我們正在進行例行性維護以提升服務品質，預計不久後恢復，造成不便敬請見見諒。")
elif current_status == "🔴 故障":
    st.error("### 🔴 系統突發故障 (Down)\n核心服務目前遭遇異常，技術團隊已收到通知並正全力搶修中，請稍後再試。")

st.divider()

# ==========================================
# 4. 後台：密碼保護的管理控制台
# ==========================================
st.subheader("🔒 管理員控制台")

# 檢查是否已登入
if not st.session_state["logged_in"]:
    # 未登入：顯示密碼輸入框
    with st.form("login_form"):
        password_input = st.text_input("請輸入管理員密碼：", type="password")
        submit_button = st.form_submit_button("登入後台")
        
        if submit_button:
            if check_password(password_input):
                st.session_state["logged_in"] = True
                st.success("密碼正確！已成功登入管理後台。")
                st.rerun()  # 重新整理頁面以顯示管理功能
            else:
                st.error("密碼錯誤，請再試一次。")
else:
    # 已登入：顯示狀態切換選項與登出按鈕
    st.info("🔓 您已成功登入，可以自由切換網站狀態。")
    
    # 狀態選擇器（自動對應目前的狀態索引）
    status_options = ["🟢 上線", "🟡 維修中", "🔴 故障"]
    current_index = status_options.index(st.session_state["site_status"])
    
    new_status = st.radio(
        "請選擇欲變更的網站狀態：",
        options=status_options,
        index=current_index
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 儲存狀態變更
        if st.button("更新網站狀態", type="primary"):
            st.session_state["site_status"] = new_status
            st.success(f"狀態已成功更新為：{new_status}")
            st.rerun()
            
    with col2:
        # 登出管理員身分
        if st.button("登出後台"):
            st.session_state["logged_in"] = False
            st.success("已成功登出。")
            st.rerun()
