# Contexto técnico de Proyecto Delta

> **Corte de la investigación:** 21 de septiembre de 2026.  
> **Repositorio principal inspeccionado:** `proyecto-delta`, rama `main`, commit `db91c13` (`T08 - Avance`).  
> **Prioridad de este documento:** MPC, MP-SPDZ, Secret Sharing, parties, Docker, networking, flujo de datos e integración.  
> **Alcance de “actual”:** estado del árbol de trabajo local y de sus referencias Git locales. No se hizo `git fetch`, no se construyó MP-SPDZ y no se modificó código ni configuración.

Este documento separa deliberadamente cuatro categorías:

- **Implementado:** existe código ejecutable para la función descrita.
- **Parcial/prototipo:** existe y es útil, pero todavía no cumple el flujo MPC final.
- **Mock:** simula el límite o contrato de un componente futuro sin ejecutar ese componente.
- **Documentado:** expresa intención o investigación, pero no constituye una implementación.

La fuente de verdad usada fue, en este orden: código ejecutable, configuración Docker, tests, README y documentación histórica de `TareasDeInvestigacion/`.

## 1. Resumen ejecutivo

Proyecto Delta implementa actualmente la entrada segura descrita por T09, no un sistema MPC completo. El flujo implementado es:

```text
Cliente CLI confiable
  ├─ metadata ───────────────> Coordinator FastAPI
  ├─ share XOR 0 por HTTP ──> Mock Party 0
  ├─ share XOR 1 por HTTP ──> Mock Party 1
  └─ share XOR 2 por HTTP ──> Mock Party 2
                                   │
                                   └─ confirmaciones HTTP ──> Coordinator
```

Lo que sí existe:

- una CLI Python que conserva el MP4 en el equipo cliente;
- preprocesamiento local con OpenCV;
- un contenedor binario propio compuesto por metadata y frames recodificados a JPEG;
- un esquema XOR de tres shares de longitud completa;
- un Coordinator que genera UUID, devuelve destinos y mantiene estados en memoria;
- tres receptores HTTP mock, cada uno en un contenedor y con un directorio de almacenamiento distinto;
- Docker Compose y una suite amplia de tests del prototipo T09.

Lo que no existe:

- un programa MPC de Proyecto Delta en `Programs/Source/*.mpc`;
- procesos `*-party.x` conectados a las mock parties;
- comunicación MPC party-a-party;
- conversión de los datos de video a entradas numéricas compatibles con un dominio MP-SPDZ;
- un disparador sincronizado de ejecución MPC;
- captura o reconstrucción autorizada de un resultado;
- estados de procesamiento o finalización MPC.

La separación conceptual entre **Control Plane** y **Data Plane** sí está reflejada en código: el Coordinator recibe `filename`, `format` y confirmaciones, mientras los bytes de los shares viajan directamente del cliente a los receptores. Sin embargo, esos receptores no son parties MP-SPDZ: son aplicaciones FastAPI que guardan bytes opacos.

El Secret Sharing actual es un esquema XOR 3-de-3 matemáticamente reconstruible y usa aleatoriedad de `secrets.token_bytes`; no es simplemente sharding. Aun así, es **provisional, independiente y no compatible de forma directa con MP-SPDZ**. En particular, `Player-Data/Input-P<i>-0` espera valores privados en claro aportados por la party `i`, para que MP-SPDZ los comparta internamente; no espera un archivo de shares XOR arbitrarios.

La integración Proyecto Delta → MP-SPDZ se clasifica como **inexistente en la aplicación actual** y **exploratoria a nivel de investigación/PoC separada**. El repositorio contiene una copia histórica del Dockerfile de MP-SPDZ en `TareasDeInvestigacion/T06/Dockerfile`, y existe un clon hermano de MP-SPDZ, pero ninguno está referenciado por el `Dockerfile`, `docker-compose.yml` o código Python actual.

El siguiente paso técnico que desbloquea el proyecto es definir un contrato pequeño y verificable de entrada MPC —dominio, tipo, escala, orden, dimensiones, tamaño y programa— y ejecutar un trabajo mínimo extremo a extremo con tres runtimes MP-SPDZ. Para preservar el diseño de cliente confiable, la ruta más directa que ofrece MP-SPDZ es su interfaz `ExternalIO`, mediante la cual el cliente se conecta a todas las parties y aporta valores privados usando el sharing propio del protocolo.

## 2. Estado del repositorio

### 2.1 Repositorio principal

| Dato | Valor observado |
|---|---|
| Ruta | `C:/Proyectos/ProyectoDelta/proyecto-delta` |
| Remoto | `https://github.com/CtpN3m01/proyecto-delta` |
| Rama | `main` |
| HEAD | `db91c13` — `T08 - Avance`, 2026-09-17 |
| Estado previo a crear este informe | limpio: `## main...origin/main` |
| Relación con `origin/main` | sin diferencia según la referencia local; no se hizo `fetch` |
| Commit de implementación principal | `87c7c0f` — `Tarea 09`, 2026-09-13 |

El directorio padre `C:/Proyectos/ProyectoDelta` no es un repositorio Git. Contiene dos repositorios hermanos independientes:

```text
C:/Proyectos/ProyectoDelta/
├── proyecto-delta/   # aplicación objeto de esta investigación
└── MP-SPDZ/          # clon externo; no es submódulo ni dependencia enlazada
```

No existe `AGENTS.md` en estos árboles.

### 2.2 Estructura principal

```text
proyecto-delta/
├── src/
│   ├── client/
│   ├── coordinator/
│   └── party_receiver/
├── tests/
│   ├── api/
│   ├── integration/
│   └── unit/
├── data/parties/
│   ├── party-0/
│   ├── party-1/
│   └── party-2/
├── TareasDeInvestigacion/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

Las carpetas `data/parties/party-{0,1,2}` solo contenían `.gitkeep` durante la inspección; no había shares generados.

### 2.3 Tecnologías y dependencias

| Área | Tecnología actual | Evidencia |
|---|---|---|
| Lenguaje | Python `>=3.10` | `pyproject.toml` |
| Imagen de aplicación | `python:3.12-slim` | `Dockerfile` |
| API | FastAPI + Uvicorn | `requirements.txt`, `src/coordinator/main.py`, `src/party_receiver/main.py` |
| Cliente HTTP | HTTPX | `src/client/networking/`, `src/party_receiver/services/share_service.py` |
| Video | OpenCV headless | `src/client/preprocessing/video_preprocessor.py` |
| Arreglos/XOR | NumPy | `src/client/sharing/share_generator.py` |
| Modelos HTTP | Pydantic, transitivo de FastAPI | `src/coordinator/models/video.py` |
| Empaquetado | setuptools, layout `src/` | `pyproject.toml` |
| Tests | pytest | `requirements-dev.txt`, `tests/` |
| Orquestación local | Docker Compose | `docker-compose.yml` |
| Base de datos/cola | ninguna | no existe configuración ni dependencia correspondiente |

`pyproject.toml` instala el comando `delta`, equivalente a `client.cli:main`. `.env.example` documenta URLs e identidad/almacenamiento de las parties; no contiene secretos.

### 2.4 Validaciones realizadas

- `docker compose config` terminó con código 0 y resolvió los cuatro servicios, la red por defecto y los tres bind mounts. Docker mostró una advertencia de acceso a `C:/Users/ianpr/.docker/config.json`, pero sí produjo la configuración final.
- La suite no pudo iniciarse en este entorno: `python -m pytest -p no:cacheprovider` devolvió `No module named pytest`. No se instalaron dependencias porque este trabajo prohíbe modificar el entorno salvo por este Markdown.
- No se ejecutó `docker compose up --build`: la investigación permitía evitar builds costosos y el análisis no requiere reconstruir las imágenes.

## 3. Estructura relevante del proyecto

| Ruta | Responsabilidad real | Estado |
|---|---|---|
| `src/client/` | CLI confiable, preprocesamiento, generación y envío de shares | implementado para T09 |
| `src/client/preprocessing/` | convierte MP4 local en contenedor binario de JPEGs | prototipo, no tensor MPC |
| `src/client/sharing/` | contrato `ShareGenerator` e implementación XOR | prototipo independiente de MP-SPDZ |
| `src/client/networking/` | clientes HTTP del Coordinator y receptores | implementado para T09 |
| `src/coordinator/` | Control Plane FastAPI y estado en memoria | parcial |
| `src/party_receiver/` | receptor HTTP reutilizado por las tres mock parties | mock |
| `data/parties/party-*` | destino persistente de los shares mediante bind mounts | almacenamiento de prototipo |
| `tests/` | pruebas de servicios, API, CLI, sharing, video y almacenamiento | implementado; no incluye MPC real |
| `TareasDeInvestigacion/T09.md` | diseño y límites de la implementación T09 | documentación alineada con el código |
| `TareasDeInvestigacion/T04.md` | arquitectura objetivo con tres parties MP-SPDZ y resultado anonimizado | diseño, no implementación |
| `TareasDeInvestigacion/T06/Dockerfile` | copia/experimento histórico del Dockerfile de MP-SPDZ | desacoplado del build actual |
| `TareasDeInvestigacion/T08.md` | plan de acceso SSH al clúster mediante Cloudflare/WARP | planeamiento; no despliega parties |

`TareasDeInvestigacion/T01.md`, `T02.md` y `T03.md` contienen investigación sobre técnicas y frameworks. Ayudan a entender la selección de MP-SPDZ como foco, pero no prueban que exista una integración ejecutable.

## 4. Componentes actuales

### 4.1 CLI del cliente confiable

**Ubicación:** `src/client/cli.py`, `src/client/__main__.py`  
**Responsabilidad:** coordinar el flujo T09 desde el host del usuario.  
**Entradas:** ruta a un archivo `.mp4`; `COORDINATOR_URL`.  
**Salidas:** llamadas HTTP, mensajes de consola y código de salida.  
**Dependencias:** `CoordinatorClient`, `PartyClient`, `VideoPreprocessor`, `ShareGenerator`.  
**Se comunica con:** Coordinator y las tres mock parties.  
**Estado:** implementado para el prototipo; no inicia MPC.

### 4.2 Preprocesador local

**Ubicación:** `src/client/preprocessing/video_preprocessor.py`, clase `VideoPreprocessor`.  
**Responsabilidad:** abrir el MP4 con OpenCV, decodificar frames y recodificar cada uno como JPEG calidad 90.  
**Entrada:** ruta local.  
**Salida:** `PreprocessedVideo(payload: bytes, metadata: VideoMetadata)`.  
**Estado:** implementado, pero su salida es un contenedor multimedia comprimido, no la matriz/tensor numérico que necesitaría un programa MPC de visión.

El payload usa:

- magic `DELTA-T09-JPEG\0`;
- longitud de metadata en entero de 32 bits big-endian;
- un área reservada de 512 bytes para JSON;
- metadata de versión, codificación, frames, alto, ancho, canales, FPS y `dtype`;
- secuencia de bloques JPEG, cada uno precedido por su longitud de 32 bits.

### 4.3 Generador de shares

**Ubicación:** `src/client/sharing/share_generator.py`; fábrica en `src/client/sharing/__init__.py`.  
**Responsabilidad:** producir exactamente tres shares de bytes.  
**Entrada:** payload binario completo.  
**Salida:** tupla `(share_0, share_1, share_2)`.  
**Estado:** prototipo; el propio docstring indica que no es compatible con MP-SPDZ.

### 4.4 Coordinator

**Ubicación:** `src/coordinator/`.  
**Responsabilidad:** registrar metadata, crear UUID4, publicar destinos, recibir confirmaciones y derivar el estado agregado.  
**Entradas:** JSON de registro/confirmación y UUID de consulta.  
**Salidas:** JSON de registro/estado.  
**Persistencia:** diccionario en memoria protegido por `RLock`.  
**Estado:** parcial; completa el Control Plane de recepción, pero carece de ejecución MPC y persistencia.

### 4.5 Party Receiver

**Ubicación:** `src/party_receiver/`.  
**Responsabilidad:** recibir bytes opacos, guardarlos y notificar su recepción.  
**Entradas:** `application/octet-stream`, UUID y variables `PARTY_ID`, `PARTY_STORAGE_DIR`, `COORDINATOR_INTERNAL_URL`.  
**Salidas:** archivo `.share`, callback HTTP y recibo JSON.  
**Estado:** mock; no contiene runtime, librerías, procesos ni protocolos de MP-SPDZ.

### 4.6 Almacenamiento local

**Ubicación:** `src/party_receiver/storage/local_storage.py`, clase `LocalStorage`.  
**Responsabilidad:** escritura atómica mediante temporal + `fsync` + `os.replace`.  
**Entrada:** UUID validado y bytes no vacíos.  
**Salida:** `<video_id>.share`.  
**Estado:** implementado para archivos locales; no representa persistencia nativa de shares MP-SPDZ.

### 4.7 Docker Compose

**Ubicación:** `Dockerfile`, `docker-compose.yml`.  
**Responsabilidad:** levantar el Coordinator y tres instancias del mismo receptor.  
**Estado:** implementado para T09; no levanta MP-SPDZ.

### 4.8 Computer Vision

No hay modelos, detección de rostros/placas ni anonimización en `src/`. OpenCV se usa exclusivamente para decodificar el MP4 y recodificar frames como JPEG en `src/client/preprocessing/video_preprocessor.py`. Su relación potencial con MPC es producir la entrada previa, pero el formato actual todavía no es el tensor numérico descrito en `TareasDeInvestigacion/T04.md`.

## 5. Coordinator / API central

La aplicación se crea en `src/coordinator/main.py` y monta el router de `src/coordinator/api/videos.py`. Se inicia con:

```bash
uvicorn coordinator.main:app --host 0.0.0.0 --port 8000
```

`video_service` es una instancia global construida al importar el router. `load_party_urls()` exige exactamente tres URLs HTTP/HTTPS; por defecto son `http://localhost:8100`, `:8101` y `:8102`.

