# Veloma Core

Core reutilizável em Django REST Framework para autenticação, autorização nativa do Django, segurança, sessões JWT, e-mail configurável e auditoria.

O primeiro módulo de negócio, o Client Portal, está em `app/client_portal/`. O frontend Next.js ainda não foi criado.

## Estrutura

```text
veloma/
├── app/
│   └── client_portal/           # Módulo de negócio: clientes, convites, protocolos e documentos
├── config/
│   ├── authentication/          # Register, login, OTP, reset, JWT e sessões
│   ├── iam/                     # Groups e Permissions nativos do Django
│   ├── security/                # IP, país, user-agent, bloqueios e rate limit
│   ├── common/                  # E-mail, configuração, respostas e serviços
│   ├── admin.py                 # Django Admin agrupado e enxuto
│   ├── settings.py              # Configuração única
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py
│   └── wsgi.py
├── templates/emails/            # Todos os templates HTML e TXT
├── scripts/
├── .env                         # Ambiente completo de desenvolvimento
├── .env.example
├── docker-compose.yml
├── docker-compose.local.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```

## Regras preservadas

```text
- Não existe CustomUser.
- Não existe AUTH_USER_MODEL próprio.
- O projeto usa django.contrib.auth.models.User.
- O projeto usa Group e Permission nativos do Django.
- username recebe o mesmo valor do email normalizado.
- is_staff e is_superuser são reservados ao Django Admin.
- STAFF_MANAGER, STAFF e USER são grupos nativos para os dashboards.
- Contas do Django Admin são recusadas no login JWT da API.
```

## Core de autenticação

```text
Register
Login
Login com OTP opcional
Verificação de OTP
Reenvio de OTP
Password recovery
Password reset com uid Base64 URL-safe
Reset token opaco, expirável e de uso único
Password change autenticado
Access token
Refresh token
Rotação de refresh token
Blacklist após rotação
Logout da sessão atual
Logout de todas as sessões
Endpoint ME
Listagem de sessões
Revogação de sessão
Limite configurável de sessões simultâneas
```

## Segurança

```text
Tentativas de login
Bloqueio temporário por utilizador
Bloqueio temporário por IP
Bloqueio manual por utilizador, IP, país ou user-agent
Rate limit geral da API
Rate limit específico para autenticação
IP Intelligence configurável pelo Admin
Acesso por país
User-agent e dispositivo
Fingerprint de dispositivo
Deteção de novo dispositivo
Deteção de novo IP
Deteção de novo país
Eventos de segurança
Auditoria de autenticação
Retenção configurável de históricos
```

Django aplica proteção na camada da aplicação. Ataques DDoS volumétricos devem ser filtrados antes da API pelo Cloudflare, Traefik, firewall ou serviço de borda.

## OTP e password reset

O OTP é armazenado com o password hasher do Django, com salt individual. O código original nunca é guardado.

Após validar um OTP de recuperação, o backend responde:

```json
{
  "success": true,
  "data": {
    "verified": true,
    "purpose": "password_reset",
    "uid": "MQ",
    "reset_token": "opaque-one-time-token",
    "expires_in": 600
  }
}
```

O frontend envia depois:

```json
{
  "uid": "MQ",
  "reset_token": "opaque-one-time-token",
  "password": "NewStrongPassword@123",
  "password2": "NewStrongPassword@123"
}
```

O backend valida expiração e uso único, altera a palavra-passe, invalida o grant e revoga as sessões configuradas.

## Ciclo de vida da conta

Nenhuma conta é apagada fisicamente. O model `AccountLifecycle` regista os estados:

```text
active       conta normal
deactivated  suspensão temporária, continua visível no Admin
archived     exclusão lógica, oculta das listas e visível em "Archived accounts"
```

Todas as operações passam por `AccountLifecycleService`:

```python
AccountLifecycleService.deactivate(user=user, performed_by=admin, reason='Contrato suspenso')
AccountLifecycleService.archive(user=user, performed_by=admin, reason='Cliente encerrado')
AccountLifecycleService.reactivate(user=user, performed_by=admin)
AccountLifecycleService.restore(user=user, performed_by=admin)
```

Cada operação corre numa transação e revoga sessões, invalida refresh tokens, bloqueia OTPs pendentes, revoga password resets pendentes, gera auditoria e envia e-mail. O `restore` retira do arquivo mas mantém a conta desativada: o acesso só volta com um `reactivate` explícito. Um administrador não pode aplicar estas ações à própria conta.

No Django Admin a exclusão física está removida (`delete_selected` e a página de exclusão individual). `Reativar` e `Restaurar` estão disponíveis apenas para superusers.

## Client portal

Módulo de negócio em `app/client_portal/`, com API em `/api/client-portal/`.

```text
Convites          criar, reenviar, revogar, validar, aceitar
Clientes          criar, editar, desativar, arquivar, restaurar, reativar
Membros           listar, editar permissões, desativar, arquivar, restaurar
Protocolos        criar, editar, transitar, atribuir, concluir, reabrir, arquivar, timeline
Requisitos        solicitar documentos e acompanhar o que falta
Comentários       públicos e notas internas (invisíveis ao cliente)
Pastas            árvore lógica por cliente, ano e competência
Documentos        upload, versões, mover, rejeitar, arquivar, download assinado
```

