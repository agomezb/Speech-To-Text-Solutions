# Normalización de Texto para Evaluación ASR

Script de normalización de texto en español para evaluación de sistemas ASR (Google, Azure, Amazon, Faster Whisper). Aplica reglas estrictas de normalización para calcular el WER (Word Error Rate) de forma justa.

## Instalación

Las dependencias ya están en `requirements.txt`:

```bash
# Activar el entorno virtual
source venv/bin/activate

# Dependencias incluidas:
# - num2words==0.5.13 (conversión de números a palabras)
# - pandas==2.2.0 (procesamiento CSV)
# - jiwer==3.0.3 (herramientas WER)
# - typer==0.12.0 (CLI)
```

## Uso Rápido

```bash
# Normalizar un archivo CSV
python normalizar_texto.py input.csv

# Especificar archivo de salida
python normalizar_texto.py input.csv -o output.csv

# Normalizar columna específica
python normalizar_texto.py archivo.csv -c nombre_columna

# Ver ayuda
python normalizar_texto.py --help

# Ejecutar tests
python test_normalizer.py
```

## Reglas de Normalización

El script aplica las siguientes transformaciones en orden:

### 1. Minúsculas
Todo el texto se convierte a minúsculas.

### 2. Separación de Letras y Números (CRÍTICO para Amazon)
Separa automáticamente letras y números que están concatenados sin espacios. Esto soluciona el problema común de Amazon ASR que concatena caracteres.

**Ejemplos de transformación:**
- `FA409516` → `FA 409516` (luego se procesa como "efe a" + números)
- `RU0922078366001` → `RU 0922078366001` 
- `i73` → `i 73` (luego se procesa como "i setenta y tres")
- `A4` → `A 4` (luego se procesa por reemplazo personalizado)

Esta función usa regex para insertar espacios entre:
- Letra seguida de número: `([a-zA-Z])(\d)` → `\1 \2`
- Número seguido de letra: `(\d)([a-zA-Z])` → `\1 \2`

### 3. Reemplazos de Dominio (antes de eliminar puntuación)

| Original | Normalizado | Tipo |
|----------|-------------|------|
| `1 TB`, `1TB` | `un terabyte` | Almacenamiento |
| `2 TB`, `2TB` | `dos terabyte` | Almacenamiento |
| `i7` | `i siete` | Procesador |
| `i5` | `i cinco` | Procesador |
| `i3` | `i tres` | Procesador |
| `A4` | `a cuatro` | Formato papel |
| `XG` | `equis ge` | Modelo |
| `FA`, `F A` | `efe a` | Código factura |

### 4. Números a Palabras (español)
- **Números cortos (≤ 4 dígitos):** Se convierten directamente
  - Ejemplo: `5` → `"cinco"`, `50` → `"cincuenta"`
- **Números largos (> 4 dígitos):** Se convierten dígito por dígito
  - Ejemplo: `0922078366001` → `"cero nueve dos dos cero siete ocho tres seis seis cero cero uno"`
  - Útil para RUC, teléfonos, códigos de factura

### 5. Eliminación de Puntuación
Se eliminan todos los signos de puntuación: `. , : ; ? ! - ( ) " '`

### 6. Post-procesamiento Español
Correcciones específicas del idioma:
- `"uno terabyte"` → `"un terabyte"`
- `"uno gigabyte"` → `"un gigabyte"`

### 7. Limpieza de Espacios
- Elimina espacios múltiples
- Elimina espacios al inicio y final

## Ejemplos

### Ejemplo 1: Completo

**Entrada:**
```
Genera una proforma para Andina Corp. con 2 laptops Core i7 y 1 TB de disco.
```

**Salida:**
```
genera una proforma para andina corp con dos laptops core i siete y un terabyte de disco
```

### Ejemplo 2: Factura con código concatenado (problema Amazon)

**Entrada:**
```
Verifica si la factura FA409516 de Hierro del Pacífico ya está pagada.
```

**Proceso:**
1. Separación: `FA409516` → `FA 409516`
2. Reemplazo: `FA` → `efe a`
3. Números largos: `409516` → `cuatro cero nueve cinco uno seis`

**Salida:**
```
verifica si la factura efe a cuatro cero nueve cinco uno seis de hierro del pacífico ya está pagada
```

### Ejemplo 3: Modelo concatenado (problema Amazon)

**Entrada:**
```
Compra laptops core i73 impresoras
```

**Proceso:**
1. Separación: `i73` → `i 73`
2. Reemplazo: `i` → `i`
3. Número corto: `73` → `setenta y tres`

**Salida:**
```
compra laptops core i setenta y tres impresoras
```

### Ejemplo 4: Número largo (RUC)

**Entrada:**
```
Crea un nuevo cliente con el nombre Julián Antonio Pérez y RUC 0922078366001.
```

