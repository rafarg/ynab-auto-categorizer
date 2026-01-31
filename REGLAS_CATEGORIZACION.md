# 📚 Ejemplos de Reglas de Categorización Avanzadas

Esta guía te ayuda a personalizar las reglas de categorización del script.

## 🎯 Cómo funcionan las reglas

Las reglas buscan coincidencias **parciales** en el nombre del comercio/beneficiario:
- No distinguen mayúsculas/minúsculas
- "mcdo" encontrará "McDonald's", "MCDONALDS", etc.
- Son búsquedas de subcadena: "amazon" encontrará "Amazon.es", "Amazon Prime", etc.

## 📝 Estructura básica

```python
self.categorization_rules = {
    "Nombre de Categoría en YNAB": ["palabra1", "palabra2", "palabra3"],
}
```

## 🇪🇸 Ejemplos para España

### Supermercados y Alimentación
```python
"Comestibles": [
    "mercadona", "carrefour", "lidl", "aldi", "dia", 
    "eroski", "alcampo", "consum", "hipercor", "el corte ingles",
    "supercor", "spar", "ahorramas", "bonpreu", "condis"
],

"Restaurantes": [
    "restaurant", "mcdonald", "burger king", "kfc", "subway",
    "domino", "pizza hut", "telepizza", "taco bell",
    "kebab", "china", "sushi", "pans", "vips", "ginos",
    "foster", "lizarran", "cerveceria", "taberna", "bar "
],

"Panadería/Pastelería": [
    "panaderia", "pasteleria", "horno", "granier", "panaria"
],

"Cafeterías": [
    "starbucks", "cafe", "cafeteria", "coffee"
],
```

### Transporte
```python
"Gasolina": [
    "repsol", "shell", "cepsa", "bp", "galp", "campsa",
    "petronor", "disa", "carburante", "gasolinera"
],

"Transporte Público": [
    "renfe", "metro", "cercanias", "emt", "tmb", "amt",
    "avanza", "alsa", "uber", "cabify", "bolt", "taxi",
    "bicing", "patinete", "lime", "metro madrid", "tmb barcelona"
],

"Parking": [
    "parking", "aparcamiento", "estacionamiento", "parkia"
],

"Peajes": [
    "autopista", "peaje", "via-t", "telepeaje"
],
```

### Hogar y Servicios
```python
"Electricidad/Agua/Gas": [
    "iberdrola", "endesa", "naturgy", "edp", "repsol butano",
    "aqualia", "canal isabel", "agbar", "gas natural"
],

"Teléfono/Internet": [
    "vodafone", "movistar", "orange", "yoigo", "masmovil",
    "pepephone", "jazztel", "lowi", "o2", "telecable"
],

"Alquiler": [
    "alquiler", "renta", "arrendamiento"
],

"Comunidad": [
    "comunidad", "gastos comunes", "derrama"
],
```

### Compras y Retail
```python
"Ropa": [
    "zara", "h&m", "mango", "pull&bear", "bershka", "stradivarius",
    "massimo dutti", "primark", "c&a", "decathlon", "sprinter",
    "cortefiel", "nike", "adidas", "puma"
],

"Electrónica": [
    "mediamarkt", "fnac", "pccomponentes", "apple", "worten",
    "amazon", "aliexpress", "mielectro"
],

"Hogar/Muebles": [
    "ikea", "leroy merlin", "bricomart", "aki", "bauhaus",
    "conforama", "el corte ingles", "hogar"
],

"Farmacia": [
    "farmacia", "pharmacy", "parafarmacia", "dosfarma"
],
```

