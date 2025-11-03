REWRITE_QUERY_PROMPT = """
Reescribe la siguiente pregunta del usuario para que sea completamente autónoma,
solo si depende del contexto previo.

REGLAS:

1. Si la pregunta puede entenderse por sí sola, devuélvela SIN cambios.
2. Si el usuario responde de forma ambigua (ej: "sí", "dale", "continuá",
   "perfecto", "seguí", "contame más"), entonces debes construir una pregunta
   explícita usando el historial para que sea autocontenida.
3. Si el asistente hizo una pregunta previamente y la respuesta del usuario es
   simplemente afirmativa, convierte la respuesta en una pregunta explícita.
4. NO resumas, NO inventes información nueva: solo reescribe.
5. Responde SOLO con la versión reescrita, sin explicaciones.

HISTORIAL (si existe):
{history_text}

PREGUNTA ORIGINAL DEL USUARIO:
{question}

PREGUNTA REESCRITA:
"""