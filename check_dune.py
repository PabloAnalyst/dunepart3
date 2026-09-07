#!/usr/bin/env python3
"""
Vigilante de Dune 3 en Cine Colombia - Nuestro Bogotá
Revisa varias páginas de cartelera y envía un correo si aparece "DUNE" en alguna.
Diseñado para correr una vez al día vía cron.
"""
import os
import sys
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

# ---------- CONFIGURACIÓN (se lee de variables de entorno) ----------
# Diccionario: nombre descriptivo -> URL a revisar
URLS = {
    "Pacine (Cine Colombia Multiplex Nuestro Bogotá)": "https://www.pacine.com/cines/cine-colombia-multiplex-nuestro-bogota",
    "Página oficial Cine Colombia (cartelera)": "https://www.cinecolombia.com/films/",
}

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


def revisar_pagina(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DuneWatcher/1.0)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    texto = resp.text.lower()
    return PALABRA_CLAVE in texto


def revisar_todas_las_paginas():
    """
    Revisa cada URL configurada. Devuelve una lista de tuplas
    (nombre, url) de las páginas donde se encontró la palabra clave.
    Si una página falla (error de red, etc.), se registra el error
    y se sigue revisando las demás en vez de detener todo el proceso.
    """
    encontrados = []
    for nombre, url in URLS.items():
        try:
            if revisar_pagina(url):
                encontrados.append((nombre, url))
        except Exception as e:
            log(f"ERROR revisando '{nombre}' ({url}): {e}")
    return encontrados


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
    encontrados = revisar_todas_las_paginas()

    ya_avisado = os.path.exists(ALERT_SENT_FLAG)

    if encontrados and not ya_avisado:
        fuentes_texto = "\n".join(f"- {nombre}: {url}" for nombre, url in encontrados)
        log(f"¡DUNE encontrado en: {', '.join(n for n, _ in encontrados)}! Enviando alerta.")
        enviar_correo(
            "🚨 DUNE 3 ya está en cartelera",
            f"Se detectó la palabra 'Dune' en las siguientes páginas:\n\n{fuentes_texto}\n\n¡Ve a comprar las boletas ya!"
        )
        # Marca que ya se avisó, para no mandar correo cada día una vez detectado
        with open(ALERT_SENT_FLAG, "w") as f:
            f.write(datetime.now().isoformat())
    elif encontrados and ya_avisado:
        log(
            "Dune sigue en cartelera "
            f"({', '.join(n for n, _ in encontrados)}), ya se había avisado antes. No se reenvía correo."
        )
    else:
        log("Todavía no aparece Dune en ninguna de las páginas revisadas.")


if __name__ == "__main__":
    main()