### Entretenimiento y Ocio
```python
"Streaming": [
    "netflix", "hbo", "disney", "amazon prime", "movistar+",
    "spotify", "apple music", "youtube premium", "dazn"
],

"Videojuegos": [
    "steam", "playstation", "xbox", "nintendo", "epic games",
    "game", "xtralife", "cex"
],

"Cine/Teatro": [
    "cine", "cinema", "kinepolis", "yelmo", "cinesa",
    "teatro", "entradas.com", "ticketmaster"
],

"Gimnasio/Deporte": [
    "gym", "gimnasio", "fitness", "crossfit", "pilates",
    "altafit", "mcfit", "metropolitan", "o2", "vivagym"
],

"Libros": [
    "fnac", "casa del libro", "amazon libro", "libreria"
],
```

### Salud y Bienestar
```python
"Médico": [
    "hospital", "clinica", "medico", "doctor", "consulta"
],

"Dentista": [
    "dentista", "odontolog", "dental", "ortodoncia"
],

"Seguros": [
    "seguro", "axa", "mapfre", "sanitas", "adeslas", "dkv",
    "mutua", "racc", "linea directa"
],
```

### Educación
```python
"Educación": [
    "colegio", "escuela", "universidad", "udemy", "coursera",
    "domestika", "platzi", "academia", "curso"
],

"Material Escolar": [
    "libreria", "papeleria", "staples", "material escolar"
],
```

### Mascotas
```python
"Mascotas": [
    "veterinario", "tiendanimal", "kiwoko", "miscota",
    "hospital veterinario", "clinica veterinaria"
],
```

### Bancos y Finanzas
```python
"Comisiones Bancarias": [
    "comision", "mantenimiento cuenta", "tarjeta"
],

"Transferencias": [
    "transferencia", "bizum"
],
```

### Impuestos y Obligaciones
```python
"Impuestos": [
    "hacienda", "aeat", "seguridad social", "ayuntamiento",
    "ibi", "basura", "multa"
],
```

## 🎨 Categorías Personalizadas

### Hobbies específicos
```python
"Fotografía": [
    "canon", "nikon", "sony camera", "fnac foto", "amazon photo"
],

"Jardinería": [
    "verdecora", "jardiland", "vivero", "semillas"
],

"Bricolaje": [
    "bricomart", "leroy merlin", "ferreteria", "herramienta"
],
```

## 💡 Tips para crear buenas reglas

1. **Usa palabras únicas**: "mercadona" es mejor que "super"
2. **Incluye variaciones**: "gym", "gimnasio", "fitness"
3. **Evita palabras comunes**: No uses "el", "la", "tienda"
4. **Prueba primero**: Usa modo simulación (opción 1) antes de aplicar
5. **Revisa tus transacciones**: Mira nombres reales en YNAB para añadir palabras clave
6. **Empieza simple**: Añade categorías conforme las necesites

## 🔧 Reglas Inteligentes

### Por monto (requiere modificar el código)
```python
def categorize_by_amount(self, amount, payee_name):
    # Gastos pequeños frecuentes
    if abs(amount) < 5:
        if any(word in payee_name.lower() for word in ["cafe", "kiosko"]):
            return "Gastos Pequeños"
    
    # Gastos grandes
    if abs(amount) > 500:
        return "Grandes Compras"
```

### Por día de la semana (requiere modificar el código)
```python
from datetime import datetime

def categorize_by_day(self, date, payee_name):
    day = datetime.strptime(date, "%Y-%m-%d").weekday()
    
    # Viernes/Sábado → probablemente ocio
    if day in [4, 5] and any(word in payee_name.lower() for word in ["bar", "restaurant"]):
        return "Ocio Fin de Semana"
```

## 📊 Mantenimiento

Revisa y actualiza tus reglas cada mes:
1. Ejecuta el script en modo simulación
2. Anota transacciones que no se categorizaron
3. Añade nuevas palabras clave
4. Elimina reglas que no uses

## 🚀 Próximos Pasos

Una vez tengas tus reglas básicas:
1. Añade categorías específicas para tus necesidades
2. Prueba con modo simulación (opción 1)
3. Refina las palabras clave
4. Programa la ejecución automática
5. ¡Disfruta de finanzas automatizadas!
