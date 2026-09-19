# IT for Banking
**Semana 06: IA Generativa y Prompt Engineering en Banca**  
*Docente:* Ing. Ivan Martinez M (Microsoft Trainer Certificado)  
*Institución:* Universidad Tecnológica del Perú (UTP)

> **Implementación 2026:** esta guía se conserva como material académico base.
> La versión oficial preparada en Fase 1 usa exclusivamente los datasets
> simulados definitivos: 15 empresas para KYC/Scoring/XAI y 30 quejas para
> clasificación V1/V2 con golden humano. Véanse `README.md` y `ppt.md`.
> Esta nueva versión aún no se ha desplegado ni evaluado con Azure OpenAI real.

---

## Contenido de la Sesión

### Teoría
- Fundamentos de Generative AI y Large Language Models (LLM).
- Prompt Engineering: Técnicas para obtener respuestas precisas y útiles.
- Uso responsable y ético de la IA.
- Comparación entre modelos de IA.
- Casos de uso en banca: chatbots, análisis de sentimiento, resumen de documentos.

### Logro de la Sesión
Al final de la sesión, el estudiante comprende el funcionamiento de los modelos de lenguaje y cómo aplicarlos de forma ética.

---

# PARTE I: LABORATORIO PRÁCTICO
## Implementación de IA para Onboarding y Scoring en Banca Empresarial

### 1. Objetivo del Taller
Implementar un flujo funcional de onboarding + scoring crediticio usando prompts, incorporando:
- Evaluación automatizada de clientes empresariales.
- Análisis de riesgo financiero.
- Explicabilidad de decisiones.
- Controles éticos y regulatorios.

### 2. Escenario
El **Banco Andino Corporativo** requiere un prototipo funcional que permita evaluar empresas en tiempo casi real utilizando IA. Se trabajará con datos simulados, replicando un entorno bancario real.

### 3. Duración y Modalidad
- **Duración:** 3 a 4 horas.
- **Modalidad:** Práctica guiada + resolución de caso.

### 4. Herramientas Sugeridas
- Motor LLM (ej. API tipo GPT / ChatGPT / Copilot).
- Excel / CSV (dataset).
- **Opcional:**
  - Python (para integración).
  - Power BI (visualización).
  - Plataforma cloud (Azure / AWS).

---

### 5. Dataset de Trabajo (Ejemplo)
Cada grupo utilizará datos como:

| Empresa | Sector | Liquidez | Endeudamiento | Flujo | Historial |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **AgroPerú SAC** | Agrícola | 1.8 | 0.4 | Positivo | Bueno |
| **TechNova SRL** | Tecnología | 1.2 | 0.7 | Variable | Regular |
| **Minera Andina** | Minería | 0.9 | 0.8 | Negativo | Malo |

---

### 6. Fases del Flujo de Trabajo

#### FASE 1: Onboarding Inteligente
- **Objetivo:** Validar cumplimiento KYC usando IA.
- **Actividad (Prompt Sugerido):**
  ```text
  Actúa como analista de cumplimiento bancario.
  Evalúa:
  - Empresa: {{empresa}}
  - Sector: {{sector}}
  - País: Perú

  Tareas:
  1. Detectar riesgos por sector
  2. Validar coherencia
  3. Determinar cumplimiento KYC

  Salida:
  Estado + Justificación
  ```
- **Resultado Esperado:** Clasificación en `Aprobado`, `Observado` o `Rechazado`.

---

#### FASE 2: Scoring Crediticio Automatizado
- **Objetivo:** Asignar nivel de riesgo financiero.
- **Actividad (Prompt Sugerido):**
  ```text
  Actúa como analista de riesgo crediticio.
  Datos:
  - Liquidez: {{liquidez}}
  - Endeudamiento: {{endeudamiento}}
  - Flujo: {{flujo}}
  - Historial: {{historial}}

  Tareas:
  1. Evaluar capacidad de pago
  2. Detectar riesgos
  3. Clasificar riesgo

  Salida:
  Score + Nivel de riesgo + Recomendación
  ```
- **Resultado Esperado:**
  - **Riesgo:** Bajo / Medio / Alto.
  - **Recomendación:** `Aprobar`, `Evaluar` o `Rechazar`.

---

#### FASE 3: Explicabilidad (Explainable AI)
- **Objetivo:** Justificar decisiones automatizadas.
- **Actividad (Prompt Sugerido):**
  ```text
  Actúa como auditor de IA.
  Explica:
  - Resultado: {{resultado}}

  Tareas:
  1. Identificar variables clave
  2. Detectar sesgos
  3. Evaluar transparencia

  Salida:
  Explicación + Nivel de confianza
  ```

---

#### FASE 4: Integración del Flujo
El flujo completo a implementar consta de las siguientes etapas:
1. Ingreso de datos
2. Evaluación KYC (Prompt 1)
3. Evaluación financiera (Prompt 2)
4. Explicación (Prompt 3)
5. Decisión final

---

#### FASE 5: Control Ético y Regulatorio
Responder analíticamente a las siguientes preguntas:
1. ¿Qué datos **NO** deben usarse?
2. ¿Dónde puede existir sesgo?
3. ¿Cómo asegurar cumplimiento normativo?
4. ¿Cómo auditar decisiones?

---

### 7. Caso Reto (Aplicación Real)
- **Empresa:** Constructora Andina SAC  
- **Sector:** Construcción  
- **Liquidez:** 0.95  
- **Endeudamiento:** 0.85  
- **Flujo:** Negativo  
- **Historial:** Regular  

**Tareas a ejecutar:**
1. Ejecutar onboarding
2. Ejecutar scoring
3. Generar explicación
4. Tomar decisión final

