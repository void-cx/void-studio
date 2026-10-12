"""
VOID Studio – OBS-Skript (Werkzeuge → Skripte → +)

Eins für alles:
  · Szenen-Packs verwalten: aus dem GitHub-Repo installieren, aktualisieren, entfernen
  · VOID Twitch Bridge: Alerts, Sounds, Chat, Ziele, letzte Unterstützer, Rückblick, Spiel-Telemetrie
  · IRL: bei Verbindungsabbruch selbst auf „Verbindung weg“ schalten und zurück
  · Infos aus OBS: Textquellen „Info · …“ in der Szene „VOID · Infos“ füllen die Overlays (Spielname, Ort, …)
  · Szenensammlung direkt in OBS einrichten, ohne Import-Dialog
  · Web-Oberfläche unter http://127.0.0.1:8787/studio (auch als OBS-Dock und auf Wunsch vom Handy im Heimnetz)

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
import base64, collections, io, json, os, queue, socket, ssl, struct, sys, threading, time, webbrowser
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STUDIO_VERSION = "1.1.0"
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
       "ignore": set(), "hide_cmd": True, "irl_auto": False, "irl_source": "Kamera 1", "irl_delay": 3, "irl_back": 5,
       "remote_on": False}
web = {"key": None, "log": collections.deque(maxlen=40), "device": None}
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
    web["log"].append([time.strftime("%H:%M:%S"), str(msg)])


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
# Wichtig: Skript-Timer laufen im Grafik-Thread von OBS und halten dabei die Python-Sperre. Alles, was dort auf die
# Oberfläche wartet (Szene umschalten, Szene anlegen), blockiert OBS, sobald die Oberfläche ihrerseits ein Python-
# Ereignis auslöst. Darum liest irl_tick nur und schaltet über einen eigenen Thread, der die Sperre abgibt (ctypes).
IRL_SCENE = "Verbindung weg"
IRL_LIVE_SCENES = ("Unterwegs", "Zwei Kameras", "Bild im Bild", "Vier Kameras", "Just Chatting")
irl = {"live": None, "since": None, "changed": 0.0, "prev": None, "busy_until": 0.0}


def irl_snapshot():
    return {"type": "irl", "live": bool(irl["live"]), "since": irl["since"]}


def source_exists(name):
    src = obs.obs_get_source_by_name(name)
    if src:
        obs.obs_source_release(src)
    return bool(src)


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
    """Szene im Programm, direkt aus libobs (Übergang auf Kanal 0), ohne die Oberfläche zu fragen."""
    tr = obs.obs_get_output_source(0)
    if not tr:
        return None
    try:
        src = obs.obs_transition_get_active_source(tr)
        if not src:
            return None
        try:
            return obs.obs_source_get_name(src)
        finally:
            obs.obs_source_release(src)
    finally:
        obs.obs_source_release(tr)


NATIVE = {}


def native():
    """libobs und Frontend-API über ctypes: ctypes gibt die Python-Sperre ab, solange OBS die Szene wechselt."""
    if "lib" not in NATIVE:
        try:
            import ctypes
            if sys.platform == "win32":
                lib, fe = ctypes.CDLL("obs.dll"), ctypes.CDLL("obs-frontend-api.dll")
            else:
                lib = fe = ctypes.CDLL(None)            # beide sind im OBS-Prozess schon geladen
            lib.obs_get_source_by_name.restype = ctypes.c_void_p
            lib.obs_get_source_by_name.argtypes = [ctypes.c_char_p]
            lib.obs_source_release.argtypes = [ctypes.c_void_p]
            fe.obs_frontend_set_current_scene.argtypes = [ctypes.c_void_p]
            NATIVE["lib"] = (lib, fe)
        except Exception as e:
            NATIVE["lib"] = None
            log(f"IRL: automatisches Umschalten nicht möglich ({e}).")
    return NATIVE["lib"]


def switch_scene(name):
    """In einem eigenen Thread aufrufen, nie aus einem Timer."""
    n = native()
    if not n:
        return False
    lib, fe = n
    src = lib.obs_get_source_by_name(name.encode("utf-8"))
    if not src:
        return False
    try:
        fe.obs_frontend_set_current_scene(src)
        return True
    finally:
        lib.obs_source_release(src)


def switch_later(name, note):
    def run():
        if switch_scene(name):
            log(note)
    threading.Thread(target=run, daemon=True).start()


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
        if now < irl["busy_until"]:                       # Umschalten läuft noch
            return
        scene = current_scene_name()
        if not live and held >= cfg["irl_delay"] and scene in IRL_LIVE_SCENES and source_exists(IRL_SCENE):
            irl.update(prev=scene, busy_until=now + 3)
            switch_later(IRL_SCENE, f"IRL: {cfg['irl_source']} ohne Signal – auf „{IRL_SCENE}“ geschaltet.")
        elif live and held >= cfg["irl_back"] and scene == IRL_SCENE and irl["prev"]:
            back, irl["prev"], irl["busy_until"] = irl["prev"], None, now + 3
            switch_later(back, f"IRL: Signal wieder da – zurück auf „{back}“.")
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


# ---------------------------------------------------------------- Web-Oberfläche (/studio, auch als OBS-Dock)
# Die Seite selbst enthält nichts Geheimes; jede /api-Anfrage braucht den Schlüssel im Header X-Void-Key. Fremde
# Webseiten kennen ihn nicht und dürfen den Header ohne CORS-Freigabe gar nicht senden.
# Regel seit 1.0.4: Diese Anfragen laufen in Server-Threads und dürfen OBS nie auf die Oberfläche warten lassen.
# Texte für die Info-Quellen gehen darum in eine Warteschlange, die info_tick im OBS-Takt abarbeitet; Szenen anlegen
# geht nur aus OBS heraus.
WEB_KEY_FILE = os.path.join(DATA_DIR, "web-key.txt")
info_writes = queue.Queue()
INFO_HELP = {
    "Titel": "Großer Titel in den Szenen. Leer = Standard des Packs.",
    "Statuszeilen": "Eine Zeile pro Text, sie wechseln sich ab. Ersetzt die Standardzeilen.",
    "Charakter": "Name deines Charakters, erscheint im Wechsel auf der Namensplatte.",
    "Splash": "Gelber Spruch am Titel.",
    "Spiel": "Name des Spiels auf dem Notizzettel.",
    "Entwickler": "Studio oder Entwickler, erscheint als „von …“.",
    "Status": "Wird zum Sticker, z. B. Demo, Early Access, Prototyp.",
    "Wunschliste": "„ja“ klebt „Auf die Wunschliste!“ daneben.",
    "Spiele des Abends": "Ein Spiel pro Zeile, Status nach Doppelpunkt, z. B. „Pixel Pilgrim: Demo“.",
    "Strecke": "Infotafel in Start und Pause.",
    "Auto": "Infotafel in Start und Pause.",
    "Serie": "Infotafel in Start und Pause.",
    "Ort": "Steht im HUD; das Wetter sucht den Ort bis zum „·“.",
    "Wetter-Ort": "Anderer Ort fürs Wetter. Leer = Ort.",
}
MULTILINE = ("Statuszeilen", "Spiele des Abends")
BOOL_SETTINGS = ("show_latest", "hide_cmd", "irl_auto", "tele_on", "remote_on")
INT_SETTINGS = {"volume": (0, 100), "goal_follow": (0, 10000000), "goal_sub": (0, 1000000), "goal_bits": (0, 100000000),
                "irl_delay": (1, 60), "irl_back": (1, 60)}
STR_SETTINGS = ("irl_source", "tele_url")


def web_key(renew=False):
    if renew or not web["key"]:
        k = None
        if not renew:
            try:
                with open(WEB_KEY_FILE, encoding="utf-8") as f:
                    k = f.read().strip()
            except OSError:
                pass
        if not k:
            import secrets
            k = secrets.token_urlsafe(18)
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(WEB_KEY_FILE, "w", encoding="utf-8") as f:
                f.write(k)
        web["key"] = k
    return web["key"]


def lan_addresses():
    """IPv4-Adressen dieses Rechners im Heimnetz bzw. VPN (z. B. Tailscale)."""
    ips = set()
    try:
        for a in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(a[4][0])
    except OSError:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as u:
            u.connect(("192.0.2.1", 9))                 # sendet nichts, ermittelt nur die Standard-Adresse
            ips.add(u.getsockname()[0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith(("127.", "169.254.")))


def web_urls():
    k, p = web_key(), cfg["port"]
    return f"http://127.0.0.1:{p}/studio#k={k}", [f"http://{ip}:{p}/studio#k={k}" for ip in lan_addresses()] if cfg["remote_on"] else []


def preview_url(p):
    prev = p.get("previews") or []
    pick = next((x for x in prev if x.get("scene") == "game"), prev[0] if prev else None)
    return src_url(pick["file"]) if pick else None


def info_labels():
    pid = active_pack()
    return pid, ((installed(pid) or {}).get("infos") or INFO_DEFAULT) if pid else []


def web_state():
    pid, labels = info_labels()
    with lock:
        live = {"paused": state["paused"], "session": state["session"], "followers": state["followers"],
                "subs": state["subs"], "latest": state["latest"], "bits_goal": state["bits_goal"]}
    s = (mgr["index"] or {}).get("studio") or {}
    local, remote = web_urls()
    return {
        "version": STUDIO_VERSION,
        "studio_update": s.get("version") if s and ver(s.get("version", 0)) > ver(STUDIO_VERSION) else None,
        "studio_changelog": s.get("changelog", []),
        "collection": obs.obs_frontend_get_current_scene_collection(),
        "pack": {"id": pid, "name": (installed(pid) or {}).get("name", pid)} if pid else None,
        "infos": [{"label": lb, "value": info["data"].get(lb, ""), "exists": lb in info["data"], "help": INFO_HELP.get(lb, ""),
                   "multiline": lb in MULTILINE} for lb in labels],
        "twitch": {"login": twitch_state["login"], "connected": current_ws[0] is not None, "saved": bool(load_token()),
                   "device": web["device"], "status": twitch_status()},
        "live": dict(live, volume=cfg["volume"], goals=snapshot()["goals"]),
        "irl": {"auto": cfg["irl_auto"], "source": cfg["irl_source"], "live": irl["live"], "since": irl["since"]},
        "packs": [{"id": p["id"], "name": p["name"], "version": p.get("version"),
                   "installed": (p.get("installed") or {}).get("version"), "status": status_of(p), "preview": preview_url(p)}
                  for p in pack_list()],
        "busy": mgr["busy"], "error": mgr["error"], "notes": mgr["notes"][-3:],
        "log": list(web["log"])[-15:],
        "settings": dict({k: cfg[k] for k in BOOL_SETTINGS + tuple(INT_SETTINGS) + STR_SETTINGS},
                         latest_items=cfg["latest_items"], ignore=", ".join(sorted(cfg["ignore"]))),
        "local_url": local, "remote_urls": remote, "port": cfg["port"],
    }


def web_infos(body):
    """{Label: Text} → Warteschlange; info_tick schreibt die Texte im OBS-Takt in die Quellen."""
    _, labels = info_labels()
    for label, text in body.items():
        if label in labels:
            info_writes.put((label, str(text if text is not None else "")[:2000]))


def apply_info_writes():
    """Im OBS-Takt: Texte in die Quellen „Info · …“ schreiben (nur libobs, keine Oberfläche)."""
    while True:
        try:
            label, text = info_writes.get_nowait()
        except queue.Empty:
            return
        src = obs.obs_get_source_by_name(INFO_PREFIX + label)
        if not src:
            log(f"Infos: Quelle „{INFO_PREFIX}{label}“ fehlt – in OBS unter VOID Studio „Infos-Szene anlegen“.")
            continue
        st = obs.obs_data_create()
        try:
            obs.obs_data_set_string(st, "text", text)
            obs.obs_source_update(src, st)
        finally:
            obs.obs_data_release(st)
            obs.obs_source_release(src)


def web_settings(body):
    st = settings_ref[0]
    if st is None:
        raise RuntimeError("Einstellungen noch nicht geladen")
    for k, v in body.items():
        if k in BOOL_SETTINGS:
            obs.obs_data_set_bool(st, k, bool(v))
        elif k in INT_SETTINGS:
            lo, hi = INT_SETTINGS[k]
            obs.obs_data_set_int(st, k, max(lo, min(hi, int(v))))
        elif k in STR_SETTINGS:
            obs.obs_data_set_string(st, k, str(v)[:300])
        elif k == "ignore":
            obs.obs_data_set_string(st, "ignore", str(v)[:2000])
        elif k == "latest_items":
            for key in LATEST_KEYS:
                obs.obs_data_set_bool(st, "latest_" + key, key in (v or []))
    script_update(st, defer_restart=True)


def web_control(action, pid=None, local=False):
    """Knöpfe der Oberfläche. Langsame Sachen (Downloads) laufen im Hintergrund, die Seite zeigt den Fortschritt."""
    simple = {"replay": ctl_replay, "pause": ctl_pause, "skip": ctl_skip, "reset_session": ctl_reset_session,
              "reset_bits": ctl_reset_bits, "test_chat": test_chat}
    if action in simple:
        simple[action]()
    elif action.startswith("test_") and action[5:] in SAMPLES:
        alert(dict(SAMPLES[action[5:]]), count=False)
    elif action == "twitch_login":
        threading.Thread(target=device_login, args=(local,), daemon=True).start()
    elif action == "twitch_logout":
        on_logout(None, None)
    elif action == "check":
        in_thread(check_updates)
    elif action == "install" and pid:
        in_thread(install_pack, str(pid))
    elif action == "install_all":
        in_thread(lambda: [install_pack(p["id"]) for p in pack_list() if p.get("installed") and status_of(p).startswith("Update")])
    elif action == "setup" and pid:
        return setup_collection(str(pid)) and mgr["notes"][-1]
    elif action == "remove" and pid:
        remove_pack(str(pid))
    elif action == "studio_update":
        in_thread(update_studio)
    elif action == "renew_key":
        web_key(renew=True)
        log("Neuer Schlüssel für die Oberfläche: alte Links und Docks funktionieren nicht mehr.")
    else:
        raise ValueError(f"unbekannte Aktion: {action}")
    return None


# ---------------------------------------------------------------- Lokaler Server für die Szenen
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")   # file:// → localhost

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):                 # keine CORS-Freigabe für die Steuerung
            return self.reply(403, b"", "text/plain", cors=False)
        self.send_response(204)
        self.cors()
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/events":
            return self.sse()
        if path == "/studio":
            return self.reply(200, WEB_HTML.encode("utf-8"), "text/html; charset=utf-8", cors=False)
        if path.startswith("/api/"):
            if not self.authorized():
                return self.json(401, {"error": "Schlüssel fehlt oder ist falsch"})
            if path == "/api/state":
                return self.json(200, web_state())
            return self.json(404, {"error": "unbekannt"})
        if path.startswith("/test/"):
            if self.client_address[0] != "127.0.0.1" and not self.authorized():
                return self.reply(403, b"nur lokal", "text/plain")
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

    def reply(self, code, body, ctype, cors=True):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if cors:
            self.cors()
        self.end_headers()
        self.wfile.write(body)

    def json(self, code, obj):
        self.reply(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", cors=False)

    def authorized(self):
        import hmac
        return hmac.compare_digest(self.headers.get("X-Void-Key", ""), web_key())

    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        if not path.startswith("/api/") or not self.authorized():
            return self.json(401, {"error": "Schlüssel fehlt oder ist falsch"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n).decode("utf-8") if 0 < n <= 65536 else "{}")
            if not isinstance(body, dict):
                raise ValueError("JSON-Objekt erwartet")
        except ValueError as e:
            return self.json(400, {"error": str(e)})
        try:
            if path == "/api/infos":
                web_infos(body)
            elif path == "/api/settings":
                web_settings(body)
            elif path == "/api/control":
                msg = web_control(str(body.get("action", "")), body.get("id"), local=self.client_address[0] == "127.0.0.1")
                return self.json(200, {"ok": True, "message": msg, "state": web_state()})
            else:
                return self.json(404, {"error": "unbekannt"})
        except Exception as e:
            log(f"Oberfläche: {e}")
            return self.json(500, {"error": str(e)})
        self.json(200, {"ok": True, "state": web_state()})

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
        if info["data"]:
            q.put(json.dumps(info_snapshot(), ensure_ascii=False))
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
        srv = ThreadingHTTPServer(("0.0.0.0" if cfg["remote_on"] else "127.0.0.1", cfg["port"]), Handler)
    except OSError as e:
        log(f"Port {cfg['port']} nicht verfügbar: {e}")
        return
    srv.daemon_threads = True
    server[0] = srv
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log(f"Event-Host läuft: http://127.0.0.1:{cfg['port']}/events · Oberfläche: http://127.0.0.1:{cfg['port']}/studio"
        + (" · auch im Heimnetz erreichbar" if cfg["remote_on"] else ""))


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


def device_login(open_browser=True):
    try:
        _device_login(open_browser)
    finally:
        web["device"] = None


def _device_login(open_browser):
    st, j = http("POST", "https://id.twitch.tv/oauth2/device",
                 {"client_id": cfg["client_id"], "scopes": SCOPES}, form=True)
    if st != 200:
        log(f"Login nicht möglich ({st}): {j.get('message', '')} – ist die App als „Öffentlich“ registriert?")
        return
    log(f"Im Browser bestätigen. Code: {j['user_code']}  ·  {j['verification_uri']}")
    interval, deadline = j.get("interval", 5), time.time() + j.get("expires_in", 1800)
    web["device"] = {"code": j["user_code"], "url": j["verification_uri"], "until": int(deadline)}
    if open_browser:
        webbrowser.open(j["verification_uri"])
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


def build_import(pdir):
    """Szenensammlung des Packs für diesen Rechner: ./-Pfade (relativ zum Pack-Ordner) → absolute Pfade,
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
    return data