### 5.1 Endpoints

| Método y ruta | Archivo / función | Servicio interno | Request | Respuesta normal | Errores relevantes | Efectos secundarios |
|---|---|---|---|---|---|---|
| `GET /health` | `src/coordinator/main.py::health` | ninguno | ninguno | `200 {"status":"ok"}` | — | ninguno |
| `POST /api/v1/videos` | `src/coordinator/api/videos.py::register_video` | `VideoService.register_video` | JSON `filename` (1–255) y `format` (1–20) | `201`, UUID, `WAITING_FOR_SHARES`, lista de parties | `415` si no es MP4; `422` por cuerpo/campos inválidos | crea `_VideoJob` en memoria con tres `PENDING` |
| `GET /api/v1/videos/{video_id}` | `get_video` | `VideoService.get_video` | UUID en ruta | `200`, estado agregado y mapa de parties | `404` desconocido; `422` UUID inválido | ninguno |
| `POST /api/v1/videos/{video_id}/confirmations` | `confirm_share` | `VideoService.confirm_share` | JSON con `party_id` entero estricto 0–2 y `status: "RECEIVED"` | `200`, estado actualizado | `404` job desconocido; `422` UUID/body/party inválido | marca la party `RECEIVED`; con las tres cambia a `READY_FOR_MPC` |

Los modelos están en `src/coordinator/models/video.py`; la lógica está en `src/coordinator/services/video_service.py`.

### 5.2 Qué conoce y qué no conoce

El Coordinator conoce:

- UUID;
- nombre original del archivo y formato dentro de `_VideoJob`;
- URLs públicas de las tres parties;
- estado agregado;
- estado de recepción por party.

No recibe mediante el código actual:

- el MP4;
- el payload preprocesado;
- los bytes de ningún share;
- dimensiones o número de frames;
- un programa/protocolo MPC;
- resultados MPC.

El nombre del archivo sí es metadata centralizada y puede contener información sensible si el usuario incluye datos descriptivos en él.

### 5.3 Límites reales

- Las confirmaciones son idempotentes, pero no están autenticadas.
- Cualquier cliente que conozca un UUID puede invocar la confirmación directamente; `READY_FOR_MPC` demuestra tres callbacks aceptados, no la existencia, integridad o compatibilidad de tres inputs.
- No hay transición hacia procesamiento, completado o fallo.
- Al reiniciar Uvicorn/contenedor desaparecen todos los jobs.
- No hay conciliación al arrancar con los archivos persistentes de las parties.
- No hay callback del Coordinator hacia parties; el Coordinator solo devuelve sus URLs y recibe notificaciones.

## 6. Cliente

### 6.1 Ejecución

Puntos de entrada:

```bash
python -m client upload ./video.mp4
delta upload ./video.mp4
```

`python -m client` delega en `client.cli:main`; `delta` se declara en `pyproject.toml`.

### 6.2 Flujo implementado

`src/client/cli.py::upload_video` ejecuta de forma secuencial:

1. verifica que la ruta exista, sea archivo y tenga extensión `.mp4` sin distinguir mayúsculas;
2. registra `filename` y `format="mp4"` en el Coordinator;
3. abre y preprocesa localmente el archivo;
4. genera tres shares XOR;
5. entrega cada share, en orden de party 0, 1 y 2;
6. consulta una sola vez el estado final;
7. retorna 0 solo si recibe `READY_FOR_MPC`.

La validación de extensión no sustituye la validación del contenido: un MP4 corrupto se detecta después, cuando OpenCV intenta abrirlo. Como el registro ocurre antes del preprocesamiento, un fallo posterior deja un job `WAITING_FOR_SHARES` hasta reiniciar el Coordinator.

### 6.3 Networking

- `src/client/networking/coordinator_client.py::CoordinatorClient` envía JSON al Coordinator y valida UUID, contrato y exactamente las parties `{0,1,2}`.
- `src/client/networking/party_client.py::PartyClient` envía bytes crudos con `Content-Type: application/octet-stream` a `/api/v1/shares/{video_id}`.
- `COORDINATOR_URL` es configurable y por defecto vale `http://localhost:8000`.
- Las URLs de parties no se configuran directamente en la CLI: llegan en la respuesta del Coordinator.

Los envíos son secuenciales y no tienen reintento automático ni rollback. Si Party 1 falla después de que Party 0 guardó su archivo, queda un trabajo parcial. La CLI no hace polling: consulta el estado una vez inmediatamente después del tercer envío.

### 6.4 Memoria y formato

El preprocesador evita conservar todos los frames crudos simultáneamente, pero sí materializa el payload completo. El generador conserva el payload, dos `bytes` aleatorios completos y un tercer `bytearray` completo antes de retornar los tres shares. No hay streaming integral de entrada, generación o HTTP.

## 7. Flujo REAL actual de datos

```text
[Host cliente confiable]
  video.mp4
     │ OpenCV: decodifica cada frame y lo vuelve a codificar JPEG calidad 90
     ▼
  payload DELTA-T09-JPEG completo en memoria
     │ XOR con S0 y S1 aleatorios
     ├──────── S0 ──HTTP :8100──> [mock-party-0] ──> data/parties/party-0/<uuid>.share
     ├──────── S1 ──HTTP :8101──> [mock-party-1] ──> data/parties/party-1/<uuid>.share
     └──────── S2 ──HTTP :8102──> [mock-party-2] ──> data/parties/party-2/<uuid>.share
                                           │
                        cada receptor guarda y hace POST de confirmación
                                           ▼
                                [Coordinator :8000]
                         WAITING_FOR_SHARES → READY_FOR_MPC

No existe paso posterior hacia MP-SPDZ.
```

### 7.1 Visibilidad por componente

