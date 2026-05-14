from flask import Flask, redirect, request
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# =====================
# ENV VARIABLES (Render)
# =====================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# IMPORTANT: replace this with your REAL Render URL after deployment
REDIRECT_URI = "https://discord-bot-dashboard-1-2cw0.onrender.com/callback"

DISCORD_API = "https://discord.com/api"


# =====================
# SAFETY CHECK
# =====================
if not CLIENT_ID or not CLIENT_SECRET:
    raise Exception("Missing CLIENT_ID or CLIENT_SECRET in environment variables")


# =====================
# ROUTES
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

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Get access token
    r = requests.post(
        f"{DISCORD_API}/oauth2/token",
        data=data,
        headers=headers
    )

    token_json = r.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return f"Failed to get access token: {token_json}", 400

    # Get user info
    user = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    return f"Logged in as: {user.get('username', 'Unknown')}"


# =====================
# RUN APP (RENDER SAFE)
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
