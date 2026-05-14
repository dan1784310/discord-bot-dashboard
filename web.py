from flask import Flask, redirect, request, session
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# =====================
# ENV VARIABLES
# =====================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# 🔴 CHANGE THIS TO YOUR REAL RENDER URL
REDIRECT_URI = "https://discord-bot-dashboard-1-2cw0.onrender.com/callback"

DISCORD_API = "https://discord.com/api"


# =====================
# SAFETY CHECK
# =====================
if not CLIENT_ID or not CLIENT_SECRET:
    print("WARNING: Missing CLIENT_ID or CLIENT_SECRET in environment variables")


# =====================
# LOGIN PAGE
# =====================
@app.route("/")
def home():
    return '<a href="/login">Login with Discord</a>'


@app.route("/login")
def login():
    return redirect(
        "https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=identify%20guilds"
    )


# =====================
# OAUTH CALLBACK
# =====================
@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return "No code provided", 400

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Get token
    r = requests.post(
        f"{DISCORD_API}/oauth2/token",
        data=data,
        headers=headers
    )

    token = r.json().get("access_token")

    if not token:
        return f"Token error: {r.json()}", 400

    # Get user info
    user = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    # Get guilds (servers)
    guilds = requests.get(
        f"{DISCORD_API}/users/@me/guilds",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    session["user"] = user
    session["guilds"] = guilds

    return redirect("/dashboard")


# =====================
# DASHBOARD (SERVER SELECTOR)
# =====================
@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    guilds = session.get("guilds", [])

    if not user:
        return redirect("/")

    html = f"""
    <h1>Welcome {user['username']}</h1>
    <h2>Your Servers:</h2>
    <hr>
    """

    for guild in guilds:
        html += f"""
        <div style="padding:10px;margin:10px;border:1px solid #ccc">
            <b>{guild['name']}</b><br>
            <a href="/server/{guild['id']}">Manage Server</a>
        </div>
        """

    return html


# =====================
# SERVER SETTINGS PAGE
# =====================
@app.route("/server/<guild_id>")
def server(guild_id):
    return f"""
    <h1>Server Settings</h1>
    <p>Guild ID: {guild_id}</p>

    <button>Change Prefix</button><br><br>
    <button>Toggle Anti-Link</button><br><br>
    <button>Toggle Leveling</button><br><br>

    <a href="/dashboard">Back</a>
    """


# =====================
# RUN APP (RENDER SAFE)
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
# =====================
# RUN APP (RENDER SAFE)
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