| Componente/actor | Datos que puede ver en la implementación actual |
|---|---|
| Proceso de la CLI | MP4 original, payload completo, metadata de frames y los tres shares |
| Coordinator | nombre, formato, UUID, endpoints y estados; no bytes de video/share |
| Contenedor mock Party 0 | S0 y su tamaño |
| Contenedor mock Party 1 | S1 y su tamaño |
| Contenedor mock Party 2 | S2 y su tamaño |
| Operador del host Docker | los tres directorios bind-mounted y, por tanto, potencialmente los tres shares |
| MP-SPDZ | nada; no recibe llamadas ni archivos |

Cada contenedor solo monta su propio directorio y la API no expone lectura de shares. Esto es separación funcional, no independencia de seguridad: los tres servicios y sus directorios residen en un solo host administrado por el mismo operador.

El MP4 original no se copia a Coordinator o parties por ninguna ruta del código inspeccionado. El tamaño del payload sí es observable por cada receptor porque los tres shares tienen la misma longitud.

## 8. Secret Sharing

### 8.1 Implementación actual

La interfaz `ShareGenerator` está en `src/client/sharing/share_generator.py`; `create_share_generator()` siempre retorna `XorShareGenerator`.

Para un payload `D` de `n` bytes:

```text
S0 = CSPRNG(n)
S1 = CSPRNG(n)
S2 = D XOR S0 XOR S1

D  = S0 XOR S1 XOR S2
```

Propiedades observadas:

| Aspecto | Implementación actual |
|---|---|
| Algoritmo | sharing XOR de tres componentes |
| Dominio | vector de bytes/operación bit a bit; NumPy usa `uint8` |
| Aleatoriedad | `secrets.token_bytes` para S0 y S1 |
| Cantidad | exactamente 3 shares |
| Umbral | se requieren los 3 para esta reconstrucción 3-de-3 |
| Tamaño | cada share mide lo mismo que el payload completo |
| Generación | host confiable del cliente |
| Serialización | bytes crudos, sin envoltorio propio del share |
| Transporte | HTTP `application/octet-stream` |
| Persistencia | `<UUID>.share` en el directorio de la party |
| Reconstrucción | solo demostrada en tests; no hay función productiva en `src/` |

Es un esquema simple de Secret Sharing sobre una cadena de bits, no sharding de frames. Dos shares no bastan para obtener `D` si las máscaras fueron generadas correctamente. No obstante, el sistema completo sigue siendo un prototipo: no hay autenticación, integridad criptográfica del archivo, protección contra sustitución/replay, borrado seguro ni separación de operadores.

Los archivos `.share` no incluyen:

- versión de esquema;
- `party_id`;
- `video_id` dentro del contenido;
- longitud/shape pública esperada;
- hash o MAC;
- dominio aritmético;
- protocolo o programa MP-SPDZ;
- número/orden de elementos.

El único vínculo con el job es el nombre de archivo derivado del UUID. Reenviar el mismo UUID reemplaza atómicamente el contenido anterior.

### 8.2 Compatibilidad con MP-SPDZ

**Clasificación: independiente/prototipo y no compatible de forma directa.**

Las razones concretas son:

1. `Player-Data/Input-P<i>-0` no almacena shares MP-SPDZ. Contiene valores privados en claro, separados por espacios, que pertenecen a la party `i`; el runtime los convierte al tipo secreto del protocolo.
2. Los shares persistentes internos de MP-SPDZ dependen del protocolo y del dominio. Pueden incluir MACs y representaciones específicas; `../MP-SPDZ/doc/io.rst` documenta archivos bajo `Persistence/Transactions-P<player>.data`, no bytes XOR genéricos.
3. MASCOT opera por defecto en un campo primo. El XOR de bytes pertenece a un dominio binario; copiar S0/S1/S2 como enteros de campo no hace que su suma reconstruya el byte original.
4. El payload actual es un contenedor de JPEGs comprimidos. Aunque se transportara como enteros, no equivale a las matrices de píxeles sobre las que se pretende calcular.
5. No existe programa `.mpc` que defina cuántos valores leer, de qué party, en qué orden, cómo combinarlos o qué revelar.

La incompatibilidad no significa que los receptores sean inútiles: cada receptor podría convertirse en un adaptador que transforme su archivo a entradas privadas de una party y participe en un programa diseñado expresamente para recombinarlas. Para conservar XOR, ese programa necesitaría un dominio/operaciones binarias o conversiones explícitas; no es una simple copia de archivo y puede ser costoso. La alternativa más directa es dejar que la interfaz de cliente de MP-SPDZ genere shares compatibles desde la representación numérica original.

## 9. Parties / nodos actuales

### 9.1 Cuántas existen y qué son

Compose define tres servicios con identidad lógica 0, 1 y 2. Los tres ejecutan el mismo objeto `party_receiver.main:app`; `PARTY_ID` cambia el título, recibo, callback y ruta por defecto.

| Party lógica | Servicio Compose | Puerto host → contenedor | Bind mount | Proceso real |
|---|---|---|---|---|
| 0 | `mock-party-0` | `8100 → 8000` | `./data/parties/party-0:/data` | Uvicorn/FastAPI |
| 1 | `mock-party-1` | `8101 → 8000` | `./data/parties/party-1:/data` | Uvicorn/FastAPI |
| 2 | `mock-party-2` | `8102 → 8000` | `./data/parties/party-2:/data` | Uvicorn/FastAPI |

No hay un binario `mascot-party.x`, `replicated-ring-party.x`, `spdz2k-party.x` u otro proceso MPC dentro de estos servicios.

### 9.2 Endpoints de cada mock party

| Método y ruta | Archivo / función | Servicio interno | Respuesta normal | Errores relevantes | Efectos |
|---|---|---|---|---|---|
| `GET /health` | `src/party_receiver/main.py::health` | ninguno | `200`, `status` y `party_id` | — | ninguno |
| `POST /api/v1/shares/{video_id}` | `src/party_receiver/api/shares.py::receive_share` | `ShareService.receive` | `200`, UUID, party y `RECEIVED` | `400` body vacío; `415` content type; `422` UUID; `500` storage; `502` callback | guarda, luego notifica |

El receptor normaliza mayúsculas/parámetros del `Content-Type`, carga el body completo con `await request.body()`, guarda primero y llama después al Coordinator mediante `ShareService._notify_coordinator()`.

Si el callback falla, el archivo permanece y el endpoint devuelve 502. Reenviar permite reintentar la notificación, pero también sobrescribe el archivo. Si el UUID nunca fue registrado, la party guarda el archivo y después recibe 404 del Coordinator, dejando un archivo huérfano.

### 9.3 Aislamiento real

- Cada contenedor solo recibe un bind mount de party; no monta explícitamente las carpetas de las otras dos.
- Todos comparten la red Docker por defecto y el mismo código/imagen base.
- Todos corren en el mismo daemon/host y los tres bind mounts están bajo el mismo árbol del repositorio.
- No hay credenciales, cuentas de sistema, hosts u operadores independientes.
- No existe endpoint de descarga, pero tampoco autenticación para escribir.
- No hay comunicación party-a-party; las únicas salidas de cada receptor van al Coordinator.

Por tanto, hay aislamiento de rutas a nivel de contenedor para el prototipo, no el aislamiento organizacional/de confianza esperado de parties MPC reales.

### 9.4 Mock Party frente a Party MP-SPDZ

Una mock party es aquí un receptor HTTP y un directorio. Una party MP-SPDZ es un proceso de runtime de protocolo que posee un ID, carga el mismo bytecode/schedule que las demás, mantiene material criptográfico/preprocesado y abre conexiones TCP punto a punto para ejecutar instrucciones secretas. Un contenedor no se convierte en party MPC solo por llamarse `party`.

## 10. Docker

### 10.1 Docker actual de Proyecto Delta

El `Dockerfile` de la raíz instala la aplicación Python y tiene como `CMD` por defecto el Coordinator. Compose sobrescribe el comando para los tres receptores.

| Servicio | Receta de imagen | Puerto publicado | Variables principales | Volumen | Responsabilidad |
|---|---|---|---|---|---|
| `coordinator-api` | `Dockerfile` raíz / mismo contexto | 8000 | `PARTY_URLS` | ninguno | Control Plane en memoria |
| `mock-party-0` | misma receta | 8100 | `PARTY_ID=0`, `PARTY_STORAGE_DIR=/data`, URL interna | party-0 | receptor mock |
| `mock-party-1` | misma receta | 8101 | `PARTY_ID=1`, `PARTY_STORAGE_DIR=/data`, URL interna | party-1 | receptor mock |
| `mock-party-2` | misma receta | 8102 | `PARTY_ID=2`, `PARTY_STORAGE_DIR=/data`, URL interna | party-2 | receptor mock |

`docker compose up --build` está documentado y la configuración resuelve correctamente. Está configurado para levantar exactamente esos cuatro servicios, no una VM/runtime MP-SPDZ.

Compose crea la red `proyecto-delta_default`. `depends_on` solo ordena el inicio de las mock parties después del Coordinator; no hay `healthcheck`, por lo que no garantiza que la API ya acepte conexiones. No hay redes separadas, límites de recursos, políticas de reinicio ni secretos de Compose.

### 10.2 Docker histórico de MP-SPDZ

`TareasDeInvestigacion/T06/Dockerfile` es una copia de un Dockerfile multiphase de MP-SPDZ:

- `buildenv`: toolchain y dependencias;
- `machine`: compila una VM, por defecto `mascot-party.x`;
- `program`: compila `tutorial` y escribe inputs de ejemplo P0/P1.

No tiene `CMD` de una party, no define Compose y no está referenciado por el build actual. Solo crea inputs P0/P1 porque el `tutorial.mpc` de ejemplo solicita datos a esas dos parties; una P2 puede participar en el protocolo sin aportar input al tutorial. El historial muestra que el Dockerfile de MP-SPDZ estuvo antes en la raíz y fue movido a `TareasDeInvestigacion/T06/`; T09 reemplazó la raíz con el Dockerfile de la aplicación.

