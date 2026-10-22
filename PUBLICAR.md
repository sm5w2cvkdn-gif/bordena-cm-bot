# Instrucciones: publicar la historia aprobada

Corrés a las 10:00 (Buenos Aires). Publicás en Instagram la historia de hoy **solo si fue aprobada**,
es decir, si ya está en la rama `main`. Nunca publiques otra cosa ni modifiques la imagen.

## Pasos

1. `git fetch origin main && git checkout main && git pull`.
2. `FECHA=$(TZ=America/Argentina/Buenos_Aires date +%F)`.
3. Si NO existe `historias/FECHA.jpg` en `main`: no fue aprobada. Respondé "Historia de FECHA no
   aprobada: no se publicó nada." y terminá.
4. Si en `historial.md` la fila de FECHA ya dice `publicada`, terminá (ya se publicó).
5. Armá la URL pública: `https://raw.githubusercontent.com/<owner>/<repo>/main/historias/FECHA.jpg`
   (`<owner>/<repo>` sale de `git remote get-url origin`). Verificá que responda 200 con
   `curl -sI <url>`; si no, esperá 60 segundos y reintentá hasta 3 veces.
6. Publicá con el conector **Windsor.ai**:
   - `get_connectors` → buscá el conector `instagram` y tomá el `id` de la cuenta de Bordena Studio.
   - `execute_action` con `connector: "instagram"`, `action: "create_story"`, `account: <id>`,
     `params: {"image_url": "<url>"}`.
   - Una sola vez. Si falla, **no reintentes en loop**: reportá el error textual y terminá.
7. Si se publicó: cambiá `pendiente` por `publicada` en la fila de FECHA de `historial.md`,
   commiteá y pusheá a `main` (si el push falla, no importa: no es crítico).
8. Respuesta final: "Publicada la historia de FECHA" + el id que devolvió Instagram.
