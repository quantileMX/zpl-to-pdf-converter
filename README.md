# Convertidor ZPL a PDF

Convertidor ligero basado en Python que transforma archivos ZPL (Zebra Programming Language) de etiquetas térmicas en documentos PDF imprimibles para etiquetas de productos de Mercado Libre.

## Características

- **Análisis de ZPL**: Extrae datos de productos desde archivos de etiquetas térmicas ZPL
- **Generación de PDF**: Crea PDFs imprimibles con códigos de barras Code 128
- **Soporte de Cantidad**: Duplica automáticamente las etiquetas según la cantidad especificada
- **Múltiples Formatos**: Herramienta CLI y API REST
- **Docker**: Listo para desplegar en contenedor
- **Ligero**: ~25MB de dependencias, ~200MB imagen Docker

## Inicio Rápido

### Opción 1: Despliegue en Servidor (Docker) - Recomendado

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/txt_to_pdf.git
cd txt_to_pdf

# Construir y ejecutar con Docker Compose
docker-compose up -d

# Acceder a la API en http://localhost:8000
# Documentación en http://localhost:8000/docs
```

### Opción 2: Uso Local (CLI)

```bash
# Crear entorno conda
conda create -n z-pdf python=3.11 -y
conda activate z-pdf

# Instalar dependencias
pip install -r requirements.txt

# Convertir un archivo
python cli/convert.py archivo.txt

# Con salida personalizada
python cli/convert.py archivo.txt -o etiquetas.pdf

# Modo detallado
python cli/convert.py archivo.txt -v
```

## Uso

### Herramienta CLI

```bash
# Conversión básica
python cli/convert.py etiquetas.txt

# Especificar archivo de salida
python cli/convert.py etiquetas.txt -o mis-etiquetas.pdf

# Salida detallada
python cli/convert.py etiquetas.txt -v
```

**Resultado:**
```
✓ Se encontraron 34 productos únicos
✓ Total de etiquetas a generar: 1916
✓ PDF generado: etiquetas.pdf
```

### API Web

#### Convertir Archivo Individual

```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@etiquetas.txt" \
  --output etiquetas.pdf
```

#### Convertir Múltiples Archivos (Lote)

```bash
curl -X POST http://localhost:8000/convert-bulk \
  -F "files=@etiquetas1.txt" \
  -F "files=@etiquetas2.txt" \
  -F "files=@etiquetas3.txt" \
  --output etiquetas.zip
```

#### Usando Python

```python
import requests

# Conversión de archivo individual
with open('etiquetas.txt', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/convert',
        files={'file': f}
    )

    with open('salida.pdf', 'wb') as out:
        out.write(response.content)
```

### Endpoints de la API

- `GET /` - Información de la API
- `GET /health` - Verificación de salud
- `GET /docs` - Documentación interactiva (Swagger UI)
- `POST /convert` - Convertir archivo individual a PDF
- `POST /convert-bulk` - Convertir múltiples archivos a ZIP

## Formato ZPL

El convertidor espera archivos ZPL con la siguiente estructura:

```
^XA                                              # Inicio de etiqueta
^CI28                                            # Codificación UTF-8
^LH0,0                                           # Posición inicial
^FO65,18^BY2^BCN,54,N,N^FDGCOI36235^FS         # Código de barras (Code 128)
^FT150,98^A0N,22,22^FH^FDGCOI36235^FS          # Texto del código
^FO22,115^A0N,18,18^FB380,2,0,L^FH^FD[NOMBRE]^FS # Nombre del producto
^FO22,150^A0N,18,18^FB380,1,0,L^FH^FD[COLOR]^FS  # Color/variante
^FO22,170^A0N,18,18^FH^FDSKU: DV002^FS         # SKU
^PQ48,0,1,Y^XZ                                  # Cantidad (48 copias)
```

### Campos Extraídos

- **Código de barras**: Valor del código de barras Code 128
- **Nombre del producto**: Descripción del producto (soporta múltiples líneas)
- **Color/Variante**: Información opcional de color o variante
- **SKU**: Código de unidad de mantenimiento de existencias
- **Cantidad**: Número de copias de etiqueta a generar

## Salida PDF

### Especificaciones de Etiqueta

- **Tamaño de etiqueta**: 4" x 2" (compatible con impresora térmica)
- **Tamaño de página**: Carta (8.5" x 11")
- **Diseño**: 2 columnas × 5 filas = 10 etiquetas por página
- **Código de barras**: Formato Code 128
- **Márgenes**: 0.25" entre etiquetas

### Diseño de Etiqueta

```
┌─────────────────────────┐
│  [===CÓDIGO-BARRAS===]  │  Código de barras (Code 128)
│   GCOI36235             │  Texto del código
│                         │
│  Nombre del Producto    │  Descripción del producto
│  Blanco                 │  Color/variante
│  SKU: DV002             │  Código SKU
└─────────────────────────┘
```

## Estructura del Proyecto

```
txt_to_pdf/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI
│   ├── parser/
│   │   ├── __init__.py
│   │   └── zpl_parser.py    # Lógica de análisis ZPL
│   ├── generator/
│   │   ├── __init__.py
│   │   └── pdf_generator.py # Generación de PDF
│   └── models/
│       ├── __init__.py
│       └── label.py         # Modelos de datos
├── cli/
│   └── convert.py           # Herramienta de línea de comandos
├── tests/
│   ├── test_parser.py
│   └── test_generator.py
├── examples/
│   └── Envio-*.txt          # Archivo de ejemplo
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Dependencias

