# UFST - XML validation Danish (for English go to the bottom)

:red_circle: Verifikationsscriptet kan ikke anses for en godkendelse af de enkelte
leverandørers digitale salgsregistreringssystemer. :red_circle:

Til understøttelse af leverandørernes udvikling af digitale salgsregistreringsløsninger frigives dette SAF-T
verifikationsscript. Verifikationsscriptet har til formål at verificere SAF-T XML-filer samt
dokumentere, hvilke rettelser, der stadig skal foretages for at imødekomme retningslinjerne for formatet. Tjekket består
af følgende dele:

- Overholder filen navngivningskonventionen?
- Overholder filen de generelle XML konventioner og kan løsningen læse indholdet?
- Følger XML-filen strukturen forelagt i XSD-dokumentet?
- Overholder alle elementer kravene for deres respektive data type?
- Er alle obligatoriske elementer tilstede?
- Er der benyttet et godkendt certifikat?
- Tester signaturkæden for alle transaktioner
- Tester værdier af elementer, op i mod den tekniske beskrivelse.

Når du anvender denne løsning, vil du blive præsenteret med output i XLSX format, som indeholder strukturelle
udfordringer i din XML fil.

## Krav

- Python 3.10 eller nyere

## Installation

1. Opret en virtuel environment (valgfrit, men anbefales):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

2. Installer de nødvendige pakker ved at køre følgende kommando:
   ```bash
   pip install -r requirements.txt

## Kørsel

For at køre programmet, brug:

```bash
python main.py
```

Når programmet køres, bliver du mødt af et inputfelt, hvor du skal angive stien til din XML-fil. Programmet vil derefter
generere en rapport og gemme den i __./../Tjekket__ relativt til XML-filens placering. Hvis der ikke findes en mappe med
navnet Tjekket, dannes denne.

## Sprogvalg og Konfigurationsfil

Ved første kørsel af scriptet bliver du promptet med valget af sprog for verifikationen. Efter valg af sprog genereres
en __config.ini__-fil, der indeholder dine præferencer. Hvis du ønsker at ændre sprog på et senere tidspunkt, skal du
slette
denne __config.ini__-fil.

## Bemærkninger

- Husk at aktivere din virtuelle environment, hvis du har oprettet en, inden du kører programmet.
- Sørg for at have en gyldig XML-fil klar til behandling.

## Eksempel

Hvis du har en fil kaldet __eksempel.xml__ i samme mappe som __main.py__, kan du køre programmet ved at skrive:

```bash
python main.py
```

og angive stien til XML-filen som: __eksempel.xml__

Rapporten vil blive gemt i __./../Tjekket/{prefix}eksempel.xlsx__.

***

# UFST - XML validation English

:red_circle: The verification script cannot be considered an endorsement of individual suppliers' digital sales
registration systems. :red_circle:

To support suppliers in developing digital sales registration solutions, this SAF-T verification script is released. The
purpose of the verification script is to verify SAF-T XML files as well as
document what corrections still need to be made to meet the format guidelines. The check consists of the following
parts:

- Does the file adhere to the naming convention?
- Does the file comply with the general XML conventions, and can the solution read the content?
- Does the XML file follow the structure presented in the XSD document?
- Do all elements meet the requirements for their respective data types?
- Are all mandatory elements present?
- Are the used certificate approved?
- Testing signature chain for all transactions
- Testing values of elements, against the technical description


When using this solution, you will be presented with output in XLSX format containing structural challenges in your XML
file.

## Requirements

- Python 3.10 or later

## Installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

2. Install the necessary packages by running the following command:
   ```bash
   pip install -r requirements.txt

## Execution

To run the program, use:

```bash
python main.py
```

When the program runs, you will be prompted with an input field where you need to specify the path to your XML file.
The program will then generate a report and save it in __./../Checked__ relative to the location of the XML file. If a
folder with the name Checked does not exist, it will be created.

## Language Selection and Configuration File

Upon the initial execution of the script, you will be prompted to choose the language for verification. After selecting
the language, a __config.ini__ file is created to store your preferences. If you need to change the language later, you
should delete the __config.ini__ file.

## Notes

- Remember to activate your virtual environment if you have created one before running the program.
- Ensure that you have a valid XML file ready for processing.

## Example

If you have a file called __example.xml__ in the same folder as __main.py__, you can run the program by typing:

```bash
python main.py
```

and specify the path to the XML file as: __example.xml__

The report will be saved in __./../Checked/{prefix}example.xlsx.__

## Licens

Copyright (c) 2023 Udvikling og forenklingsstyrelsen - UFST

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.