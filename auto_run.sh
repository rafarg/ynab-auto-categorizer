#!/bin/bash
#
# Script de ejecución automática para YNAB Auto-Categorizer
#
# Modos de uso:
#   ./auto_run.sh categorize   - Modo interactivo de categorización
#   ./auto_run.sh report       - Solo mostrar reportes
#
# Para programar con cron (reporte semanal cada lunes a las 9am):
# 0 9 * * 1 /ruta/completa/a/auto_run.sh report >> /ruta/a/logs/ynab.log 2>&1
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_CMD="python3"

# Cargar variables de entorno desde .env
if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

# Verificar token
if [ -z "$YNAB_API_TOKEN" ]; then
    echo "❌ Error: YNAB_API_TOKEN no está configurado"
    echo "   Crea un archivo .env con tu token"
    exit 1
fi

# Modo de ejecución
MODE="${1:-report}"

echo "=========================================="
echo "🏦 YNAB Auto-Categorizer"
echo "🕒 $(date)"
echo "📋 Modo: $MODE"
echo "=========================================="

$PYTHON_CMD "${SCRIPT_DIR}/ynab_auto_categorizer.py" "$MODE"