def make_import(pdir):
    """import.json im Pack-Ordner, für den Import-Dialog von OBS."""
    with open(os.path.join(pdir, "import.json"), "w", encoding="utf-8") as f:
        json.dump(build_import(pdir), f, ensure_ascii=False, indent=4)


# ---------- Szenensammlung direkt in OBS einrichten ----------
# OBS hat dafür keinen Skript-Aufruf; der Import-Dialog schreibt die Sammlung aber auch nur als JSON in den
# Sammlungsordner. Genau das machen wir, mit den Geräte-Einstellungen einer schon vorhandenen Fassung.
KEEP_KINDS = ("browser_source", "scene", "group")      # die kommen immer frisch aus dem Pack


def obs_scenes_dir():
    get = getattr(obs, "os_get_config_path_ptr", None)
    d = get("obs-studio/basic/scenes") if get else None
    if not d:
        base = os.environ.get("APPDATA") or os.path.expanduser(
            "~/Library/Application Support" if sys.platform == "darwin" else "~/.config")
        d = os.path.join(base, "obs-studio", "basic", "scenes")
    return d if os.path.isdir(d) else None


def obs_collections(d):
    """Sammlungen im Ordner: Name → Datei."""
    out = {}
    for fn in os.listdir(d):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(d, fn), encoding="utf-8") as f:
                    out.setdefault(json.load(f).get("name"), os.path.join(d, fn))
            except (OSError, ValueError):
                pass
    return out