---

### 8. Entregables del Taller
Cada grupo debe presentar:
- Resultados de evaluación.
- Prompts utilizados (versiones optimizadas/mejoradas).
- Análisis de riesgo.
- Justificación de decisión.
- Evaluación ética.

---

# PARTE II: CASO PRÁCTICO COMPLETO
## "Banco Andino - Clasificador de quejas de clientes con GenAI"

### 1. Contexto y Objetivo
Banco Andino recibe diariamente decenas de correos de clientes con quejas sobre posibles fraudes con tarjetas, problemas de servicio (tiempos de atención, demoras) y disconformidad con productos (condiciones, comisiones).

El área de atención al cliente busca utilizar un modelo de IA generativa para clasificar automáticamente estas quejas en categorías y generar respuestas base coherentes, evaluando previamente errores y sesgos antes de un despliegue en producción.

**Rol:** Cada equipo actuará como *"equipo de experiencia de cliente + IA"* y diseñará prompts para un LLM (ChatGPT / Copilot) con el fin de:
- Clasificar correos de queja en al menos tres categorías: **Fraude**, **Servicio** y **Producto**.
- Generar borradores de respuesta base, listos para revisión humana.
- Analizar y documentar errores frecuentes y posibles sesgos del modelo.

---

### 2. Dataset de Correos de Queja (Simulado)
El docente provee entre 15 y 30 quejas en texto libre, organizadas bajo las siguientes categorías de referencia:
- **Fraude:** Cobros no reconocidos en tarjeta, transferencias no autorizadas.
- **Servicio:** Maltrato o mala atención en agencia/call center, tiempos de espera excesivos, errores operativos.
- **Producto:** Reclamos por comisiones o tasas de interés, condiciones de préstamo o tarjeta consideradas engañosas.

*Estructura de cada queja:* Asunto, cuerpo del correo y metadatos opcionales (tipo de producto, monto, fecha).

---

### 3. Diseño de Prompts para Clasificación
Diseñar prompts estructurados con salida en **JSON** o **tabla**.

#### Instrucción Base Sugerida:
```text
Actúa como analista de quejas de un banco. Lee el texto de la queja del
cliente y clasifícala en una de estas categorías: FRAUDE, SERVICIO, PRODUCTO.
Devuelve tu respuesta SOLO en formato JSON con los
campos: categoria, subcategoria, resumen_breve.
```

#### Variantes Enriquecidas:
- Incluir un campo `confianza` (`alta` / `media` / `baja`) para filtrar casos dudosos.
- Incluir un campo `prioridad` (`alta` / `media` / `baja`) con criterios explícitos (ej. Fraudes de montos elevados = alta prioridad).
- Probar al menos **dos versiones de prompt** y contrastar la precisión obtenida.

---

### 4. Diseño de Prompts para Respuestas Base
El modelo debe generar un borrador de comunicación empática y profesional para revisión de un analista humano.

#### Prompt Sugerido:
```text
Usa la categoría de queja (FRAUDE, SERVICIO o PRODUCTO) y el texto original del
cliente. Redacta una respuesta breve y empática en español, en tono profesional de
banco, que:
- Agradezca el contacto.
- Resuma la preocupación del cliente en 1 frase.
- Indique los próximos pasos concretos (ej. bloquear tarjeta, abrir caso de investigación, derivar a área).
- Evite hacer promesas que el banco no pueda garantizar.
Devuelve SOLO un campo respuesta_redactada.
```

#### Criterios de Validación:
- Coherencia con la categoría asignada.
- Ausencia de alucinaciones (no inventar políticas ni plazos irreales) o compromisos indebidos (no asumir culpas preliminares).

---

### 5. Metodología Paso a Paso en Grupo
1. **Lectura y Etiquetado Humano:**
   - Clasificar manualmente 10–15 quejas para establecer el *Ground Truth* (*etiqueta golden*).
2. **Diseño y Prueba de Prompts (45–60 min):**
   - Ejecutar la clasificación con la versión inicial del prompt.
   - Comparar predicción IA vs. etiqueta humana (conteo de aciertos y matriz de confusión).
   - Iterar y afinar el prompt (p. ej., delimitando casos frontera y definiciones).
3. **Generación y Revisión de Respuestas Base:**
   - Evaluar tono, ausencia de asunciones de culpabilidad temprana y neutralidad en el trato frente a variables del cliente.
4. **Análisis de Errores y Sesgos:**
   - Detectar patrones de falla (correos con reclamos múltiples/mixtos, lenguaje coloquial o agresivo).
   - Analizar si el modelo prioriza o atiende distinto en función del vocabulario o modismos utilizados.

---

### 6. Campos y Visualizaciones Críticas
Propuesta de tablero de control (Power BI o Excel):
- **Campos:** `categoria_ia`, `categoria_humana`, `confianza`, `prioridad`, `fecha`, `producto_relacionado`.
- **Visualizaciones:**
  - Gráfico de barras: volumen de quejas por categoría.
  - Matriz de confusión: IA vs. Humano para identificar desviaciones y tasas de error.

---

### 7. Discusión Final y Recomendaciones
Cada equipo responderá:
1. ¿En qué tipo de quejas funcionó mejor la clasificación y en cuáles surgieron mayores discrepancias?
2. ¿Qué ajustes al prompt lograron un impacto medible en el rendimiento?
3. ¿Qué políticas de gobernanza propondrían antes del paso a producción?
   - Revisión humana obligatoria en casos clasificados como Fraude (*Human-in-the-Loop*).
   - Reentrenamiento y ajuste periódico de prompts con nuevos casos.
   - Monitoreo continuo de sesgos y métricas de error por categoría.
