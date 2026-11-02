#!/usr/bin/env python3
"""Společný omezovač rychlosti: každý síťový požadavek nástrojů musí jít přes něj (SKILL.md, oddíl „Síť“).

Použití (z kořene projektu, vždy s -I):
  python3 -I tools/omezovac.py <nástroj.py|nástroj.sh|cesta> [argumenty]   spustí nástroj, jeho požadavky jdou přes limit
  python3 -I tools/omezovac.py curl <argumenty curl>                        jeden požadavek curl přes limit
  python3 -I tools/omezovac.py stav                                         které weby jsou zablokované a do kdy
  python3 -I tools/omezovac.py hook                                         hook PreToolUse pro Claude Code (JSON na stdin)
  python3 -I tools/omezovac.py nainstaluj-hook [složka projektu]            přidá hook do .claude/settings.json

Pravidla (limit platí pro každý web zvlášť a sdílí se přes soubory ve složce pracovni/.omezovac/,
takže platí pro všechny souběžné procesy a subagenty):
  - vyhledávání, API a HTML stránky: nejvýš 1 požadavek za 2 s (třída „pomalu“),
  - dlaždice a obrázky skenů (.jpg, .png, TileGroup, IIIF default.jpg…): nejvýš 5 za s (třída „rychle“),
  - odpověď 429 nebo 503: web je na 20 minut zablokovaný pro všechny procesy, nástroj skončí
    s kódem 75 a požadavek se neopakuje. Zablokovaný web odmítne každý další požadavek hned.
Web = poslední dvě části jména (ebadatelna.soapraha.cz → soapraha.cz). Localhost se neomezuje.

Python nástroje (urllib, requests i vše postavené na http.client) se zachytávají v procesu, shell
skripty a podprocesy dostanou na PATH náhradní curl, který vede sem. Nástroje se nijak neupravují.
Proměnné: RODOKMEN_OMEZOVAC_DIR = jiná složka se stavem (např. společná pro víc worktree),
RODOKMEN_OMEZOVAC_I_LOKALNI=1 = omezovat i localhost (testy).
Hook hlídá i nástroj WebFetch (počká na volný čas, zablokovaný web odmítne); odpověď 429/503 u něj
ale nevidí. Prohlížeč (Browser, Chrome) hook nehlídá.
Meze: netestováno na Windows (msvcrt místo fcntl); redirecty uvnitř jednoho curl -L (nejvýš 5) se
nepočítají zvlášť; síťové přístupy mimo http.client a curl (holé sockety, jiné programy) hlídá jen hook.
"""
import atexit, json, os, re, shutil, signal, subprocess, sys, tempfile, time, urllib.parse

try:
    import fcntl
except ImportError:                      # Windows
    fcntl = None
    import msvcrt

INTERVAL = {"pomalu": 2.0, "rychle": 0.2}   # nejmenší odstup požadavků na jeden web (s)
BLOKACE = 20 * 60                           # na jak dlouho zablokovat web po 429/503 (s)
KOD_KONEC = 75                              # návratový kód při blokaci (EX_TEMPFAIL)
ZNACKA = "@@OMEZOVAC@@"
RYCHLE_CESTA = re.compile(r"\.(jpe?g|png|gif|webp|tiff?|jp2)$", re.I)
RYCHLE_URL = re.compile(r"TileGroup|/tiles?/|(default|native)\.(jpe?g|png)", re.I)


# ---------- společný stav na disku ----------

def koren(start=None):
    p = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isfile(os.path.join(p, "data", "STAV.md")):
            return p
        nad = os.path.dirname(p)
        if nad == p:
            return None
        p = nad


def adresar():
    d = os.environ.get("RODOKMEN_OMEZOVAC_DIR")
    if not d:
        k = koren()
        d = os.path.join(k, "pracovni", ".omezovac") if k else os.path.join(tempfile.gettempdir(), "rodokmen-omezovac")
    os.makedirs(d, exist_ok=True)
    return d


