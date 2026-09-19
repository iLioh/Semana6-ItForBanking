# Infraestructura Azure de la demo

El grupo `rg-iblaboratorio06-dev` de la suscripción Azure for Students contiene
App Service Linux F1 (React compilado + FastAPI), Azure SQL Basic, Blob Storage
privado, Azure OpenAI `gpt-5-mini`, Key Vault y observabilidad. Los recursos
están en `westus3`. Pueden consumir crédito estudiantil mientras existan.

`infra/main.bicep` mantiene el despliegue reproducible. Antes de cualquier
reconciliación, ejecutar `az deployment group what-if` con los valores reales
del tenant, el administrador SQL y la IP permitida. El archivo
`main.bicepparam` contiene placeholders; **no desplegarlo sin sustituirlos**.

El tenant educativo no permitió crear app registrations. La demo usa
`enableUserAuth=false`, `allowedClientIp=179.6.6.51` e identidad administrada
del App Service para SQL/Blob/OpenAI. No es una configuración productiva para
un banco ni debe abrirse a todas las IP. Para producción son necesarios Entra
para usuarios, roles, Private Endpoints/VNet y gobierno de seguridad.

Antes de Fase 2, `prepared-private` aún contiene datos de la versión anterior.
La versión oficial cargará solo los cuatro CSV simulados de `data/official/`.
`raw-private` existe por la plantilla, pero la aplicación no lo usa.
El frontend no tiene acceso directo a ningún contenedor. Azure SQL no usa
contraseña; las migraciones y el usuario contenido del runtime se aplican con
`scripts/bootstrap_azure_sql.py` desde el equipo del administrador Entra.

El paquete de App Service se crea con `scripts/package_azure_app.py` después de
`npm run build`. El ZIP incluye exclusivamente `src/`, `prompts/`,
`frontend/dist/` y `requirements.txt`; excluye `data/`, `.env`, `.venv` y
`node_modules`. App Service ejecuta el build Python en Azure.
