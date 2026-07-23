# Deploy — Coolify + Traefik

Domínios:

```text
veloma.app      → veloma-app  (Next.js, porta 3000)
api.veloma.app  → veloma-api  (Django/Gunicorn, porta 8000)
```

PostgreSQL, Redis, MinIO, ClamAV, Celery e Celery Beat ficam internos, sem domínio.

## 1. Repositório

O Coolify faz deploy a partir de um repositório Git. O `.env` está no `.gitignore`:
as variáveis são definidas no Coolify, nunca no repositório.

```bash
git remote add origin git@github.com:<conta>/veloma.git
git push -u origin main
```

## 2. Segredos de produção

Gerar valores novos — os do desenvolvimento não vão para produção:

```bash
python3 scripts/generate_secrets.py
```

Isso produz `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`,
`CREDENTIALS_ENCRYPTION_KEY`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` e
`DJANGO_SUPERUSER_PASSWORD`.

> `CREDENTIALS_ENCRYPTION_KEY` cifra a password SMTP e o token de IP Intelligence
> guardados no banco. Se for trocada depois de haver dados cifrados, esses
> segredos deixam de poder ser lidos e têm de ser reintroduzidos no Admin.

## 3. Recurso no Coolify

1. **New Resource → Docker Compose**, apontado ao repositório e ao
   `docker-compose.yml` da raiz.
2. Definir os domínios por serviço:
   - `veloma-app` → `https://veloma.app` (porta 3000)
   - `veloma-api` → `https://api.veloma.app` (porta 8000)
3. Colar as variáveis de ambiente (secção 4). O `.env.example` serve de referência.
4. Deploy.

O compose não declara redes próprias e usa `expose` em vez de `ports`: é o Traefik
do Coolify que publica os dois serviços. Não acrescentar NGINX.

## 4. Variáveis de ambiente

Diferenças face ao `.env.example` de desenvolvimento:

```text
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=api.veloma.app,veloma.app,veloma-api,veloma-app
DJANGO_CORS_ALLOWED_ORIGINS=https://veloma.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://api.veloma.app,https://veloma.app
FRONTEND_URL=https://veloma.app
INTERNAL_API_URL=http://veloma-api:8000
MINIO_ENDPOINT=<endpoint público do MinIO>
TRUST_PROXY_HEADERS=true
RUN_MIGRATIONS=true
RUN_COLLECTSTATIC=true
RUN_BOOTSTRAP=true
```

`MINIO_ENDPOINT` tem de ser alcançável pelo browser: as URLs de download são
assinadas para esse host. Com o endereço interno (`http://veloma-minio:9000`) a
assinatura é válida mas o cliente não consegue lá chegar.

`RUN_BOOTSTRAP=true` cria grupos, configurações, templates de e-mail e o
administrador inicial. É idempotente e pode ficar ligado.

## 5. Depois do primeiro deploy

```text
1. Entrar em https://api.veloma.app/admin/ com o superuser do .env.
2. Configuration → Email vendors: criar o vendor SMTP real e marcá-lo como default.
3. Configuration → Document settings: confirmar limites de upload e ligar
   require_antivirus com antivirus_host=veloma-clamav.
4. Configuration → Security settings: rever rate limits e retenção.
5. Criar os utilizadores da equipa e colocá-los nos grupos STAFF_MANAGER ou STAFF.
6. Criar o primeiro cliente e enviar o convite.
```

## 6. Verificação

```bash
curl -s https://api.veloma.app/health/          # {"status": "ok", ...}
curl -s -o /dev/null -w '%{http_code}\n' https://veloma.app/
curl -s -o /dev/null -w '%{http_code}\n' https://api.veloma.app/api/docs/
```

Se `api.veloma.app` devolver `no available server`, o router do Traefik existe mas
o contentor não está saudável: ver os logs de `veloma-api` no Coolify.

## 7. Notas de operação

- **ClamAV** só publica imagens amd64; o compose fixa `platform: linux/amd64`.
  Em servidores x86 corre nativamente. O primeiro arranque descarrega as
  definições e demora alguns minutos — `start_period` está a 180 s.
- **Backups**: os volumes `veloma-postgres-data` e `veloma-minio-data` contêm
  respetivamente a base de dados e todos os documentos. Nada é apagado
  fisicamente pela aplicação, por isso o backup destes dois volumes é o backup
  do sistema.
- **Escala**: `GUNICORN_WORKERS` e `CELERY_CONCURRENCY` são variáveis de ambiente.