```
fastapi==0.109.0           # Framework web
uvicorn[standard]==0.27.0  # Servidor ASGI
python-multipart==0.0.6    # Carga de archivos
reportlab==4.0.9           # Generación de PDF
python-barcode==0.15.1     # Códigos de barras Code 128
pillow==10.2.0             # Soporte de imágenes
pydantic==2.5.3            # Validación de datos
```

**Tamaño total**: ~25MB instalado

## Configuración

### Variables de Entorno

```bash
# Tamaño máximo de carga de archivo (bytes)
MAX_UPLOAD_SIZE=10485760  # 10MB por defecto

# Nivel de registro
LOG_LEVEL=info
```

### Límites

- **Tamaño máximo de archivo**: 10MB
- **Máximo de etiquetas por archivo**: 10,000
- **Máxima cantidad por etiqueta**: 10,000
- **Máximo de archivos por solicitud lote**: 20
- **Tiempo de espera de solicitud**: 60 segundos

## Despliegue

### Desarrollo Local

```bash
# Crear entorno conda
conda create -n z-pdf python=3.11 -y
conda activate z-pdf

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar CLI
python cli/convert.py ejemplo.txt

# Ejecutar servidor API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Despliegue Docker

```bash
# Usando Docker Compose (recomendado)
docker-compose up -d

# O construir y ejecutar manualmente
docker build -t zpl-converter .
docker run -d -p 8000:8000 --name zpl-converter zpl-converter

# Ver registros
docker logs -f zpl-converter

# Detener contenedor
docker-compose down
```

### Despliegue en Producción

Para producción, considerar:

1. **Proxy Inverso**: Usar nginx o Traefik
2. **HTTPS**: Habilitar certificados SSL/TLS
3. **Autenticación**: Agregar autenticación con clave API
4. **Limitación de Tasa**: Prevenir abuso
5. **Monitoreo**: Agregar verificaciones de salud y métricas

Ejemplo de configuración nginx:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 10M;
    }
}
```

### Despliegue en la Nube

El contenedor Docker puede desplegarse en:

- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

## Pruebas

```bash
# Activar entorno
conda activate z-pdf

# Ejecutar pruebas
python -m pytest tests/ -v

# Probar con archivo de ejemplo
python cli/convert.py examples/Envio-59320753-Etiquetas-de-productos.txt -v

# Probar endpoints de API
curl http://localhost:8000/health
curl http://localhost:8000/
```

## Manejo de Errores

El convertidor maneja:

- **ZPL malformado**: Marcadores faltantes, sintaxis inválida
- **Datos inválidos**: Códigos de barras vacíos, SKUs faltantes
- **Problemas de archivo**: Muy grande, codificación incorrecta
- **Límites de recursos**: Demasiadas etiquetas, sin memoria

Respuestas de error incluyen:

- `400 Bad Request`: Formato de archivo inválido o sintaxis ZPL
- `413 Payload Too Large`: El archivo excede el límite de tamaño
- `500 Internal Server Error`: Fallo en generación de PDF

