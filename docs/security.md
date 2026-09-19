# Seguridad y límites

- Los cuatro CSV oficiales son **simulados** y provienen del ZIP definitivo. No se ingieren RAW ni datos personales reales para estos casos.
- La referencia académica del Caso 1 y el golden humano del Caso 2 se cargan **solo después de las predicciones**. Ninguna etiqueta humana entra en los contextos de los prompts.
- Los prompts evitan afirmar consultas regulatorias reales, confirmación de fraude, aprobación crediticia o plazos de devolución.
- Caso 1 separa recomendación IA, decisión humana y estado de revisión. Caso 2 separa clasificación IA, borrador y revisión; FRAUDE exige revisión humana.
- API y logs no incluyen cuerpos de solicitud en mensajes operativos. Los comentarios de la demo cloud están restringidos a valores predefinidos.
- El Azure existente corresponde a la implementación anterior hasta la Fase 2. No se modificó en la Fase 1.
- El acceso cloud actual se restringe por IP y no dispone de autenticación individual. Para producción bancaria se requieren Entra ID, roles, VNet/Private Endpoints, controles de acceso y revisión de cumplimiento.
