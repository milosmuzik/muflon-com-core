"""
.github/scripts/gemini_bot.py

Logika za "Gemini Bot" workflow (.github/workflows/gemini-bot.yml):
1. Přečte úkol z komentáře na issue (za "/gemini").
2. Zavolá Gemini a požádá ho o kompletní obsah souborů, které úkol vyžeší.
3. Rozparsuje odpověď na jednotlivé (cesta_k_souboru, obsah) dvojice.
4. Založí novou větev, zapíše soubory, commitne, pushne.
5. Otevře Pull Request a okomentuje původní issue.

Očekávané proměnné prostředí (nastavené ve workflow souboru):
  GEMINI_API_KEY   - klíč pro Gemini API
  GITHUB_TOKEN     - token s právy na push + vytvoření PR (stačí výchozí
                      workflow token, viz `permissions:` ve workflow YAML)
  COMMENT_BODY     - tělo komentáře, který bota spustil (obsahuje "/gemini")
  ISSUE_NUMBER     - číslo issue, pod kterým komentář padl
  REPO_FULL_NAME   - "vlastnik/repozitar"

Pozn.: tenhle soubor byl v repu dřív jako polorozbitý fragment přímo uvnitř
gemini-bot.yml (chybějící hlavička, uťatý konec). Přesunuto sem jako
samostatný, kompletní a spustitelný skript.
"""

import os
import re
import subprocess
import sys
import time

from github import Github
from google import genai

FORMAT_INSTRUKCE = """Jsi vývojářský asistent pro tenhle GitHub repozitář. Dostaneš úkol a máš
vrátit KOMPLETNÍ obsah každého souboru, který je potřeba vytvořit nebo
přepsat, aby byl úkol hotový.

Formát odpovědi je ZÁVAZNÝ, nepiš kolem něj žádný další text:

### FILE: cesta/k/souboru.ext
```
<celý obsah souboru, ne jen diff nebo výňatek>
```

Pro každý další soubor zopakuj stejný blok (řádek "### FILE: ..." následovaný
blokem v trojitých zpětných uvozovkách). Cesty piš relativně ke kořeni
repozitáře. Vrať jen soubory, které se skutečně mění nebo přidávají -
neopisuj soubory beze změny.

Úkol:
{ukol}
"""

VZOR_SOUBORU = re.compile(
    r"###\s*FILE:\s*(?P<cesta>\S+)\s*\n```[a-zA-Z0-9]*\n(?P<obsah>.*?)```",
    re.DOTALL,
)


def ziskej_env(nazev: str) -> str:
    hodnota = os.environ.get(nazev)
    if not hodnota:
        print(f"Chybí proměnná prostředí {nazev}.", file=sys.stderr)
        sys.exit(1)
    return hodnota


def zavolej_gemini(ukol: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=FORMAT_INSTRUKCE.format(ukol=ukol),
    )
    return response.text or ""


def rozparsuj_soubory(output_text: str) -> list[tuple[str, str]]:
    return [
        (m.group("cesta").strip(), m.group("obsah"))
        for m in VZOR_SOUBORU.finditer(output_text)
    ]


def main() -> None:
    comment_body = ziskej_env("COMMENT_BODY")
    issue_num = int(ziskej_env("ISSUE_NUMBER"))
    repo_full_name = ziskej_env("REPO_FULL_NAME")
    gemini_key = ziskej_env("GEMINI_API_KEY")
    github_token = ziskej_env("GITHUB_TOKEN")

    gh = Github(github_token)
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(issue_num)

    user_prompt = comment_body.replace("/gemini", "", 1).strip()
    if not user_prompt:
        issue.create_comment("Napiš za `/gemini` i samotný úkol, ať vím, co mám udělat.")
        return

    issue.create_comment(f"🤖 Pracuju na tom: {user_prompt}")

    try:
        output_text = zavolej_gemini(user_prompt, gemini_key)
    except Exception as e:  # necháváme širší except - jde o hraniční skript, ne appku
        issue.create_comment(f"Volání Gemini selhalo: {e}")
        sys.exit(1)

    matches = rozparsuj_soubory(output_text)
    if not matches:
        issue.create_comment(
            "Nepodařilo se rozpoznat formát souborů z odpovědi modelu:\n\n" + output_text[:3000]
        )
        return

    # Příprava nové Git větve
    branch_name = f"gemini-task-{issue_num}-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    subprocess.run(["git", "config", "user.name", "Gemini Bot"], check=True)
    subprocess.run(["git", "config", "user.email", "gemini-bot@actions.local"], check=True)

    changed_files = []
    for file_path, content in matches:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "add", file_path], check=True)
        changed_files.append(file_path)

    subprocess.run(["git", "commit", "-m", f"Gemini: {user_prompt[:50]}"], check=True)
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    # Založení Pull Requestu
    pr = repo.create_pull(
        title=f"Gemini: Změny pro #{issue_num}",
        body=(
            f"Automaticky vygenerované změny podle požadavku v #{issue_num}:\n> {user_prompt}\n\n"
            "Upravené soubory:\n- " + "\n- ".join(changed_files)
        ),
        head=branch_name,
        base=repo.default_branch,
    )

    issue.create_comment(
        f"✅ Hotovo! Vytvořil jsem změny v souborech a otevřel Pull Request: #{pr.number}\n\n"
        f"Můžeš ho zkontrolovat a sloučit zde: {pr.html_url}"
    )


if __name__ == "__main__":
    main()