class Zamek:
    """Výhradní zámek nad souborem stavu webu; drží ho jen kratičce (čtení, zápis)."""
    def __init__(self, cesta):
        self.cesta = cesta

    def __enter__(self):
        self.f = os.fdopen(os.open(self.cesta, os.O_RDWR | os.O_CREAT, 0o644), "r+b")
        if fcntl:
            fcntl.flock(self.f, fcntl.LOCK_EX)
        else:
            while True:
                try:
                    self.f.seek(0)
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
        return self

    def __exit__(self, *a):
        try:
            if not fcntl:
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.f.close()          # zavření uvolní i flock

    def nacti(self):
        self.f.seek(0)
        try:
            return json.loads(self.f.read().decode() or "{}")
        except ValueError:
            return {}

    def uloz(self, stav):
        self.f.seek(0)
        self.f.truncate()
        self.f.write(json.dumps(stav).encode())
        self.f.flush()


def soubor(web):
    return os.path.join(adresar(), re.sub(r"[^\w.:-]", "_", web) + ".json")


def web_z_hostu(host):
    h = (host or "").lower().strip("[]").rstrip(".")
    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+|[0-9a-f]*:[0-9a-f:]*", h):
        return h
    cast = h.split(".")
    n = 3 if len(cast) >= 3 and len(cast[-1]) == 2 and cast[-2] in ("co", "com", "org", "net", "gov", "ac") else 2
    return ".".join(cast[-n:])


def lokalni(host):
    h = (host or "").lower().strip("[]")
    if os.environ.get("RODOKMEN_OMEZOVAC_I_LOKALNI"):
        return False
    return h in ("localhost", "::1", "") or h.startswith("127.") or h.endswith(".localhost")


def trida(url):
    cesta = urllib.parse.urlsplit(url).path
    return "rychle" if RYCHLE_CESTA.search(cesta) or RYCHLE_URL.search(url) else "pomalu"


def konec(zprava):
    sys.stderr.write("omezovač: " + zprava + "\n")
    sys.stderr.flush()
    if os.environ.get("RODOKMEN_OMEZOVAC_SKUPINA") and hasattr(os, "killpg"):
        os.killpg(os.getpgrp(), signal.SIGTERM)      # shell skript s blokovaným curl se ukončí celý
    os._exit(KOD_KONEC)             # záměrně ne výjimka: nástroje umí SystemExit i Exception odchytit


def cas(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))


def rezervuj(web, tr, spat=True):
    """Zarezervuje nejbližší volný čas pro požadavek na web a (spat) počká na něj."""
    ted = time.time()
    with Zamek(soubor(web)) as z:
        s = z.nacti()
        do = s.get("blokace_do", 0)
        if do <= ted:
            slot = max(ted, s.get("dalsi", {}).get(tr, 0))
            s.setdefault("dalsi", {})[tr] = slot + INTERVAL[tr]
            z.uloz(s)
    if do > ted:
        konec(f"{web} je zablokovaný do {cas(do)} ({s.get('duvod', '429/503')}); nic neopakuj, počkej a zkus to později.")
    if spat and slot - ted > 0:
        if slot - ted >= 3:
            sys.stderr.write(f"omezovač: {web} ({tr}) – čekám {slot - ted:.0f} s\n")
        time.sleep(slot - ted)


def blokuj(web, kod):
    do = time.time() + BLOKACE
    with Zamek(soubor(web)) as z:
        s = z.nacti()
        s["blokace_do"] = max(s.get("blokace_do", 0), do)
        s["duvod"] = f"HTTP {kod}"
        z.uloz(s)
    konec(f"{web} vrátil HTTP {kod}, zablokováno na 20 minut (do {cas(do)}). Nástroj končí, požadavek se neopakuje.")


# ---------- Python: zachycení http.client (urllib, requests, urllib3…) ----------