def merge_collection(new, old):
    """Aus der alten Fassung übernehmen: Einstellungen gleichnamiger Geräte (Kamera, Spielaufnahme, Medienquellen,
    Texte) und alles, was nicht aus dem Pack stammt (eigene Quellen und Szenen, die Infos)."""
    olds = {s.get("name"): s for s in old.get("sources", [])}
    names = {s["name"] for s in new["sources"]}
    for s in new["sources"]:
        o = olds.get(s["name"])
        if o and o.get("id") == s["id"] and s["id"] not in KEEP_KINDS:
            s["settings"] = o.get("settings", s["settings"])
    extra = [s for n, s in olds.items() if n not in names]
    new["sources"] += extra
    new["scene_order"] += [{"name": s["name"]} for s in extra if s.get("id") == "scene"]
    return new


def setup_collection(pid, quiet=False):
    """Sammlung des Packs in OBS anlegen oder erneuern; gibt ihren Namen zurück. quiet (nach dem Installieren):
    nur neu anlegen, nie ersetzen, und nichts melden."""
    pdir = os.path.join(PACKS_DIR, pid)

    def fail(msg):
        if not quiet:
            mgr["notes"].append(msg)
            log(msg)
        return None
    try:
        data = build_import(pdir)
    except Exception as e:
        return fail(f"{pid}: Sammlung nicht erstellt: {e}")
    name = data.get("name") or pid
    d = obs_scenes_dir()
    if not d:
        return fail(f"OBS-Sammlungsordner nicht gefunden. Bitte von Hand importieren: Szenensammlung → Importieren → {pdir}{os.sep}import.json")
    if obs.obs_frontend_get_current_scene_collection() == name:
        return fail(f"„{name}“ ist gerade aktiv und lässt sich so nicht ersetzen. Kurz eine andere Szenensammlung wählen, dann noch einmal „In OBS einrichten“.")
    path = obs_collections(d).get(name)
    replaced = bool(path)
    if path:
        if quiet:
            return None
        with open(path, encoding="utf-8") as f:
            data = merge_collection(data, json.load(f))
        shutil.copy(path, path + ".bak")                 # vorherige Fassung zur Sicherheit
    else:
        stem = _re.sub(r"[^\w\- ]+", "_", name).strip("_ ") or "VOID"
        path, n = os.path.join(d, stem + ".json"), 2
        while os.path.exists(path):
            path, n = os.path.join(d, f"{stem}_{n}.json"), n + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    if not quiet:
        msg = (f"„{name}“ ist in OBS {'erneuert (Kamera, Spielaufnahme und eigene Quellen übernommen)' if replaced else 'eingerichtet'}. "
               f"Szenensammlung → {name}. Steht sie noch nicht im Menü, OBS einmal neu starten.")
        mgr["notes"].append(msg)
        log(msg)
    return name


