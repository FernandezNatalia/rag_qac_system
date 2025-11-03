REWRITE_QUERY_PROMPT = """
Reescribe la siguiente pregunta del usuario para que sea completamente autónoma,
solo si depende del contexto previo.

REGLAS:

1. Si el usuario responde de forma ambigua (ej: "sí", "dale", "continuá",
   "perfecto", "seguí", "contame más"), entonces debes construir una pregunta
   explícita usando el historial para que sea autocontenida.
2. Si el asistente hizo una pregunta previamente y la respuesta del usuario es
   simplemente afirmativa, convierte la respuesta en una pregunta explícita.
3. NO resumas, NO inventes información nueva: solo reescribe.
4. Responde SOLO con la versión reescrita, sin explicaciones.

HISTORIAL (si existe):
{history_text}

PREGUNTA ORIGINAL DEL USUARIO:
{question}

PREGUNTA REESCRITA:
"""