#!/bin/bash
#
# Script de ejecución automática para YNAB Auto-Categorizer
#
# Modos de uso:
#   ./auto_run.sh categorize   - Modo interactivo de categorización
#   ./auto_run.sh report       - Solo mostrar reportes
#   ./auto_run.sh email        - Enviar reporte por email
#
# Para programar envío semanal, ejecuta: ./setup_cron.sh
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