# ---------- Infos aus OBS: Szene „VOID · Infos“ mit Textquellen „Info · …“ ----------
INFO_SCENE = "VOID · Infos"
INFO_PREFIX = "Info · "
INFO_DEFAULT = ["Titel", "Statuszeilen"]
INFO_HINT = ("Doppelklick auf eine Info-Quelle und Text eintragen – die Overlays übernehmen ihn sofort. "
             "Leer = Standard. Mehrere Zeilen = Wechsel bzw. Liste. Diese Szene nicht live zeigen.")
info = {"data": {}}
info_lock = threading.Lock()


def info_snapshot():
    return {"type": "info", "data": info["data"]}


def each_source(fn):
    """fn(source) für jede Quelle; obs_enum_sources gibt eine Liste mit Referenzen zurück."""
    lst = obs.obs_enum_sources() or []
    try:
        for src in lst:
            fn(src)
    finally:
        if lst:
            obs.source_list_release(lst)


def source_text(src):
    st = obs.obs_source_get_settings(src)
    try:
        return obs.obs_data_get_string(st, "text")
    finally:
        obs.obs_data_release(st)


def info_tick():
    """Texte der Info-Quellen lesen; bei einer Änderung an alle Szenen schicken. Nur lesen: läuft im Grafik-Thread
    (siehe IRL oben), Szenen oder Quellen anlegen darf hier nie passieren."""
    try:
        apply_info_writes()
        data = {}
        def read(src):
            n = obs.obs_source_get_name(src) or ""
            if n.startswith(INFO_PREFIX):
                data[n[len(INFO_PREFIX):]] = source_text(src).strip()
        each_source(read)
        if data != info["data"]:
            info["data"] = data
            send_all(info_snapshot())
    except Exception as e:
        log(f"Infos: {e}")


def active_pack():
    """Pack der aktiven Sammlung, erkannt an den Browserquellen (…/packs/<id>/obs/…)."""
    found = []
    def look(src):
        if not found and obs.obs_source_get_unversioned_id(src) == "browser_source":
            st = obs.obs_source_get_settings(src)
            m = _re.search(r"/packs/([^/]+)/obs/", obs.obs_data_get_string(st, "local_file").replace("\\", "/"))
            obs.obs_data_release(st)
            if m:
                found.append(m.group(1))
    each_source(look)
    return found[0] if found else None


def text_kind():
    latest = getattr(obs, "obs_get_latest_input_type_id", None)
    for kind in ("text_gdiplus", "text_ft2_source"):
        k = latest(kind) if latest else None
        if k:
            return k
    return None


def ensure_infos(announce=False):
    """Szene „VOID · Infos“ mit den Feldern des aktiven Packs anlegen bzw. ergänzen (vorhandene Texte bleiben)."""
    with info_lock:
        _ensure_infos(announce)


def _ensure_infos(announce):
    pid = active_pack()
    if not pid:
        return announce and log("Infos: Diese Szenensammlung gehört zu keinem VOID-Pack.")
    labels = (installed(pid) or {}).get("infos") or INFO_DEFAULT
    kind = text_kind()
    if not kind:
        return log("Infos: keine Textquelle in dieser OBS-Version gefunden.")
    src = obs.obs_get_source_by_name(INFO_SCENE)
    if src:
        scene = obs.obs_scene_from_source(src)          # geliehen, gehört zu src
    else:
        scene = obs.obs_scene_create(INFO_SCENE)
        src = obs.obs_source_get_ref(obs.obs_scene_get_source(scene))
        obs.obs_scene_release(scene)
        scene = obs.obs_scene_from_source(src)
    added = []
    try:
        y = 40
        for label in [None] + list(labels):
            name = INFO_PREFIX + label if label else "Hinweis"
            have = obs.obs_get_source_by_name(name)
            if have:
                obs.obs_source_release(have)
            else:
                st = obs.obs_data_create()
                obs.obs_data_set_string(st, "text", "" if label else INFO_HINT)
                obj = obs.obs_source_create(kind, name, st, None)
                item = obs.obs_scene_add(scene, obj)
                pos = obs.vec2()
                pos.x, pos.y = 40.0, float(y)
                obs.obs_sceneitem_set_pos(item, pos)
                obs.obs_data_release(st)
                obs.obs_source_release(obj)
                added.append(label or name)
            y += 60
    finally:
        obs.obs_source_release(src)
    if added or announce:
        log(f"Infos: Szene „{INFO_SCENE}“ " + (f"ergänzt um {', '.join(a for a in added if a != 'Hinweis')}." if added else "ist vollständig."))


def on_frontend_event(event):
    if event in (obs.OBS_FRONTEND_EVENT_FINISHED_LOADING, obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED):
        try:                                    # Oberflächen-Thread: hier darf die Infos-Szene entstehen
            ensure_infos()
        except Exception as e:
            log(f"Infos: {e}")


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
            coll = setup_collection(pid, quiet=True)
            note = (f"{info['name']} {info['version']} installiert und in OBS eingerichtet: Szenensammlung → {coll}. Steht sie noch nicht im Menü, OBS einmal neu starten."
                    if coll else
                    f"{info['name']} {info['version']} installiert. Jetzt „In OBS einrichten“ klicken oder importieren: Szenensammlung → Importieren → {dest}{os.sep}import.json")
        elif old.get("structure") != new.get("structure"):
            note = f"{info['name']} auf {info['version']} aktualisiert. Die Szenen haben sich geändert – bitte „In OBS einrichten“ (Kamera und Spielaufnahme bleiben)."
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


def ui_setup(props, prop):
    pid = selected(props)
    if pid and installed(pid):
        setup_collection(pid)
    elif pid:
        log("Erst installieren, dann einrichten.")
    fill_packs(props)
    return True


def ui_infos(props, prop):
    ensure_infos(announce=True)
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


