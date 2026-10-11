"""
VOID Studio – OBS-Skript (Werkzeuge → Skripte → +)

Eins für alles:
  · Szenen-Packs verwalten: aus dem GitHub-Repo installieren, aktualisieren, entfernen
  · VOID Twitch Bridge: Alerts, Sounds, Chat, Ziele, letzte Unterstützer, Rückblick, Spiel-Telemetrie
  · IRL: bei Verbindungsabbruch selbst auf „Verbindung weg“ schalten und zurück

Erster Start: Dieses Skript einmal in OBS hinzufügen. Es kopiert sich nach %APPDATA%/VOID-Bridge/void-studio.py;
alle über VOID Studio installierten Szenensammlungen nutzen genau diese eine Kopie.

Daten (gemeinsam für alle Packs) in %APPDATA%/VOID-Bridge/ (macOS/Linux: ~/.config/VOID-Bridge/):
  void-studio.py           die zentrale Kopie dieses Skripts
  packs/<pack>/            installierte Szenen-Packs, darin import.json für OBS
  void-twitch-token.json   Zugang zu Twitch – wie ein Passwort behandeln, nicht teilen
  void-bridge-state.json   Letzte Unterstützer, Session, Bits-Ziel
  sounds/                  optional: follow.mp3, sub.mp3, … oder default.mp3

Updates: Packs (HTML, Schriften, Übergänge) per Knopfdruck, geprüft per SHA-256.
VOID Studio selbst wird nur angezeigt und erst nach Bestätigung eingespielt.
"""
import obspython as obs
import base64, collections, io, json, os, queue, socket, ssl, struct, threading, time, webbrowser
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STUDIO_VERSION = "1.0.4"
DEFAULT_REPO = "void-cx/void-studio"            # GitHub owner/repo – in den Einstellungen änderbar
PORTAL_STUDIO = "https://my.void.cx/studio"     # VOID Studio im Portal: Stream-Statistiken, Go-Live im Discord, Downloads
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~/.config"), "VOID-Bridge")
TOKEN_FILE = os.path.join(DATA_DIR, "void-twitch-token.json")
STATE_FILE = os.path.join(DATA_DIR, "void-bridge-state.json")
SOUND_DIR = os.path.join(DATA_DIR, "sounds")
PACKS_DIR = os.path.join(DATA_DIR, "packs")
STUDIO_PATH = os.path.join(DATA_DIR, "void-studio.py")
os.makedirs(SOUND_DIR, exist_ok=True)
os.makedirs(PACKS_DIR, exist_ok=True)
SCOPES = ("moderator:read:followers channel:read:subscriptions bits:read "
          "channel:read:redemptions user:read:chat")
EVENTSUB_URL = "wss://eventsub.wss.twitch.tv/ws?keepalive_timeout_seconds=30"
SOUND_EXT = {".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav"}
CLIENT_ID = "r95fjm0m90hk3kslgnjn8y2b8ygx4n"   # öffentliche Twitch-App (Client-Typ Public)
ALERT_TYPES = ("follow", "sub", "resub", "gift", "cheer", "raid", "redeem")

LATEST_KEYS = ("follow", "sub", "gift", "cheer", "raid")
cfg = {"repo": DEFAULT_REPO, "show_latest": True, "latest_items": ["follow", "sub", "cheer"], "tele_on": False, "tele_url": "http://127.0.0.1:25555/api/ets2/telemetry",
       "client_id": CLIENT_ID, "port": 8787, "volume": 70, "goal_follow": 0, "goal_sub": 0, "goal_bits": 0,
       "ignore": set(), "hide_cmd": True, "irl_auto": False, "irl_source": "Kamera 1", "irl_delay": 3, "irl_back": 5}
stop = threading.Event()
clients, clients_lock = set(), threading.Lock()
gen = [0]
current_ws = [None]
twitch_state = {"login": None}           # verbundener Kanal, für die Anzeige im Skript-Fenster
server = [None]
started = [None]
badges = {}
lock = threading.RLock()


def log(msg):
    print(f"[VOID Studio] {msg}")


# ---------------------------------------------------------------- Zustand: Letzte, Session, Ziele
def fresh_session():
    return {"started": time.time(), "follows": [], "subs": [], "gifts": {}, "bits": {}, "raids": [], "km": 0}


state = {"latest": {}, "session": fresh_session(), "bits_goal": 0,
         "followers": None, "subs": None, "paused": False, "last_alert": None}


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            s = json.load(f)
        state["latest"] = s.get("latest", {})
        state["bits_goal"] = s.get("bits_goal", 0)
        sess = s.get("session") or {}
        if time.time() - sess.get("started", 0) < 12 * 3600:    # ältere Sessions verfallen
            state["session"] = {**fresh_session(), **sess}
    except (OSError, ValueError):
        pass


def save_state():
    with lock:
        data = {k: state[k] for k in ("latest", "session", "bits_goal")}
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError as e:
        log(f"Zustand nicht gespeichert: {e}")


def sound_map():
    out = {}
    if os.path.isdir(SOUND_DIR):
        for fn in os.listdir(SOUND_DIR):
            name, ext = os.path.splitext(fn)
            if ext.lower() in (".mp3", ".ogg", ".wav") and (name in ALERT_TYPES or name == "default"):
                out[name] = f"http://127.0.0.1:{cfg['port']}/sounds/{urllib.parse.quote(fn)}"
    return out


def snapshot():
    with lock:
        goals = []
        for key, label, cur in (("follow", "Follower-Ziel", state["followers"]),
                                ("sub", "Abo-Ziel", state["subs"]),
                                ("bits", "Bits-Ziel", state["bits_goal"])):
            target = cfg["goal_" + key]
            if target > 0 and cur is not None:
                goals.append({"key": key, "label": label, "cur": cur, "target": target})
        return {"type": "state", "paused": state["paused"], "volume": cfg["volume"], "sounds": sound_map(),
                "show_latest": cfg["show_latest"], "latest_items": cfg["latest_items"],
                "counts": {"followers": state["followers"], "subs": state["subs"]},
                "latest": state["latest"], "session": state["session"], "goals": goals}


def send_all(obj):
    data = json.dumps(obj, ensure_ascii=False)
    with clients_lock:
        for q in list(clients):
            q.put(data)


def push_state():
    send_all(snapshot())


def add_unique(lst, name):
    if name not in lst:
        lst.append(name)


