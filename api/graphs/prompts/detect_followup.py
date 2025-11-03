DETECT_FOLLOWUP_PROMPT = """
Clasifica el nuevo mensaje del usuario según estas reglas:

1. Si es un saludo, despedida, agradecimiento o charla social corta
   (ej: "hola", "gracias", "buenas", "cómo estás", "adiós"),
   responde SOLO: smalltalk

2. Si es una pregunta que puede entenderse sin el historial,
   responde SOLO: standalone

3. Si es una continuación que depende del contexto anterior
   (ej: "¿y después qué pasó?", "explícame mejor", "y un ejemplo?",
    o respuestas breves a una pregunta hecha por el asistente, como
    "sí", "dale", "ok", "continuá", "mostrame", "perfecto"),
   responde SOLO: followup

NO EXPLIQUES. Responde con solo una palabra.

Historial:
{history}

Nuevo mensaje:
{question}

Respuesta:
"""