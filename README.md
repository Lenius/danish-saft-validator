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

---

## 🧩 Indhold

- [Forudsætninger](#forudsætninger)
- [Installation og kloning](#installation-og-kloning)
- [Mappestruktur](#mappestruktur)
- [Bygning af Docker-billede](#bygning-af-docker-billede)
- [Kørsel af validator](#kørsel-af-validator)
  - [Interaktiv kørsel](#interaktiv-kørsel)
  - [Automatiseret kørsel (non-interaktiv)](#automatiseret-kørsel-non-interaktiv)
- [Output og rapport](#output-og-rapport)
- [Ændring af sprog](#ændring-af-sprog)
- [Opdatering med Git](#opdatering-med-git)
- [Fejlfinding](#fejlfinding)
- [Eksempel på .gitignore](#eksempel-på-gitignore)

---

## 🔧 Forudsætninger

Du skal have:
- **Docker** installeret  
  (Windows/macOS → [Docker Desktop](https://www.docker.com/products/docker-desktop),  
  Linux → via din pakkemanager)
- **Git** til at hente og opdatere projektet.

Du behøver **ikke** at installere Python.

---

## 📥 Installation og kloning

Klon projektet første gang:

```bash
git clone https://github.com/Lenius/danish-saft-validator.git
cd danish-saft-validator
