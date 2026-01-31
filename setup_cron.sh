#!/bin/bash
#
# Configura el cron job para enviar el reporte semanal por email
# Ejecuta: ./setup_cron.sh
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📧 Configuración de envío automático de reportes YNAB"
echo "======================================================"
echo ""

# Verificar que existe el .env con las credenciales
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo "❌ Error: No se encontró el archivo .env"
    echo "   Copia .env.example a .env y configura tus credenciales"
    exit 1
fi

# Verificar que están configuradas las credenciales de Gmail
source "${SCRIPT_DIR}/.env"
if [ -z "$GMAIL_USER" ] || [ "$GMAIL_USER" = "tu_email@gmail.com" ]; then
    echo "❌ Error: Configura GMAIL_USER en .env"
    exit 1
fi
if [ -z "$GMAIL_APP_PASSWORD" ] || [ "$GMAIL_APP_PASSWORD" = "xxxx xxxx xxxx xxxx" ]; then
    echo "❌ Error: Configura GMAIL_APP_PASSWORD en .env"
    echo ""
    echo "Para crear una contraseña de aplicación:"
    echo "1. Ve a https://myaccount.google.com/apppasswords"
    echo "2. Selecciona 'Correo' y 'Mac'"
    echo "3. Copia la contraseña generada a .env"
    exit 1
fi

echo "✅ Credenciales de Gmail configuradas"
echo ""

# Preguntar hora de envío
read -p "¿A qué hora quieres recibir el reporte los domingos? (0-23) [10]: " HOUR
HOUR=${HOUR:-10}

# Crear la línea de cron
CRON_CMD="0 ${HOUR} * * 0 cd ${SCRIPT_DIR} && source .env && export YNAB_API_TOKEN YNAB_BUDGET_ID GMAIL_USER GMAIL_APP_PASSWORD REPORT_EMAIL && /usr/bin/python3 ${SCRIPT_DIR}/ynab_auto_categorizer.py email >> ${SCRIPT_DIR}/email.log 2>&1"

echo ""
echo "Se añadirá la siguiente tarea programada:"
echo "  📅 Cada domingo a las ${HOUR}:00"
echo "  📧 Enviar reporte a: ${REPORT_EMAIL:-$GMAIL_USER}"
echo ""

read -p "¿Continuar? (s/n) [s]: " CONFIRM
CONFIRM=${CONFIRM:-s}

if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    echo "Cancelado"
    exit 0
fi

# Verificar si ya existe una entrada similar
EXISTING=$(crontab -l 2>/dev/null | grep "ynab_auto_categorizer.py email")
if [ -n "$EXISTING" ]; then
    echo ""
    echo "⚠️  Ya existe una tarea programada para el reporte YNAB:"
    echo "   $EXISTING"
    read -p "¿Reemplazar? (s/n) [n]: " REPLACE
    REPLACE=${REPLACE:-n}

    if [ "$REPLACE" = "s" ] || [ "$REPLACE" = "S" ]; then
        # Eliminar la entrada existente
        crontab -l 2>/dev/null | grep -v "ynab_auto_categorizer.py email" | crontab -
    else
        echo "Manteniendo la configuración existente"
        exit 0
    fi
fi

# Añadir al crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ Tarea programada añadida correctamente"
echo ""
echo "📋 Para verificar: crontab -l"
echo "📋 Para eliminar:  crontab -e (y borrar la línea)"
echo ""
echo "💡 Puedes probar el envío ahora ejecutando:"
echo "   ./auto_run.sh email"
