# 🏦 YNAB Auto-Categorizer

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![YNAB API](https://img.shields.io/badge/YNAB-API-green.svg)](https://api.ynab.com/)

Sistema automático para categorizar transacciones de YNAB y generar reportes semanales.

## ✨ Características

- ✅ **Categorización automática** basada en reglas personalizables
- 📊 **Reportes semanales** en HTML con gráficos interactivos
- 🔄 **Modo simulación** para probar sin riesgo
- ⚙️ **Totalmente automatizable** con cron o programador de tareas
- 🇪🇸 **Reglas preconfigurradas para España** (Mercadona, Repsol, etc.)
- 🔐 **Seguro** - nunca expone tu token

## 🎥 Vista previa

```bash
$ python3 ynab_auto_categorizer.py

🏦 YNAB Auto-Categorizer
1. Categorizar transacciones (modo simulación)
2. Categorizar transacciones (aplicar cambios)
3. Ver reporte semanal
4. Ver reporte del último mes

📊 Encontradas 15 transacciones sin categorizar

✓ 2025-01-28 | MERCADONA                  |   €45.67 → Comestibles
✓ 2025-01-27 | REPSOL GASOLINERA         |   €52.30 → Gasolina
✓ 2025-01-26 | NETFLIX.COM               |   €12.99 → Entretenimiento
```

## 📋 Requisitos Previos

- Python 3.7 o superior
- Una cuenta de YNAB (You Need A Budget)
- Token de API de YNAB

## 🚀 Instalación Rápida

### 1. Instalar Python (si no lo tienes)

**Windows:**
- Descarga desde https://www.python.org/downloads/
- Durante instalación, marca "Add Python to PATH"

**Mac:**
```bash
# Si tienes Homebrew instalado
brew install python3
```

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. Instalar dependencias

```bash
pip install requests
```

### 3. Obtener tu Token de YNAB

1. Ve a https://app.ynab.com/settings/developer
2. Haz clic en "New Token"
3. Dale un nombre (ej: "Auto-Categorizer")
4. Copia el token (¡guárdalo bien, solo se muestra una vez!)

### 4. Configurar el script

**Opción A: Variable de entorno (recomendado)**

**Windows (PowerShell):**
```powershell
$env:YNAB_API_TOKEN = "tu-token-aqui"
```

**Windows (CMD):**
```cmd
set YNAB_API_TOKEN=tu-token-aqui
```

**Mac/Linux:**
```bash
export YNAB_API_TOKEN="tu-token-aqui"
```

Para hacerlo permanente, añade esta línea a tu `.bashrc`, `.zshrc` o `.bash_profile`:
```bash
echo 'export YNAB_API_TOKEN="tu-token-aqui"' >> ~/.bashrc
```

**Opción B: Editar el archivo directamente**

Abre `ynab_auto_categorizer.py` y reemplaza:
```python
API_TOKEN = os.getenv("YNAB_API_TOKEN", "TU_TOKEN_AQUI")
```

Por:
```python
API_TOKEN = "tu-token-real-aqui"
```

## 🎯 Uso Básico

### Ejecutar el script

```bash
python3 ynab_auto_categorizer.py
```

Verás un menú con opciones:
```
1. Categorizar transacciones (modo simulación)
2. Categorizar transacciones (aplicar cambios)
3. Ver reporte semanal
4. Ver reporte del último mes
```

### Primer uso recomendado

1. **Ejecuta opción 1** (simulación) para ver qué categorizaría
2. Si te gusta el resultado, ejecuta **opción 2** para aplicar cambios
3. Revisa con **opción 3** tu reporte semanal

## ⚙️ Personalización

### Añadir tus propias reglas de categorización

Edita el diccionario `categorization_rules` en el archivo:

```python
self.categorization_rules = {
    "Tu Categoría": ["palabra1", "palabra2", "palabra3"],
    "Comestibles": ["mercadona", "carrefour", "tu_super_favorito"],
    # ... más reglas
}
```

**Importante:** 
- El nombre de la categoría debe existir en tu presupuesto YNAB
- Las palabras clave buscan coincidencias parciales (no distinguen mayúsculas/minúsculas)

### Ejemplos de reglas personalizadas:

```python
"Mascotas": ["veterinario", "tiendanimal", "kiwoko"],
"Hogar": ["ikea", "leroy merlin", "bricomart"],
"Educación": ["udemy", "coursera", "libros"],
```

## 🤖 Automatización

### Windows (Programador de tareas)

1. Abre "Programador de tareas"
2. "Crear tarea básica"
3. Nombre: "YNAB Auto-Categorizer"
4. Frecuencia: Semanal (elige día y hora)
5. Acción: "Iniciar un programa"
6. Programa: `python`
7. Argumentos: `C:\ruta\al\ynab_auto_categorizer.py`

### Mac/Linux (Cron)

Edita tu crontab:
```bash
crontab -e
```

Añade esta línea para ejecutar cada lunes a las 9am:
```bash
0 9 * * 1 /usr/bin/python3 /ruta/completa/ynab_auto_categorizer.py
```

### Ejecutar automáticamente con un script auxiliar

Crea un archivo `auto_categorize.sh` (Mac/Linux) o `auto_categorize.bat` (Windows):

**Mac/Linux:**
```bash
#!/bin/bash
export YNAB_API_TOKEN="tu-token"
python3 /ruta/al/ynab_auto_categorizer.py <<EOF
2
s
EOF
```

**Windows:**
```batch
@echo off
set YNAB_API_TOKEN=tu-token
python C:\ruta\al\ynab_auto_categorizer.py
```

Haz el script ejecutable (Mac/Linux):
```bash
chmod +x auto_categorize.sh
```

## 📊 Generar Reportes en HTML

Para ver reportes más bonitos, usa el script auxiliar:

```bash
python3 generate_html_report.py
```

Esto creará un archivo `reporte_ynab.html` que puedes abrir en tu navegador.

## 🔧 Solución de Problemas

### Error: "No module named 'requests'"
```bash
pip install requests
```

### Error: "Missing scopes" o "Unauthorized"
- Verifica que tu token esté correcto
- Asegúrate de haber copiado el token completo
- Genera un nuevo token si es necesario

### Error: "Category not found"
- Las categorías en `categorization_rules` deben existir exactamente como aparecen en YNAB
- Ve a YNAB y verifica los nombres de tus categorías

### Las reglas no funcionan
- Verifica que las palabras clave estén en minúsculas
- Las búsquedas son parciales: "mcdo" encontrará "McDonald's"
- Prueba primero con opción 1 (simulación) para ver qué detecta

## 📁 Estructura de Archivos

```
ynab-auto-categorizer/
├── ynab_auto_categorizer.py    # Script principal
├── generate_html_report.py     # Generador de reportes HTML
├── README.md                    # Esta guía
└── requirements.txt             # Dependencias (opcional)
```

## 🆘 Soporte

Si tienes problemas:
1. Verifica que Python esté instalado: `python3 --version`
2. Verifica que requests esté instalado: `pip list | grep requests`
3. Prueba tu token en: https://api.ynab.com/v1/budgets (con Postman o similar)

## 🔐 Seguridad

- **NUNCA** compartas tu token de API
- Usa variables de entorno en vez de escribir el token en el código
- Si subes el código a GitHub, añade el token a `.gitignore`
- Puedes revocar tokens en cualquier momento desde YNAB

## 📝 Próximos Pasos

Una vez que funcione bien:
1. Personaliza las reglas de categorización
2. Configura la ejecución automática semanal
3. Revisa los reportes para ajustar tu presupuesto
4. Añade más reglas según vayas usando el sistema

¡Disfruta de tus finanzas automatizadas! 🎉
