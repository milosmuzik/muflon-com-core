# Muflon Com Core

Anglická obdoba [Muflon Core](https://github.com/milosmuzik/muflon-core) —
znalostní systém pro redakční práci na anglické mutaci Rádia Muflon
(radiomuflon.com). Stejný datový model, stejné stránky, stejné API, stejný
redakční standard jako CZ Core — jen s obsahem v angličtině a bez českých
kapel v katalogu (radiomuflon.com jede na vlastním streamu na zeno.fm se
stávajícím playlistem Rádia Muflon, ale bez českých interpretů).

Pokrývá Etapu 1 (interpreti, hudebníci, alba, skladby, vazby, zdroje), Etapu 2
(příběhy, události, historie změn, propojení), redakční workflow (návrh →
ověřeno → schváleno → publikováno → archivováno) a Muflonní kalendář. Obsahuje
i AI agentní rutiny (viz níže) — na rozdíl od CZ Core jsou tu od začátku
aktivní, protože Gemini u tohoto projektu dělá většinu redakční práce (dohledání
zdrojů, návrhy do kalendáře, doplňování katalogu) samostatně.

## Technologie

- **Next.js 14** (App Router, Server Components, Server Actions) + TypeScript
- **Prisma** + **PostgreSQL**
- **Tailwind CSS**
- **Gemini API** — tři agentní rutiny (import karet, návrhy kalendáře,
  dohledávání zdrojů/doplňování katalogu) + GitHub Actions bot
  (`.github/workflows/gemini-bot.yml`, spouští se komentářem `/gemini <úkol>`
  na issue)

## Spuštění naostro (Vercel)

1. Nahraj tento kód do (nového, samostatného) GitHub repozitáře
   `muflon-com-core`.
2. Na [vercel.com](https://vercel.com) → **Add New Project** → vyber
   repozitář.
3. V nastavení projektu přidej **Vercel Postgres** (Storage → Create Database
   → Postgres, poháněno Neonem) — Vercel sám doplní proměnnou `DATABASE_URL`.
   Použij **novou, samostatnou** databázi — ne tu od CZ Core.
4. Nastav proměnné prostředí (viz `.env.example` a `CLAUDE.md`) — vlastní
   `AUTH_PASSWORD` a `IMPORT_API_KEY`, jiné než u CZ Core.
5. Nasaď. Databáze bude zpočátku prázdná — `prisma/data/playlist.tsv`
   obsahuje jen hlavičku, dokud nedoplníš skutečný playlist anglického
   streamu (stávající playlist Rádia Muflon minus české kapely).
6. Až bude appka na živé URL, na webu radiomuflon.com přepiš v `<script>`
   konstantu `CORE_BASE` na tuhle novou adresu.

## Lokální vývoj

```bash
npm install
cp .env.example .env      # vlož skutečný DATABASE_URL
npm run db:push           # vytvoří tabulky podle prisma/schema.prisma
npm run db:seed           # naimportuje prisma/data/playlist.tsv (zatím prázdné)
npm run dev                 # http://localhost:3000
```

`npm run db:studio` otevře Prisma Studio — vizuální prohlížeč databáze.

## Struktura

Stejná jako CZ Core — viz `CLAUDE.md` pro plnou architekturu (datový model,
AI integrace, sociální sítě, proměnné prostředí).

## Co je jinak oproti CZ Core

- Bez "Vanaheim" hacku v `/api/public/kapela` (řešil kolizi jmen konkrétní
  české a zahraniční kapely — tady nepotřeba, katalog neobsahuje české kapely).
- Bez jednorázových importních/opravných skriptů vázaných na konkrétní české
  karty (`import-kabat.ts` apod.) a bez hotových dat CZ katalogu
  (`prisma/data/*.json`, `playlist.tsv` s CZ playlistem).
- AI prompty v `lib/agent/` mají navíc explicitní instrukci psát výstupní
  texty (`popis`, `poznamka`, `rozsireni`) anglicky — samotné prompty zůstávají
  česky (jsou to interní instrukce pro Gemini, ne obsah pro čtenáře).
- Redakční UI (administrace) zůstává česky, stejně jako v CZ Core — je to
  interní nástroj, ne veřejná část webu.

## Redakční standard

Anglická obdoba Muflon Standard MS-2.0 — hierarchie zdrojů a schválený
whitelist (`RENOMOVANE_ZDROJE_DOMENY` v `lib/constants.ts`) jsou identické
s CZ Core, protože jde převážně o mezinárodní rockové/metalové zdroje. Karty
se píšou/generují přímo anglicky, nezávisle na CZ Core (žádný import/překlad
existujících českých karet).