def zapni_python():
    import http.client as hc
    put, get = hc.HTTPConnection.putrequest, hc.HTTPConnection.getresponse

    def putrequest(self, method, url, *a, **k):
        host = getattr(self, "_tunnel_host", None) or self.host
        if url.startswith(("http://", "https://")):          # absolutní adresa při průchodu proxy
            host = urllib.parse.urlsplit(url).hostname or host
        self._omez_web = None
        if not lokalni(host):
            self._omez_web = web_z_hostu(host)
            rezervuj(self._omez_web, trida(url))
        return put(self, method, url, *a, **k)

    def getresponse(self):
        r = get(self)
        if getattr(self, "_omez_web", None) and r.status in (429, 503):
            blokuj(self._omez_web, r.status)
        return r

    hc.HTTPConnection.putrequest = putrequest
    hc.HTTPConnection.getresponse = getresponse


def nahradni_curl():
    """Složka s příkazem curl, který vede přes omezovač; přidá se na začátek PATH podprocesů."""
    d = tempfile.mkdtemp(prefix="omezovac_")
    atexit.register(shutil.rmtree, d, True)
    p = os.path.join(d, "curl")
    with open(p, "w") as f:
        f.write(f'#!/bin/sh\nexec "{sys.executable}" -I "{os.path.abspath(__file__)}" curl "$@"\n')
    os.chmod(p, 0o755)
    os.environ["RODOKMEN_OMEZOVAC_SHIM"] = d
    os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def spust_nastroj(cesta, args):
    if not os.path.isfile(cesta):
        v_nastrojich = os.path.join(os.path.dirname(os.path.abspath(__file__)), cesta)
        if not os.path.isfile(v_nastrojich):
            sys.exit(f"omezovač: nástroj {cesta} neexistuje")
        cesta = v_nastrojich
    nahradni_curl()
    if cesta.endswith(".py"):
        import runpy
        zapni_python()
        sys.argv = [cesta, *args]
        runpy.run_path(cesta, run_name="__main__")
    elif cesta.endswith(".sh"):
        env = dict(os.environ, RODOKMEN_OMEZOVAC_SKUPINA="1")
        p = subprocess.Popen(["bash", cesta, *args], env=env, start_new_session=hasattr(os, "killpg"))
        try:
            kod = p.wait()
        except KeyboardInterrupt:
            if hasattr(os, "killpg"):
                os.killpg(p.pid, signal.SIGTERM)
            kod = p.wait()
        sys.exit(KOD_KONEC if kod == -signal.SIGTERM else kod)
    else:
        sys.exit("omezovač: spouští jen .py a .sh (a „curl“)")


# ---------- curl ----------

KRATKE_S_ARG = set("AbcCdDeEFHKmoPQrtTuUwxXyYz")
KRATKE_BEZ = set("sSLkfvIiGNOJVgqhnaBlRpj#0123456")
DLOUHE_S_ARG = {"--user-agent", "--referer", "--cookie", "--cookie-jar", "--output", "--header", "--data",
                "--data-raw", "--data-binary", "--data-ascii", "--data-urlencode", "--form", "--form-string",
                "--request", "--max-time", "--connect-timeout", "--retry-delay", "--retry-max-time", "--proxy",
                "--user", "--range", "--upload-file", "--cacert", "--capath", "--cert", "--key", "--resolve",
                "--connect-to", "--dump-header", "--limit-rate", "--interface", "--json", "--time-cond",
                "--output-dir", "--stderr", "--unix-socket", "--max-redirs", "--max-filesize", "--speed-limit",
                "--speed-time", "--keepalive-time", "--dns-servers", "--proxy-user", "--oauth2-bearer",
                "--continue-at", "--request-target", "--expect100-timeout", "--ciphers", "--url"}
