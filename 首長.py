import threading
from flask import Flask, jsonify, render_template_string
import discord
from discord.ext import commands

# 1. 初始化 Discord 機器人
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. 初始化 Flask 網頁應用
app = Flask(__name__)

# 簡單的 HTML 範本，用於前端顯示
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Discord 機器人狀態面板</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; background: #2c2f33; color: white; text-align: center; padding-top: 50px; }
        .card { background: #23272a; padding: 20px; display: inline-block; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .status { font-weight: bold; color: #43b581; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🤖 {{ name }} 狀態面板</h2>
        <p>目前狀態: <span class="status">{{ status }}</span></p>
        <p>延遲 (Ping): {{ latency }} ms</p>
        <p>已加入的伺服器總數: {{ guild_count }} 個</p>
    </div>
    <script>
        // 每 5 秒自動重新整理網頁獲取最新狀態
        setTimeout(() => { location.reload(); }, 5000);
    </script>
</body>
</html>
"""

# Flask 路由：顯示狀態網頁
@app.route('/')
def home():
    if bot.is_ready():
        status_info = {
            "name": str(bot.user),
            "status": "線上 (Online)",
            "latency": round(bot.latency * 1000),
            "guild_count": len(bot.guilds)
        }
    else:
        status_info = {
            "name": "未連線機器人",
            "status": "離線 (Offline)",
            "latency": 0,
            "guild_count": 0
        }
    return render_template_string(HTML_TEMPLATE, **status_info)

# Flask 路由：提供 API 接口（供未來擴充或給其他前端讀取）
@app.route('/api/status')
def api_status():
    if bot.is_ready():
        return jsonify({
            "online": True,
            "bot_name": str(bot.user),
            "ping_ms": round(bot.latency * 1000),
            "guilds": len(bot.guilds)
        })
    return jsonify({"online": False, "message": "Bot is not ready yet."})

# 3. Discord 機器人事件
@bot.event
def on_ready():
    print(f"機器人已上線：{bot.user}")

# 4. 建立多線程運行網頁
def run_flask():
    # host="0.0.0.0" 允許外部網路連線，port=5000
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # 先啟動 Flask 網頁線程
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 再啟動 Discord 機器人（請替換成你在 Discord Developer Portal 取得的 Token）
    # 參考教學：https://discord.com/developers/applications
    TOKEN = st.secrets["DISCORD_TOKEN"]
    bot.run(TOKEN)