**Salida:**
```
crea un nuevo cliente con el nombre julián antonio pérez y ruc cero nueve dos dos cero siete ocho tres seis seis cero cero uno
```

## Estructura del CSV

El CSV de entrada debe tener al menos una columna de texto:

```csv
filename,text,status,transcription_time
1,"Genera una cotización para el cliente...",success,2.08
2,"Prepara un presupuesto urgente...",success,1.26
```

El script agrega una columna `text_normalized` con el texto procesado.

## Uso Programático

```python
from normalizar_texto import TextNormalizer

# Uso básico
normalizer = TextNormalizer()
resultado = normalizer.normalize("Texto con 5 laptops i7 y 1 TB")
print(resultado)
# Output: texto con cinco laptops i siete y un terabyte

# Con reemplazos personalizados
custom_dict = {
    "ssd": "disco sólido",
    "ram": "memoria ram",
    "8gb": "ocho gigabytes"
}
normalizer = TextNormalizer(custom_replacements=custom_dict)
resultado = normalizer.normalize("Laptop con 8GB RAM y SSD")
print(resultado)
# Output: laptop con ocho gigabytes memoria ram y disco sólido
```

## Procesamiento de Archivos CSV

```python
from normalizar_texto import TextNormalizer, CSVNormalizer
from pathlib import Path

# Crear normalizador y procesador
normalizer = TextNormalizer()
csv_processor = CSVNormalizer(normalizer)

# Procesar archivo
csv_processor.process_csv(
    input_path=Path("google_clean.csv"),
    output_path=Path("google_normalized.csv"),
    text_column="text"
)
```

## Arquitectura SOLID

El código sigue los principios SOLID para mantenibilidad y extensibilidad:

### Single Responsibility Principle (SRP)
- `TextNormalizer`: Solo normaliza texto
- `CSVNormalizer`: Solo procesa archivos CSV
- Cada método tiene una única responsabilidad clara

### Open/Closed Principle (OCP)
- Fácilmente extensible mediante diccionarios personalizados
- Puedes agregar nuevas reglas sin modificar el código existente

### Dependency Inversion Principle (DIP)
- `CSVNormalizer` depende de la abstracción `TextNormalizer`
- Puedes inyectar cualquier normalizador compatible

## Validación

El script incluye una suite de 18 tests que validan todas las reglas:

```bash
python test_normalizer.py
```

**Tests incluidos:**
- Conversión a minúsculas
- Eliminación de puntuación
- Números simples y largos
- Todos los reemplazos personalizados (i7, i5, TB, A4, XG, FA)
- Combinaciones de transformaciones
- Casos edge (texto vacío, solo puntuación)
- Mantenimiento de acentos

## Solución de Problemas

### Error: "La columna 'text' no existe"
**Solución:** Especifica el nombre correcto de la columna con `-c`:
```bash
python normalizar_texto.py archivo.csv -c nombre_columna_correcta
```

### Error: "FileNotFoundError"
**Solución:** Verifica la ruta del archivo:
```bash
ls -la *.csv  # Lista los archivos CSV disponibles
```

## Casos de Uso para Tesis ASR

### 1. Normalizar transcripciones de todos los motores

```bash
python normalizar_texto.py google_clean.csv -o google_normalized.csv
python normalizar_texto.py azure_clean.csv -o azure_normalized.csv
python normalizar_texto.py amazon_clean.csv -o amazon_normalized.csv
python normalizar_texto.py whisper_clean.csv -o whisper_normalized.csv
```

### 2. Normalizar Ground Truth

**Importante:** Normaliza tu Ground Truth con las mismas reglas para garantizar una comparación justa:

```bash
python normalizar_texto.py ground_truth.csv -o ground_truth_normalized.csv
```

### 3. Calcular WER con jiwer

```python
from jiwer import wer
import pandas as pd

# Leer archivos normalizados
ground_truth = pd.read_csv('ground_truth_normalized.csv')
hypothesis = pd.read_csv('google_normalized.csv')

# Calcular WER
references = ground_truth['text_normalized'].tolist()
hypotheses = hypothesis['text_normalized'].tolist()

error_rate = wer(references, hypotheses)
print(f"WER: {error_rate:.2%}")
```

## Archivos Incluidos

```
normalizar_texto.py          # Script principal con CLI
test_normalizer.py           # Suite de 18 tests
README_NORMALIZACION.md      # Esta documentación
```

## Referencias

- **num2words**: Conversión de números a palabras en español
- **pandas**: Procesamiento de archivos CSV
- **jiwer**: Biblioteca para cálculo de WER (Word Error Rate)
- **typer**: Framework CLI moderno para Python

## Autor

Script desarrollado para tesis de comparación de motores ASR (Google, Azure, Amazon, Faster Whisper).

## Licencia

Ver archivo LICENSE en el repositorio.

