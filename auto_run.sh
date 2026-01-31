#!/bin/bash
#
# Script de ejecución automática para YNAB Auto-Categorizer
# Úsalo para programar tareas con cron
#
# Ejemplo de crontab (ejecutar cada lunes a las 9am):
# 0 9 * * 1 /ruta/completa/a/auto_run.sh >> /ruta/a/logs/ynab.log 2>&1
#

# Configuración
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_CMD="python3"
LOG_FILE="${SCRIPT_DIR}/ynab_auto.log"

# Cargar token desde archivo .env si existe
if [ -f "${SCRIPT_DIR}/.env" ]; then
    export $(cat "${SCRIPT_DIR}/.env" | grep -v '^#' | xargs)
fi

# Verificar que el token esté configurado
if [ -z "$YNAB_API_TOKEN" ]; then
    echo "❌ Error: YNAB_API_TOKEN no está configurado"
    echo "   Crea un archivo .env con tu token o configura la variable de entorno"
    exit 1
fi

# Fecha y hora
echo "========================================" >> "$LOG_FILE"
echo "🕒 Ejecución: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Categorizar automáticamente (sin confirmación)
echo "📝 Categorizando transacciones..." >> "$LOG_FILE"
$PYTHON_CMD "${SCRIPT_DIR}/ynab_auto_categorizer.py" <<EOF >> "$LOG_FILE" 2>&1
2
s
EOF

# Generar reporte HTML
echo "📊 Generando reporte HTML..." >> "$LOG_FILE"
$PYTHON_CMD "${SCRIPT_DIR}/generate_html_report.py" >> "$LOG_FILE" 2>&1

echo "✅ Completado" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Opcional: Enviar notificación
# notify-send "YNAB" "Transacciones categorizadas y reporte generado"
