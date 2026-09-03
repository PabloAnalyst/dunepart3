#!/usr/bin/env python3
"""
Vigilante de Dune 3 en Cine Colombia - Nuestro Bogotá
Revisa la cartelera y envía un correo si aparece "DUNE".
Diseñado para correr una vez al día vía cron.
"""

import os
import sys
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

# ---------- CONFIGURACIÓN (se lee de variables de entorno) ----------
URL = "https://www.pacine.com/cines/cine-colombia-multiplex-nuestro-bogota"
PALABRA_CLAVE = "dune"

EMAIL_FROM = os.environ.get("DUNE_EMAIL_FROM")       # tu correo de Gmail
EMAIL_PASSWORD = os.environ.get("DUNE_EMAIL_PASSWORD")  # contraseña de aplicación (no la normal)
EMAIL_TO = os.environ.get("DUNE_EMAIL_TO", EMAIL_FROM)  # a quién avisar (por defecto, a ti mismo)

LOG_FILE = "log.txt"
ALERT_SENT_FLAG = "ya_avisado.flag"

# ---------- FUNCIONES ----------

def log(mensaje):
    linea = f"[{datetime.now().isoformat(timespec='seconds')}] {mensaje}"
    print(linea)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def revisar_pagina():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DuneWatcher/1.0)"}
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()
    texto = resp.text.lower()
    return PALABRA_CLAVE in texto


def enviar_correo(asunto, cuerpo):
    if not EMAIL_FROM or not EMAIL_PASSWORD:
        log("ERROR: faltan credenciales de correo (DUNE_EMAIL_FROM / DUNE_EMAIL_PASSWORD).")
        return False
    msg = MIMEText(cuerpo)
    msg["Subject"] = asunto
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        log(f"Correo enviado a {EMAIL_TO}: {asunto}")
        return True
    except Exception as e:
        log(f"ERROR enviando correo: {e}")
        return False


def main():
    try:
        encontrado = revisar_pagina()
    except Exception as e:
        log(f"ERROR revisando la página: {e}")
        sys.exit(1)

    ya_avisado = os.path.exists(ALERT_SENT_FLAG)

    if encontrado and not ya_avisado:
        log("¡DUNE encontrado en la cartelera! Enviando alerta.")
        enviar_correo(
            "🚨 DUNE 3 ya está en la cartelera de Nuestro Bogotá",
            f"Se detectó la palabra 'Dune' en:\n{URL}\n\n¡Ve a comprar las boletas ya!"
        )
        # Marca que ya se avisó, para no mandar correo cada día una vez detectado
        with open(ALERT_SENT_FLAG, "w") as f:
            f.write(datetime.now().isoformat())
    elif encontrado and ya_avisado:
        log("Dune sigue en cartelera, ya se había avisado antes. No se reenvía correo.")
    else:
        log("Todavía no aparece Dune en la cartelera.")


if __name__ == "__main__":
    main()