Regras principais:

```text
- Registo público desativado: contas USER só nascem de um convite válido.
- Convite com token opaco, de uso único, guardado apenas como hash.
- Isolamento por vínculo: o client_id enviado pelo frontend nunca é aceite sem validação.
- Notas internas e documentos staff_only filtrados no queryset, não no frontend.
- Estados do protocolo com transições válidas; reabertura só por STAFF_MANAGER.
- Upload valida extensão, tamanho e MIME real, calcula SHA-256 e versiona sem substituir.
- Download exige permissão, scan limpo, URL assinada curta e gera auditoria.
- Nenhuma exclusão física: nem na API, nem no Admin.
```

Grupos nativos usados: `STAFF_MANAGER`, `STAFF` e `USER`.

Configuração de uploads, antivírus e convites no Admin, em `Configuration → Document settings`.

## Serviço de e-mail

```text
Modos:
├── sync
├── async
└── auto

Conteúdo:
├── HTML
└── TXT

Vendors:
├── SMTP
└── Development console
```

Os vendors são configurados no Django Admin. Password SMTP e token do IP Intelligence são cifrados com Fernet antes de serem guardados no banco.

O serviço não possui nomes de templates fixos. Cada finalidade é configurada no Admin com:

```text
purpose
subject
html_template
text_template
delivery_mode
vendor
active
```

Os ficheiros permanecem diretamente em:

```text
templates/emails/
```

## Django Admin

O Admin continua usando autenticação, utilizadores, grupos e permissões nativos do Django.

```text
Authentication
├── Users
├── Groups
├── Authentication activity
├── OTP challenges
├── Password reset grants
├── User sessions
├── Access blocks
├── Security events
└── Archived accounts

Client portal
├── Clients
├── Client members
├── Invitations
├── Protocols
├── Documents
└── Folders

Configuration
├── Authentication settings
├── Security settings
├── Document settings
├── Email vendors
├── Email templates
└── Email delivery logs
```

Logs, OTPs, tokens e eventos são somente leitura. As ações administrativas ficam limitadas a revogar sessões, ativar ou desativar bloqueios, resolver eventos e testar vendors de e-mail.

## Docker Compose

```text
veloma-rc
├── veloma-api
├── veloma-postgres
├── veloma-redis
├── veloma-celery
├── veloma-celery-beat
├── veloma-minio
├── veloma-minio-init
└── veloma-clamav
```

Não existe `veloma-app` nesta fase. Ele será criado com o frontend Next.js.

O ClamAV só publica imagens amd64; em hosts arm64 o Compose usa emulação (`platform: linux/amd64`).

Não existe rede personalizada. O Coolify pode ligar o serviço `veloma-api` ao Traefik usando a rede administrada pela própria plataforma.

## Execução local

```bash
cd /Users/cosmeaf/projects/veloma

docker compose \
  -f docker-compose.yml \
  -f docker-compose.local.yml \
  up -d --build
```

Acessos:

O `docker-compose.local.yml` publica portas altas para não colidir com outros projetos:

```text
API:        http://localhost:19080
Admin:      http://localhost:19080/admin/
Swagger:    http://localhost:19080/api/docs/
Health:     http://localhost:19080/health/
PostgreSQL: localhost:19032
Redis:      localhost:19079
MinIO API:  http://localhost:19090
MinIO UI:   http://localhost:19091
```

A conta de desenvolvimento é criada automaticamente com os valores do `.env`:

```text
DJANGO_SUPERUSER_USERNAME
DJANGO_SUPERUSER_PASSWORD
```

## Endpoints

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/otp/verify/
POST /api/auth/otp/resend/
POST /api/auth/password/recovery/
POST /api/auth/password/reset/
POST /api/auth/password/change/
POST /api/auth/token/refresh/
POST /api/auth/logout/
POST /api/auth/logout/all/
GET  /api/auth/me/
GET  /api/auth/sessions/
POST /api/auth/sessions/{session_id}/revoke/
```

## Testes

Com PostgreSQL e Redis:

```bash
docker exec -it veloma-api python manage.py test
```

Teste rápido com SQLite e cache local:

```bash
cd /Users/cosmeaf/projects/veloma

DATABASE_ENGINE=sqlite \
MINIO_ENABLED=false \
USE_LOCAL_MEMORY_CACHE=true \
CELERY_TASK_ALWAYS_EAGER=true \
python manage.py test
```

## Validação estática

```bash
python3 scripts/validate_project.py
python3 -m compileall -q .
```

## Produção

O `.env` incluído é exclusivo para desenvolvimento. Antes de produção, altere no Coolify:

```text
DJANGO_SECRET_KEY
POSTGRES_PASSWORD
REDIS_PASSWORD
CREDENTIALS_ENCRYPTION_KEY
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
DJANGO_SUPERUSER_PASSWORD
DJANGO_ALLOWED_HOSTS
DJANGO_CORS_ALLOWED_ORIGINS
DJANGO_CSRF_TRUSTED_ORIGINS
```