def ui_web(*_):
    webbrowser.open(web_urls()[0])
    return False


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
        tip(obs.obs_properties_add_button(g, "m_install", "Installieren / aktualisieren", ui_install),
            "Ein neues Pack wird dabei gleich als Szenensammlung in OBS eingerichtet.")
        tip(obs.obs_properties_add_button(g, "m_setup", "In OBS einrichten", ui_setup),
            "Legt die Szenensammlung des Packs in OBS an oder erneuert sie nach einem Update. "
            "Kamera, Spielaufnahme und eigene Quellen bleiben. Nicht für die gerade aktive Sammlung.")
        tip(obs.obs_properties_add_button(g, "m_infos", "Infos-Szene anlegen", ui_infos),
            "Szene „VOID · Infos“ mit Textquellen für Titel, Spielname, Ort … in der aktiven Sammlung. "
            "Entsteht sonst beim Laden von selbst.")
        tip(obs.obs_properties_add_button(g, "m_open", "Pack-Ordner öffnen (import.json)", ui_open),
            "Darin liegt import.json, falls du lieber über Szenensammlung → Importieren gehst.")
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

    def webui(g):
        local, remote = web_urls()
        if settings_ref[0] is not None:
            obs.obs_data_set_string(settings_ref[0], "web_url", local)
        tip(obs.obs_properties_add_text(g, "web_url", "Adresse", obs.OBS_TEXT_DEFAULT),
            "Zum Kopieren. Als Dock: Docks → Benutzerdefinierte Browser-Docks → Name „VOID Studio“, diese Adresse.")
        obs.obs_properties_add_button(g, "w_open", "Im Browser öffnen", ui_web)
        tip(obs.obs_properties_add_bool(g, "remote_on", "Auch im Heimnetz erreichbar (Handy, Tablet)"),
            "Andere Geräte im selben Netz oder per VPN (z. B. Tailscale) öffnen die Oberfläche mit Schlüssel. "
            "Den Link zeigt die Oberfläche unter Einstellungen.")
        if remote:
            obs.obs_properties_add_text(g, "w_remote", "Im Heimnetz: " + "  ·  ".join(remote), INFO)

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
          "Packs installieren, als Szenensammlung in OBS einrichten und aktuell halten. Texte wie Spielname oder Ort "
          "trägst du in OBS in der Szene „VOID · Infos“ ein.", packs)
    group(p, "g_web", "Web-Oberfläche",
          "Alles aus diesem Fenster und die Infos (Spielname, Ort …) übersichtlich im Browser oder als Dock in OBS.", webui)
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


