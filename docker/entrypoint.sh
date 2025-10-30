#!/usr/bin/env bash
set -euo pipefail
trap "echo 'Afbrudt af brugeren. Lukker container...'; exit 0" SIGINT SIGTERM

cd /app

# Sørg for at volumemappe findes og er skrivbar
mkdir -p /app/config

# Valgfrit: nulstil config ved at slette target
if [ "${CONFIG_RESET:-0}" = "1" ]; then
  rm -f /app/config/config.ini || true
fi

# VIGTIGT: tving /app/config.ini til at være symlink til /app/config/config.ini
# -n: overwrite, -f: force, -s: symlink, -T: treat dest as normal file
ln -sfnT /app/config/config.ini /app/config.ini

lang="${CONFIG_LANG:-dk}"
xml="${XML_PATH:-}"

# Første kørsel? (dvs. ingen config endnu) -> fød sprog først, derefter sti hvis sat
if [ ! -f "/app/config/config.ini" ]; then
  if [ -n "${xml}" ]; then
    [ -f "${xml}" ] || { echo "Fejl: XML_PATH findes ikke: ${xml}" >&2; exit 1; }
    printf "%s\n%s\n" "${lang}" "${xml}" | python /app/main.py
  else
    # Ren interaktiv første kørsel
    python /app/main.py
  fi
else
  # Config findes allerede
  if [ -n "${xml}" ]; then
    [ -f "${xml}" ] || { echo "Fejl: XML_PATH findes ikke: ${xml}" >&2; exit 1; }
    printf "%s\n" "${xml}" | python /app/main.py
  else
    python /app/main.py
  fi
fi

#work/in/SAF-T Cash Register_25139135_20251030025907_1_1.xml
#work/in/sneker.xml