def record(ev):
    t, u, n = ev["type"], ev.get("user", ""), ev.get("amount", 0) or 0
    with lock:
        L, S = state["latest"], state["session"]
        if t == "follow":
            L["follow"] = {"user": u}
            add_unique(S["follows"], u)
            if state["followers"] is not None:
                state["followers"] += 1
        elif t in ("sub", "resub"):
            L["sub"] = {"user": u, "months": ev.get("months")}
            add_unique(S["subs"], u)
            if t == "sub" and state["subs"] is not None:
                state["subs"] += 1
        elif t == "gift":
            L["gift"] = {"user": u, "amount": n}
            S["gifts"][u] = S["gifts"].get(u, 0) + n
            if state["subs"] is not None:
                state["subs"] += n
        elif t == "cheer":
            L["cheer"] = {"user": u, "amount": n}
            S["bits"][u] = S["bits"].get(u, 0) + n
            state["bits_goal"] += n
        elif t == "raid":
            L["raid"] = {"user": u, "amount": n}
            S["raids"].append({"user": u, "amount": n})
    save_state()
    push_state()


def alert(ev, count=True):
    send_all(ev)
    log(f"Alert: {ev['type']} – {ev.get('user')}" + ("" if count else " (Test/Wiederholung)"))
    if count:
        with lock:
            state["last_alert"] = ev
        record(ev)


# ---------------------------------------------------------------- Spiel-Telemetrie (optional)
def odometer(raw):
    """Kilometerstand aus Funbit-Format (truck.odometer) oder RenCloud-Format."""
    try:
        if "truck" in raw:
            return float(raw["truck"]["odometer"])
        return float(raw["TruckValues"]["CurrentValues"]["DashboardValues"]["Odometer"])
    except (KeyError, TypeError, ValueError):
        return None


def telemetry_loop():
    last_ok, odo0, warned = None, None, False
    while not stop.is_set():
        if not cfg["tele_on"]:
            time.sleep(1)
            continue
        with clients_lock:
            listening = bool(clients)
        if not listening:
            time.sleep(1)
            continue
        try:
            with urllib.request.urlopen(cfg["tele_url"] + ("&" if "?" in cfg["tele_url"] else "?") + f"t={time.time()}",
                                        timeout=1.5) as r:
                raw = json.loads(r.read())
            if not last_ok:
                log("Telemetrie verbunden.")
            last_ok, warned = True, False
            send_all({"type": "telemetry", "data": raw})
            odo = odometer(raw)
            if odo:
                with lock:
                    s = state["session"]
                    if s.get("odo0") is None or odo < s["odo0"]:
                        s["odo0"] = odo
                    km = int(odo - s["odo0"])
                    changed = km != s.get("km", 0)
                    s["km"] = km
                if changed:
                    push_state()
            time.sleep(0.4)
        except Exception as e:
            if last_ok or not warned:
                log(f"Telemetrie nicht erreichbar ({cfg['tele_url']}): {e}")
                send_all({"type": "telemetry", "data": None})
            last_ok, warned = False, True
            time.sleep(3)


# ---------------------------------------------------------------- Steuerung
# ---------- IRL: Verbindungsabbruch erkennen und Szene wechseln ----------
# Läuft im OBS-Takt (timer_add), nicht in einem eigenen Thread: Szenen dürfen nur von dort umgeschaltet werden.
IRL_SCENE = "Verbindung weg"
IRL_LIVE_SCENES = ("Unterwegs", "Zwei Kameras", "Bild im Bild", "Vier Kameras", "Just Chatting")
irl = {"live": None, "since": None, "changed": 0.0, "prev": None}


def irl_snapshot():
    return {"type": "irl", "live": bool(irl["live"]), "since": irl["since"]}


def source_live(name):
    """True, wenn die Medienquelle läuft und Bild hat; None, wenn es sie in dieser Szenensammlung nicht gibt."""
    src = obs.obs_get_source_by_name(name)
    if not src:
        return None
    try:
        return obs.obs_source_media_get_state(src) == obs.OBS_MEDIA_STATE_PLAYING and obs.obs_source_get_width(src) > 0
    finally:
        obs.obs_source_release(src)


def current_scene_name():
    src = obs.obs_frontend_get_current_scene()
    if not src:
        return None
    try:
        return obs.obs_source_get_name(src)
    finally:
        obs.obs_source_release(src)


def switch_scene(name):
    src = obs.obs_get_source_by_name(name)
    if not src:
        return False
    try:
        obs.obs_frontend_set_current_scene(src)
        return True
    finally:
        obs.obs_source_release(src)


def irl_tick():
    try:
        if not cfg["irl_auto"]:
            return
        live = source_live(cfg["irl_source"])
        if live is None:
            return
        now = time.time()
        if live != irl["live"]:
            irl.update(live=live, changed=now, since=None if live else int(now))
            send_all(irl_snapshot())                     # „Verbindung weg“ zeigt, seit wann, und meldet die Rückkehr
        held = now - irl["changed"]
        scene = current_scene_name()
        if not live and held >= cfg["irl_delay"] and scene in IRL_LIVE_SCENES and switch_scene(IRL_SCENE):
            irl["prev"] = scene
            log(f"IRL: {cfg['irl_source']} ohne Signal – auf „{IRL_SCENE}“ geschaltet.")
        elif live and held >= cfg["irl_back"] and scene == IRL_SCENE and irl["prev"] and switch_scene(irl["prev"]):
            log(f"IRL: Signal wieder da – zurück auf „{irl['prev']}“.")
            irl["prev"] = None
    except Exception as e:                                # ein Fehler im Takt darf OBS nicht stören
        log(f"IRL: {e}")


def ctl_replay(*_):
    with lock:
        ev = state["last_alert"]
    if ev:
        alert(dict(ev, replay=True), count=False)
    else:
        log("Noch kein Alert zum Wiederholen.")
    return False


def ctl_pause(*_):
    with lock:
        state["paused"] = not state["paused"]
        p = state["paused"]
    log("Alerts pausiert." if p else "Alerts laufen wieder.")
    push_state()
    return False


def ctl_skip(*_):
    send_all({"type": "control", "action": "skip"})
    return False


def ctl_reset_session(*_):
    with lock:
        state["session"] = fresh_session()          # setzt auch die gefahrenen km zurück
    save_state()
    push_state()
    log("Session zurückgesetzt.")
    return False


def ctl_reset_bits(*_):
    with lock:
        state["bits_goal"] = 0
    save_state()
    push_state()
    log("Bits-Ziel zurückgesetzt.")
    return False