def script_update(settings, defer_restart=False):
    """defer_restart: aus einer Anfrage der Oberfläche – den Server erst nach der Antwort neu starten."""
    settings_ref[0] = settings
    cfg["repo"] = obs.obs_data_get_string(settings, "repo").strip() or DEFAULT_REPO
    g = lambda k: obs.obs_data_get_int(settings, k)
    port = g("port")
    remote = obs.obs_data_get_bool(settings, "remote_on")
    port_changed = port != cfg["port"] or remote != cfg["remote_on"] or server[0] is None
    first = started[0] is None
    cfg.update(port=port, remote_on=remote, volume=g("volume"), goal_follow=g("goal_follow"),
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
    if port_changed and defer_restart:
        threading.Timer(0.5, start_server).start()
    elif port_changed:
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
    obs.timer_add(info_tick, 1000)
    obs.obs_frontend_add_event_callback(on_frontend_event)
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
    obs.timer_remove(info_tick)
    obs.obs_frontend_remove_event_callback(on_frontend_event)
    stop.set()
    stop_eventsub()
    stop_server()
    save_state()


# ---------------------------------------------------------------- Web-Oberfläche (aus studio/web.html, build/embed_web.py)
WEB_HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>VOID Studio</title>
<style>
:root{--bg:#07071A;--panel:#0F0F26;--panel2:#16163A;--line:rgba(255,255,255,.09);--text:#F2F3FA;--mute:#A3A6C2;
  --violet:#B303F8;--blue:#1141E4;--lilac:#D27BFF;--sky:#7C9BFF;--green:#3BE39A;--red:#FF5468;--yellow:#FFD45C}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
body{min-height:100vh;background:radial-gradient(800px 500px at 0% 0%,rgba(179,3,248,.16),transparent 70%),radial-gradient(800px 600px at 100% 100%,rgba(17,65,228,.18),transparent 70%),var(--bg);background-attachment:fixed}
a{color:var(--sky)}
header{position:sticky;top:0;z-index:5;background:rgba(7,7,26,.88);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.top{display:flex;align-items:center;gap:12px;padding:12px 16px 8px;flex-wrap:wrap}
.logo{display:flex;align-items:center;gap:10px;font-weight:700;font-size:18px;letter-spacing:.01em}
.logo i{width:26px;height:26px;border-radius:8px;background:linear-gradient(135deg,var(--violet),var(--blue));display:inline-block}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-left:auto}
.chip{font-size:12px;padding:3px 10px;border-radius:12px;background:var(--panel2);color:var(--mute);white-space:nowrap}
.chip.ok{color:#0b2a1d;background:var(--green)}.chip.warn{color:#2a1f00;background:var(--yellow)}.chip.bad{color:#fff;background:var(--red)}
nav{display:flex;gap:2px;padding:0 10px;overflow-x:auto}
nav button{flex:1;min-width:max-content;padding:10px 14px;background:none;border:0;border-bottom:2px solid transparent;color:var(--mute);font:inherit;font-weight:600;cursor:pointer}
nav button.on{color:var(--text);border-color:var(--lilac)}
main{padding:16px;max-width:1100px;margin:0 auto}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}
.card h2{margin:0 0 4px;font-size:15px}
.card p.sub{margin:0 0 12px;color:var(--mute);font-size:13px}
.field{margin:0 0 14px}
.field label{display:flex;justify-content:space-between;gap:8px;font-weight:600;font-size:13px;margin-bottom:5px}
.field small{display:block;color:var(--mute);font-size:12px;margin-top:4px}
.saved{color:var(--green);font-weight:500;opacity:0;transition:opacity .3s}.saved.on{opacity:1}
input[type=text],input[type=number],textarea{width:100%;padding:9px 11px;border-radius:9px;border:1px solid var(--line);background:#0A0A1F;color:var(--text);font:inherit}
textarea{min-height:84px;resize:vertical}
input:focus,textarea:focus{outline:2px solid rgba(210,123,255,.55);outline-offset:0;border-color:transparent}
input[type=range]{width:100%;accent-color:var(--lilac)}
.check{display:flex;align-items:center;gap:9px;margin:6px 0;font-size:14px;cursor:pointer}
.field label.check{justify-content:flex-start;font-weight:400;font-size:14px}
#infos-card{grid-column:1/-1}
#infos-form{display:grid;gap:0 18px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.check input{width:18px;height:18px;accent-color:var(--violet)}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{padding:9px 14px;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font:inherit;font-weight:600;cursor:pointer}
.btn:hover{border-color:rgba(210,123,255,.5)}
.btn.primary{background:linear-gradient(135deg,var(--violet),var(--blue));border:0}
.btn.danger{color:var(--red)}
.btn.small{padding:6px 10px;font-size:13px}
.btn:disabled{opacity:.5;cursor:default}
.note{padding:10px 12px;border-radius:10px;background:var(--panel2);color:var(--mute);font-size:13px;margin:0 0 12px}
.note.warn{background:rgba(255,212,92,.12);color:var(--yellow)}
.note.ok{background:rgba(59,227,154,.10);color:var(--green)}
.goal{margin:8px 0 12px}.goal .t{display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px}
.bar{height:8px;border-radius:4px;background:rgba(255,255,255,.08);overflow:hidden}
.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--violet),var(--sky));border-radius:4px;transition:width .6s}
.kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:14px}.kv b{color:var(--mute);font-weight:500}
.pack{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-top:1px solid var(--line)}
.pack:first-of-type{border-top:0}
.pack img{width:132px;aspect-ratio:16/9;object-fit:cover;border-radius:8px;background:var(--panel2);flex-shrink:0}
.pack .n{font-weight:700}.pack .s{color:var(--mute);font-size:13px;margin:2px 0 8px}
.code{font:600 26px/1 ui-monospace,Consolas,monospace;letter-spacing:.12em;color:var(--lilac);margin:6px 0}
.url{font:12px/1.4 ui-monospace,Consolas,monospace;word-break:break-all;background:#0A0A1F;border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:6px 0}
.log{font:12px/1.5 ui-monospace,Consolas,monospace;color:var(--mute);max-height:260px;overflow:auto}
.log div{padding:2px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:var(--panel2);border:1px solid var(--line);padding:10px 16px;border-radius:12px;opacity:0;transition:opacity .3s;pointer-events:none;max-width:90vw}
.toast.on{opacity:1}
.hidden{display:none!important}
.big{font-size:22px;font-weight:700}
@media (max-width:420px){main{padding:10px}.grid{grid-template-columns:1fr}.pack img{width:96px}}
</style>
</head>
<body>
<header>
  <div class="top">
    <div class="logo"><i></i>VOID Studio</div>
    <div class="chips" id="chips"></div>
  </div>
  <nav id="tabs">
    <button data-tab="infos" class="on">Infos</button>
    <button data-tab="live">Live</button>
    <button data-tab="packs">Packs</button>
    <button data-tab="settings">Einstellungen</button>
  </nav>
</header>
<main>
  <div id="nokey" class="card hidden">
    <h2>Schlüssel fehlt</h2>
    <p class="sub">Öffne die Oberfläche über VOID Studio in OBS (Werkzeuge → Skripte → VOID Studio → Web-Oberfläche → „Im Browser öffnen“), oder füge den Link mit Schlüssel ein.</p>
  </div>

  <section id="tab-infos">
    <div class="grid">
      <div class="card" id="infos-card">
        <h2 id="infos-title">Infos</h2>
        <p class="sub" id="infos-sub"></p>
        <div id="infos-form"></div>
      </div>
    </div>
  </section>

  <section id="tab-live" class="hidden">
    <div class="grid">
      <div class="card">
        <h2>Alerts</h2>
        <p class="sub" id="alert-state"></p>
        <div class="field"><label>Lautstärke <span id="vol-v"></span></label><input type="range" min="0" max="100" id="volume"></div>
        <div class="row">
          <button class="btn" data-act="pause" id="pause-btn">Pausieren</button>
          <button class="btn" data-act="skip">Überspringen</button>
          <button class="btn" data-act="replay">Letzten wiederholen</button>
        </div>
      </div>
      <div class="card">
        <h2>Testen</h2>
        <p class="sub">Schickt eine Beispiel-Einblendung an alle offenen Szenen, ohne Twitch.</p>
        <div class="row">
          <button class="btn small" data-act="test_follow">Follow</button>
          <button class="btn small" data-act="test_sub">Abo</button>
          <button class="btn small" data-act="test_resub">Abo verlängert</button>
          <button class="btn small" data-act="test_gift">Geschenk-Abos</button>
          <button class="btn small" data-act="test_cheer">Bits</button>
          <button class="btn small" data-act="test_raid">Raid</button>
          <button class="btn small" data-act="test_redeem">Kanalpunkte</button>
          <button class="btn small" data-act="test_chat">Chatnachricht</button>
        </div>
      </div>
      <div class="card">
        <h2>Ziele</h2>
        <p class="sub">Fortschrittsbalken in den Szenen. 0 blendet ein Ziel aus.</p>
        <div id="goals"></div>
        <div class="field"><label>Follower-Ziel</label><input type="number" min="0" data-set="goal_follow"></div>
        <div class="field"><label>Abo-Ziel</label><input type="number" min="0" data-set="goal_sub"></div>
        <div class="field"><label>Bits-Ziel</label><input type="number" min="0" step="100" data-set="goal_bits"></div>
        <button class="btn small" data-act="reset_bits">Bits-Ziel zurücksetzen</button>
      </div>
      <div class="card">
        <h2>Session</h2>
        <p class="sub">Daraus entsteht der Rückblick in „Stream endet“.</p>
        <div class="kv" id="session"></div>
        <div class="row" style="margin-top:12px"><button class="btn small danger" data-act="reset_session" data-confirm="Session-Rückblick zurücksetzen?">Rückblick zurücksetzen</button></div>
      </div>
      <div class="card hidden" id="irl-card">
        <h2>IRL</h2>
        <p class="sub" id="irl-state"></p>
      </div>
    </div>
  </section>

  <section id="tab-packs" class="hidden">
    <div class="grid">
      <div class="card" style="grid-column:1/-1">
        <div id="studio-update" class="note warn hidden"></div>
        <div id="pack-busy" class="note hidden"></div>
        <div class="row">
          <button class="btn" data-act="check">Nach Updates suchen</button>
          <button class="btn" data-act="install_all">Alle Pack-Updates installieren</button>
        </div>
      </div>
      <div class="card" style="grid-column:1/-1"><div id="packs"></div></div>
    </div>
  </section>

  <section id="tab-settings" class="hidden">
    <div class="grid">
      <div class="card">
        <h2>Twitch</h2>
        <p class="sub" id="twitch-state"></p>
        <div id="device" class="hidden">
          <div class="note">Bei Twitch bestätigen: <a id="device-link" target="_blank" rel="noopener">twitch.tv/activate</a> öffnen und diesen Code eingeben:</div>
          <div class="code" id="device-code"></div>
        </div>
        <div class="row">
          <button class="btn primary" data-act="twitch_login">Mit Twitch verbinden</button>
          <button class="btn" data-act="twitch_logout" data-confirm="Von Twitch abmelden?">Abmelden</button>
        </div>
      </div>
      <div class="card">
        <h2>Chat</h2>
        <div class="field"><label>Ausgeblendete Namen</label><input type="text" data-set="ignore"><small>Kommagetrennt, z. B. Bots wie streamelements, nightbot.</small></div>
        <label class="check"><input type="checkbox" data-set="hide_cmd">Befehle mit ! ausblenden</label>
      </div>
      <div class="card">
        <h2>Spielszenen und Rückblick</h2>
        <label class="check"><input type="checkbox" data-set="show_latest">Letzte Unterstützer an der Game-Kamera zeigen</label>
        <div id="latest-items" style="padding-left:26px"></div>
      </div>
      <div class="card">
        <h2>IRL</h2>
        <p class="sub">Überwacht die Kamera-Quelle und schaltet bei einem Abbruch auf „Verbindung weg“ und zurück.</p>
        <label class="check"><input type="checkbox" data-set="irl_auto">Bei Abbruch automatisch umschalten</label>
        <div class="field"><label>Kamera-Quelle</label><input type="text" data-set="irl_source"></div>
        <div class="row">
          <div class="field" style="flex:1"><label>Umschalten nach (s)</label><input type="number" min="1" max="60" data-set="irl_delay"></div>
          <div class="field" style="flex:1"><label>Zurück nach (s)</label><input type="number" min="1" max="60" data-set="irl_back"></div>
        </div>
      </div>
      <div class="card">
        <h2>Telemetrie (ETS2/ATS)</h2>
        <label class="check"><input type="checkbox" data-set="tele_on">Spiel-Telemetrie weiterreichen</label>
        <div class="field"><label>Telemetrie-URL</label><input type="text" data-set="tele_url"></div>
      </div>
      <div class="card">
        <h2>Zugriff</h2>
        <p class="sub">Als Dock in OBS: Docks → Benutzerdefinierte Browser-Docks → Name „VOID Studio“, diese Adresse:</p>
        <div class="url" id="local-url"></div>
        <button class="btn small" data-copy="local-url">Kopieren</button>
        <hr style="border:0;border-top:1px solid var(--line);margin:16px 0">
        <label class="check"><input type="checkbox" data-set="remote_on">Auch im Heimnetz erreichbar (Handy, Tablet)</label>
        <small style="color:var(--mute);font-size:12px">Geräte im selben Netz oder per VPN (z. B. Tailscale) öffnen die Oberfläche mit diesem Link. Wer ihn hat, kann VOID Studio steuern – nicht weitergeben.</small>
        <div id="remote-urls"></div>
        <div class="row" style="margin-top:12px"><button class="btn small danger" data-act="renew_key" data-confirm="Neuen Schlüssel erzeugen? Alle bisherigen Links und Docks funktionieren danach nicht mehr.">Neuen Schlüssel erzeugen</button></div>
      </div>
      <div class="card">
        <h2>Protokoll</h2>
        <div class="log" id="log"></div>
      </div>
    </div>
  </section>
</main>
<div class="toast" id="toast"></div>
<script>
/* VOID Studio – Web-Oberfläche. Schlüssel aus #k=…, jede Anfrage schickt ihn im Header X-Void-Key. */
let KEY=new URLSearchParams(location.hash.slice(1)).get('k')||'';
try{if(KEY)localStorage.setItem('voidKey',KEY);else KEY=localStorage.getItem('voidKey')||''}catch(_){}
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const el=(t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const num=n=>Number(n||0).toLocaleString('de-DE');
let S=null;

async function api(path,body){
  const r=await fetch(path,{method:body?'POST':'GET',headers:Object.assign({'X-Void-Key':KEY},body?{'Content-Type':'application/json'}:{}),
    body:body?JSON.stringify(body):undefined,cache:'no-store'});
  const j=await r.json().catch(()=>({}));
  if(r.status===401){showNoKey();throw new Error('Schlüssel fehlt')}
  if(!r.ok)throw new Error(j.error||('HTTP '+r.status));
  return j;
}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('on');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('on'),2600)}
function showNoKey(){$('#nokey').classList.remove('hidden');$$('section').forEach(s=>s.classList.add('hidden'))}

