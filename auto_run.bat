@echo off
REM Script de ejecución automática para YNAB Auto-Categorizer (Windows)
REM Úsalo para programar tareas con el Programador de tareas de Windows

REM Configuración
set SCRIPT_DIR=%~dp0
set PYTHON_CMD=python
set LOG_FILE=%SCRIPT_DIR%ynab_auto.log

REM Cargar token desde .env si existe
if exist "%SCRIPT_DIR%.env" (
    for /f "tokens=1,2 delims==" %%a in ('type "%SCRIPT_DIR%.env" ^| findstr /v "^#"') do set %%a=%%b
)

REM Verificar token
if "%YNAB_API_TOKEN%"=="" (
    echo Error: YNAB_API_TOKEN no esta configurado
    echo Crea un archivo .env con tu token o configura la variable de entorno
    pause
    exit /b 1
)

REM Fecha y hora
echo ======================================== >> "%LOG_FILE%"
echo Ejecucion: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM Categorizar automáticamente
echo Categorizando transacciones... >> "%LOG_FILE%"
echo 2
echo s
) | %PYTHON_CMD% "%SCRIPT_DIR%ynab_auto_categorizer.py" >> "%LOG_FILE%" 2>&1

REM Generar reporte HTML
echo Generando reporte HTML... >> "%LOG_FILE%"
%PYTHON_CMD% "%SCRIPT_DIR%generate_html_report.py" >> "%LOG_FILE%" 2>&1

echo Completado >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Opcional: mostrar notificación
REM msg %username% "YNAB: Transacciones categorizadas"