# ---------------------------------------------------------------- Lokaler Server für die Szenen
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")   # file:// → localhost

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/events":
            return self.sse()
        if path.startswith("/test/"):
            sample = SAMPLES.get(path[6:])
            if sample:
                alert(dict(sample), count=False)
            return self.reply(200 if sample else 404, b"ok" if sample else b"unbekannt", "text/plain")
        if path.startswith("/sounds/"):
            name = os.path.basename(urllib.parse.unquote(path[8:]))
            ext = os.path.splitext(name)[1].lower()
            fp = os.path.join(SOUND_DIR, name)
            if ext in SOUND_EXT and os.path.isfile(fp):
                with open(fp, "rb") as f:
                    return self.reply(200, f.read(), SOUND_EXT[ext])
            return self.reply(404, b"nicht gefunden", "text/plain")
        if path in ("/", "/status"):
            with clients_lock:
                n = len(clients)
            body = json.dumps({"bridge": "VOID Twitch Bridge", "listeners": n,
                               "twitch": current_ws[0] is not None}).encode()
            return self.reply(200, body, "application/json")
        self.reply(404, b"nicht gefunden", "text/plain")

    def reply(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.cors()
        self.end_headers()
        q = queue.Queue()
        q.put(json.dumps(snapshot(), ensure_ascii=False))
        if irl["live"] is not None:
            q.put(json.dumps(irl_snapshot()))
        if badges:
            q.put(json.dumps({"type": "badges", "map": badges}))
        with clients_lock:
            clients.add(q)
        try:
            self.wfile.write(b"retry: 3000\n\n")
            self.wfile.flush()
            while not stop.is_set():
                try:
                    data = q.get(timeout=15)
                    self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionError, OSError):
            pass
        finally:
            with clients_lock:
                clients.discard(q)


def start_server():
    stop_server()
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", cfg["port"]), Handler)
    except OSError as e:
        log(f"Port {cfg['port']} nicht verfügbar: {e}")
        return
    srv.daemon_threads = True
    server[0] = srv
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log(f"Event-Host läuft: http://127.0.0.1:{cfg['port']}/events")


def stop_server():
    if server[0]:
        server[0].shutdown()
        server[0].server_close()
        server[0] = None


# ---------------------------------------------------------------- Twitch-Zugang
def http(method, url, data=None, headers=None, form=False):
    body, h = None, dict(headers or {})
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def load_token():
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_token(t):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"access_token": t["access_token"], "refresh_token": t.get("refresh_token", "")}, f)


def refresh():
    tok = load_token()
    if not tok or not tok.get("refresh_token"):
        return None
    st, j = http("POST", "https://id.twitch.tv/oauth2/token", {
        "client_id": cfg["client_id"], "grant_type": "refresh_token",
        "refresh_token": tok["refresh_token"]}, form=True)
    if st != 200:
        log("Zugang abgelaufen – bitte neu mit Twitch verbinden.")
        return None
    save_token(j)
    return j["access_token"]


def session():
    """Gültiges Token + eigene User-ID, erneuert bei Bedarf."""
    tok = load_token()
    if not tok or not cfg["client_id"]:
        return None
    for attempt in range(2):
        st, j = http("GET", "https://id.twitch.tv/oauth2/validate",
                     headers={"Authorization": f"OAuth {tok['access_token']}"})
        if st == 200:
            missing = set(SCOPES.split()) - set(j.get("scopes") or [])
            if missing:
                log("Neue Berechtigungen nötig (" + ", ".join(sorted(missing)) +
                    ") – bitte „Mit Twitch verbinden“ erneut klicken.")
            return {"token": tok["access_token"], "uid": j["user_id"], "login": j["login"]}
        if attempt == 0 and refresh():
            tok = load_token()
            continue
        return None


