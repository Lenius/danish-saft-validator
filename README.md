# 🇩🇰 Danish SAF-T Validator

**Danish SAF-T Validator** er et officielt Python-baseret værktøj fra Skattestyrelsen (UFST), der bruges til at **validere danske SAF-T XML-filer**.

Denne version gør det nemt at køre valideringen via **Docker** – uden behov for lokal Python-installation.

Validatoren kontrollerer blandt andet:
- XML-struktur og format (mod XSD)
- Datatyper og obligatoriske felter
- Digitale signaturer og certifikater
- At værdier følger de tekniske retningslinjer
- At alle transaktioner kan læses og valideres korrekt

Efter hver validering genereres en **Excel-rapport (XLSX)** med resultaterne.

### 🐧 Eksempel – Bash (Linux/macOS)

```bash
# Interaktiv kørsel (du bliver spurgt om sprog og XML-fil)
docker run --rm -it \
  -v "$(pwd)/work:/work" \
  -v "$(pwd)/config:/app/config" \
  danish-saft-validator:latest
# Eksempel på input:
# dk
# /work/in/test.xml
```

### 🐧 Eksempel – PowerShell (Windows)

```bash
# Interaktiv kørsel (du bliver spurgt om sprog og XML-fil)
docker run --rm -it \
  -v "$(pwd)/work:/work" \
  -v "$(pwd)/config:/app/config" \
  danish-saft-validator:latest
# Eksempel på input:
# dk
# /work/in/test.xml
```

---
## 🧩 Indhold

- [Forudsætninger](#-forudsætninger)
- [Installation og kloning](#-kloning--opdatering-med-git)
- [Mappestruktur](#-mappestruktur)
- [Bygning af Docker-billede](#bygning-af-docker-image)
- [Kørsel af validator](#kørsel-af-validator)
  - [Interaktiv kørsel](#interaktiv-kørsel)
- [Output og rapport](#-output)
- [Ændring af sprog](#-skift-sprog-senere)
- [Opdatering med Git](#opdatering-med-git)

---

## 📦 Forudsætninger

Du skal have:

- **Docker** installeret  
  - [Docker Desktop](https://www.docker.com/products/docker-desktop) til Windows/macOS  
  - `sudo apt install docker` på Linux  
- **Git** installeret for at kunne hente og opdatere projektet.

Ingen Python-installation er nødvendig.

---

## 📁 Mappestruktur

Projektet bruger følgende struktur:

```
.
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ main.py                  ← SAF-T validator fra UFST
├─ config/                  ← gemmer sprogvalg (config.ini)
└─ work/
   ├─ in/                   ← læg dine SAF-T XML-filer her
   └─ Tjekket/              ← rapporter (.xlsx) genereres her
```

> Sørg for at mapperne `config` og `work/in` findes, før du kører containeren.

---

## 🧠 Kloning & opdatering med Git

Klon projektet første gang:

```bash
git clone https://github.com/lenius/danish-saft-validator.git
cd danish-saft-validator
```

Opdater senere med:

```bash
git pull
```

---

## 🐳 Bygning af Docker-image

Fra projektmappen:

```bash
docker build -t danish-saft-validator:latest .
```

Dette skaber et lokalt Docker-image du kan køre igen og igen.

---

## ▶️ Kørsel via terminal

### 🟢 Interaktiv (du svarer i terminalen)
Her bliver du spurgt om sprog (`dk`/`en`) og derefter XML-sti.

```bash
docker run --rm -it \
  -v "$(pwd)/work:/work" \
  -v "$(pwd)/config:/app/config" \
  danish-saft-validator:latest
# Eksempel på input:
# dk
# /work/in/test.xml
```

- Første gang bruges `CONFIG_LANG` til at vælge sprog.  
- Derefter gemmes sprogvalget i `config/config.ini`.

### 🔁 Skift sprog senere
Slet `config/config.ini`

---

## 💡 Output

Efter kørsel findes rapporten i:

```
./work/Tjekket/{prefix}test.xlsx
```

Rapporten åbnes i Excel og viser bl.a.:

- Fejl og advarsler
- Manglende elementer
- Ugyldige datatyper
- Certifikatstatus og signaturer

---

## ⚙️ Docker-Compose (nem lokal kørsel)

```yaml
version: "3.9"
services:
  validator:
    image: danish-saft-validator:latest
    build: .
    tty: true
    environment:
      TZ: Europe/Copenhagen
      # CONFIG_LANG: dk
      # XML_PATH: /work/in/test.xml
    volumes:
      - ./work:/work
      - ./config:/app/config
```

Kør derefter:
```bash
docker compose build
docker compose run --rm danish-saft-validator
```