DLOUHE_BEZ = {"--silent", "--show-error", "--location", "--insecure", "--fail", "--fail-with-body", "--head",
              "--include", "--globoff", "--get", "--remote-name", "--remote-name-all", "--no-buffer",
              "--compressed", "--http1.0", "--http1.1", "--http2", "--ipv4", "--ipv6", "--progress-bar",
              "--no-progress-meter", "--verbose", "--junk-session-cookies", "--list-only", "--netrc",
              "--no-keepalive", "--raw", "--tcp-nodelay", "--path-as-is", "--remote-time", "--create-dirs",
              "--anyauth", "--basic", "--digest", "--disable", "--version", "--help", "--remote-header-name",
              "--location-trusted", "--retry-connrefused"}
ZAKAZANE = {"-Z": "souběžné stahování", "--parallel": "souběžné stahování", "-K": "konfigurační soubor",
            "--config": "konfigurační soubor", "--next": "víc požadavků v jednom curl", "-:": "víc požadavků v jednom curl",
            "--retry": "automatické opakování", "-w": "vlastní -w (status čte omezovač)",
            "--write-out": "vlastní -w (status čte omezovač)"}


def spust_curl(args):
    urls, i, glob, loc, maxr = [], 0, False, False, False

    def zakaz(n):
        sys.exit(f"omezovač: curl s {n} ({ZAKAZANE[n]}) nejde přes omezovač; rozděl na samostatné volání.")

    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            urls += args[i:]
            break
        if a.startswith("--"):
            n, eq, v = a.partition("=")
            if n in ZAKAZANE:
                zakaz(n)
            glob |= n == "--globoff"
            loc |= n == "--location"
            maxr |= n == "--max-redirs"
            if n == "--url":
                urls.append(v if eq else args[i])
                i += 0 if eq else 1
            elif n in DLOUHE_S_ARG:
                i += 0 if eq else 1
            elif n not in DLOUHE_BEZ:
                sys.exit(f"omezovač: neznámý přepínač curl {n}; doplň ho do tabulek v omezovac.py, nebo ho nepoužívej.")
        elif a.startswith("-") and len(a) > 1:
            j = 1
            while j < len(a):
                c = a[j]
                j += 1
                if "-" + c in ZAKAZANE:
                    zakaz("-" + c)
                glob |= c == "g"
                loc |= c == "L"
                if c in KRATKE_S_ARG:
                    i += 1 if j >= len(a) else 0
                    break
                if c not in KRATKE_BEZ:
                    sys.exit(f"omezovač: neznámý přepínač curl -{c}; doplň ho do tabulek v omezovac.py.")
        else:
            urls.append(a)
    if len(urls) != 1:
        sys.exit(f"omezovač: curl smí mít právě jednu adresu (je jich {len(urls)}); každý požadavek zvlášť.")
    url = urls[0] if "://" in urls[0] else "http://" + urls[0]
    if re.search(r"[\[\]{}]", url) and not glob:
        sys.exit("omezovač: adresa se znaky [ ] { } by se v curl rozbalila na víc požadavků; přidej -g nebo je odstraň.")
    host = urllib.parse.urlsplit(url).hostname
    omez = not lokalni(host)
    if omez:
        rezervuj(web_z_hostu(host), trida(url))
    cesta = os.environ.get("PATH", "")
    shim = os.environ.get("RODOKMEN_OMEZOVAC_SHIM")
    if shim:
        cesta = os.pathsep.join(p for p in cesta.split(os.pathsep) if p != shim)
    curl = shutil.which("curl", path=cesta)
    if not curl:
        sys.exit("omezovač: curl nenalezen")
    cmd = [curl, "-w", f"%{{stderr}}{ZNACKA} %{{http_code}} %{{url_effective}}\n"]
    if loc and not maxr:
        cmd += ["--max-redirs", "5"]
    p = subprocess.run(cmd + args, stderr=subprocess.PIPE)
    chyby = p.stderr.decode("utf-8", "replace")
    m = re.search(re.escape(ZNACKA) + r" (\d+) (\S*)\n?", chyby)
    sys.stderr.write(re.sub(re.escape(ZNACKA) + r" \d+ \S*\n?", "", chyby))
    sys.stderr.flush()
    if m and omez:
        if int(m[1]) in (429, 503):
            blokuj(web_z_hostu(host), int(m[1]))
        konecny = urllib.parse.urlsplit(m[2]).hostname
        if konecny and not lokalni(konecny) and web_z_hostu(konecny) != web_z_hostu(host):
            rezervuj(web_z_hostu(konecny), trida(m[2]), spat=False)   # přesměrování jinam se započítá dodatečně
    sys.exit(p.returncode)


