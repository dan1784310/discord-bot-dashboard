from flask import Flask, redirect, request, session
import requests
import os

app = Flask(__name__)

# MUST be set in Render env vars (not hardcoded)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# 🔴 MUST match Discord + Render exactly
REDIRECT_URI = "https://discord-bot-dashboard-1-2cw0.onrender.com/callback"

DISCORD_API = "https://discord.com/api"


# =====================
# HOME
# =====================
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return '<a href="/login">Login with Discord</a>'


# =====================
# LOGIN
# =====================
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
# CALLBACK (SAFE VERSION)
# =====================
@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return redirect("/")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        # Get token
        r = requests.post(
            f"{DISCORD_API}/oauth2/token",
            data=data,
            headers=headers
        )

        token_data = r.json()
        access_token = token_data.get("access_token")

        if not access_token:
            print("TOKEN ERROR:", token_data)
            return redirect("/")

        # Get user
        user = requests.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        # Get servers
        guilds = requests.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        session.clear()
        session["user"] = user
        session["guilds"] = guilds

        return redirect("/dashboard")

    except Exception as e:
        print("Callback error:", e)
        return redirect("/")


# =====================
# DASHBOARD (SERVER SELECTOR)
# =====================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    user = session["user"]
    guilds = session.get("guilds", [])

    html = f"""
    <h1>Welcome {user['username']}</h1>
    <h2>Your Servers</h2>
    <hr>
    """

    for g in guilds:
        html += f"""
        <div style="padding:10px;margin:10px;border:1px solid #ccc">
            <b>{g['name']}</b><br>
            <a href="/server/{g['id']}">Manage</a>
        </div>
        """

    return html


# =====================
# SERVER PAGE
# =====================
@app.route("/server/<guild_id>")
def server(guild_id):
    if "user" not in session:
        return redirect("/")

    return f"""
    <h1>Server Settings</h1>
    <p>Guild ID: {guild_id}</p>

    <button>Change Prefix</button><br><br>
    <button>Anti-Link</button><br><br>
    <button>Leveling</button><br><br>

    <a href="/dashboard">Back</a>
    """


# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
