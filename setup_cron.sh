#!/bin/bash
#
# Configura el envío automático de reportes YNAB usando launchd
# (funciona incluso si el Mac estaba suspendido)
#
# Ejecuta: ./setup_cron.sh
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_NAME="com.ynab.weekly-report"
PLIST_FILE="${SCRIPT_DIR}/${PLIST_NAME}.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "📧 Configuración de envío automático de reportes YNAB"
echo "======================================================"
echo ""

# Verificar que existe el .env con las credenciales
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo "❌ Error: No se encontró el archivo .env"
    echo "   Copia .env.example a .env y configura tus credenciales"
    exit 1
fi

# Verificar credenciales
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

# Crear el archivo plist actualizado
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ${SCRIPT_DIR} &amp;&amp; source .env &amp;&amp; export YNAB_API_TOKEN YNAB_BUDGET_ID GMAIL_USER GMAIL_APP_PASSWORD REPORT_EMAIL &amp;&amp; /usr/bin/python3 ${SCRIPT_DIR}/ynab_auto_categorizer.py email >> ${SCRIPT_DIR}/email.log 2>&amp;1</string>
    </array>

    <!-- Ejecutar cada domingo a las ${HOUR}:00 -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <!-- Logs -->
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/launchd.log</string>
</dict>
</plist>
EOF

echo ""
echo "Se configurará la siguiente tarea programada:"
echo "  📅 Cada domingo a las ${HOUR}:00"
echo "  📧 Enviar reporte a: ${REPORT_EMAIL:-$GMAIL_USER}"
echo "  💤 Se ejecutará al despertar si el Mac estaba suspendido"
echo ""

read -p "¿Continuar? (s/n) [s]: " CONFIRM
CONFIRM=${CONFIRM:-s}

if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    echo "Cancelado"
    exit 0
fi

# Crear directorio si no existe
mkdir -p "$LAUNCH_AGENTS_DIR"

# Detener servicio existente si lo hay
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "🔄 Deteniendo servicio existente..."
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist" 2>/dev/null
fi

# Copiar plist a LaunchAgents
cp "$PLIST_FILE" "$LAUNCH_AGENTS_DIR/"

# Cargar el servicio
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist"

echo ""
echo "✅ Servicio instalado correctamente"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver estado:    launchctl list | grep ynab"
echo "   Ver logs:      tail -f ${SCRIPT_DIR}/email.log"
echo "   Desinstalar:   launchctl unload ~/Library/LaunchAgents/${PLIST_NAME}.plist"
echo ""
echo "💡 Puedes probar el envío ahora ejecutando:"
echo "   ./auto_run.sh email"