# ---------- stav, hook ----------

def vypis_stav():
    d = adresar()
    ted = time.time()
    radky = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            try:
                s = json.load(open(os.path.join(d, f)))
            except ValueError:
                continue
            do = s.get("blokace_do", 0)
            radky.append(f"{f[:-5]}: " + (f"ZABLOKOVÁN do {cas(do)} ({s.get('duvod')})" if do > ted else "volný"))
    print("\n".join(radky) or "žádný web zatím nebyl použit")


NET = {"curl", "wget", "aria2c", "http", "https", "xh", "lynx", "w3m", "links", "nc", "ncat", "netcat", "telnet"}
SITOVE_SKRIPTY = {"ahmp_scan.py", "anno.py", "anno_snap.py", "aron_img.py", "aron_search.py", "ebadatelna.py",
                  "kramerius.py", "mista.py", "policie_prihlasky.py", "portafontium.py", "soal_zoomify.py",
                  "trebon.py", "ahmp_search.sh", "matricula_dl.sh", "matricula_batch.sh"}
SITOVE_TOKENY = re.compile(r"\b(urllib|http\.client|httplib|requests|httpx|aiohttp|urlopen|ftplib|smtplib|"
                           r"websockets?|socket)\b|\bfetch\(", re.I)
PRED = (r"(?:^|[;&|(\n`]|\$\()[ \t]*(?:(?:env|sudo|command|exec|time|nohup|nice|xargs|builtin)[ \t]+(?:-\S+[ \t]+)*"
        r"|[A-Za-z_]\w*=\S*[ \t]+)*\\?")
PRIKAZ = re.compile(PRED + r"(?P<dir>\S*/)?(?P<cmd>[\w.+-]+)(?P<args>[^;&|\n]*)")
VNORENE = re.compile(r"""\b(?:ba|z|da)?sh[ \t]+-\w*c[ \t]+(["'])(.*?)\1|\beval[ \t]+(["'])(.*?)\3|\$\(([^)]*)\)|`([^`]*)`""", re.S)


def precti(cesta, cwd):
    try:
        return open(os.path.join(cwd, cesta), errors="replace").read()
    except OSError:
        return ""


