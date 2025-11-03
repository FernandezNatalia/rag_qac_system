SUMMARIZE_HISTORY_PROMPT = """
Resume la conversación siguiente en un máximo de 10 líneas,
manteniendo el contexto técnico y temático del diálogo.

Instrucciones:
- No inventes contenido.
- Mantén los nombres de conceptos tal como aparecen.
- Si el asistente hizo una pregunta o pidió confirmación, inclúyela como parte del resumen.
- Escribe en español, de forma clara y neutral.

Conversación:
{conversation}
"""