## Rendimiento

Pruebas de referencia (archivo de ejemplo con 1,916 etiquetas):

- **Análisis**: < 1 segundo
- **Generación de PDF**: ~2 segundos
- **Tiempo Total**: ~3 segundos
- **Uso de Memoria**: ~50MB base + ~1MB por 100 etiquetas
- **Tamaño de PDF**: ~120 bytes por etiqueta

## Seguridad

- **Validación de archivos**: Verificaciones de extensión y tamaño
- **Sanitización de entrada**: Validación de comandos ZPL
- **Límites de recursos**: Previene ataques DoS
- **Seguridad del contenedor**: Usuario no root, imagen mínima
- **Sin ejecución de código**: Procesamiento puro de datos

## Solución de Problemas

### Problemas Comunes

**1. Errores de importación**
```bash
# Asegúrate de estar en el entorno z-pdf
conda activate z-pdf
pip install -r requirements.txt
```

**2. Archivo no encontrado**
```bash
# Usa rutas absolutas o relativas
python cli/convert.py /ruta/completa/al/archivo.txt
```

**3. Falla en construcción de Docker**
```bash
# Limpiar caché de Docker y reconstruir
docker system prune -a
docker-compose build --no-cache
```

**4. Caracteres especiales no se muestran**
```
# ZPL usa codificación hex (_C3_B3 = ó)
# El analizador decodifica automáticamente estos
```

**5. Código de barras no legible**
```
# Asegúrate que el código contenga solo caracteres alfanuméricos
# Code 128 soporta: A-Z, 0-9
```

## Ejemplo de Salida

Conversión de ejemplo del archivo de etiquetas de Mercado Libre:

```bash
$ python cli/convert.py examples/Envio-59320753-Etiquetas-de-productos.txt -v

Entrada:  Envio-59320753-Etiquetas-de-productos.txt
Salida: Envio-59320753-Etiquetas-de-productos.pdf

Analizando archivo ZPL...
✓ Se encontraron 34 productos únicos
✓ Total de etiquetas a generar: 1916

Etiquetas de ejemplo:
  1. Servilletero Despachador De Servilletas Barramesa...
     SKU: DV002, Cant: 48
  2. Despachador De Toalla Interdoblada Tipo Sanitas...
     SKU: DV046, Cant: 10
  3. Dispensador Toalla Interdoblada / Sanitas Oval...
     SKU: DV075, Cant: 84
  ... y 31 más

Generando PDF...
✓ PDF generado exitosamente

✓ PDF generado: Envio-59320753-Etiquetas-de-productos.pdf
```

**Resultado**: PDF de 230 KB con 192 páginas conteniendo 1,916 etiquetas estilo térmico

## Guía de Despliegue para IT

### Requisitos del Servidor

- **Sistema Operativo**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **RAM**: Mínimo 512MB, recomendado 1GB
- **Disco**: 500MB para imagen + espacio para PDFs generados
- **Puerto**: 8000 (configurable)

### Instalación Paso a Paso

```bash
# 1. Instalar Docker (si no está instalado)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clonar repositorio
git clone https://github.com/TU_USUARIO/txt_to_pdf.git
cd txt_to_pdf

# 4. Iniciar servicio
docker-compose up -d

# 5. Verificar estado
docker ps
curl http://localhost:8000/health
```

### Mantenimiento

```bash
# Ver logs
docker-compose logs -f

# Reiniciar servicio
docker-compose restart

# Detener servicio
docker-compose down

# Actualizar a nueva versión
git pull
docker-compose up -d --build
```

### Monitoreo

```bash
# Verificar salud del contenedor
docker ps | grep zpl-to-pdf

# Ver uso de recursos
docker stats zpl-to-pdf

# Verificar logs de errores
docker logs zpl-to-pdf | grep ERROR
```

## Soporte

Para problemas o preguntas:

- Crear un issue en GitHub
- Revisar la documentación de la API en `/docs`
- Revisar la sección de solución de problemas arriba

## Licencia

MIT License - libre para usar en proyectos comerciales o personales.

---

**Desarrollado para impresión de etiquetas de Mercado Libre** 🏷️