def kontrola(text, cwd, hloubka=0):
    """Vrátí důvod zamítnutí, nebo None."""
    for m in VNORENE.finditer(text):
        vnitrek = next((g for g in (m[2], m[4], m[5], m[6]) if g), "")
        if hloubka < 4 and vnitrek:
            d = kontrola(vnitrek, cwd, hloubka + 1)
            if d:
                return d
    for m in PRIKAZ.finditer(text):
        cmd, args, dr = m["cmd"], m["args"], m["dir"] or ""
        zakl = cmd.rsplit("/", 1)[-1]
        if zakl in NET:
            return f"„{zakl}“ mimo omezovač"
        if zakl in ("magick", "convert", "identify", "composite", "montage", "chrome", "chromium", "google-chrome") \
                and re.search(r"https?://", args):
            return f"„{zakl}“ s adresou http(s)"
        if re.fullmatch(r"python[\d.]*|py", zakl):
            arg = [a for a in args.split() if not a.startswith("-")]
            sk = arg[0] if arg else ""
            if os.path.basename(sk) == "omezovac.py":
                continue
            if re.search(r"(^|\s)-c\s|<<|\s-(\s|$)", args + " ") or (not arg and "<" in text):
                if SITOVE_TOKENY.search(text):
                    return "Python s přístupem na síť mimo omezovač"
            elif sk.endswith(".py") and (os.path.basename(sk) in SITOVE_SKRIPTY or SITOVE_TOKENY.search(precti(sk, cwd))):
                return f"skript {os.path.basename(sk)} jde na síť"
        elif zakl in ("bash", "sh", "zsh") or zakl.endswith((".sh", ".py")):
            sk = (dr + cmd) if zakl.endswith((".sh", ".py")) else next((a for a in args.split() if not a.startswith("-")), "")
            if sk.endswith(".sh") and (os.path.basename(sk) in SITOVE_SKRIPTY or re.search(r"\b(curl|wget)\b", precti(sk, cwd))):
                return f"skript {os.path.basename(sk)} jde na síť"
            if sk.endswith(".py") and (os.path.basename(sk) in SITOVE_SKRIPTY or SITOVE_TOKENY.search(precti(sk, cwd))):
                return f"skript {os.path.basename(sk)} jde na síť"
        elif zakl == "node" and re.search(r"\s-[ep]\s", " " + args) and \
                re.search(r"\bfetch\(|https?\.(get|request)|XMLHttpRequest|axios", text):
            return "node s přístupem na síť"
    return None


def hook():
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return
    cwd = d.get("cwd") or os.getcwd()
    if not koren(cwd):                       # mimo projekt rodokmenu hook nic nehlídá
        return
    if d.get("tool_name") == "WebFetch":     # nástroj Claude Code, ne skript: stejný limit, hook počká na volný čas
        url = d.get("tool_input", {}).get("url", "")
        host = urllib.parse.urlsplit(url).hostname
        if host and not lokalni(host):
            w = web_z_hostu(host)
            with Zamek(soubor(w)) as z:
                do = z.nacti().get("blokace_do", 0)
            if do > time.time():
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse", "permissionDecision": "deny",
                    "permissionDecisionReason": f"Omezovač rychlosti: {w} je zablokovaný do {cas(do)} (HTTP 429/503). "
                                                "Nic neopakuj, zkus to později."}}))
                return
            rezervuj(w, trida(url))
        return
    if d.get("tool_name") != "Bash":
        return
    duvod = kontrola(d.get("tool_input", {}).get("command", ""), cwd)
    if duvod:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": f"Omezovač rychlosti: {duvod}. Každý síťový požadavek musí jít přes omezovač: "
                                        "python3 -I tools/omezovac.py <nástroj.py|nástroj.sh> <argumenty>  nebo  "
                                        "python3 -I tools/omezovac.py curl <argumenty>. Viz SKILL.md, oddíl „Síť“."}}))


def nainstaluj_hook(slozka):
    cesta = os.path.join(os.path.abspath(slozka or "."), ".claude", "settings.json")
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    s = json.load(open(cesta)) if os.path.isfile(cesta) else {}
    prikaz = 'python3 -I "$CLAUDE_PROJECT_DIR/tools/omezovac.py" hook'
    polozky = s.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if any("omezovac.py" in h.get("command", "") for p in polozky for h in p.get("hooks", [])):
        print("hook už je v", cesta)
        return
    polozky.append({"matcher": "Bash|WebFetch", "hooks": [{"type": "command", "command": prikaz}]})
    with open(cesta, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("hook přidán do", cesta)


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "curl":
        spust_curl(a[1:])
    elif a[0] == "stav":
        vypis_stav()
    elif a[0] == "hook":
        hook()
    elif a[0] == "nainstaluj-hook":
        nainstaluj_hook(a[1] if len(a) > 1 else None)
    else:
        spust_nastroj(a[0], a[1:])


if __name__ == "__main__":
    main()
