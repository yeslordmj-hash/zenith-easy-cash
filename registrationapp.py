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
ADMIN_SECRET_ROUTE = "zenith-secret-admin"

# --- TELEGRAM CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"


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


# --- HTML & CSS TEMPLATES ---

POPUP_MODAL_CSS = """
<style>
    /* Popup Modal Animation Styles */
    .modal-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.7); display: flex; justify-content: center; align-items: center;
        z-index: 9999; animation: fadeIn 0.3s ease-in-out;
    }
    .modal-card {
        background: #1e1e1e; color: #fff; width: 90%; max-width: 400px;
        padding: 30px; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        animation: scaleUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .icon-container {
        width: 90px; height: 90px; margin: 0 auto 20px auto;
        background: #2e7d32; border-radius: 50%; display: flex; justify-content: center; align-items: center;
        box-shadow: 0 0 20px rgba(46, 125, 50, 0.6);
        animation: rotateIn 0.6s ease-in-out;
    }
    .checkmark {
        font-size: 45px; color: white; font-weight: bold;
    }
    .modal-card h3 { color: #4caf50; font-size: 24px; margin-bottom: 10px; }
    .modal-card p { color: #ccc; font-size: 15px; line-height: 1.5; margin-bottom: 20px; }
    .modal-btn {
        background: linear-gradient(135deg, #2e7d32, #4caf50); color: white; border: none;
        padding: 12px 25px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.4); transition: opacity 0.2s;
    }
    .modal-btn:hover { opacity: 0.9; }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes scaleUp { from { transform: scale(0.7); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    @keyframes rotateIn { 
        0% { transform: rotate(-90deg) scale(0); opacity: 0; } 
        100% { transform: rotate(0deg) scale(1); opacity: 1; } 
    }
</style>

<div class="modal-overlay" id="successModal">
    <div class="modal-card">
        <div class="icon-container">
            <div class="checkmark">✓</div>
        </div>
        <h3 id="modalTitle">{{ modal_title }}</h3>
        <p id="modalDesc">{{ modal_desc|safe }}</p>
        <button class="modal-btn" onclick="closeModal()">Continue</button>
    </div>
</div>

<script>
    function closeModal() {
        document.getElementById('successModal').style.display = 'none';
    }
</script>
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
        .nav-links { text-align: center; margin-top: 20px; font-size: 14px; }
        .nav-links a { color: #028a0f; text-decoration: none; font-weight: bold; margin: 0 10px; }
        .ticker-wrap { background: #111; color: #0f0; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 13px; margin-bottom: 20px; text-align: center; overflow: hidden; white-space: nowrap; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Zenith Easy Cash Ghana</h2>
        <h3>Online Investor Registration & Portal</h3>

        <div class="ticker-wrap" id="payoutTicker">
            <span>Live Payouts: Loading recent withdrawals...</span>
        </div>

        <div class="instructions">
            <strong>Guidelines:</strong>
            <ul>
                <li>Minimum Investment: <strong>200 GHs</strong> | Maximum Investment: <strong>500,000 GHs</strong></li>
                <li>Duration: <strong>7 Days Maturity</strong> (Top-ups & Multiple Accounts Allowed!)</li>
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
                <label>Phone Number:</label>
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
                <input type="text" name="transaction_id" placeholder="Enter MoMo Transaction ID (Optional if uploading screenshot)">
                <div style="margin-top: 8px;">
                    <input type="file" name="payment_screenshot" accept="image/*" style="border:none; padding:0;">
                    <small style="color: #666;">Upload payment screenshot image</small>
                </div>
            </div>
            <button type="submit">Submit Registration & Investment</button>
        </form>

        <div class="nav-links">
            <a href="{{ url_for('track') }}">🔍 Track / Top-Up Investment</a>
        </div>
    </div>

    {% if show_modal %}
        {{ popup_html|safe }}
    {% endif %}

    <script>
        const ghanaNames = ["Kwame Mensah", "Abena Osei", "Kofi Boateng", "Afia Serwaa", "Yaw Ansah", "Akosua Frimpong", "Esi Dapaah", "Kojo Addo", "Ama Serwaa", "Nii Armah"];
        const towns = ["Accra", "Kumasi", "Takoradi", "Tamale", "Cape Coast", "Sunyani", "Ho", "Koforidua"];
        
        function updateTicker() {
            const randomName = ghanaNames[Math.floor(Math.random() * ghanaNames.length)];
            const randomTown = towns[Math.floor(Math.random() * towns.length)];
            const randomAmount = (Math.floor(Math.random() * 4800) + 200).toLocaleString();
            const tickerEl = document.getElementById('payoutTicker');
            tickerEl.innerHTML = `🟢 <b>LIVE PAYOUT:</b> ${randomName} from ${randomTown} successfully withdrew <b>GHs ${randomAmount}</b> via MoMo!`;
        }
        setInterval(updateTicker, 5000);
        updateTicker();
    </script>
</body>
</html>
"""

