# Spuštění webu lokálně v Podmanu

Web se sestaví uvnitř kontejneru (Red Hat UBI, bez root, port 8080) a servíruje ho nginx.
Podrobnosti o image jsou v komentáři na začátku [`Containerfile`](Containerfile).

## Předpoklady

- Podman 5 (`podman --version`); na macOS musí běžet stroj: `podman machine start`.
- Node.js a npm jen pro krok „data“ (generuje se mimo kontejner).

## Postup

Všechny příkazy ze složky `web/`.

1. Vygenerovat data webu a `nginx.conf`:

   ```bash
   npm run data
   ```

2. Sestavit image:

   ```bash
   podman build -t rodokmen-web -f Containerfile .
   ```

3. Spustit kontejner:

   ```bash
   podman run --rm -p 8080:8080 rodokmen-web
   ```

4. Otevřít <http://localhost:8080>. Zastavení: `Ctrl+C`.

## Přihlášení

- Bez parametru `--nasazeni` (jako výše) a bez vyplněné `prihlaseni.odpoved` v `data/web.json` je web lokálně otevřený.
- Je-li odpověď vyplněná, brána se zapne i lokálně – zadej odpověď na rodinnou otázku.
- Pro ostrý provoz (CapRover) použij `npm run data -- --nasazeni`; bez odpovědi v `web.json` skončí chybou, aby web neotevřel nikdo cizí.

## Po změně dat nebo obsahu

Kroky 1–3 zopakuj (`npm run data`, `podman build …`, `podman run …`). Rychlý náhled bez kontejneru: `npm run nahled`.

## Časté potíže

| Problém | Řešení |
|---|---|
| `Cannot connect to Podman` | `podman machine start` |
| Build selže na `COPY nginx.conf` | nejdřív `npm run data` (vyrobí `nginx.conf`) |
| Port 8080 je obsazený | `podman run --rm -p 8081:8080 rodokmen-web` a otevři port 8081 |