El clon hermano `C:/Proyectos/ProyectoDelta/MP-SPDZ/Dockerfile` tiene cambios locales adicionales (Bookworm, Clang genérico y uso explícito de `python3`), pero tampoco se integra con `proyecto-delta/docker-compose.yml`.

### 10.3 Variables de entorno actuales

| Variable | Consumidor | Valor por defecto/referencia | Función |
|---|---|---|---|
| `COORDINATOR_URL` | CLI | `http://localhost:8000` | API pública de control |
| `PARTY_URLS` | Coordinator | `http://localhost:8100,http://localhost:8101,http://localhost:8102` | destinos públicos devueltos a la CLI |
| `COORDINATOR_INTERNAL_URL` | receivers | `http://coordinator-api:8000` en Compose | callback por DNS Docker |
| `PARTY_ID` | receiver | `0` en código; Compose fija 0/1/2 | identidad lógica |
| `PARTY_STORAGE_DIR` | receiver | ruta `data/parties/party-<id>`; `/data` en Compose | ubicación de `.share` |

`.env.example` documenta valores de referencia, pero Compose asigna por servicio las variables internas. No hay variables de host, puerto, protocolo, programa o certificados MP-SPDZ.

## 11. Networking

### 11.1 Tráfico actual de Proyecto Delta

| Origen → destino | Plano | Transporte/puerto | Contenido |
|---|---|---|---|
| CLI → Coordinator | control | HTTP, host `localhost:8000` por defecto | metadata y consultas |
| CLI → Party 0/1/2 | datos | HTTP, host `localhost:8100/8101/8102` | un share binario por destino |
| Party → Coordinator | control | HTTP por DNS Docker `coordinator-api:8000` | `party_id`, `RECEIVED` |
| Coordinator → Party | ninguno activo | — | solo entrega las URLs al cliente |
| Party → Party | inexistente | — | no hay sockets MPC |
| Proyecto Delta → MP-SPDZ | inexistente | — | no hay llamada, archivo compartido o proceso |

Todo el tráfico de T09 es HTTP sin TLS ni autenticación a nivel de aplicación. Las direcciones `localhost` funcionan porque la CLI está diseñada para correr en el mismo host que publica los puertos. En un cliente remoto, `localhost` apuntaría al equipo equivocado; `PARTY_URLS` y `COORDINATOR_URL` tendrían que ser direcciones enrutable(s), idealmente protegidas.

### 11.2 Networking que MP-SPDZ requeriría

MP-SPDZ utiliza TCP punto a punto entre todos los pares de parties. Según `../MP-SPDZ/doc/networking.rst` y `../MP-SPDZ/doc/runtime-options.rst`:

- una party se identifica con `-p <id>` o el primer argumento posicional;
- el puerto por defecto es `5000 + party_id`;
- `-pn/--portnumbase` cambia la base y `-mp/--my-port` el puerto individual;
- `-h/--hostname` indica el host de Party 0, que por defecto coordina el descubrimiento inicial;
- `-ip/--ip-file-name` permite un archivo común `host[:port]` por party;
- todas las parties deben poder alcanzarse entre sí;
- el uso predeterminado de TLS depende del modelo del protocolo; los protocolos de mayoría honesta lo activan por defecto y usan certificados `P<i>` en `Player-Data`/`SSL_DIR`.

Esto es una red diferente de los endpoints HTTP 8100–8102. Para nodos reales se necesitarían, al menos, un puerto de runtime MPC por party, posibles puertos de cliente externo, reglas de firewall y distribución segura de certificados/programas.

`Scripts/mascot.sh` es útil para pruebas locales, pero no distribuye parties entre contenedores: `Scripts/run-common.sh` lanza todos los procesos en la misma máquina, usa `-h localhost` y elige una base aleatoria 10000–19999 salvo que se defina `PORT`. Para nodos separados se usan los binarios directamente, un archivo de hosts o `Scripts/compile-run.py -H`, que distribuye por SSH.

## 12. Estados del sistema

Solo existen los siguientes estados de dominio, definidos en `src/coordinator/models/video.py`.

### 12.1 Estado del job

| Estado | Se asigna en | Condición | Quién lo cambia |
|---|---|---|---|
| `WAITING_FOR_SHARES` | `VideoService.register_video()` | inmediatamente al crear el UUID | Coordinator |
| `READY_FOR_MPC` | `VideoService.confirm_share()` | las tres parties están `RECEIVED` | Coordinator tras callback |

### 12.2 Estado individual de party

| Estado | Condición |
|---|---|
| `PENDING` | valor inicial al registrar el job |
| `RECEIVED` | callback válido con esa `party_id` |

Transición real:

```text
registro
  └─> WAITING_FOR_SHARES
       ├─ P0: PENDING → RECEIVED
       ├─ P1: PENDING → RECEIVED
       └─ P2: PENDING → RECEIVED
                         └─> READY_FOR_MPC
```

No existen `CREATED`, `PROCESSING`, `COMPLETED`, `FAILED` ni un estado de resultado. `READY_FOR_MPC` no inicia nada. Tampoco distingue “archivo guardado pero callback fallido”, valida igualdad de longitudes o confirma que el input sea utilizable por un protocolo.

## 13. Persistencia

| Información | Ubicación actual | Duración/reinicio |
|---|---|---|
| metadata del job | `_jobs` en RAM del Coordinator | se pierde al reiniciar proceso/contenedor |
| estados | mismo diccionario en RAM | se pierden |
| MP4 original | ruta local del usuario | Proyecto Delta no lo copia |
| payload preprocesado | memoria de la CLI | desaparece al terminar el proceso |
| shares | archivos del host bajo `data/parties/party-*` | persisten por bind mount |
| inputs MP-SPDZ | inexistentes | — |
| bytecode/schedules Delta | inexistentes | — |
| outputs MPC | inexistentes | — |
| logs de aplicación | stdout/stderr de procesos/contenedores | dependen del driver Docker; no se configura volumen |

No se usa JSON persistente, SQLite ni otra base de datos. Tras reiniciar solo quedan los `.share`; el Coordinator ya no reconoce sus UUID. No hay proceso de reconciliación, expiración o limpieza.

En MP-SPDZ, `Player-Data` tiene un significado mucho más amplio: puede contener inputs privados, material preprocesado, claves/certificados y memoria persistida. Los shares escritos por instrucciones MPC se almacenan en formatos específicos bajo `Persistence/`. Ninguna de esas rutas está conectada a `data/parties/`.

## 14. Integración actual con MP-SPDZ

### 14.1 Búsqueda en la aplicación

En `src/`, `Dockerfile` y `docker-compose.yml` no se encontraron:

- imports de MP-SPDZ;
- `subprocess` que ejecute `compile.py` o `*-party.x`;
- archivos `.mpc`;
- mounts hacia `Programs`, `Player-Data` o `Persistence`;
- sockets MP-SPDZ;
- servicio/contenedor de runtime;
- selección de protocolo;
- lectura de outputs.

Las únicas referencias activas declaran precisamente la ausencia de integración: `README.md`, `TareasDeInvestigacion/T09.md` y el docstring de `XorShareGenerator`.

### 14.2 Evidencia externa y estado del clon hermano

El clon `C:/Proyectos/ProyectoDelta/MP-SPDZ` estaba en `master`, commit local `892ac0e2` del 2026-08-17 (`v0.4.3-4-g892ac0e2`), alineado con su `origin/master` local sin haber hecho fetch. No es submódulo ni dependencia del proyecto.

Su working tree no estaba limpio: 216 rutas aparecían modificadas. De las 143 rutas con diff, 142 diferencias desaparecen al ignorar finales de línea; el único cambio sustantivo es `Dockerfile`. Debe preservarse y no tomarse como un checkout upstream limpio sin revisar.

Los seis submódulos declarados por MP-SPDZ estaban sin inicializar: `Programs/Circuits`, `deps/SimpleOT`, `deps/SimplestOT_C`, `deps/libOTe`, `deps/simde` y `deps/sse2neon`.

Además, en ese checkout no existían:

- `Player-Data/`;
- `Programs/Bytecode/`;
- `Programs/Schedules/`;
- binarios `*.x` relevantes;
- programas fuente que mencionen Proyecto Delta.

Esto no contradice la prueba previa reportada por el equipo dentro de Docker; indica que los artefactos no están presentes hoy en el filesystem host inspeccionado.

### 14.3 Clasificación

| Alcance | Clasificación | Justificación |
|---|---|---|
| Aplicación Proyecto Delta → MP-SPDZ | **inexistente** | no hay punto de conexión ejecutable |
| Investigación/PoC separada | **inicial** | Dockerfile histórico y ejecución previa del tutorial reportada |
| Preparación arquitectónica | **parcial** | hay cliente confiable, abstracción de sharing, destinos y receptores que pueden evolucionar |

La ejecución previa de `Scripts/mascot.sh tutorial` demuestra que MP-SPDZ puede funcionar en Docker, no que Proyecto Delta pueda alimentar o iniciar esa ejecución.

## 15. Funcionamiento relevante de MP-SPDZ