TRACK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Track & Manage Investments - Zenith Easy Cash</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 700px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2e7d32; color: white; border: none; padding: 12px; width: 100%; font-size: 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1b5e20; }
        .card { background: #f1f8e9; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 5px solid #2e7d32; line-height: 1.5; }
        .flash { background: #ffebee; color: #c62828; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; }
        .back { text-align: center; margin-top: 20px; }
        .back a { color: #028a0f; text-decoration: none; font-weight: bold; }
        .btn-withdraw { background: #028a0f; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px; }
        .btn-topup { background: #ffa000; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; margin-top: 10px; border: none; cursor: pointer;}
        .topup-box { background: #fff8e1; padding: 10px; margin-top: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Track & Manage Your Investments</h2>
        <p style="text-align: center; color: #666; font-size: 14px;">Enter your phone number to view all your active investment accounts, countdowns, and top-ups.</p>

        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}

        <form method="POST">
            <div class="form-group">
                <label>Phone Number:</label>
                <input type="text" name="number" value="{{ searched_number }}" required placeholder="Enter your registered phone number">
            </div>
            <button type="submit">Search Accounts</button>
        </form>

        {% if investors %}
            <h3 style="margin-top: 30px; text-align:left; color:#333;">Found Accounts ({{ investors|length }})</h3>
            {% for inv in investors %}
            <div class="card">
                <p><strong>Name:</strong> {{ inv.name }}</p>
                <p><strong>Investment Amount:</strong> {{ inv.amount }} GHs</p>
                <p><strong>Payment Proof / ID:</strong> {{ inv.transaction_id }}</p>
                <p><strong>Job / Region:</strong> {{ inv.work }} / {{ inv.region }}</p>
                <p><strong>Registered On:</strong> {{ inv.date_time }}</p>
                <p><strong>Maturity Date:</strong> <span style="color: #028a0f; font-weight: bold;">{{ inv.maturity_date }}</span></p>
                <p><strong>Status:</strong> <span style="color: #e65100; font-weight: bold;">{{ inv.status }}</span></p>
                
                {% if inv.status == 'Payment Confirmed & Active' %}
                <form action="{{ url_for('topup', index=inv.global_idx) }}" method="POST" class="topup-box" enctype="multipart/form-data">
                    <label style="font-size:12px;">Top-Up Amount (GHs):</label>
                    <input type="number" name="topup_amount" min="10" step="0.01" required placeholder="Enter amount to add" style="padding:6px; margin-bottom:5px;">
                    <label style="font-size:11px;">Top-up Transaction ID or Screenshot:</label>
                    <input type="text" name="topup_proof" placeholder="Transaction ID or leave blank" style="padding:5px; margin-bottom:5px; font-size:12px;">
                    <input type="file" name="topup_screenshot" accept="image/*" style="font-size:11px; margin-bottom:5px;">
                    <button type="submit" class="btn-topup" style="width:auto; padding:6px 12px; font-size:13px; display:block;">Submit Top-Up</button>
                </form>
                {% endif %}

                {% if inv.can_withdraw and inv.status != 'Withdrawal Requested' and inv.status != 'Withdrawn Completed' %}
                    <a href="{{ url_for('withdraw', index=inv.global_idx) }}" class="btn-withdraw">📥 Request Withdrawal Now</a>
                {% elif inv.status == 'Withdrawal Requested' %}
                    <p style="color: #2e7d32; font-weight: bold; margin-top:10px;">⏳ Withdrawal Requested. Admin is processing payment.</p>
                {% elif inv.status == 'Withdrawn Completed' %}
                    <p style="color: #555; font-weight: bold; margin-top:10px;">✅ Investment Completed & Paid Out.</p>
                {% endif %}
            </div>
            {% endfor %}
        {% elif searched_number %}
            <p style="text-align:center; color:#c62828; margin-top:20px;">No investment records found for phone number: <strong>{{ searched_number }}</strong></p>
        {% endif %}

        <div class="back">
            <a href="{{ url_for('index') }}">← Back to Registration Page</a>
        </div>
    </div>

    {% if show_modal %}
        {{ popup_html|safe }}
    {% endif %}
</body>
</html>
"""

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
        .container { max-width: 1100px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; float: left; margin-top: 0; }
        .logout { float: right; }
        .logout a { background: #c62828; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; }
        .settings-box { background: #fff8e1; border: 1px solid #ffa000; padding: 15px; margin-bottom: 25px; border-radius: 5px; clear: both; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 13px; }
        th { background-color: #2e7d32; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .btn-action { background: #2e7d32; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 12px; border: none; cursor: pointer; display: inline-block; margin: 2px;}
        .btn-payout { background: #d32f2f; }
        .status-pending { color: #e65100; font-weight: bold; }
        .clear { clear: both; }
        img.proof-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #ccc; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div>
            <h2>Admin Dashboard</h2>
            <div class="logout">
                <a href="{{ url_for('admin_logout') }}">Logout</a>
            </div>
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

        <h3>Registered Investors & Active Accounts</h3>
        <table>
            <thead>
                <tr>
                    <th>Name / Number</th>
                    <th>Amount & Proof</th>
                    <th>Job / Region</th>
                    <th>Registered</th>
                    <th>Maturity</th>
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
                            <small>ID: {{ inv.transaction_id }}</small><br>
                            {% if inv.screenshot %}
                                <a href="{{ url_for('uploaded_file', filename=inv.screenshot) }}" target="_blank">
                                    <img src="{{ url_for('uploaded_file', filename=inv.screenshot) }}" class="proof-thumb" title="Click to view full screenshot">
                                </a>
                            {% endif %}
                        </td>
                        <td>{{ inv.work }}<br><small>{{ inv.region }}</small></td>
                        <td>{{ inv.date_time }}</td>
                        <td>{{ inv.maturity_date }}</td>
                        <td><span class="status-pending">{{ inv.status }}</span></td>
                        <td>
                            {% if inv.status == 'Pending Admin Payment Confirmation' %}
                                <form action="{{ url_for('confirm_payment', index=idx) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn-action">Confirm Payment</button>
                                </form>
                            {% elif inv.status == 'Withdrawal Requested' %}
                                <form action="{{ url_for('complete_withdrawal', index=idx) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn-action btn-payout">Pay Out & Close</button>
                                </form>
                            {% else %}
                                <span>{{ inv.status }}</span>
                            {% html_placeholder="" %}
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

      investor_data = {
          "name": request.form["name"],
          "number": request.form["number"].strip(),
          "amount": amount,
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

      # Send Telegram Alert
      alert_msg = (
          f"🚨 <b>NEW INVESTMENT REGISTRATION</b>\n\n"
          f"👤 <b>Name:</b> {investor_data['name']}\n"
          f"📞 <b>Number:</b> {investor_data['number']}\n"
          f"💰 <b>Amount:</b> GHs {investor_data['amount']}\n"
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

      # Render index with success modal popup
      modal_title = "Successfully Registered!"
      modal_desc = f"Your investment of <b>GHs {amount:,.2f}</b> has been submitted successfully.<br>Waiting for Admin confirmation."
      popup_html = POPUP_MODAL_CSS.replace("{{ modal_title }}", modal_title).replace(
          "{{ modal_desc }}", modal_desc
      )

      return render_template_string(
          HTML_TEMPLATE,
          settings=settings,
          show_modal=True,
          popup_html=popup_html,
      )

    except ValueError:
      flash("Invalid input. Please check your data.")
      return redirect(url_for("index"))

  return render_template_string(
      HTML_TEMPLATE, settings=settings, show_modal=False
  )


@app.route("/track", methods=["GET", "POST"])
def track():
  investors_found = []
  searched_number = ""
  show_modal = False
  popup_html = ""

  if request.method == "POST" or "number" in request.args:
    searched_number = request.form.get("number", "").strip() or request.args.get(
        "number", ""
    ).strip()
    investors = load_investors()

    now = datetime.now()
    for idx, inv in enumerate(investors):
      if inv.get("number") == searched_number:
        inv_copy = inv.copy()
        inv_copy["global_idx"] = idx
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

    if not investors_found and searched_number:
      flash("No investment record found for this phone number.")

    # Check if redirected from a successful action
    action = request.args.get("action")
    amt = request.args.get("amt", "")
    if action == "topup":
      show_modal = True
      modal_title = "Top-Up Successful!"
      modal_desc = f"Your top-up of <b>GHs {amt}</b> has been successfully added to your investment account!"
      popup_html = POPUP_MODAL_CSS.replace(
          "{{ modal_title }}", modal_title
      ).replace("{{ modal_desc }}", modal_desc)
    elif action == "withdraw":
      show_modal = True
      modal_title = "Withdrawal Requested!"
      modal_desc = f"Your withdrawal request for <b>GHs {amt}</b> has been submitted successfully! Admin will pay out shortly."
      popup_html = POPUP_MODAL_CSS.replace(
          "{{ modal_title }}", modal_title
      ).replace("{{ modal_desc }}", modal_desc)

  return render_template_string(
      TRACK_TEMPLATE,
      investors=investors_found,
      searched_number=searched_number,
      show_modal=show_modal,
      popup_html=popup_html,
  )


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
        save_all_investors(investors)

        proof_text = (
            topup_proof if topup_proof else ("Screenshot attached" if filename else "None")
        )
        send_telegram_alert(
            f"📈 <b>INVESTMENT TOP-UP RECEIVED</b>\n\n"
            f"👤 <b>Name:</b> {inv['name']}\n"
            f"📞 <b>Number:</b> {inv['number']}\n"
            f"➕ <b>Added:</b> GHs {topup_amt}\n"
            f"🧾 <b>Proof:</b> {proof_text}\n"
            f"💰 <b>New Total:</b> GHs {inv['amount']}",
            os.path.join(app.config["UPLOAD_FOLDER"], filename)
            if filename
            else None,
        )
        return redirect(
            url_for("track", number=inv["number"], action="topup", amt=topup_amt)
        )
    except ValueError:
      flash("Invalid top-up amount.")

    return redirect(url_for("track", number=inv["number"]))
  return redirect(url_for("track"))


@app.route("/withdraw/<int:index>", methods=["GET"])
def withdraw(index):
  investors = load_investors()
  if 0 <= index < len(investors):
    inv = investors[index]
    now = datetime.now()
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
            f"💰 <b>Amount Due:</b> GHs {inv['amount']}"
        )
        return redirect(
            url_for(
                "track",
                number=inv["number"],
                action="withdraw",
                amt=inv["amount"],
            )
        )
    except Exception:
      pass
    return redirect(url_for("track", number=inv["number"]))
  return redirect(url_for("track"))


# --- SECRET ADMIN ROUTES ---


@app.route(f"/{ADMIN_SECRET_ROUTE}", methods=["GET", "POST"])
def admin_login():
  if request.method == "POST":
    password = request.form.get("password")
    if password == ADMIN_PASSWORD:
      session["admin_logged_in"] = True
      return redirect(url_for("admin_dashboard"))
    else:
      flash("Incorrect admin password.")
      return redirect(url_for(f"admin_login"))

  return render_template_string(ADMIN_LOGIN_TEMPLATE)


@app.route("/admin-dashboard")
def admin_dashboard():
  if not session.get("admin_logged_in"):
    return redirect(url_for("admin_login"))

  investors = load_investors()
  settings = load_settings()
  return render_template_string(
      ADMIN_DASHBOARD_TEMPLATE,
      investors=investors,
      settings=settings,
      enumerate=enumerate,
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


@app.route("/admin-logout")
def admin_logout():
  session.pop("admin_logged_in", None)
  return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5001, debug=True)