/* ---------- Tabs ---------- */
function tab(name){
  $$('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.tab===name));
  $$('main>section').forEach(s=>s.classList.toggle('hidden',s.id!=='tab-'+name));
  try{localStorage.setItem('voidTab',name)}catch(_){}
}
$$('#tabs button').forEach(b=>b.onclick=()=>tab(b.dataset.tab));
try{const t=localStorage.getItem('voidTab');if(t&&$('#tab-'+t))tab(t)}catch(_){}

/* ---------- Eingaben: beim Tippen nicht überschreiben ---------- */
const busy=new WeakSet();
function setVal(inp,v){if(document.activeElement===inp||busy.has(inp))return;
  if(inp.type==='checkbox')inp.checked=!!v;else if(inp.value!==String(v??''))inp.value=v??''}
function debounce(fn,ms){let h;return(...a)=>{clearTimeout(h);h=setTimeout(()=>fn(...a),ms)}}

/* ---------- Infos ---------- */
let infoKeys='';
function renderInfos(){
  const form=$('#infos-form'),list=S.infos||[];
  $('#infos-title').textContent=S.pack?`Infos · ${S.pack.name}`:'Infos';
  $('#infos-sub').innerHTML=S.pack
    ?'Die Overlays übernehmen jede Änderung sofort. Leer = Standard des Packs.'+(list.some(i=>!i.exists)?' <br><b style="color:var(--yellow)">In OBS fehlt die Szene „VOID · Infos“ oder ein Feld darin: in OBS unter Werkzeuge → Skripte → VOID Studio „Infos-Szene anlegen“.</b>':'')
    :`Die aktive Szenensammlung „${esc(S.collection||'')}“ gehört zu keinem VOID-Pack. In OBS eine Pack-Sammlung wählen.`;
  const keys=list.map(i=>i.label).join('|');
  if(keys!==infoKeys){
    infoKeys=keys;form.innerHTML='';
    list.forEach(i=>{
      const f=el('div','field');const lab=el('label','',`<span>${esc(i.label)}</span><span class="saved">gespeichert</span>`);
      let inp;
      if(i.label==='Wunschliste'){
        inp=el('input');inp.type='checkbox';const c=el('label','check');c.append(inp,document.createTextNode('„Auf die Wunschliste!“-Sticker zeigen'));
        f.append(lab,c);inp.onchange=()=>saveInfo(i.label,inp.checked?'ja':'',lab);
      }else{
        inp=i.multiline?el('textarea'):el('input');if(!i.multiline)inp.type='text';
        inp.oninput=debounce(()=>saveInfo(i.label,inp.value,lab),700);
        f.append(lab,inp);
      }
      inp.dataset.info=i.label;
      if(i.help&&i.label!=='Wunschliste')f.append(el('small','',esc(i.help)));
      form.append(f);
    });
  }
  list.forEach(i=>{const inp=form.querySelector(`[data-info="${CSS.escape(i.label)}"]`);if(!inp)return;
    if(inp.type==='checkbox')setVal(inp,/^(ja|an|1|x|yes|true)$/i.test(i.value));else setVal(inp,i.value)});
}
async function saveInfo(label,value,lab){
  try{await api('/api/infos',{[label]:value});const s=lab.querySelector('.saved');s.classList.add('on');setTimeout(()=>s.classList.remove('on'),1500)}
  catch(e){toast('Nicht gespeichert: '+e.message)}
}

/* ---------- Einstellungen (data-set) ---------- */
$$('[data-set]').forEach(inp=>{
  const k=inp.dataset.set;
  const send=v=>api('/api/settings',{[k]:v}).then(r=>{S=r.state;render()}).catch(e=>toast('Nicht gespeichert: '+e.message));
  if(inp.type==='checkbox')inp.onchange=()=>send(inp.checked);
  else if(inp.type==='number')inp.onchange=()=>send(parseInt(inp.value||'0',10));
  else inp.oninput=debounce(()=>send(inp.value),700);
});
$('#volume').oninput=()=>$('#vol-v').textContent=$('#volume').value+' %';
$('#volume').onchange=()=>api('/api/settings',{volume:parseInt($('#volume').value,10)}).catch(e=>toast(e.message));
const LATEST=[['follow','Follow'],['sub','Abo'],['gift','Geschenk'],['cheer','Bits'],['raid','Raid']];
LATEST.forEach(([k,l])=>{const c=el('label','check');const i=el('input');i.type='checkbox';i.dataset.latest=k;c.append(i,document.createTextNode(l));$('#latest-items').append(c);
  i.onchange=()=>api('/api/settings',{latest_items:$$('[data-latest]').filter(x=>x.checked).map(x=>x.dataset.latest)}).catch(e=>toast(e.message))});

/* ---------- Knöpfe (data-act) ---------- */
document.addEventListener('click',async ev=>{
  const b=ev.target.closest('[data-act]');
  if(b){
    if(b.dataset.confirm&&!confirm(b.dataset.confirm))return;
    b.disabled=true;
    try{const r=await api('/api/control',{action:b.dataset.act,id:b.dataset.id});S=r.state;render();if(r.message)toast(r.message)}
    catch(e){toast(e.message)}
    finally{b.disabled=false}
    return;
  }
  const c=ev.target.closest('[data-copy]');
  if(c){const t=$('#'+c.dataset.copy).textContent;
    (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>toast('Kopiert')).catch(()=>{
      const r=document.createRange();r.selectNodeContents($('#'+c.dataset.copy));getSelection().removeAllRanges();getSelection().addRange(r);toast('Markiert – Strg+C')})}
});

/* ---------- Anzeige ---------- */
function render(){
  if(!S)return;
  const tw=S.twitch;
  $('#chips').innerHTML=[
    tw.connected?`<span class="chip ok">Twitch: ${esc(tw.login||'verbunden')}</span>`:`<span class="chip ${tw.saved?'warn':'bad'}">Twitch: ${tw.saved?'verbindet …':'nicht verbunden'}</span>`,
    S.pack?`<span class="chip">${esc(S.pack.name)}</span>`:'',
    S.live.paused?'<span class="chip warn">Alerts pausiert</span>':'',
    S.studio_update?`<span class="chip warn">Update ${esc(S.studio_update)}</span>`:'',
    `<span class="chip">${esc(S.version)}</span>`].join('');
  renderInfos();
  /* Live */
  $('#alert-state').textContent=S.live.paused?'Pausiert – neue Alerts warten, bis du fortsetzt.':'Alerts laufen.';
  $('#pause-btn').textContent=S.live.paused?'Fortsetzen':'Pausieren';
  setVal($('#volume'),S.live.volume);$('#vol-v').textContent=$('#volume').value+' %';
  $('#goals').innerHTML=(S.live.goals||[]).map(g=>`<div class="goal"><div class="t"><span>${esc(g.label)}</span><span>${num(g.cur)} / ${num(g.target)}</span></div><div class="bar"><i style="width:${Math.min(100,g.cur/g.target*100)}%"></i></div></div>`).join('')||'<p class="sub">Keine Ziele aktiv.</p>';
  const ss=S.live.session||{},cnt=o=>Object.values(o||{}).reduce((a,b)=>a+b,0);
  $('#session').innerHTML=`<b>Neue Follower</b><span>${num((ss.follows||[]).length)}</span><b>Abos</b><span>${num((ss.subs||[]).length)}</span>
    <b>Verschenkte Abos</b><span>${num(cnt(ss.gifts))}</span><b>Bits</b><span>${num(cnt(ss.bits))}</span><b>Raids</b><span>${num((ss.raids||[]).length)}</span>
    <b>Follower gesamt</b><span>${S.live.followers==null?'–':num(S.live.followers)}</span><b>Abonnenten</b><span>${S.live.subs==null?'–':num(S.live.subs)}</span>`;
  const irlOn=S.irl.auto||(S.pack&&S.pack.id==='irl');
  $('#irl-card').classList.toggle('hidden',!irlOn);
  if(irlOn){const since=S.irl.since?Math.max(0,Math.round(Date.now()/1000-S.irl.since)):0;
    $('#irl-state').innerHTML=S.irl.live==null?`„${esc(S.irl.source)}“ wird überwacht, sobald die Quelle in der Sammlung ist.`
      :S.irl.live?`<span class="big" style="color:var(--green)">Signal da</span><br>„${esc(S.irl.source)}“ läuft.`
      :`<span class="big" style="color:var(--red)">Signal weg</span><br>seit ${Math.floor(since/60)}:${String(since%60).padStart(2,'0')} min`;}
  /* Packs */
  const up=$('#studio-update');up.classList.toggle('hidden',!S.studio_update);
  if(S.studio_update)up.innerHTML=`VOID Studio ${esc(S.studio_update)} ist verfügbar: ${esc((S.studio_changelog||[]).slice(0,2).join(' · '))}<div class="row" style="margin-top:8px"><button class="btn small primary" data-act="studio_update">Jetzt aktualisieren</button></div>`;
  const msg=[S.busy,S.error,...(S.notes||[]).slice(-1)].filter(Boolean);
  $('#pack-busy').classList.toggle('hidden',!msg.length);$('#pack-busy').textContent=msg.join(' · ');
  $('#packs').innerHTML=(S.packs||[]).map(p=>`<div class="pack">${p.preview?`<img src="${esc(p.preview)}" alt="" loading="lazy">`:'<img alt="">'}
    <div><div class="n">${esc(p.name)}</div><div class="s">${esc(p.status)}</div><div class="row">
      <button class="btn small ${p.installed?'':'primary'}" data-act="install" data-id="${esc(p.id)}">${p.installed?(p.status.startsWith('Update')?'Aktualisieren':'Neu installieren'):'Installieren'}</button>
      ${p.installed?`<button class="btn small" data-act="setup" data-id="${esc(p.id)}">In OBS einrichten</button>
      <button class="btn small danger" data-act="remove" data-id="${esc(p.id)}" data-confirm="${esc(p.name)} entfernen? Die Szenensammlung in OBS bleibt.">Entfernen</button>`:''}
    </div></div></div>`).join('')||'<p class="sub">Pack-Liste wird geladen …</p>';
  /* Einstellungen */
  $('#twitch-state').textContent=tw.status;
  $('#device').classList.toggle('hidden',!tw.device);
  if(tw.device){$('#device-code').textContent=tw.device.code;$('#device-link').href=tw.device.url;$('#device-link').textContent=tw.device.url.replace(/^https?:\/\//,'')}
  $$('[data-set]').forEach(i=>setVal(i,S.settings[i.dataset.set]));
  $$('[data-latest]').forEach(i=>setVal(i,(S.settings.latest_items||[]).includes(i.dataset.latest)));
  $('#local-url').textContent=S.local_url;
  $('#remote-urls').innerHTML=S.settings.remote_on?(S.remote_urls.length?S.remote_urls.map((u,i)=>`<div class="url" id="ru${i}">${esc(u)}</div><button class="btn small" data-copy="ru${i}">Kopieren</button>`).join('')
    :'<div class="note warn">Keine Netzwerk-Adresse gefunden.</div>'):'';
  $('#log').innerHTML=(S.log||[]).slice().reverse().map(([t,m])=>`<div>${esc(t)} · ${esc(m)}</div>`).join('');
}

async function poll(){
  if(!KEY){showNoKey();return}
  try{S=await api('/api/state');render()}catch(e){if(e.message!=='Schlüssel fehlt')$('#chips').innerHTML='<span class="chip bad">VOID Studio nicht erreichbar – läuft OBS?</span>'}
}
poll();
setInterval(()=>{if(!document.hidden)poll()},2000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()});
</script>
</body>
</html>
"""  # Ende WEB_HTML