Esta sección describe solo lo necesario para diseñar la integración. Se contrastó el clon local con el [README oficial](https://github.com/data61/MP-SPDZ), la documentación oficial de [Input/Output](https://mp-spdz.readthedocs.io/en/latest/io.html) y [Networking](https://mp-spdz.readthedocs.io/en/latest/networking.html).

### 15.1 Programas y compilación

Los programas de alto nivel viven normalmente en:

```text
Programs/Source/<programa>.mpc
```

Ejemplo de compilación en campo primo:

```bash
python3 ./compile.py -F 64 tutorial
```

Aquí `-F 64` solicita capacidad para enteros de 64 bits en el campo primo; no fija que el primo tenga exactamente 64 bits. El compilador selecciona un primo suficientemente grande y muestra sus parámetros.

Para un ring de 64 bits:

```bash
python3 ./compile.py -R 64 tutorial
```

`compile.py` usa el paquete Python `Compiler`, pero los secretos no existen durante esta fase: se genera un programa para runtime. Los artefactos principales son:

- tapes en `Programs/Bytecode/*.bc`;
- un schedule en `Programs/Schedules/*.sch`;
- opcionalmente inputs públicos bajo `Programs/Public-Input/`.

Todas las parties de un job deben ejecutar los mismos artefactos/programa. Compilar no ejecuta el cálculo ni genera un resultado.

### 15.2 Qué proceso representa una party

El ejecutable depende del protocolo:

- `mascot-party.x`: MASCOT, aritmética módulo un primo, seguridad maliciosa con mayoría deshonesta;
- `replicated-ring-party.x`: replicated secret sharing en `2^k`, tres parties;
- `spdz2k-party.x`, `shamir-party.x`, etc.: otros dominios/modelos.

El ID se suministra como primer argumento o con `-p`. Para tres procesos MASCOT distribuidos, la forma general documentada por el runtime es:

```bash
./mascot-party.x -N 3 -p 0 -h <host-party-0> -pn 5000 <programa>
./mascot-party.x -N 3 -p 1 -h <host-party-0> -pn 5000 <programa>
./mascot-party.x -N 3 -p 2 -h <host-party-0> -pn 5000 <programa>
```

Cada línea se ejecutaría en su nodo correspondiente, con los mismos `.bc/.sch`. En este ejemplo se usan los puertos 5000, 5001 y 5002. También se puede usar `-ip <archivo>` para enumerar hosts/puertos.

### 15.3 Scripts oficiales útiles

- `Scripts/mascot.sh <programa>`: ejecuta MASCOT localmente; `PLAYERS` vale 2 por defecto.
- `PLAYERS=3 Scripts/mascot.sh <programa>`: levanta tres procesos MASCOT en una máquina.
- `Scripts/ring.sh <programa>`: fija tres procesos `replicated-ring-party.x` locales.
- `Scripts/compile-run.py`: compila programa y VM si hace falta y ejecuta localmente.
- `Scripts/compile-run.py -H HOSTS ...`: distribución remota mediante SSH sin contraseña; requiere `fabric`, un build estático, certificados/llaves `P<i>`, sus demás dependencias y una política deliberada de despliegue.
- `Scripts/setup-ssl.sh` y `Scripts/setup-clients.sh`: generan material de parties/clientes para escenarios TLS de desarrollo.

Estos scripts son herramientas del framework. Proyecto Delta todavía no decide cuál debe usar ni quién lo invoca. Los `.sh` se ejecutan con Bash/Linux, desde la raíz de MP-SPDZ y con VM, bytecode e inputs ya preparados; no son comandos PowerShell nativos.

### 15.4 Inputs de computing parties

Un programa llama, por ejemplo, `sint.get_input_from(i)` o `sfix.get_input_from(i)`. Sin `-I`, el runtime lee valores en texto, separados por espacios, desde:

```text
Player-Data/Input-P<i>-0
```

El archivo de P0 solo necesita estar disponible para P0, el de P1 para P1, etc. Los valores están en claro para su party propietaria y MP-SPDZ los transforma en valores secretos del protocolo durante la ejecución. Por eso estos archivos no son destino directo de los `.share` actuales.

Los programas binarios usan el prefijo relacionado `Player-Data/Input-Binary-P<party>-<thread>`. Tampoco es un contenedor genérico para los shares XOR de T09: su interpretación depende de las instrucciones y del dominio compilado.

`-IF <prefijo>` permite cambiar el prefijo de input. Esto podría ser útil para aislar jobs por UUID, pero requiere un contrato de nombres y un programa que conozca cantidad y orden de los valores.

### 15.5 Cliente externo

MP-SPDZ incluye `ExternalIO/client.py` y ejemplos como `Programs/Source/bankers_bonus.mpc`. Una sola instancia de `Client`, que requiere `gmpy2`, se conecta coordinadamente por TLS a todas las computing parties; `Client.send_private_inputs()` genera una entrada privada compatible con el dominio/protocolo y, del lado del programa, se usa `sint.receive_from_client()`. No equivale a sustituir cada POST actual por una llamada independiente. El cliente usa un puerto base más el ID de party. El [README de ExternalIO](https://github.com/data61/MP-SPDZ/blob/master/ExternalIO/README.md) lo documenta para protocolos aritméticos.

Esta interfaz encaja con la propiedad de Proyecto Delta “el cliente confiable distribuye directamente y ninguna party recibe el original completo”. Requiere, sin embargo:

- convertir frames a valores del dominio elegido;
- definir puertos de clientes en el programa `.mpc`;
- certificados `C<id>` y `P<i>`;
- que todas las parties estén ejecutando el mismo programa y esperando ese job;
- chunking/control de tamaño para video;
- correlacionar la conexión con `video_id` en una capa de control.

### 15.6 Shares persistentes y sockets

MP-SPDZ también ofrece `read_from_socket`/`write_to_socket` y `read_from_file`/`write_to_file` para shares. El formato de persistencia es específico del tipo/protocolo: puede incluir MAC, usa orden y representación numérica propios y se almacena normalmente en `Persistence/Transactions-P<player>.data`. Inyectar directamente shares autenticados obligaría a generar exactamente ese formato y su material correlacionado; no es una sustitución simple de `XorShareGenerator`.

### 15.7 Outputs

Un valor permanece secreto hasta que el programa decide revelarlo o persistirlo. Opciones relevantes:

- `.reveal()` y `print_ln`: salida pública; por defecto se imprime en stdout de Party 0;
- `.reveal_to(party)`: revelación privada a una computing party;
- `reveal_to_clients`: retorno autorizado a clientes externos;
- `-OF <prefix>`: redirige salida a archivos `<prefix>-P<party>-<thread>`;
- `binary_output`: archivos binarios específicos.

MP-SPDZ no devuelve automáticamente un “resultado de API”. Proyecto Delta debe decidir qué resultado se autoriza, quién lo recibe y cómo se traduce a estado/archivo.

### 15.8 Dockerfile de MP-SPDZ

El Dockerfile externo es multiphase:

1. `buildenv` instala compilador y dependencias;
2. `machine` compila el ejecutable indicado, MASCOT por defecto;
3. `program` compila `tutorial` por defecto y añade inputs P0/P1.

No contiene `CMD` para arrancar una party ni orquesta varios nodos. En consecuencia, una imagen no equivale por sí sola a un cluster MPC; Compose/Kubernetes/systemd u otro supervisor debe crear un proceso con ID/configuración distintos en cada trust domain.

### 15.9 División correcta de responsabilidades

| MP-SPDZ ya resuelve | Proyecto Delta todavía debe resolver |
|---|---|
| tipos secretos y ejecución del bytecode | conversión del video a valores del dominio |
| sharing/input protocolario | elección y uso del mecanismo de entrada |
| preprocessing criptográfico del protocolo | manifest, chunking y asociación con `video_id` |
| comunicación TCP entre computing parties | despliegue, IDs, hosts, puertos y supervisión |
| MACs/autenticación cuando el protocolo los define | autenticación de APIs y gestión de certificados |
| instrucciones para revelar/persistir outputs | política, formato y entrega del resultado autorizado |

Proyecto Delta no debería reimplementar MASCOT, la generación de MACs ni la red MPC. Su adaptador debe alimentar las interfaces soportadas y encargarse del ciclo de negocio alrededor de la VM.

## 16. Mock Parties vs MP-SPDZ real

| Aspecto | Mock actual | MP-SPDZ real |
|---|---|---|
| Proceso | Uvicorn + FastAPI | VM C++ `*-party.x` |
| Identidad | `PARTY_ID` de entorno | ID posicional o `-p`; configuración de participantes |
| Recepción | POST HTTP con bytes opacos | instrucciones de input del programa, archivos, stdin, sockets o ExternalIO |
| Formato actual | `.share` XOR arbitrario | valores privados o shares/formato específico del protocolo |
| Networking | cliente→party y party→Coordinator | conexiones TCP entre todos los pares; opcionalmente conexiones de clientes |
| Comunicación party-party | ninguna | parte esencial del protocolo |
| Cálculo | ninguno | interpreta bytecode MPC bajo el protocolo elegido |
| Secret Sharing | generado fuera con XOR 3-de-3 | generado/autenticado según protocolo y dominio |
| Almacenamiento | un archivo opaco por UUID | inputs, preprocessing, memoria, persistencia y outputs con formatos diferenciados |
| Sincronización | cada POST es independiente | todas las parties deben ejecutar el mismo job/programa de forma coordinada |
| Resultado | recibo `RECEIVED` | valor secreto, apertura pública/privada o persistencia definida por el programa |
| Aislamiento | tres contenedores en un host | idealmente nodos y operadores/trust domains independientes |
| Seguridad de transporte | HTTP sin TLS | TCP; TLS según protocolo/opciones, más certificados para clientes cuando aplique |
| Persistencia de estado | Coordinator en RAM | MP-SPDZ no sustituye la persistencia de negocio del Coordinator |

### Qué se puede conservar

- el principio de preprocesamiento en el cliente confiable;
- el Coordinator como asignador de UUID, catálogo de parties y Control Plane;
- la distribución directa sin concentrar el dato en el Coordinator;
- la abstracción `ShareGenerator` como punto de sustitución, aunque su contrato probablemente deba evolucionar a lotes numéricos/streaming;
- el receptor por nodo como API de control o área de staging, si se decide una integración basada en archivos;
- la escritura atómica de archivos como técnica, no como formato MPC;
- los IDs 0/1/2 y la configuración por entorno como conceptos.

### Qué debe reemplazarse o ampliarse

- `XorShareGenerator` o el significado de sus salidas;
- el contenedor JPEG como input final del cálculo;
- `READY_FOR_MPC` basado únicamente en callbacks;
- la imagen de cada party para incluir runtime, artefactos y supervisor;
- la topología de un solo host para un escenario de seguridad real;
- el endpoint de bytes sin autenticación, manifest, hash o límites;
- el modelo de estados para incluir preparación, ejecución, output y fallo;
- el manejo de resultados.

## 17. Flujo necesario para integrar MP-SPDZ

No hay una conexión única que pueda añadirse al final del flujo actual. Primero deben alinearse representación, protocolo, programa, despliegue y orquestación.

### 17.1 Paso 1: definir el contrato numérico

Antes de Secret Sharing se necesita un manifest público, versionado, con al menos:

- versión de preprocesamiento;
- cantidad y orden de frames/lotes;
- shape y orden de canales;
- tipo entero/fijo, signo, rango y escala;
- dominio requerido por el programa (`mod p`, `2^k` o binario);
- número exacto de elementos;
- versión/nombre del programa MPC;
- protocolo y cantidad de parties;
- estrategia de chunking y límites.

El payload JPEG actual puede servir para transporte/reconstrucción de la prueba T09, pero una VM MPC no decodifica JPEG automáticamente. Para el objetivo de visión, el cliente deberá producir los valores numéricos que el programa realmente opera.

### 17.2 Paso 2: crear un programa MPC mínimo

Se necesita un archivo de Proyecto Delta en `../MP-SPDZ/Programs/Source/`, primero para una operación pequeña y determinista. Debe especificar:

- de dónde vienen los inputs;
- cuántos valores llegan;
- cómo se representan;
- qué cálculo se ejecuta;
- qué resultado puede revelarse y a quién.

Después se compila y versiona su `.sch` y todos sus `.bc` junto con la versión exacta del runtime. No conviene comenzar con video completo: primero debe probarse un escalar o tensor pequeño a través del mismo camino de producción.

### 17.3 Paso 3: elegir el límite de entrada

Hay dos caminos razonables; la decisión debe quedar explícita.

#### Camino A — interfaz cliente de MP-SPDZ

```text
Cliente confiable
  → tensor numérico por lotes
  → ExternalIO Client.send_private_inputs()
  → conexiones directas a P0/P1/P2
  → sint/sfix.receive_from_client()
  → cálculo MPC
```

Ventajas:

- MP-SPDZ produce shares compatibles con el protocolo;
- ninguna computing party recibe el input completo;
- se evita reimplementar MACs y serialización interna;
- conserva el Data Plane directo.

Cambios:

- `XorShareGenerator` deja de generar los archivos actuales;
- `PartyClient` debe hablar el protocolo de cliente MP-SPDZ o encapsular un adaptador oficial;
- las parties deben exponer puertos de cliente y certificados;
- el programa debe escuchar y aceptar conexiones;
- el Coordinator debe devolver endpoints de runtime/client, no solo receptores HTTP.

#### Camino B — conservar receptores como staging

```text
Cliente
  → fragmento compatible por party
  → Party Receiver
  → validación/manifest y conversión a input privado de esa party
  → runtime P0/P1/P2 sincronizado
  → programa combina los tres inputs dentro de MPC
```

Los `.share` XOR actuales no pueden copiarse sin más a `Input-P<i>-0`. Posibles variantes conceptuales son:

- convertir cada byte XOR en bits e implementar su combinación en un programa/dominio binario;
- cambiar el cliente a fragmentos aditivos módulo `p` y hacer que un programa MASCOT sume los tres inputs privados;
- usar otro esquema alineado con el protocolo elegido.

En todos los casos, cada fragmento se ingresa como **valor privado conocido por su party**; MP-SPDZ vuelve a compartirlo/autenticarlo durante el input. La inyección directa de shares internos autenticados es dependiente del protocolo y no es recomendable como primer adaptador.

Este camino permite reutilizar FastAPI y `LocalStorage`, pero agrega doble sharing, conversión, staging y coordinación. Debe justificarse frente a ExternalIO.

### 17.4 Paso 4: desplegar una party real por nodo

Cada nodo necesita:

- la misma revisión, configuración y protocolo de MP-SPDZ, con un binario compatible con la arquitectura de cada nodo;
- el mismo schedule/bytecode;
- solo sus inputs/secretos/clave privada;
- ID distinto;
- hostname/puerto alcanzable por las otras parties;
- directorio por job;
- un supervisor que arranque, observe y termine el proceso;
- puertos separados para HTTP/control, runtime MPC y ExternalIO si se usa.

No se debe hornear input de producción ni todas las claves privadas en una imagen compartida. El Dockerfile experimental con `cryptoplayers=3` genera material útil para pruebas, pero todas las instancias derivadas de esa imagen podrían contener todas las claves.

También debe fijarse una arquitectura/target portable. El Dockerfile permite `-march=native`; un binario compilado en x86-64 no debe asumirse válido en nodos ARM64/Raspberry Pi.

### 17.5 Paso 5: correlacionar y sincronizar el job

MP-SPDZ no conoce `video_id`. Una capa de Proyecto Delta debe mapear:

```text
video_id
  → manifest/versiones
  → programa + bytecode
  → protocolo y dominio
  → hosts/puertos/party IDs
  → prefijo/ruta de input por party
  → ejecución/PID/contenedor
  → output autorizado
```

Un flujo posible, todavía no implementado, es:

1. Coordinator registra job y devuelve destinos/capacidades.
2. Cliente entrega inputs y manifest directamente.
3. Cada nodo valida y reporta “input preparado”, no solo “bytes recibidos”.
4. Coordinator o un orquestador emite una orden idempotente con la misma versión/job a los tres nodos.
5. Cada supervisor inicia exactamente una party del mismo programa.
6. Las parties establecen la red MP-SPDZ y ejecutan.
7. El componente autorizado captura el resultado o lo retorna al cliente.
8. Los nodos notifican éxito/fallo y limpian material temporal según política.

El Coordinator puede conservarse fuera del Data Plane: no necesita recibir inputs ni outputs sensibles para coordinar IDs, barreras y estados.

### 17.6 Paso 6: manejar el resultado

Debe decidirse explícitamente:

- resultado público, privado a una party o privado al cliente;
- uso de `.reveal()`, `.reveal_to()` o `reveal_to_clients()`;
- formato, autenticidad y asociación con `video_id`;
- quién hace postprocesamiento;
- cómo se reportan código de salida, timeout, logs y errores.

Capturar stdout de Party 0 es suficiente para una PoC mínima, pero no constituye por sí solo un contrato robusto de resultados.

## 18. Compatibilidad del Secret Sharing actual con MP-SPDZ

**Conclusión específica: los shares actuales no son utilizables directamente por MP-SPDZ.**

No deben copiarse ni renombrarse **sin conversión** como `Input-P0-0`, `Input-P1-0` y `Input-P2-0`: esos archivos representan inputs privados en claro, no shares preconstruidos. En un adaptador de staging sí podrían decodificarse los `.share` y serializar sus bytes/bits como valores privados en los `Input-P<i>-0`, siempre que un programa hecho para ello los recombine; en ese punto son inputs conocidos por cada party, no shares internos de MP-SPDZ. Tampoco deben escribirse como persistencia de shares, porque faltan dominio, representación, MACs y relación con el material de autenticación del protocolo.

El cambio conceptual preferido para el primer end-to-end es:

```text
MP4 local
  → representación numérica definida por el programa
  → mecanismo oficial de input privado de MP-SPDZ
  → shares internos compatibles
  → cálculo MPC
```

Si el equipo decide conservar sharing previo en el cliente, debe diseñarlo conjuntamente con el programa y el dominio. Una opción de puente sería que cada party introduzca su fragmento como input privado y que el programa los combine sin revelarlos; eso sigue siendo una adaptación, no compatibilidad directa.

## 19. Protocolo MP-SPDZ usado o previsto

No existe una decisión activa de protocolo en código o Compose.

Evidencia encontrada:

- `TareasDeInvestigacion/T03.md` compara MP-SPDZ con MPyC y favorece las capacidades de MP-SPDZ, pero elegir framework no elige protocolo.
- `TareasDeInvestigacion/T04.md` propone tres parties y declara que el protocolo/modelo de amenaza está pendiente.
- `TareasDeInvestigacion/T06/Dockerfile` usa `mascot-party.x` como `machine` por defecto y compila `tutorial` para campo primo.
- El antecedente aportado por el equipo es una ejecución exitosa de `Scripts/mascot.sh tutorial` con dos parties.
- `Scripts/mascot.sh` usa dos players por defecto, aunque MASCOT admite `-N 3`/`PLAYERS=3`.
- MP-SPDZ también aporta `replicated-ring-party.x` y `Scripts/ring.sh` para exactamente tres parties, pero Proyecto Delta no lo ha seleccionado.

Por tanto:

| Pregunta | Respuesta actual |
|---|---|
| Framework foco | MP-SPDZ |
| Protocolo probado aisladamente | MASCOT, tutorial, dos parties según contexto del equipo |
| Protocolo conectado a T09 | ninguno |
| Protocolo definitivo de tres parties | no decidido |
| Dominio definitivo | no decidido |
| Modelo de amenaza definitivo | no decidido |

No debe deducirse que MASCOT es la decisión final solo porque sea el valor por defecto del Dockerfile experimental.

## 20. Ejecución actual

Todos los comandos de Proyecto Delta se ejecutan desde la raíz `proyecto-delta/`.

### 20.1 Preparar la CLI en PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

En Linux/macOS, el README usa:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 20.2 Levantar entorno T09

```bash
docker compose up --build
```

Servicios esperados:

- Coordinator: `http://localhost:8000`;
- Party 0: `http://localhost:8100`;
- Party 1: `http://localhost:8101`;
- Party 2: `http://localhost:8102`.

### 20.3 Ejecutar cliente

```bash
python -m client upload ./video.mp4
```

Equivalente tras instalar el paquete:

```bash
delta upload ./video.mp4
```

### 20.4 Consultar estado

```bash
curl http://localhost:8000/api/v1/videos/<video_id>
```

### 20.5 Ejecutar pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -e .
python -m pytest
```

En la sesión de investigación no estaban instaladas las dependencias de prueba y el comando terminó antes de recolectar tests con `No module named pytest`.

### 20.6 Ejecutar MPC desde Proyecto Delta

**Actualmente no existe un flujo ejecutable para esta etapa.**

### 20.7 Ejecutar MP-SPDZ de forma aislada

Estos comandos pertenecen al repositorio externo y no reciben datos de Proyecto Delta. El README de MP-SPDZ documenta:

```bash
cd ../MP-SPDZ
docker build --tag mpspdz:mascot-party --build-arg machine=mascot-party.x .
docker run --rm -it mpspdz:mascot-party python3 ./Scripts/compile-run.py mascot tutorial
```

Para una prueba local de tres procesos ya preparados:

```bash
PLAYERS=3 Scripts/mascot.sh tutorial
```

`PLAYERS=3 Scripts/mascot.sh tutorial` es un comando Bash/Linux y se ejecuta desde la raíz de MP-SPDZ. El clon host inspeccionado no tenía binarios, bytecode, schedules ni `Player-Data`; además, algunos scripts Python, incluidos `compile.py` y `Scripts/compile-run.py`, estaban materializados con finales de línea CRLF. Para ejecutarlos directamente en Linux habría que normalizar esos archivos o partir de un checkout limpio; invocar Python explícitamente evita el problema del *shebang*. Esos comandos requerirían construir/compilar o usar la imagen correspondiente y no se ejecutaron en esta investigación.

## 21. Tests actuales

Hay 84 funciones `test_*` distribuidas en ocho archivos. La parametrización puede producir más casos recolectados; no se obtuvo el conteo de pytest porque la dependencia no estaba instalada.

| Archivo | Funciones | Cobertura principal |
|---|---:|---|
| `tests/api/test_coordinator_api.py` | 16 | endpoints, validaciones, UUID, concurrencia, estados, OpenAPI |
| `tests/integration/test_cli.py` | 7 | orquestación CLI con dependencias sustituidas, errores y códigos de salida |
| `tests/integration/test_party_receiver.py` | 18 | API de receptor, almacenamiento, 5 MiB, identidad, callbacks y fallos |
| `tests/unit/test_client_networking.py` | 11 | contratos HTTP y traducción de errores |
| `tests/unit/test_local_storage.py` | 6 | escritura atómica, overwrite, separación y traversal |
| `tests/unit/test_share_generator.py` | 6 | tres shares, reconstrucción XOR, aleatoriedad, chunks y errores |
| `tests/unit/test_video_preprocessor.py` | 3 | MP4 real pequeño, metadata/frames y archivos inválidos |
| `tests/unit/test_video_service.py` | 17 | registro, transición, idempotencia, concurrencia y configuración |

### 21.1 Qué está bien cubierto

- lógica del Coordinator y concurrencia en memoria;
- esquema XOR y reconstrucción matemática;
- validación básica de video;
- contrato del cliente y receptor;
- escritura atómica y protección de ruta;
- fallos de HTTP simulados.

### 21.2 Qué falta

- E2E real con `docker compose up` y un MP4;
- red real entre procesos/contenedores;
- restart y conciliación de Coordinator/shares;
- autenticación, TLS, integridad y replay;
- límites de tamaño, cuotas y presión de memoria para video real;
- programa, compilación, runtime, inputs y outputs MP-SPDZ;
- tres parties MPC en hosts/contenedores separados;
- sincronización, timeouts, fallos parciales y reintentos MPC;
- compatibilidad entre versión de bytecode y runtime;
- Computer Vision/anonimización, que todavía no existe.

Los tests llamados `integration` integran componentes Python dentro del proceso de pytest o mediante transports mock; no validan la integración con MP-SPDZ.

## 22. Comparación entre arquitectura planeada e implementación real

| Área | Planeado | Implementado | Diferencia |
|---|---|---|---|
| Cliente confiable | prepara y protege el dato localmente | CLI local funcional | alineado para T09 |
| Coordinator | IDs, metadata, destinos y coordinación | registro/estado de recepción en RAM | faltan persistencia y ciclo MPC |
| Video original | nunca cruza un servidor central | solo se abre localmente | alineado en el código actual |
| Preprocesamiento | frames y representación útil para MPC | frames recodificados como JPEG | formato provisional con pérdida |
| Representación numérica | matrices/tensores y dominio definido | contenedor binario de JPEGs | no hay contrato MPC |
| Secret Sharing | compatible con protocolo MPC | XOR 3-de-3 sobre bytes | independiente/no directo |
| Party 0 | nodo MP-SPDZ | receptor FastAPI | mock |
| Party 1 | nodo MP-SPDZ | receptor FastAPI | mock |
| Party 2 | nodo MP-SPDZ | receptor FastAPI | mock |
| Comunicación directa | cliente → cada party | sí, HTTP a cada receptor | contrato de transporte, no input MPC |
| Coordinator fuera del Data Plane | no recibe shares | cumplido | sigue viendo filename/estado |
| Aislamiento | nodos/trust domains independientes | contenedores/directorios en un host | insuficiente para modelo real |
| Almacenamiento | share propio por party | `.share` separado por bind mount | no es formato MP-SPDZ |
| Docker | parties MPC desplegadas | Coordinator + tres mocks | runtime ausente |
| MP-SPDZ | framework de ejecución central | checkout/PoC separado | sin conexión |
| Inputs MPC | valores/shares en dominio elegido | ninguno | pendiente |
| Ejecución MPC | parties ejecutan mismo programa | ninguna | pendiente |
| Comunicación party-party | TCP del protocolo | ninguna | pendiente |
| Resultado en shares | resultado MPC permanece secreto | ninguno | pendiente |
| Reconstrucción autorizada | revelar solo resultado anonimizado | ninguna | pendiente |
| Estados | recepción, ejecución, éxito/fallo | dos estados de job y dos de party | solo barrera de recepción |
| Computer Vision | cálculo/anonimización dentro de MPC | no existe | fuera del alcance actual |

La principal brecha no es Docker por sí solo: es que T09 termina exactamente donde debería comenzar el runtime MPC.

## 23. Riesgos e inconsistencias reales

### 23.1 Integración y semántica

- `READY_FOR_MPC` puede alcanzarse sin inputs válidos: las confirmaciones no están autenticadas y pueden llamarse directamente.
- No se verifica que los tres archivos tengan misma longitud, versión, manifest o job registrado antes de persistir.
- El formato XOR no coincide con ningún input directo configurado de MP-SPDZ.
- El preprocesamiento produce JPEG comprimido, no los valores que un cálculo de visión espera.
- No hay protocolo, dominio, programa, versión de bytecode ni modelo de amenaza elegidos.
- No existe dueño del arranque sincronizado ni contrato de resultado.

### 23.2 Disponibilidad y consistencia

- El Coordinator pierde todo al reiniciar, mientras los shares persisten y quedan huérfanos.
- Guardar precede al callback; un 502 significa “guardado pero no confirmado”, estado que el modelo no representa.
- Un fallo durante los envíos secuenciales deja recepción parcial sin reintento automático.
- Reenviar reemplaza el share existente sin hash, versión o control de concurrencia.
- `depends_on` no espera salud del Coordinator.

### 23.3 Seguridad y aislamiento

- HTTP no tiene TLS, autenticación ni autorización.
- Un actor puede subir bytes a cualquier UUID válido o inventado y puede falsificar confirmaciones.
- Los tres shares residen bajo un mismo host/operador; comprometerlo evita el supuesto de no colusión.
- Cada receptor observa longitud, y el Coordinator observa filename.
- No hay límite de body, cuota de disco, rate limit ni política de borrado.
- La imagen experimental de MP-SPDZ puede generar/copiar todas las claves en la misma capa; eso no modela parties independientes.
- MASCOT usa conexiones inter-party no cifradas por defecto; activar `-e` requiere certificados y una futura elección debe decidir explícitamente ese material y el modelo de red.

### 23.4 Operación y portabilidad

- Las URLs `localhost` solo sirven para una CLI en el host local.
- `Scripts/mascot.sh` lanza todas las parties localmente y no sirve como launcher de un proceso por contenedor remoto.
- El checkout externo está sucio, con submódulos sin inicializar y sin binarios/artefactos; no es una base reproducible todavía.
- `-march=native` puede producir binarios no portables entre x86-64 y ARM64.
- MP-SPDZ advierte que bytecode y runtime deben corresponder a la misma versión.

### 23.5 Escala

- Payload y tres shares completos se materializan en RAM.
- Cada receiver carga el body completo.
- Cada frame se comprime con pérdida; esto puede invalidar supuestos numéricos posteriores.
- El volumen de video puede hacer inviable introducir un elemento por píxel sin chunking y una prueba de rendimiento, aunque esa validación pertenece a una etapa posterior.

## 24. Trabajo pendiente relacionado con MPC

### 24.1 Prioridad inmediata

1. Definir un cálculo MPC mínimo y su contrato numérico completo.
2. Decidir protocolo, dominio y modelo de amenaza para **tres** parties; no asumir MASCOT por defecto.
3. Elegir ExternalIO o staging por receiver como límite de entrada.
4. Crear un programa `.mpc` mínimo y ejecutarlo con tres parties sobre un dato diminuto aportado por la CLI.
5. Diseñar un manifest por `video_id` y estados de input preparado/ejecución/resultado/fallo.
6. Crear una topología reproducible con un proceso MP-SPDZ por party y puertos explícitos.
7. Probar el camino completo antes de escalar a frames o Computer Vision.

El hito inmediato debería demostrar:

```text
CLI Proyecto Delta
  → tres runtimes MP-SPDZ
  → programa Delta mínimo
  → resultado autorizado
  → estado final en Coordinator
```

### 24.2 Integración MP-SPDZ

- versionar fuente, bytecode, schedule y runtime;
- transformar el preprocesamiento a valores del dominio;
- implementar lotes/streaming y backpressure;
- separar puertos HTTP, inter-party y cliente MPC;
- distribuir certificados y una sola clave privada por party;
- implementar supervisor idempotente por job;
- aislar rutas/prefijos con UUID (`-IF` si se usan archivos);
- capturar códigos de salida, timeout y logs;
- retornar resultado mediante un mecanismo explícitamente autorizado;
- agregar tests E2E con fallo de una party y reanudación/limpieza.

### 24.3 Seguridad / producción posterior

- desplegar parties en trust domains/hosts distintos;
- mTLS/autenticación/autorización en APIs de control y datos;
- almacenamiento cifrado y gestión de secretos/certificados;
- base persistente y conciliación de jobs;
- protección contra replay, sustitución y duplicados;
- cuotas, límites, observabilidad y auditoría;
- rotación de certificados y hardening;
- revisión formal del modelo de amenaza y de la revelación de outputs;
- evaluación de portabilidad/rendimiento en hardware objetivo.

Estas tareas son importantes, pero no deben ocultar el bloqueo inmediato: todavía no hay un solo valor de Proyecto Delta entrando y saliendo de un programa MP-SPDZ.

## 25. Archivos clave

| Archivo | Responsabilidad | Importancia para continuar |
|---|---|---|
| `README.md` | comandos y alcance T09 | entrada rápida al proyecto |
| `docker-compose.yml` | Coordinator y tres mock parties | topología actual a evolucionar |
| `Dockerfile` | imagen Python de aplicación | no contiene MP-SPDZ |
| `.env.example` | URLs e identidad/almacenamiento | configuración de networking actual |
| `pyproject.toml` | paquete y comando `delta` | ejecución/instalación CLI |
| `src/client/cli.py` | orquestación del cliente | punto principal del flujo |
| `src/client/preprocessing/video_preprocessor.py` | formato DELTA-T09-JPEG | debe alinearse al contrato MPC |
| `src/client/sharing/share_generator.py` | XOR provisional | principal pieza a sustituir/adaptar |
| `src/client/networking/coordinator_client.py` | Control Plane desde CLI | contrato Coordinator |
| `src/client/networking/party_client.py` | entrega directa HTTP | posible punto de ExternalIO/adaptador |
| `src/coordinator/api/videos.py` | endpoints de jobs | ampliar ciclo MPC |
| `src/coordinator/models/video.py` | estados/modelos actuales | evidencia exacta del lifecycle |
| `src/coordinator/services/video_service.py` | estado en memoria/transiciones | reemplazar o persistir al crecer |
| `src/party_receiver/main.py` | factory reutilizada por tres mocks | punto para sidecar/supervisor si se conserva |
| `src/party_receiver/api/shares.py` | endpoint de bytes | contrato de staging actual |
| `src/party_receiver/services/share_service.py` | guarda + callback | coordinación de recepción |
| `src/party_receiver/storage/local_storage.py` | escritura atómica | técnica reutilizable |
| `tests/` | especificación ejecutable de T09 | preservar al cambiar integración |
| `TareasDeInvestigacion/T04.md` | arquitectura objetivo | contraste diseño/realidad |
| `TareasDeInvestigacion/T09.md` | alcance y límites T09 | documentación más alineada |
| `TareasDeInvestigacion/T06/Dockerfile` | experimento MP-SPDZ histórico | referencia, no build actual |
| `../MP-SPDZ/README.md` | ejecución/protocolos upstream | referencia operacional primaria |
| `../MP-SPDZ/Dockerfile` | build multiphase de VM/programa | base experimental, actualmente modificada |
| `../MP-SPDZ/compile.py` | compilador de `.mpc` | genera `.bc/.sch` |
| `../MP-SPDZ/Scripts/run-common.sh` | launcher local usado por scripts | explica players/puertos/logs |
| `../MP-SPDZ/Scripts/mascot.sh` | launcher local MASCOT | PoC, no multi-host |
| `../MP-SPDZ/doc/io.rst` | contratos de input/output | clave para el adaptador |
| `../MP-SPDZ/doc/networking.rst` | topología TCP/certificados | clave para nodos reales |
| `../MP-SPDZ/ExternalIO/client.py` | cliente privado multiparty | ruta candidata desde la CLI |
| `../MP-SPDZ/ExternalIO/README.md` | ejemplo de ExternalIO | guía de integración oficial |

## 26. Mapa rápido para futuras sesiones

### Para cambiar el Coordinator

Revisar, en orden:

```text
src/coordinator/models/video.py
src/coordinator/services/video_service.py
src/coordinator/api/videos.py
src/coordinator/main.py
tests/unit/test_video_service.py
tests/api/test_coordinator_api.py
```

### Para cambiar recepción de shares

```text
src/party_receiver/api/shares.py
src/party_receiver/services/share_service.py
src/party_receiver/storage/local_storage.py
src/party_receiver/main.py
tests/integration/test_party_receiver.py
```

### Para cambiar Secret Sharing o input MPC

```text
src/client/sharing/share_generator.py
src/client/sharing/__init__.py
src/client/cli.py
src/client/networking/party_client.py
../MP-SPDZ/doc/io.rst
../MP-SPDZ/ExternalIO/
```

No asumir que `Input-P<i>-0` acepta los `.share` existentes.

### Para trabajar con parties

Hoy las define `docker-compose.yml` y todas usan `src/party_receiver/main.py`. Para parties reales, revisar además `../MP-SPDZ/doc/networking.rst`, `../MP-SPDZ/doc/runtime-options.rst`, el binario del protocolo y el programa/schedule compartido.

### Para integrar MP-SPDZ

Orden recomendado de lectura/trabajo:

```text
1. este documento, secciones 14–19
2. TareasDeInvestigacion/T04.md y T09.md
3. ../MP-SPDZ/README.md (Running Computation)
4. ../MP-SPDZ/doc/io.rst
5. ../MP-SPDZ/ExternalIO/README.md
6. ../MP-SPDZ/doc/networking.rst
7. definir ../MP-SPDZ/Programs/Source/<programa-delta>.mpc
```

### Para cambiar Docker

- aplicación T09: `Dockerfile` y `docker-compose.yml` de la raíz;
- experimento histórico: `TareasDeInvestigacion/T06/Dockerfile`;
- upstream/clon externo: `../MP-SPDZ/Dockerfile`.

No confundir estas tres recetas.

### Para ejecutar lo disponible

```bash
docker compose up --build
python -m client upload ./video.mp4
python -m pytest
```

El tercer comando requiere haber instalado `requirements-dev.txt`. No hay todavía un comando de Proyecto Delta que continúe desde `READY_FOR_MPC` hacia una ejecución MPC real.

## 27. Actualización posterior al pull: Tarea 07

> **Pull revisado:** avance de `db91c13` a `3cf1aee` (`Tarea 07`), 21 de septiembre de 2026. Se inspeccionó únicamente el delta introducido por este pull.

El pull agrega solo `TareasDeInvestigacion/T07.md` (70 líneas). No modifica código Python, tests, Dockerfile, Compose, variables de entorno ni la integración de Proyecto Delta. Por tanto, no cambia las conclusiones funcionales de las secciones anteriores: las tres parties actuales siguen siendo receptores HTTP mock y no existe todavía un flujo Proyecto Delta → MP-SPDZ.

### Información nueva relevante

T07 documenta un procedimiento manual para experimentar con MP-SPDZ en varias máquinas:

- entrada interactiva a una imagen mediante `docker run --rm -it --network host ... bash`;
- generación de credenciales con `Scripts/setup-ssl.sh <n> <ssl_dir>` y necesidad de mantener `ssl_dir` consistente con `CONFIG`/`CONFIG.mine`;
- preparación de SSH y transferencia manual de archivos con `ssh-copy-id` y `scp`;
- ejecución de `mascot-party.x` con dos parties, ambas apuntando a la IP de Party 0;
- ejecución de `replicated-ring-party.x` con tres parties y los IDs 0, 1 y 2.

Esto aporta evidencia documental de que el equipo ya está explorando:

- comunicación inter-party entre hosts reales;
- identidad explícita de cada proceso mediante su ID;
- distribución de credenciales y artefactos por nodo;
- MASCOT como prueba de dos parties y replicated secret sharing como prueba de tres parties.

### Cómo afecta al diagnóstico

T07 reduce la incertidumbre sobre la intención operativa multinodo, pero sigue siendo un **runbook de investigación**, no una integración. Sus comandos ejecutan el programa upstream `tutorial`; no reciben los `.share` de T09, no conocen `video_id`, no son iniciados por el Coordinator y no devuelven un resultado a Proyecto Delta.

La indicación de usar `--network host` es una solución posible para la prueba descrita, no un requisito general de Docker ni una topología de producción. Una red bridge correctamente configurada también puede permitir comunicación entre contenedores; la elección debe considerar plataforma, exposición de puertos, aislamiento y firewall.

El ejemplo MASCOT continúa siendo de **dos** parties y no valida todavía la topología objetivo de tres. El ejemplo `replicated-ring-party.x` sí coincide en cantidad de parties, pero no constituye por sí mismo una selección definitiva de protocolo: aún deben fijarse dominio, modelo de amenaza, inputs, programa Delta y política de salida.

En consecuencia, el siguiente hito no cambia: convertir este procedimiento manual en una prueba reproducible donde un dato mínimo generado por la CLI entre a tres runtimes MP-SPDZ, ejecute un programa de Proyecto Delta y produzca un resultado asociado al mismo `video_id`.
