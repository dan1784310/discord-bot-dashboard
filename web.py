from flask import Flask, redirect, request, session
import requests
import os

app = Flask(__name__)

# =====================
# REQUIRED SECRET (MUST EXIST IN RENDER)
# =====================
app.secret_key = os.environ["SECRET_KEY"]

# safer session handling for HTTPS (Render)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True
)

# =====================
# ENV VARIABLES
# =====================
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

# MUST MATCH DISCORD DEV PORTAL EXACTLY
REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://discord-bot-dashboard-1-2cw0.onrender.com/callback"
)

DISCORD_API = "https://discord.com/api"


# =====================
# HOME
# =====================
@app.route("/")
def home():
    if session.get("user"):
        return redirect("/dashboard")
    return '<a href="/login">Login with Discord</a>'


# =====================
# LOGIN
# =====================
@app.route("/login")
def login():
    if not CLIENT_ID:
        return "Missing CLIENT_ID", 500

    return redirect(
        "https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=identify%20guilds"
    )


# =====================
# CALLBACK (ROBUST VERSION)
# =====================
@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return redirect("/")

    try:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        r = requests.post(
            f"{DISCORD_API}/oauth2/token",
            data=data,
            headers=headers
        )

        token_json = r.json()
        token = token_json.get("access_token")

        if not token:
            print("TOKEN ERROR:", token_json)
            return redirect("/login")

        user = requests.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {token}"}
        ).json()

        guilds = requests.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"}
        ).json()

        # IMPORTANT: clear + reassign session
        session.clear()
        session["user"] = user
        session["guilds"] = guilds

        return redirect("/dashboard")

    except Exception as e:
        print("Callback crash:", e)
        return redirect("/login")


# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    user = session.get("user")

    if not user:
        return redirect("/login")

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
    if not session.get("user"):
        return redirect("/login")

    return f"""
    <h1>Server Settings</h1>
    <p>Guild ID: {guild_id}</p>

    <button>Change Prefix</button><br><br>
    <button>Anti-Link</button><br><br>
    <button>Leveling</button><br><br>

    <a href="/dashboard">Back</a>
    """


# =====================
# RUN (LOCAL ONLY)
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
