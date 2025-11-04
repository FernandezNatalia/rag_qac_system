# RAG Chatbot API

Asistente conversacional con memoria y recuperación aumentada (RAG), construido con **FastAPI**, **LangGraph**, **LLM**, **vectorstore** y persistencia en **SQLite**.  

Esta API expone un chatbot que:

- Responde preguntas usando un modelo de lenguaje (LLM) + documentos indexados  
- Mantiene memoria de conversación persistente por `session_id`  
- Detecta si el turno es follow-up (ej: “Me podrías decir más?”) y reescribe la pregunta  
- Detecta smalltalk y responde sin buscar en la base de conocimiento  
- Resume el historial automáticamente cuando crece demasiado  
- Devuelve citas o fuentes del contexto recuperado  
- Se ejecuta localmente o con Docker

---

## Cómo funciona el chatbot?

La lógica principal se basa en un **grafo de estados** (LangGraph) que orquesta cada paso de la conversación.

### Flujo de procesamiento

Usuario → load_history → detect_followup → (smalltalk | rewrite_query)
→ rag_pipeline → save_history → summarize_history → Respuesta

### Explicación resumida de los nodos

| Nodo | Función |
|------|---------|
| `load_history` | Carga historial reciente y resumen desde SQLite |
| `detect_followup` | Decide si la pregunta depende del historial o es smalltalk |
| `smalltalk` | Responde sin RAG si es saludo, conversación ligera, etc. |
| `rewrite_query` | Reescribe la pregunta si es follow-up (para dar contexto al RAG) |
| `rag_pipeline` | Recupera documentos relevantes + construye prompt + responde |
| `save_history` | Guarda pregunta + respuesta + metadatos para trazabilidad |
| `summarize_history` | Resume conversaciones largas para mantener límite de tokens |

### Diagrama del grafo

```mermaid
flowchart TD
    A[load_history] --> B[detect_followup]
    B -->|smalltalk| C[smalltalk]
    B -->|requiere RAG| D[rewrite_query]
    C --> E[save_history]
    D --> F[rag_pipeline]
    F --> E[save_history]
    E --> G[summarize_history]
    G --> H[END]
```

### Uso de la API
#### POST /chat
Envía una pregunta con un session_id y recibe respuesta con fuentes y metadatos.

Request
```
POST /chat
Content-Type: application/json
{
  "session_id": "user-123",
  "question": "¿Qué es el modelo de RLS y cuál es su ecuación general?"
}
```

Response
```
{
  "question_rewritten": "¿Qué es el modelo de regresión lineal simple y cuál es su ecuación general?",
  "answer": "El modelo de regresión lineal simple es un método estadístico que se utiliza para predecir una variable de respuesta cuantitativa ...",
  "followup": false,
  "skip_rag": false,
  "sources": [
      {
        "id": "page_80_chunk_1",
        "page": 80,
        "chapter": "3 Linear Regression",
        "section": "3.1 Simple Linear Regression",
        "subsection": "3.1.1 Estimating the Coefficients"
      },
      {
        "id": "page_79_chunk_1",
        "page": 79,
        "chapter": "3 Linear Regression",
        "section": "3.1 Simple Linear Regression"
      }
    ],
  "history_used": false
}
```


### Persistencia de historial
La app usa una base SQLite que una vez creada se ubicará automáticamente en:

```
db/chat_history.sqlite
```

Se almacenan:
| Tabla              | Contenido                                        |
| ------------------ | ------------------------------------------------ |
| `chat_history`     | Mensajes usuario/assistant con orden y timestamp |
| `session_summary`  | Resumen comprimido del historial                 |
| `rag_answers_meta` | Fuentes y contexto usado por el pipeline RAG     |
| `rag_evals`        | Evaluaciones automáticas tipo RAGAS              |

### Arquitectura del Sistema

El siguiente diagrama muestra la arquitectura completa del proyecto:
<img width="600" height="600" alt="arq_img" src="https://github.com/user-attachments/assets/bec12348-cb80-48cf-a19a-a7e9ccb56b88" />


### Requisitos previos

- Python 3.10 o superior y `pip`
- Cuenta en OpenAI con una API Key válida
- (Opcional) Docker 24+ y Docker Compose si preferís la ejecución containerizada

### Puesta en marcha desde cero

1. **Cloná el repositorio y creá un entorno virtual (opcional pero recomendado)**
   ```bash
   git clone <repo>
   cd rag_qac_system
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

2. **Instalá las dependencias**
   ```bash
   pip install -r api/requirements.txt
   ```

3. **Configurá tus credenciales**
   - Copiá el archivo `.env` en la raíz del proyecto (o crealo) con tu clave de OpenAI:
     ```bash
     echo "OPENAI_API_KEY=tu_api_key" > .env
     ```
   - Los servicios cargan automáticamente este archivo al iniciar (ver `load_dotenv()` en `api/app/server.py`). Si la variable falta, la aplicación arrojará un error.

4. **Prepará la base de conocimiento** *(solo es necesario la primera vez o cuando cambies la fuente)*
   - Asegurate de que el PDF a indexar exista en `api/data/raw/`. Por defecto el proyecto incluye `PDF-GenAI-Challenge.pdf`.
   - Ejecutá los scripts en este orden:
     ```bash
     python api/scripts/preprocess.py \
       --input_pdf api/data/raw/PDF-GenAI-Challenge.pdf \
       --output_json api/data/processed/clean_chunks.json

     python api/scripts/build_vectorstore.py \
       --input api/data/processed/clean_chunks.json \
       --output api/vector_store
     ```
   - `preprocess.py` limpia el PDF y genera chunks enriquecidos con metadatos.
   - `build_vectorstore.py` crea el índice FAISS que usará el flujo RAG. Si cambiás el PDF, volvé a ejecutar ambos comandos.

5. **Iniciá la API**
   - **Modo local**
     ```bash
     uvicorn api.app.server:app --reload --host 0.0.0.0 --port 8000
     ```
   - **Modo Docker Compose**
     ```bash
     docker compose up --build
     ```

   La API quedará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`. El endpoint `/health` devuelve un estado simple para verificar que el servicio esté listo.

