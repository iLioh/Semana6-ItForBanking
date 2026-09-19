# Informe ejecutivo — Laboratorio 06

La Fase 1 deja preparada localmente una demo con dos casos totalmente simulados. Caso 1 ejecuta tres prompts reales en secuencia (KYC, scoring y explicabilidad) y compara con una referencia académica independiente. Caso 2 compara clasificación V1/V2 sobre 30 quejas con un golden humano balanceado, calcula métricas y genera un borrador mediante prompt separado. Ambos flujos requieren revisión humana.

React, FastAPI, SQLAlchemy/Alembic y los proveedores IA mock/Azure comparten contratos estructurados. Las pruebas locales utilizan exclusivamente mocks; **no se obtuvieron métricas reales ni se desplegó esta versión en Azure durante Fase 1**. La Fase 2 debe limpiar datos de ejecución, migrar Azure SQL, cargar los CSV, desplegar y medir con Azure OpenAI.