def device_login():
    st, j = http("POST", "https://id.twitch.tv/oauth2/device",
                 {"client_id": cfg["client_id"], "scopes": SCOPES}, form=True)
    if st != 200:
        log(f"Login nicht möglich ({st}): {j.get('message', '')} – ist die App als „Öffentlich“ registriert?")
        return
    log(f"Im Browser bestätigen. Code: {j['user_code']}  ·  {j['verification_uri']}")
    webbrowser.open(j["verification_uri"])
    interval, deadline = j.get("interval", 5), time.time() + j.get("expires_in", 1800)
    while time.time() < deadline and not stop.is_set():
        time.sleep(interval)
        st, t = http("POST", "https://id.twitch.tv/oauth2/token", {
            "client_id": cfg["client_id"], "scopes": SCOPES, "device_code": j["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}, form=True)
        if st == 200:
            save_token(t)
            log("Mit Twitch verbunden.")
            start_eventsub()
            return
        msg = t.get("message", "")
        if msg == "authorization_pending":
            continue
        if msg == "slow_down":
            interval += 5
            continue
        log(f"Login abgebrochen: {msg or st}")
        return
    log("Login-Code abgelaufen.")


# ---------------------------------------------------------------- Minimaler WebSocket-Client
class WS:
    def __init__(self, url):
        u = urllib.parse.urlsplit(url)
        host, path = u.hostname, (u.path or "/") + ("?" + u.query if u.query else "")
        raw = socket.create_connection((host, u.port or 443), timeout=15)
        self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Handshake abgebrochen")
            buf += chunk
        head, self.buf = buf.split(b"\r\n\r\n", 1)
        status = head.split(b"\r\n", 1)[0]
        if b" 101 " not in status:
            raise ConnectionError(status.decode(errors="replace"))

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("Verbindung geschlossen")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def send(self, op, data=b""):
        mask, n = os.urandom(4), len(data)
        h = bytes([0x80 | op])
        if n < 126:
            h += bytes([0x80 | n])
        elif n < 65536:
            h += bytes([0xFE]) + struct.pack(">H", n)
        else:
            h += bytes([0xFF]) + struct.pack(">Q", n)
        self.sock.sendall(h + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv_json(self):
        parts = []
        while True:
            b1, b2 = self._read(2)
            op, n = b1 & 0x0F, b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            if b2 & 0x80:
                m = self._read(4)
                data = bytes(x ^ m[i % 4] for i, x in enumerate(self._read(n)))
            else:
                data = self._read(n)
            if op == 9:
                self.send(10, data)
                continue
            if op == 10:
                continue
            if op == 8:
                raise ConnectionError("Twitch hat die Verbindung geschlossen")
            parts.append(data)
            if b1 & 0x80:
                return json.loads(b"".join(parts).decode("utf-8"))

    def timeout(self, s):
        self.sock.settimeout(s)

    def close(self):
        try:
            self.send(8, struct.pack(">H", 1000))
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


# ---------------------------------------------------------------- Helix: Zahlen und Badges
def helix(s, path):
    st, j = http("GET", "https://api.twitch.tv/helix/" + path,
                 headers={"Client-Id": cfg["client_id"], "Authorization": f"Bearer {s['token']}"})
    return j if st == 200 else None


def refresh_counts(s):
    f = helix(s, f"channels/followers?broadcaster_id={s['uid']}&first=1")
    sb = helix(s, f"subscriptions?broadcaster_id={s['uid']}&first=1")
    with lock:
        if f:
            state["followers"] = f.get("total", 0)
        if sb:
            state["subs"] = sb.get("total", 0)
    push_state()


def load_badges(s):
    out = {}
    for path in ("chat/badges/global", f"chat/badges?broadcaster_id={s['uid']}"):
        j = helix(s, path)
        for b in (j or {}).get("data", []):
            for v in b.get("versions", []):
                out[f"{b['set_id']}/{v['id']}"] = v.get("image_url_2x") or v.get("image_url_1x")
    badges.clear()
    badges.update(out)
    send_all({"type": "badges", "map": badges})


def stats_loop(my_gen):
    while not stop.is_set() and gen[0] == my_gen:
        s = session()
        if s:
            refresh_counts(s)
        for _ in range(300):                       # alle 5 Minuten abgleichen
            if stop.is_set() or gen[0] != my_gen:
                return
            time.sleep(1)


# ---------------------------------------------------------------- EventSub
def subscribe_all(s, session_id):
    me = s["uid"]
    b, chat = {"broadcaster_user_id": me}, {"broadcaster_user_id": me, "user_id": me}
    subs = [
        ("channel.follow", "2", {"broadcaster_user_id": me, "moderator_user_id": me}),
        ("channel.subscribe", "1", b), ("channel.subscription.message", "1", b),
        ("channel.subscription.gift", "1", b), ("channel.cheer", "1", b),
        ("channel.raid", "1", {"to_broadcaster_user_id": me}),
        ("channel.channel_points_custom_reward_redemption.add", "1", b),
        ("channel.chat.message", "1", chat), ("channel.chat.message_delete", "1", chat),
        ("channel.chat.clear", "1", chat), ("channel.chat.clear_user_messages", "1", chat),
    ]
    ok = 0
    for typ, ver, cond in subs:
        st, j = http("POST", "https://api.twitch.tv/helix/eventsub/subscriptions", {
            "type": typ, "version": ver, "condition": cond,
            "transport": {"method": "websocket", "session_id": session_id}},
            headers={"Client-Id": cfg["client_id"], "Authorization": f"Bearer {s['token']}"})
        if st in (200, 202, 409):
            ok += 1
        else:
            log(f"{typ}: {st} {j.get('message', '')}")
    log(f"{ok}/{len(subs)} Events abonniert für {s['login']}.")


def tier(ev):
    return {"1000": 1, "2000": 2, "3000": 3}.get(str(ev.get("tier", "")), None)


def normalize(typ, ev):
    name = ev.get("user_name") or ev.get("user_login") or "Anonym"
    if typ == "channel.follow":
        return {"type": "follow", "user": name}
    if typ == "channel.subscribe":
        return None if ev.get("is_gift") else {"type": "sub", "user": name, "tier": tier(ev)}
    if typ == "channel.subscription.message":
        return {"type": "resub", "user": name, "tier": tier(ev),
                "months": ev.get("cumulative_months", 0), "text": (ev.get("message") or {}).get("text", "")}
    if typ == "channel.subscription.gift":
        return {"type": "gift", "user": "Anonym" if ev.get("is_anonymous") else name,
                "amount": ev.get("total", 1), "tier": tier(ev)}
    if typ == "channel.cheer":
        return {"type": "cheer", "user": "Anonym" if ev.get("is_anonymous") else name,
                "amount": ev.get("bits", 0), "text": ev.get("message", "")}
    if typ == "channel.raid":
        return {"type": "raid", "user": ev.get("from_broadcaster_user_name", "Unbekannt"),
                "amount": ev.get("viewers", 0)}
    if typ == "channel.channel_points_custom_reward_redemption.add":
        return {"type": "redeem", "user": name, "title": (ev.get("reward") or {}).get("title", ""),
                "text": ev.get("user_input", "")}
    return None


def chat_event(typ, ev):
    if typ == "channel.chat.message":
        user = ev.get("chatter_user_name", "")
        text = (ev.get("message") or {}).get("text", "")
        if ev.get("chatter_user_login", "").lower() in cfg["ignore"] or user.lower() in cfg["ignore"]:
            return None
        if cfg["hide_cmd"] and text.startswith("!"):
            return None
        frags = []
        for f in (ev.get("message") or {}).get("fragments", []):
            if f.get("type") == "emote" and f.get("emote"):
                frags.append({"e": f["emote"]["id"], "t": f.get("text", "")})
            else:
                frags.append({"t": f.get("text", "")})
        return {"type": "chat", "id": ev.get("message_id"), "uid": ev.get("chatter_user_id"), "user": user,
                "color": ev.get("color") or "", "frags": frags,
                "badges": [f"{b['set_id']}/{b['id']}" for b in ev.get("badges", [])]}
    if typ == "channel.chat.message_delete":
        return {"type": "chat_delete", "id": ev.get("message_id")}
    if typ == "channel.chat.clear_user_messages":
        return {"type": "chat_delete_user", "uid": ev.get("target_user_id")}
    if typ == "channel.chat.clear":
        return {"type": "chat_clear"}
    return None


def handle(typ, ev):
    if typ.startswith("channel.chat."):
        c = chat_event(typ, ev)
        if c:
            send_all(c)
        return
    a = normalize(typ, ev)
    if a:
        alert(a)


def eventsub_loop(my_gen):
    alive = lambda: not stop.is_set() and gen[0] == my_gen
    seen = collections.deque(maxlen=500)
    backoff = 2
    while alive():
        ws = None
        try:
            s = session()
            if not s:
                log("Nicht mit Twitch verbunden.")
                return
            ws = WS(EVENTSUB_URL)
            current_ws[0] = ws
            welcome = ws.recv_json()["payload"]["session"]
            ws.timeout((welcome.get("keepalive_timeout_seconds") or 30) + 10)
            subscribe_all(s, welcome["id"])
            twitch_state["login"] = s["login"]
            if not badges:
                threading.Thread(target=load_badges, args=(s,), daemon=True).start()
            backoff = 2
            while alive():
                msg = ws.recv_json()
                meta, payload = msg["metadata"], msg.get("payload", {})
                mt = meta["message_type"]
                if mt == "notification":
                    if meta["message_id"] in seen:
                        continue
                    seen.append(meta["message_id"])
                    handle(payload["subscription"]["type"], payload["event"])
                elif mt == "session_reconnect":
                    new = WS(payload["session"]["reconnect_url"])      # Abos ziehen mit um
                    w = new.recv_json()["payload"]["session"]
                    new.timeout((w.get("keepalive_timeout_seconds") or 30) + 10)
                    ws.close()
                    ws = current_ws[0] = new
                elif mt == "revocation":
                    log(f"Twitch hat {payload['subscription']['type']} beendet: {payload['subscription']['status']}")
        except Exception as e:
            if not alive():
                break
            log(f"Verbindung getrennt ({e}). Neuer Versuch in {backoff} s.")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
        finally:
            if ws:
                ws.close()


def start_eventsub():
    stop_eventsub()
    if load_token() and cfg["client_id"]:
        threading.Thread(target=eventsub_loop, args=(gen[0],), daemon=True).start()
        threading.Thread(target=stats_loop, args=(gen[0],), daemon=True).start()


def stop_eventsub():
    gen[0] += 1
    if current_ws[0]:
        current_ws[0].close()
        current_ws[0] = None


# ---------------------------------------------------------------- Testdaten
SAMPLES = {
    "follow": {"type": "follow", "user": "Aetherwanderer"},
    "sub": {"type": "sub", "user": "Nachtfalke", "tier": 1},
    "resub": {"type": "resub", "user": "Kaelthas_DE", "months": 14, "tier": 1,
              "text": "Seit Tag eins dabei. Auf die nächsten Abyss-Runs!"},
    "gift": {"type": "gift", "user": "Lichtbringerin", "amount": 5, "tier": 1},
    "cheer": {"type": "cheer", "user": "Runenleser", "amount": 500, "text": "Für neue Server-Hardware"},
    "raid": {"type": "raid", "user": "VOIDCrew", "amount": 23},
    "redeem": {"type": "redeem", "user": "Sternenstaub", "title": "Trink was!", "text": ""},
}


def test_chat(*_):
    send_all({"type": "chat", "id": f"test-{time.time()}", "uid": "0", "user": "Testkanal", "color": "#7FC8FF",
              "badges": ["broadcaster/1"], "frags": [{"t": "Testnachricht aus der VOID Bridge "}, {"e": "25", "t": "Kappa"}]})
    return False


# ---------------------------------------------------------------- Pack-Manager
import hashlib, shutil, tempfile, zipfile, re as _re

mgr = {"index": None, "error": "", "busy": "", "notes": []}


def ver(v):
    return tuple(int(x) for x in _re.findall(r"\d+", str(v))[:3]) or (0,)


def src_url(name):
    """GitHub owner/repo → Asset des neuesten Releases; volle URL → direkt (z. B. eigener Spiegel oder Test)."""
    base = cfg["repo"].strip() or DEFAULT_REPO
    if base.startswith(("http://", "https://")):
        return base.rstrip("/") + "/" + name
    return f"https://github.com/{base}/releases/latest/download/{name}"


def fetch(name, timeout=30):
    req = urllib.request.Request(src_url(name), headers={"User-Agent": f"VOID-Studio/{STUDIO_VERSION}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def check_updates(timeout=15):
    try:
        mgr["index"] = json.loads(fetch("index.json", timeout))
        mgr["error"] = ""
        s = mgr["index"].get("studio", {})
        if ver(s.get("version", 0)) > ver(STUDIO_VERSION):
            log(f"VOID Studio {s['version']} verfügbar (installiert {STUDIO_VERSION}).")
    except Exception as e:
        mgr["error"] = f"Pack-Quelle nicht erreichbar: {e}"
        log(mgr["error"])


def installed(pid):
    try:
        with open(os.path.join(PACKS_DIR, pid, "pack.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def pack_list():
    """Alle bekannten Packs: aus dem Index plus lokal installierte."""
    out = {p["id"]: dict(p) for p in (mgr["index"] or {}).get("packs", [])}
    if os.path.isdir(PACKS_DIR):
        for pid in os.listdir(PACKS_DIR):
            inst = installed(pid)
            if inst:
                out.setdefault(pid, {"id": pid, "name": inst.get("name", pid), "version": None})
                out[pid]["installed"] = inst
    return sorted(out.values(), key=lambda p: p["name"].lower())


def status_of(p):
    inst = p.get("installed")
    if not inst:
        return "neu"
    if p.get("version") and ver(p["version"]) > ver(inst.get("version")):
        return f"Update {inst.get('version')} → {p['version']}"
    return f"installiert {inst.get('version')}"


TEMPLATE_DIR = "_vorlage"                 # im Pack: die Vorlage liegt hier, oben nur import.json für OBS


def template_of(pdir):
    """Vorlage der Szenensammlung; ältere Packs (bis 1.0.0) haben sie noch direkt im Pack-Ordner."""
    for tpl in (os.path.join(pdir, TEMPLATE_DIR, "import.template.json"), os.path.join(pdir, "import.template.json")):
        if os.path.isfile(tpl):
            return tpl
    return None


def make_import(pdir):
    """import.json des Packs auf diesen Rechner zuschneiden: ./-Pfade (relativ zum Pack-Ordner) → absolute Pfade,
    Skript → zentrale Kopie."""
    tpl = template_of(pdir)
    if not tpl:
        raise FileNotFoundError("keine import.template.json im Pack")
    with open(tpl, encoding="utf-8") as f:
        data = json.load(f)
    root = pdir.replace("\\", "/")

    def walk(v):
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, str) and v.startswith("./"):
            return root + v[1:]
        return v
    data = walk(data)
    for s in data.get("modules", {}).get("scripts-tool", []):
        s["path"] = STUDIO_PATH.replace("\\", "/")
    with open(os.path.join(pdir, "import.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def install_pack(pid):
    info = next((p for p in (mgr["index"] or {}).get("packs", []) if p["id"] == pid), None)
    if not info:
        log(f"{pid}: nicht in der Pack-Quelle gefunden.")
        return
    mgr["busy"] = f"{info['name']} wird geladen …"
    try:
        blob = fetch(info["file"], 120)
        if hashlib.sha256(blob).hexdigest() != info["sha256"]:
            raise ValueError("Prüfsumme stimmt nicht – Download verworfen")
        old = installed(pid)
        dest = os.path.join(PACKS_DIR, pid)
        tmp = tempfile.mkdtemp(dir=PACKS_DIR)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for m in z.infolist():
                parts = m.filename.split("/", 1)                    # oberste Ordnerebene abschneiden
                if len(parts) < 2 or not parts[1] or ".." in parts[1]:
                    continue
                target = os.path.join(tmp, *parts[1].split("/"))
                if m.is_dir():
                    os.makedirs(target, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with z.open(m) as src, open(target, "wb") as out:
                        shutil.copyfileobj(src, out)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.replace(tmp, dest)
        man = installed(pid) or {}
        man.update(id=pid, name=info["name"], version=info["version"])     # Index ist maßgeblich
        with open(os.path.join(dest, "pack.json"), "w", encoding="utf-8") as f:
            json.dump(man, f, ensure_ascii=False, indent=2)
        make_import(dest)
        new = installed(pid)
        if not old:
            note = f"{info['name']} {info['version']} installiert. Einmal importieren: Szenensammlung → Importieren → {dest}{os.sep}import.json"
        elif old.get("structure") != new.get("structure"):
            note = f"{info['name']} auf {info['version']} aktualisiert. Die Szenen haben sich geändert – bitte import.json erneut importieren."
        else:
            note = f"{info['name']} auf {info['version']} aktualisiert. Kein neuer Import nötig."
        mgr["notes"].append(note)
        log(note)
    except Exception as e:
        log(f"{info['name']}: {e}")
    finally:
        mgr["busy"] = ""


def remove_pack(pid):
    d = os.path.join(PACKS_DIR, pid)
    if os.path.isdir(d):
        shutil.rmtree(d)
        log(f"{pid} entfernt. Die Szenensammlung in OBS bitte selbst löschen.")


def running_elsewhere():
    """Pfad dieser Datei, wenn OBS sie nicht aus der zentralen Kopie lädt (z. B. direkt aus dem Download-Ordner)."""
    me = os.path.abspath(__file__)
    return None if os.path.normcase(me) == os.path.normcase(STUDIO_PATH) else me


def write_studio(path, blob):
    if os.path.isfile(path):
        shutil.copy2(path, path + f".{STUDIO_VERSION}.bak")
    with open(path, "wb") as f:
        f.write(blob)


def update_studio():
    s = (mgr["index"] or {}).get("studio")
    if not s or ver(s["version"]) <= ver(STUDIO_VERSION):
        log("VOID Studio ist aktuell.")
        return
    try:
        blob = fetch(s["file"], 60)
        if hashlib.sha256(blob).hexdigest() != s["sha256"]:
            raise ValueError("Prüfsumme stimmt nicht – Update verworfen")
        write_studio(STUDIO_PATH, blob)
        # Lädt OBS dieses Skript aus einem anderen Ordner (erste Einrichtung aus dem Download), diese Datei auch
        # ersetzen, sonst bliebe die Szenensammlung, in der es eingebunden ist, auf der alten Version.
        other = running_elsewhere()
        if other:
            try:
                write_studio(other, blob)
            except OSError as e:
                log(f"{other} nicht ersetzt ({e}); dort läuft weiter {STUDIO_VERSION}.")
        note = f"VOID Studio {s['version']} eingespielt. Jetzt in OBS: Werkzeuge → Skripte → „Skripte neu laden“."
        mgr["notes"].append(note)
        log(note)
    except Exception as e:
        mgr["notes"].append(f"Studio-Update fehlgeschlagen: {e}")
        log(f"Studio-Update fehlgeschlagen: {e}")


def self_install():
    """Beim ersten Start (oder mit neuerer Version) diese Datei als zentrale Kopie ablegen."""
    me = os.path.abspath(__file__)
    if os.path.normcase(me) == os.path.normcase(STUDIO_PATH):
        return
    try:
        with open(STUDIO_PATH, encoding="utf-8") as f:
            m = _re.search(r'STUDIO_VERSION = "([^"]+)"', f.read())
        there = m.group(1) if m else "0"
    except OSError:
        there = "0"
    if ver(STUDIO_VERSION) > ver(there):
        shutil.copy2(me, STUDIO_PATH)
        log(f"Zentrale Kopie angelegt: {STUDIO_PATH}")


def in_thread(fn, *a):
    threading.Thread(target=fn, args=a, daemon=True).start()


def selected(props):
    return obs.obs_data_get_string(settings_ref[0], "pack") if settings_ref[0] else ""


settings_ref = [None]


def ui_check(props, prop):
    check_updates()
    fill_packs(props)
    return True


def ui_install(props, prop):
    pid = selected(props)
    if pid:
        install_pack(pid)                      # wenige MB; danach steht der neue Stand gleich in der Liste
        fill_packs(props)
    return True


def ui_install_all(props, prop):
    todo = [p["id"] for p in pack_list() if p.get("installed") and status_of(p).startswith("Update")]
    if not todo:
        log("Alle installierten Packs sind aktuell.")
    for pid in todo:
        install_pack(pid)
    fill_packs(props)
    return True


def ui_remove(props, prop):
    pid = selected(props)
    if pid:
        remove_pack(pid)
        fill_packs(props)
    return True


def ui_open(props, prop):
    pid = selected(props)
    d = os.path.join(PACKS_DIR, pid) if pid and os.path.isdir(os.path.join(PACKS_DIR, pid)) else PACKS_DIR
    try:
        os.startfile(d)                       # Windows
    except AttributeError:
        webbrowser.open("file://" + d)
    return False


def ui_studio(props, prop):
    update_studio()                            # eine Datei, kurz; danach steht der Hinweis gleich im Fenster
    fill_packs(props)
    return True


def ui_open_central(props, prop):
    try:
        os.startfile(DATA_DIR)                 # Windows
    except AttributeError:
        webbrowser.open("file://" + DATA_DIR)
    return False


# ---------------------------------------------------------------- OBS-Oberfläche
HOTKEYS = [("replay", "VOID: Letzten Alert wiederholen", ctl_replay),
           ("pause", "VOID: Alerts pausieren/fortsetzen", ctl_pause),
           ("skip", "VOID: Aktuellen Alert überspringen", ctl_skip)]
hotkey_ids = {}


def ui_portal(*_):
    webbrowser.open(PORTAL_STUDIO)
    return False


def script_description():
    return ("<b>VOID Studio</b><br>Szenen-Packs verwalten und die VOID Twitch Bridge – Alerts, Sounds, Chat, "
            "Ziele und Rückblick ohne Fremddienst.<br>Ausgaben unter „Skript-Protokoll“. "
            "Hotkeys unter Einstellungen → Tastenkürzel („VOID: …“).")


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "repo", DEFAULT_REPO)
    obs.obs_data_set_default_int(settings, "port", 8787)
    obs.obs_data_set_default_int(settings, "volume", 70)
    obs.obs_data_set_default_bool(settings, "show_latest", True)
    for k in LATEST_KEYS:
        obs.obs_data_set_default_bool(settings, "latest_" + k, k in ("follow", "sub", "cheer"))
    obs.obs_data_set_default_bool(settings, "hide_cmd", True)
    obs.obs_data_set_default_string(settings, "ignore", "streamelements, nightbot, streamlabs, moobot")
    obs.obs_data_set_default_string(settings, "tele_url", "http://127.0.0.1:25555/api/ets2/telemetry")
    obs.obs_data_set_default_string(settings, "irl_source", "Kamera 1")
    obs.obs_data_set_default_int(settings, "irl_delay", 3)
    obs.obs_data_set_default_int(settings, "irl_back", 5)


def studio_head():
    """Statuszeile oben im Skript-Fenster."""
    packs = pack_list()
    head = f"VOID Studio {STUDIO_VERSION} · {sum(1 for x in packs if x.get('installed'))} Packs installiert, {len(packs)} verfügbar"
    s = (mgr["index"] or {}).get("studio")
    if s and ver(s.get("version", 0)) > ver(STUDIO_VERSION):
        head += f"\nUpdate verfügbar: VOID Studio {s['version']} – " + "; ".join(s.get("changelog", [])[:3])
    if mgr["error"]:
        head += "\n" + mgr["error"]
    if mgr["busy"]:
        head += "\n" + mgr["busy"]
    if mgr["notes"]:
        head += "\n" + mgr["notes"][-1]
    return head


def fill_packs(props):
    """Pack-Liste, Statuszeile und Studio-Update-Knopf neu befüllen. OBS ruft script_properties() nur beim Öffnen
    des Fensters auf; ein Knopf mit Rückgabe True zeichnet nur neu, darum hier von Hand."""
    lst = obs.obs_properties_get(props, "pack")
    if lst:
        obs.obs_property_list_clear(lst)
        for x in pack_list():
            obs.obs_property_list_add_string(lst, f"{x['name']} – {status_of(x)}", x["id"])
    info = obs.obs_properties_get(props, "studio_info")
    if info:
        obs.obs_property_set_description(info, studio_head())
    status = obs.obs_properties_get(props, "twitch_status")
    if status:
        obs.obs_property_set_description(status, twitch_status())
    up = obs.obs_properties_get(props, "m_studio")
    if up:
        s = (mgr["index"] or {}).get("studio") or {}
        newer = bool(s) and ver(s.get("version", 0)) > ver(STUDIO_VERSION)
        obs.obs_property_set_visible(up, newer)
        if newer:
            obs.obs_property_set_description(up, f"VOID Studio auf {s['version']} aktualisieren")


def twitch_status():
    if twitch_state["login"] and current_ws[0] is not None:
        return f"Verbunden als {twitch_state['login']}. Alerts, Chat und Ziele kommen live in die Szenen."
    if load_token():
        return "Anmeldung gespeichert, die Verbindung zu Twitch wird aufgebaut."
    return "Nicht verbunden. Ohne Verbindung bleiben Alerts, Chat und Ziele in den Szenen leer."


def group(p, name, label, intro, build):
    """Eine Kategorie als Rahmen mit Überschrift und kurzer Erklärung; die Einstellungen darin behalten ihre Namen."""
    g = obs.obs_properties_create()
    if intro:
        obs.obs_properties_add_text(g, name + "_info", intro, getattr(obs, "OBS_TEXT_INFO", obs.OBS_TEXT_DEFAULT))
    build(g)
    obs.obs_properties_add_group(p, name, label, obs.OBS_GROUP_NORMAL, g)


def tip(prop, text):
    """Tooltip am Feld."""
    obs.obs_property_set_long_description(prop, text)
    return prop


def script_properties():
    if mgr["index"] is None:
        check_updates(timeout=8)               # erstes Öffnen: Liste sofort holen, sonst bliebe sie leer
    p = obs.obs_properties_create()
    INFO = getattr(obs, "OBS_TEXT_INFO", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(p, "studio_info", studio_head(), INFO)

    def packs(g):
        tip(obs.obs_properties_add_list(g, "pack", "Pack", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING),
            "Pack auswählen, dann installieren, aktualisieren, Ordner öffnen oder entfernen.")
        obs.obs_properties_add_button(g, "m_install", "Installieren / aktualisieren", ui_install)
        tip(obs.obs_properties_add_button(g, "m_open", "Pack-Ordner öffnen (import.json)", ui_open),
            "Darin liegt import.json für OBS: Szenensammlung → Importieren.")
        obs.obs_properties_add_button(g, "m_remove", "Entfernen", ui_remove)
        obs.obs_properties_add_button(g, "m_check", "Nach Updates suchen", ui_check)
        obs.obs_properties_add_button(g, "m_all", "Alle Pack-Updates installieren", ui_install_all)
        obs.obs_properties_add_button(g, "m_studio", "VOID Studio aktualisieren", ui_studio)
        other = running_elsewhere()
        if other:
            obs.obs_properties_add_text(g, "studio_where", (
                f"Dieses Skript läuft aus {other}. Updates landen in beiden Dateien, sicherer ist aber die zentrale Kopie: "
                f"unter Werkzeuge → Skripte dieses Skript entfernen und mit + {STUDIO_PATH} hinzufügen. "
                "Die Packs nutzen sie ohnehin."), INFO)
            obs.obs_properties_add_button(g, "m_central", "Ordner der zentralen Kopie öffnen", ui_open_central)

    def twitch(g):
        obs.obs_properties_add_text(g, "twitch_status", twitch_status(), INFO)
        tip(obs.obs_properties_add_button(g, "login", "Mit Twitch verbinden", on_login),
            "Öffnet die Bestätigung bei Twitch im Browser. Gilt für alle Packs.")
        obs.obs_properties_add_button(g, "logout", "Abmelden", on_logout)
        tip(obs.obs_properties_add_button(g, "portal", "Stream-Statistiken im Portal öffnen", ui_portal),
            "my.void.cx/studio: Zuschauer, Chat, Follower und Abos deiner Streams.")

    def alerts(g):
        obs.obs_properties_add_int_slider(g, "volume", "Lautstärke", 0, 100, 1)
        obs.obs_properties_add_button(g, "c_replay", "Letzten Alert wiederholen", ctl_replay)
        obs.obs_properties_add_button(g, "c_pause", "Alerts pausieren / fortsetzen", ctl_pause)
        obs.obs_properties_add_button(g, "c_skip", "Aktuellen Alert überspringen", ctl_skip)

    def tests(g):
        for key, label in [("follow", "Follow"), ("sub", "Abo"), ("resub", "Abo verlängert"), ("gift", "Geschenk-Abos"),
                           ("cheer", "Bits"), ("raid", "Raid"), ("redeem", "Kanalpunkte")]:
            obs.obs_properties_add_button(g, "t_" + key, label,
                                          lambda props, prop, k=key: (alert(dict(SAMPLES[k]), count=False), False)[1])
        obs.obs_properties_add_button(g, "t_chat", "Chatnachricht", test_chat)

    def goals(g):
        obs.obs_properties_add_int(g, "goal_follow", "Follower-Ziel", 0, 10000000, 1)
        obs.obs_properties_add_int(g, "goal_sub", "Abo-Ziel", 0, 1000000, 1)
        obs.obs_properties_add_int(g, "goal_bits", "Bits-Ziel", 0, 100000000, 100)
        obs.obs_properties_add_button(g, "c_bits", "Bits-Ziel zurücksetzen", ctl_reset_bits)

    def scenes(g):
        tip(obs.obs_properties_add_bool(g, "show_latest", "Letzte Unterstützer an der Game-Kamera zeigen"),
            "Erscheint in den Spielszenen über den Zielen.")
        for k, label in [("follow", "Follow"), ("sub", "Abo"), ("gift", "Geschenk"), ("cheer", "Bits"), ("raid", "Raid")]:
            obs.obs_properties_add_bool(g, "latest_" + k, "   " + label)
        tip(obs.obs_properties_add_button(g, "c_session", "Session-Rückblick zurücksetzen", ctl_reset_session),
            "Der Rückblick in „Stream endet“ zählt ab hier neu.")

    def chat(g):
        tip(obs.obs_properties_add_text(g, "ignore", "Ausgeblendete Namen", obs.OBS_TEXT_DEFAULT),
            "Kommagetrennt, z. B. Bots wie streamelements, nightbot.")
        obs.obs_properties_add_bool(g, "hide_cmd", "Befehle mit ! ausblenden")

    def telemetry(g):
        obs.obs_properties_add_bool(g, "tele_on", "Spiel-Telemetrie weiterreichen")
        tip(obs.obs_properties_add_text(g, "tele_url", "Telemetrie-URL", obs.OBS_TEXT_DEFAULT),
            "Funbit-Format, z. B. http://127.0.0.1:25555/api/ets2/telemetry")

    def irl_group(g):
        tip(obs.obs_properties_add_bool(g, "irl_auto", "Bei Abbruch auf „Verbindung weg“ schalten"),
            "Nur aus den Kamera-Szenen (Unterwegs, Zwei Kameras, Bild im Bild, Vier Kameras, Just Chatting); "
            "kommt das Signal zurück, geht es in die Szene von vorher.")
        tip(obs.obs_properties_add_text(g, "irl_source", "Kamera-Quelle", obs.OBS_TEXT_DEFAULT),
            "Name der Medienquelle, die überwacht wird. Standard: Kamera 1")
        obs.obs_properties_add_int(g, "irl_delay", "Umschalten nach (Sekunden)", 1, 60, 1)
        obs.obs_properties_add_int(g, "irl_back", "Zurück nach stabilem Signal (Sekunden)", 1, 60, 1)

    def tech(g):
        tip(obs.obs_properties_add_int(g, "port", "Lokaler Port", 1024, 65535, 1),
            "Über diesen Port holen sich die Szenen die Live-Daten. Nur ändern, wenn 8787 belegt ist.")
        tip(obs.obs_properties_add_text(g, "repo", "Pack-Quelle", obs.OBS_TEXT_DEFAULT),
            "GitHub owner/repo oder eine eigene URL. Standard: " + DEFAULT_REPO)

    group(p, "g_packs", "Szenen-Packs",
          "Packs installieren und aktuell halten. Nach dem ersten Installieren die Szenensammlung einmal in OBS importieren.", packs)
    group(p, "g_twitch", "Twitch", None, twitch)
    group(p, "g_alerts", "Alerts",
          "Einblendung mit Sound bei Follow, Abo, Bits, Raid und Kanalpunkten. Eigene Sounds: " + SOUND_DIR, alerts)
    group(p, "g_tests", "Testen", "Schickt eine Beispiel-Einblendung an alle offenen Szenen, ohne Twitch.", tests)
    group(p, "g_goals", "Ziele", "Fortschrittsbalken in den Szenen. 0 blendet ein Ziel aus.", goals)
    group(p, "g_scenes", "Spielszenen und Rückblick", None, scenes)
    group(p, "g_chat", "Chat", None, chat)
    group(p, "g_tele", "Telemetrie (ETS2/ATS)", "Für die Szene „ETS2 Telemetrie“; braucht einen laufenden Telemetrie-Server.", telemetry)
    group(p, "g_irl", "IRL", "Für das IRL-Pack: überwacht die Kamera-Quelle und schaltet bei einem Abbruch selbst um.", irl_group)
    group(p, "g_tech", "Technik", None, tech)
    fill_packs(p)
    return p


def on_login(props, prop):
    threading.Thread(target=device_login, daemon=True).start()
    return False


def on_logout(props, prop):
    stop_eventsub()
    twitch_state["login"] = None
    try:
        os.remove(TOKEN_FILE)
    except OSError:
        pass
    log("Abgemeldet.")
    return False


def script_update(settings):
    settings_ref[0] = settings
    cfg["repo"] = obs.obs_data_get_string(settings, "repo").strip() or DEFAULT_REPO
    g = lambda k: obs.obs_data_get_int(settings, k)
    port = g("port")
    port_changed = port != cfg["port"] or server[0] is None
    first = started[0] is None
    cfg.update(port=port, volume=g("volume"), goal_follow=g("goal_follow"),
               goal_sub=g("goal_sub"), goal_bits=g("goal_bits"),
               hide_cmd=obs.obs_data_get_bool(settings, "hide_cmd"),
               tele_on=obs.obs_data_get_bool(settings, "tele_on"),
               show_latest=obs.obs_data_get_bool(settings, "show_latest"),
               latest_items=[k for k in LATEST_KEYS if obs.obs_data_get_bool(settings, "latest_" + k)],
               tele_url=obs.obs_data_get_string(settings, "tele_url").strip() or cfg["tele_url"],
               irl_auto=obs.obs_data_get_bool(settings, "irl_auto"),
               irl_source=obs.obs_data_get_string(settings, "irl_source").strip() or "Kamera 1",
               irl_delay=max(1, g("irl_delay")), irl_back=max(1, g("irl_back")),
               ignore={n.strip().lower() for n in obs.obs_data_get_string(settings, "ignore").split(",") if n.strip()})
    if port_changed:
        start_server()
    if first:                            # Twitch-Verbindung einmal beim Laden starten
        started[0] = True
        start_eventsub()
    push_state()


def script_load(settings):
    stop.clear()
    settings_ref[0] = settings
    try:
        self_install()
    except OSError as e:
        log(f"Zentrale Kopie nicht möglich: {e}")
    for pid in os.listdir(PACKS_DIR):                       # von Hand entpackte (z. B. private) Packs vorbereiten
        d = os.path.join(PACKS_DIR, pid)
        if template_of(d) and not os.path.isfile(os.path.join(d, "import.json")):
            try:
                make_import(d)
                log(f"{pid}: import.json erzeugt – jetzt in OBS importieren: {d}{os.sep}import.json")
            except Exception as e:
                log(f"{pid}: import.json nicht erzeugt: {e}")
    in_thread(check_updates)
    threading.Thread(target=telemetry_loop, daemon=True).start()
    obs.timer_add(irl_tick, 500)
    log(f"Daten und Sounds: {DATA_DIR}")
    load_state()
    for key, desc, fn in HOTKEYS:
        hid = obs.obs_hotkey_register_frontend("void_bridge_" + key, desc,
                                               lambda pressed, f=fn: f() if pressed else None)
        arr = obs.obs_data_get_array(settings, "hotkey_" + key)
        obs.obs_hotkey_load(hid, arr)
        obs.obs_data_array_release(arr)
        hotkey_ids[key] = hid


def script_save(settings):
    for key, hid in hotkey_ids.items():
        arr = obs.obs_hotkey_save(hid)
        obs.obs_data_set_array(settings, "hotkey_" + key, arr)
        obs.obs_data_array_release(arr)


def script_unload():
    obs.timer_remove(irl_tick)
    stop.set()
    stop_eventsub()
    stop_server()
    save_state()
