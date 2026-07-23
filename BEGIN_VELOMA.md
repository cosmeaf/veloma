```text
PROMPT MESTRE — VELOMA

Atue como arquiteto de software, programador sénior Django/DRF, programador sénior Next.js, especialista em autenticação, segurança web, Docker e Coolify.

Você trabalhará diretamente no projeto:

/Users/cosmeaf/projects/veloma

OBJETIVO PRINCIPAL

Concluir e validar todo o core backend da Veloma e, somente depois de confirmar que o core está funcional, desenvolver:

1. Frontend completo em Next.js.
2. Site institucional da Veloma.
3. Sistema completo de autenticação integrado ao backend.
4. Dashboard separado para STAFF.
5. Dashboard separado para USER.
6. Deploy preparado para Coolify com Traefik.
7. Primeiro módulo institucional do backend somente após o core estar validado.

DOMÍNIOS

Frontend e site institucional:

https://veloma.app

Backend Django REST Framework:

https://api.veloma.app

Django Admin:

https://api.veloma.app/admin/

Documentação Swagger:

https://api.veloma.app/api/docs/

OpenAPI Schema:

https://api.veloma.app/api/schema/

Health check:

https://api.veloma.app/health/

Não utilizar:

- api.velopa.app
- NGINX próprio
- CustomUser
- AUTH_USER_MODEL personalizado
- autenticação simulada no frontend
- dados falsos
- módulos de negócio antes da validação do core
- localStorage para access ou refresh token
- código estático para templates de e-mail
- nomes de vendors de e-mail fixos no código
- configurações críticas espalhadas pelo frontend

==================================================
1. REGRA DE EXECUÇÃO
==================================================

Antes de criar o frontend ou qualquer aplicação de negócio:

1. Ler todo o projeto existente.
2. Ler o README.md.
3. Ler o .env e o .env.example.
4. Ler config/settings.py.
5. Ler config/urls.py.
6. Ler todos os models, serializers, services, views, permissions, middleware, tasks, migrations e testes.
7. Executar a validação existente.
8. Subir os serviços Docker.
9. Executar migrations.
10. Executar bootstrap.
11. Executar manage.py check.
12. Executar toda a suíte de testes.
13. Testar manualmente todos os endpoints de autenticação.
14. Corrigir qualquer falha encontrada.
15. Somente quando o core estiver funcional, iniciar o frontend.

Não reescrever o backend do zero.

Reutilizar o que já existe.

Não criar novas camadas sem necessidade real.

Não duplicar serviços.

Não mover o projeto para uma arquitetura diferente.

Não dividir settings.py em base.py, development.py ou production.py.

Manter um único:

config/settings.py

==================================================
2. ESTRUTURA ATUAL DO BACKEND
==================================================

O backend existente está organizado assim:

veloma/
├── app/
│   └── __init__.py
│
├── config/
│   ├── authentication/
│   ├── iam/
│   ├── security/
│   ├── common/
│   ├── admin.py
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py
│   └── wsgi.py
│
├── templates/
│   └── emails/
│
├── scripts/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── docker-compose.local.yml
├── docker-entrypoint.sh
├── .env
└── .env.example

Responsabilidades:

config/authentication/
- Register.
- Login.
- OTP.
- Password recovery.
- Password reset.
- JWT.
- Refresh.
- Logout.
- Sessões.
- Auditoria de autenticação.

config/iam/
- Uso dos Groups e Permissions nativos do Django.
- Controle RBAC.
- Permissões para STAFF e USER.

config/security/
- IP do utilizador.
- Proxy headers.
- User-Agent.
- Device fingerprint.
- IP Intelligence.
- País.
- Bloqueios.
- Rate limiting.
- Proteção contra brute force.
- Eventos de segurança.

config/common/
- Serviço de e-mail.
- Vendors de e-mail.
- Configurações globais.
- Criptografia de credenciais.
- Tasks Celery.
- Respostas padronizadas.
- Tratamento de exceções.

app/
- Deve permanecer sem módulos de negócio até o core ser completamente validado.

==================================================
3. DJANGO NATIVO — NÃO ALTERAR
==================================================

O projeto utiliza exclusivamente:

django.contrib.auth.models.User
django.contrib.auth.models.Group
django.contrib.auth.models.Permission
django.contrib.admin

Não criar CustomUser.

Não adicionar AUTH_USER_MODEL.

Não alterar internamente o Django Admin.

Não substituir Group ou Permission.

Não criar model de perfil apenas para repetir campos que já existem no User.

O registo deve continuar usando:

first_name
last_name
email
password
password2

Regra:

username = email normalizado
email = email normalizado

Normalização:

email.strip().lower()

==================================================
4. SEPARAÇÃO DE ACESSOS
==================================================

Existem três tipos de ambiente completamente separados.

DJANGO ADMIN

- Utiliza autenticação nativa do Django.
- Acesso por /admin/.
- Requer is_staff=True.
- Pode usar is_superuser ou permissões administrativas específicas.
- Não deve autenticar no dashboard frontend.
- O backend já deve recusar login JWT de contas administrativas.

STAFF DA PLATAFORMA

- User nativo do Django.
- is_staff=False.
- is_superuser=False.
- Pertence ao Group STAFF.
- Acessa somente /staff.
- Não acessa /admin/.
- Não acessa áreas exclusivas de USER.

USER OU CLIENTE

- User nativo do Django.
- is_staff=False.
- is_superuser=False.
- Pertence ao Group USER.
- Acessa somente /dashboard.
- Não acessa /staff/.
- Não acessa /admin/.

Regra central:

Django Admin
≠
Staff Dashboard
≠
Customer Dashboard

O frontend pode esconder rotas e menus, mas a autorização final deve sempre ser validada pelo backend.

==================================================
5. MODELS EXISTENTES DO CORE
==================================================

O backend já possui models próprios para dados operacionais, sem substituir o User.

Authentication:

OTPChallenge
- OTP de registo.
- OTP de login.
- OTP de recuperação.
- Código armazenado com password hasher do Django.
- Salt individual.
- Tentativas.
- Reenvios.
- Expiração.
- Bloqueio.
- Uso único.
- IP.
- User-Agent.

PasswordResetGrant
- Token opaco.
- Hash do token armazenado.
- Expiração.
- Uso único.
- Revogação.
- Relação com OTP validado.
- IP.
- User-Agent.

UserSession
- UUID da sessão.
- User.
- Refresh JTI.
- Estado.
- IP.
- User-Agent.
- Dispositivo.
- Fingerprint.
- País.
- Metadados.
- Última atividade.
- Expiração.
- Revogação.

AuthenticationActivity
- Login.
- Falha.
- Bloqueio.
- OTP.
- Recovery.
- IP.
- País.
- Utilizador.
- Motivo.
- Metadados.

AccessBlock
- Bloqueio por utilizador.
- Bloqueio por IP.
- Bloqueio por país.
- Bloqueio por User-Agent.
- Temporário ou permanente.
- Automático ou manual.

SecurityEvent
- Eventos informativos.
- Alertas.
- Eventos críticos.
- Auditoria.
- Investigação.
- Resolução administrativa.

Configuration:

AuthenticationSettings
- Ativar ou desativar registo.
- Exigir validação de e-mail.
- OTP no login.
- Tamanho do OTP.
- Validade.
- Tentativas.
- Reenvios.
- Cooldown.
- Validade do reset.
- Grupo padrão.
- Revogação após alteração de senha.
- Bloqueio de admin no login da API.

SecuritySettings
- Tentativas máximas.
- Janela de login.
- Tempo de bloqueio.
- Bloqueio de utilizador.
- Bloqueio de IP.
- Máximo de sessões.
- Rate limit.
- IP Intelligence.
- Países permitidos.
- Alertas de dispositivo, IP e país.
- Retenção de logs.

EmailSettings
- sync.
- async.
- auto.
- fallback.
- tentativas.
- backoff.

EmailVendor
- SMTP.
- Console de desenvolvimento.
- Host.
- Porta.
- Username.
- Password cifrada.
- TLS.
- SSL.
- From.
- Reply-To.
- Prioridade.
- Vendor padrão.
- Vendor de fallback.

EmailTemplate
- Purpose.
- Subject.
- HTML template.
- TXT template.
- Delivery mode.
- Vendor.
- Active.

EmailDeliveryLog
- Destinatários.
- Assunto.
- Purpose.
- Vendor.
- Modo.
- Estado.
- Tentativas.
- Erro.
- Task Celery.
- Data de envio.

Não duplicar esses models.

==================================================
6. ENDPOINTS EXISTENTES
==================================================

Utilizar os endpoints reais do backend:

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

Antes de implementar o frontend:

1. Conferir o OpenAPI Schema.
2. Conferir os serializers reais.
3. Conferir o formato padronizado das respostas.
4. Não inventar campos.
5. Gerar tipos TypeScript a partir do OpenAPI quando possível.
6. Tratar todos os códigos de erro e estados intermediários.

==================================================
7. FORMATO DO UTILIZADOR
==================================================

O backend apresenta o utilizador aproximadamente assim:

{
  "id": 1,
  "first_name": "Nome",
  "last_name": "Sobrenome",
  "email": "utilizador@dominio.com",
  "last_login": "data ISO ou null",
  "roles": ["USER"],
  "status": "active",
  "is_active": true,
  "is_admin": false,
  "is_platform_staff": false
}

Não confiar somente em is_platform_staff.

Validar também:

roles.includes("STAFF")
roles.includes("USER")
is_admin
is_active
status

==================================================
8. FLUXO DE REGISTO
==================================================

Tela:

/criar-conta

Campos:

first_name
last_name
email
password
password2
aceitação dos termos
aceitação da política de privacidade

Regras:

- Formulário acessível.
- Validação no frontend com as mesmas regras básicas.
- A validação definitiva pertence ao backend.
- Mostrar requisitos de password.
- Não revelar se uma conta existe além da resposta legítima do backend.
- Não armazenar password.
- Não enviar espaços indevidos.
- Normalizar e-mail visualmente.

Após registo:

Se requires_otp=true:

- Guardar challenge_id somente durante o fluxo.
- Redirecionar para /verificar-email.
- Mostrar e-mail parcialmente mascarado.
- Mostrar contador baseado em expires_at.
- Permitir reenvio.
- Respeitar retry_after e cooldown.
- Substituir challenge_id quando o backend gerar novo desafio.
- Não simular OTP.
- Não colocar OTP em URL.

Se requires_otp=false:

- Mostrar confirmação.
- Direcionar para login.

==================================================
9. FLUXO DE LOGIN
==================================================

Tela:

/entrar

Campos:

email
password
lembrar dispositivo apenas como preferência visual, sem reduzir segurança

Após login:

Se requires_otp=true:

- Receber challenge_id.
- Ir para /confirmar-login.
- Validar OTP.
- Após validação, receber access, refresh, session_id e user.

Se requires_otp=false:

- Receber tokens e user diretamente.

Redirecionamento:

STAFF:
- /staff

USER:
- /dashboard

Admin Django:
- O backend deve recusar.
- Mostrar mensagem explicando que administradores devem usar /admin/.
- Não criar link público chamativo para o Admin.

==================================================
10. RECUPERAÇÃO DE PASSWORD
==================================================

Fluxo completo:

1. /recuperar-password
2. Enviar e-mail.
3. Receber challenge_id.
4. /validar-recuperacao
5. Informar OTP.
6. Backend valida OTP.
7. Backend devolve:

{
  "verified": true,
  "purpose": "password_reset",
  "uid": "Base64 URL-safe",
  "reset_token": "token opaco de uso único",
  "expires_in": 600
}

8. Frontend mantém uid e reset_token somente durante o fluxo seguro.
9. Redirecionar para /redefinir-password.
10. Enviar:

{
  "uid": "...",
  "reset_token": "...",
  "password": "...",
  "password2": "..."
}

11. Mostrar confirmação.
12. Limpar completamente uid e reset_token.
13. Redirecionar para login.

O frontend controla:

- Interface.
- Contador.
- Navegação.
- Estados.
- Mensagens.
- Limpeza dos dados temporários.

O backend controla:

- Geração.
- Hash.
- Expiração.
- Tentativas.
- Uso único.
- Revogação.
- Alteração da password.
- Revogação das sessões.

Não tentar validar token apenas no frontend.

==================================================
11. TOKENS NO FRONTEND
==================================================

O backend atualmente devolve access e refresh no response JSON.

Para o navegador, implementar um BFF usando Route Handlers do Next.js.

Arquitetura:

Browser
    │
    ▼
Next.js Route Handlers
    │
    ▼
https://api.veloma.app

O navegador não deve receber tokens para guardar em localStorage.

Os Route Handlers devem:

- Receber as credenciais do browser.
- Chamar o backend Django.
- Receber access e refresh.
- Guardar ambos em cookies HttpOnly.
- Usar Secure em produção.
- Usar SameSite=Lax ou mais restritivo quando possível.
- Definir Path adequado.
- Definir Max-Age coerente com as expirações.
- Nunca expor o refresh token ao JavaScript.
- Renovar access token usando o refresh.
- Atualizar cookies após rotação.
- Limpar cookies em logout.
- Limpar cookies quando refresh estiver inválido.
- Evitar múltiplos refresh simultâneos.
- Não criar loop infinito de refresh.

Cookies sugeridos:

veloma_access
veloma_refresh
veloma_session

Não usar:

localStorage
sessionStorage
IndexedDB para tokens
variáveis globais persistentes

O frontend pode manter o objeto user em memória e recuperá-lo novamente por /me.

==================================================
12. FRONTEND
==================================================

Criar o frontend em:

/Users/cosmeaf/projects/veloma/frontend

Stack:

- Next.js com App Router.
- TypeScript estrito.
- React.
- Tailwind CSS.
- Server Components quando fizer sentido.
- Client Components somente quando houver interação.
- React Hook Form para formulários.
- Zod para validação.
- API nativa fetch.
- Lucide Icons ou equivalente leve.
- Sem Redux, salvo necessidade real.
- Sem Axios, salvo necessidade real.
- Sem biblioteca pesada de UI.
- Componentes acessíveis e reutilizáveis.

Estrutura sugerida:

frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── features/
│   │   ├── authentication/
│   │   ├── account/
│   │   ├── sessions/
│   │   ├── institutional/
│   │   └── contact/
│   ├── lib/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── cookies/
│   │   ├── validation/
│   │   └── utils/
│   ├── content/
│   │   └── site.ts
│   ├── types/
│   └── styles/
├── public/
├── Dockerfile
├── package.json
├── tsconfig.json
└── next.config.ts

Evitar pastas e abstrações sem uso real.

==================================================
13. SITE INSTITUCIONAL
==================================================

Criar um site institucional profissional para a Veloma.

Posicionamento inicial:

Veloma é uma empresa de contabilidade e apoio empresarial, com conhecimento dos contextos de Portugal e Brasil, focada em atendimento próximo, clareza, organização, rapidez e acompanhamento contínuo.

Todo o conteúdo deve ficar centralizado e fácil de alterar.

Não espalhar textos institucionais em dezenas de componentes.

Usar:

src/content/site.ts

ou estrutura equivalente simples.

Não criar CMS nesta fase.

Páginas:

/
- Home.

/sobre
- História.
- Missão.
- Forma de trabalho.
- Experiência Portugal e Brasil.
- Valores.

/servicos
- Visão geral dos serviços.

/servicos/contabilidade-empresas
- Contabilidade para empresas.

/servicos/trabalhadores-independentes
- Apoio a trabalhadores independentes.
- Recibos verdes.
- Organização fiscal.

/servicos/abertura-de-empresa
- Abertura de empresa.
- Enquadramento inicial.
- Organização documental.

/servicos/fiscalidade
- Obrigações fiscais.
- Acompanhamento.
- Planeamento responsável.

/servicos/processamento-salarial
- Processamento salarial.
- Obrigações relacionadas com colaboradores.

/servicos/apoio-portugal-brasil
- Apoio a clientes com contexto Portugal e Brasil.
- Explicação de diferenças práticas.
- Organização e encaminhamento contabilístico.

/como-trabalhamos
- Diagnóstico.
- Recolha documental.
- Planeamento.
- Execução.
- Acompanhamento.

/faq
- Perguntas frequentes.

/contactos
- Formulário.
- E-mail.
- Telefone.
- Horários.
- Localização apenas se os dados reais forem fornecidos.

/privacidade
- Política de privacidade.

/termos
- Termos de utilização.

/cookies
- Política de cookies.

Não inventar:

- Moradas.
- Telefones.
- Números de clientes.
- Anos de experiência.
- Certificações.
- Parceiros.
- Avaliações.
- Métricas.
- Preços.
- Nomes de profissionais.
- Garantias de resultado.

Usar placeholders claramente centralizados quando os dados reais não existirem.

==================================================
14. HOME PAGE
==================================================

A Home deve conter:

1. Header.
2. Hero.
3. Proposta de valor.
4. Serviços principais.
5. Diferenciais.
6. Como trabalhamos.
7. Apoio Portugal e Brasil.
8. Prova social, somente com dados reais.
9. FAQ resumida.
10. Call to action.
11. Footer completo.

Hero sugerido:

Título:

Contabilidade clara para decisões mais seguras.

Subtítulo:

A Veloma apoia empresas e profissionais com acompanhamento contabilístico próximo, organizado e adaptado à realidade de Portugal e Brasil.

CTAs:

Falar com a Veloma
Conhecer os serviços

Não usar frases exageradas como:

- A melhor contabilidade de Portugal.
- Garantimos economia.
- Zero impostos.
- Resultados garantidos.
- Revolucionamos o mercado.

==================================================
15. DESIGN
==================================================

Estilo:

- Moderno.
- Minimalista.
- Profissional.
- Tecnológico.
- Futurista sem parecer ficção científica.
- Seguro.
- Confiável.
- Espaçoso.
- Responsivo.

Evitar:

- Excesso de gradientes.
- Neon exagerado.
- Cards em todas as seções.
- Animações pesadas.
- Vídeos automáticos.
- Template genérico de startup.
- Imagens de banco excessivamente artificiais.
- Texto pequeno.
- Contraste fraco.
- Menus confusos.

Criar design tokens:

- Cores.
- Tipografia.
- Espaçamento.
- Border radius.
- Sombras.
- Larguras.
- Breakpoints.
- Estados de focus.
- Estados de erro.
- Estados de sucesso.

Todo o site deve funcionar em:

- Desktop.
- Tablet.
- Smartphone.
- Teclado.
- Leitor de tela.

==================================================
16. AUTENTICAÇÃO — TELAS
==================================================

Criar:

/entrar
/criar-conta
/verificar-email
/confirmar-login
/recuperar-password
/validar-recuperacao
/redefinir-password

Área autenticada:

/dashboard
/dashboard/perfil
/dashboard/seguranca
/dashboard/sessoes

Área STAFF:

/staff
/staff/perfil
/staff/seguranca
/staff/sessoes

Não criar funcionalidades empresariais falsas.

Nesta fase, os dashboards devem mostrar somente recursos do core:

- Dados do utilizador.
- Roles.
- Status.
- Último login.
- Segurança da conta.
- Alteração de password.
- Sessões ativas.
- Revogação de sessão.
- Encerrar outras sessões.
- Logout.
- Alertas de novo dispositivo, quando retornados.
- Estado geral do acesso.

O STAFF dashboard pode ter layout diferente, mas não deve fingir possuir gestão de clientes se não existir endpoint real.

==================================================
17. PROTEÇÃO DE ROTAS
==================================================

Criar middleware do Next.js para proteção inicial.

Porém:

- Middleware não substitui validação backend.
- Server Components protegidos devem validar sessão.
- Route Handlers devem validar access token.
- Em caso de access expirado, tentar refresh.
- Em caso de refresh inválido, limpar cookies.
- Redirecionar para /entrar.
- Evitar revelar páginas protegidas antes da validação.

Regras:

/staff/*
- Requer Group STAFF.
- Requer is_admin=false.

/dashboard/*
- Requer Group USER.
- Requer is_admin=false.

/entrar e /criar-conta
- Se autenticado, redirecionar conforme role.

/admin/
- Não pertence ao Next.js.
- Permanece exclusivamente no backend Django.

==================================================
18. SERVIÇO DE E-MAIL
==================================================

O backend já possui serviço reutilizável.

Modos:

sync
async
auto

Conteúdo:

HTML
TXT

Templates:

templates/emails/

Não criar subpastas dentro de templates/emails.

Não fixar nomes de template dentro do serviço.

Usar sempre o mecanismo por finalidade:

EmailService.send_by_purpose(
    purpose="...",
    recipients=[...],
    context={...},
)

O Admin configura:

- Purpose.
- Subject.
- HTML template.
- TXT template.
- Delivery mode.
- Vendor.
- Active.

Vendors configuráveis pelo Admin:

- SMTP.
- Console de desenvolvimento.
- Outros vendors somente se houver necessidade real e contrato desacoplado.

Credenciais devem continuar cifradas no banco.

Não remover a chave externa de cifragem.

O frontend nunca recebe credenciais de vendor.

==================================================
19. TEMPLATES DE E-MAIL
==================================================

O projeto já possui templates HTML e TXT para eventos como:

- Registo.
- OTP de registo.
- OTP de login.
- Recuperação de password.
- Password alterada.
- Conta ativada.
- Conta desativada.
- Conta bloqueada.
- Conta desbloqueada.
- Login bem-sucedido.
- Login falhado.
- Limite de tentativas.
- Brute force.
- Login suspeito.
- Novo IP.
- IP bloqueado.
- Novo país.
- País bloqueado.
- Novo dispositivo.
- Dispositivo desconhecido.
- User-Agent bloqueado.
- Sessão criada.
- Sessão expirada.
- Sessão revogada.
- Múltiplas sessões.
- Todas as sessões revogadas.
- Token expirado.
- Token revogado.
- Alerta de segurança.
- Rate limit.

Revisar todos os templates.

Garantir:

- HTML válido.
- Versão TXT equivalente.
- Design simples.
- Compatibilidade com clientes de e-mail.
- Sem JavaScript.
- Sem CSS externo.
- Sem informação sensível.
- Sem token exposto desnecessariamente.
- Context variables documentadas.
- Links baseados nos domínios corretos.

Links frontend:

https://veloma.app

Nunca enviar o utilizador para páginas inexistentes.

==================================================
20. DJANGO ADMIN
==================================================

Manter o Admin enxuto.

Mostrar somente duas áreas principais:

AUTHENTICATION

- Users.
- Groups.
- Authentication activity.
- OTP challenges.
- Password reset grants.
- User sessions.
- Access blocks.
- Security events.

CONFIGURATION

- Authentication settings.
- Security settings.
- Email settings.
- Email vendors.
- Email templates.
- Email delivery logs.

Regras:

- Logs devem ser read-only.
- OTPs devem ser read-only.
- Hashes nunca devem ser exibidos integralmente.
- Tokens nunca devem ser exibidos.
- Eventos devem ser read-only, com ação de resolver.
- Sessões devem permitir revogação controlada.
- Bloqueios devem permitir ativar e desativar.
- Vendors devem permitir teste.
- Não criar dashboard administrativo customizado.
- Não substituir Django Admin.
- Não instalar tema pesado sem necessidade.

==================================================
21. PRIMEIRA APLICAÇÃO APÓS O CORE
==================================================

Somente depois de todos os testes do core passarem, criar a primeira aplicação institucional:

app/website/

Responsabilidade mínima:

- Receber contactos do site.
- Validar formulário.
- Aplicar rate limit.
- Aplicar honeypot.
- Registar consentimento de privacidade.
- Enviar notificação por EmailService.
- Enviar confirmação ao visitante, quando configurado.
- Registar o pedido de contacto.
- Permitir consulta no Django Admin.
- Não transformar isso num CRM completo.

Endpoint sugerido:

POST /api/site/contact/

Campos:

name
email
phone opcional
company opcional
service opcional
message
privacy_accepted
website campo honeypot invisível

Segurança:

- Rate limit por IP.
- Limite de tamanho.
- Sanitização.
- Validação.
- Não renderizar HTML enviado pelo utilizador.
- Não aceitar anexos inicialmente.
- Não expor erros internos.
- Não enviar spam para o visitante.
- Não guardar dados além do necessário.

Templates:

templates/emails/website_contact.html
templates/emails/website_contact.txt
templates/emails/website_contact_confirmation.html
templates/emails/website_contact_confirmation.txt

Continuar sem criar subpastas.

==================================================
22. SEO
==================================================

Implementar:

- Metadata API do Next.js.
- Title único.
- Description única.
- Canonical.
- Open Graph.
- Twitter cards.
- sitemap.xml.
- robots.txt.
- JSON-LD para Organization.
- JSON-LD para ProfessionalService, somente com dados reais.
- Breadcrumbs.
- URLs limpas.
- Página 404.
- Página de erro.
- Favicon.
- Manifest básico.

Idioma principal:

pt-PT

Não misturar pt-BR nos textos institucionais.

Pode explicar que a equipa possui experiência nos contextos de Portugal e Brasil, sem escrever o site inteiro em português do Brasil.

==================================================
23. COOKIES E PRIVACIDADE
==================================================

Criar consentimento de cookies enxuto.

Não bloquear cookies estritamente necessários.

Categorias:

- Necessários.
- Analíticos, somente se forem realmente instalados.
- Marketing, somente se forem realmente instalados.

Não instalar Google Analytics, Meta Pixel ou outras ferramentas sem configuração explícita.

A política de privacidade deve explicar:

- Formulários.
- Dados de conta.
- Logs de segurança.
- IP.
- User-Agent.
- Sessões.
- Cookies.
- Retenção.
- Direitos do titular.
- Contacto.

Não inventar responsável de proteção de dados.

==================================================
24. DOCKER
==================================================

O Compose atual utiliza:

name: veloma-rc

Serviços atuais:

veloma-api
veloma-postgres
veloma-redis
veloma-celery
veloma-celery-beat
veloma-minio
veloma-minio-init

Adicionar somente depois do frontend funcionar:

veloma-app

Estrutura final:

veloma-rc
├── veloma-app
├── veloma-api
├── veloma-postgres
├── veloma-redis
├── veloma-celery
├── veloma-celery-beat
├── veloma-minio
└── veloma-minio-init

O serviço frontend deve:

- Usar Docker multi-stage.
- Executar Next.js em modo standalone.
- Expor internamente a porta 3000.
- Possuir healthcheck.
- Não publicar porta de banco.
- Não publicar Redis.
- Não publicar MinIO Console em produção.
- Não incluir NGINX.
- Não criar rede personalizada desnecessária.
- Permitir integração com Traefik do Coolify.

==================================================
25. COOLIFY E TRAEFIK
==================================================

Configurar no Coolify:

veloma.app
→ veloma-app:3000

www.veloma.app
→ redirecionar para https://veloma.app

api.veloma.app
→ veloma-api:8000

Não usar NGINX.

Traefik do Coolify será responsável por:

- Proxy reverso.
- HTTPS.
- Certificados.
- Domínios.
- Redirecionamentos.
- Comunicação externa.

PostgreSQL, Redis, Celery e MinIO devem permanecer internos.

Configuração CORS backend:

DJANGO_ALLOWED_HOSTS:
api.veloma.app

DJANGO_CORS_ALLOWED_ORIGINS:
https://veloma.app
https://www.veloma.app

DJANGO_CSRF_TRUSTED_ORIGINS:
https://api.veloma.app
https://veloma.app
https://www.veloma.app

Configuração frontend:

NEXT_PUBLIC_SITE_URL=https://veloma.app
BACKEND_API_URL=https://api.veloma.app

Para chamadas internas entre containers, usar o hostname do serviço somente quando a implantação permitir:

INTERNAL_BACKEND_API_URL=http://veloma-api:8000

Não expor INTERNAL_BACKEND_API_URL ao browser.

==================================================
26. .ENV
==================================================

Preservar o .env completo existente.

Adicionar variáveis do frontend de forma organizada.

Não remover chaves atuais.

Não substituir valores automaticamente sem documentar.

Criar:

frontend/.env.example

Não guardar segredo real em variável NEXT_PUBLIC_*.

Somente dados públicos podem usar NEXT_PUBLIC_*.

Segredos de cookies e BFF devem permanecer server-side.

Variáveis esperadas:

NEXT_PUBLIC_SITE_URL
BACKEND_API_URL
INTERNAL_BACKEND_API_URL
AUTH_COOKIE_SECURE
AUTH_COOKIE_SAMESITE
AUTH_ACCESS_COOKIE_NAME
AUTH_REFRESH_COOKIE_NAME
AUTH_SESSION_COOKIE_NAME

==================================================
27. PERFORMANCE E ECONOMIA
==================================================

O projeto deve ser rápido e económico.

Regras:

- Server Components por padrão.
- JavaScript cliente somente quando necessário.
- Imagens otimizadas.
- Fontes locais ou otimizadas.
- Lazy loading.
- Sem animações pesadas.
- Sem vídeos automáticos.
- Sem dependências duplicadas.
- Sem CMS nesta fase.
- Sem microserviços.
- Sem Kubernetes.
- Sem Elasticsearch.
- Sem filas adicionais além do Celery/Redis.
- Sem banco adicional.
- Sem serviço pago obrigatório.
- Sem API externa quando uma solução local simples resolver.
- Sem criar camada genérica para uma única utilização.

==================================================
28. ACESSIBILIDADE
==================================================

Garantir:

- HTML semântico.
- Labels reais.
- Mensagens de erro associadas aos campos.
- Navegação por teclado.
- Focus visível.
- Contraste adequado.
- aria-live para erros e confirmações.
- Não depender somente de cor.
- OTP acessível.
- Auto-focus sem prender o utilizador.
- Possibilidade de colar o OTP completo.
- Respeitar prefers-reduced-motion.

==================================================
29. TESTES BACKEND
==================================================

Executar e corrigir:

python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test

Testar:

- Register sem OTP.
- Register com OTP.
- OTP correto.
- OTP incorreto.
- OTP expirado.
- OTP usado.
- Reenvio.
- Cooldown.
- Limite de reenvio.
- Login.
- Login OTP.
- Login admin recusado.
- Login bloqueado.
- Password recovery.
- Reset token válido.
- Reset expirado.
- Reset usado duas vezes.
- Password change.
- Refresh.
- Rotação.
- Blacklist.
- Logout.
- Logout all.
- Limite de sessões.
- Revogação de sessão.
- Bloqueio por user.
- Bloqueio por IP.
- Bloqueio por país.
- Bloqueio por User-Agent.
- Rate limiting.
- E-mail sync.
- E-mail async.
- E-mail auto.
- Vendor padrão.
- Vendor fallback.
- Templates HTML e TXT.
- Limpeza de registros antigos.

==================================================
30. TESTES FRONTEND
==================================================

Executar:

npm run lint
npm run typecheck
npm run build

Criar testes end-to-end dos fluxos críticos com Playwright:

- Registo.
- Verificação de e-mail.
- Login.
- Login OTP.
- Recuperação.
- Reset.
- Redirecionamento USER.
- Redirecionamento STAFF.
- Bloqueio de acesso cruzado.
- Logout.
- Logout de todas as sessões.
- Revogação de sessão.
- Refresh automático.
- Token inválido.
- Sessão expirada.
- Formulário de contacto.
- Responsividade básica.

Não criar centenas de testes superficiais.

Priorizar fluxos críticos.

==================================================
31. OBSERVABILIDADE E DEBUG
==================================================

Manter logs estruturados no backend.

Não imprimir:

- Password.
- OTP.
- Access token.
- Refresh token.
- Reset token.
- SMTP password.
- Chaves de cifragem.
- Cookies.

Adicionar correlation/request ID se ainda não existir e se puder ser implementado sem quebrar o core.

Frontend deve:

- Exibir mensagem amigável.
- Registar erro técnico apenas no servidor.
- Não mostrar stack trace.
- Não mostrar resposta crua do backend.
- Não esconder erros críticos durante desenvolvimento.

==================================================
32. CRITÉRIOS DE ACEITE
==================================================

O trabalho somente estará concluído quando:

[ ] O backend subir sem erro.
[ ] Migrations forem aplicadas.
[ ] Bootstrap funcionar.
[ ] Django Admin funcionar.
[ ] Todos os testes backend passarem.
[ ] Todos os endpoints de autenticação funcionarem.
[ ] OTP for de uso único.
[ ] Reset token for de uso único.
[ ] Sessões puderem ser listadas e revogadas.
[ ] Admin não conseguir autenticar no frontend.
[ ] STAFF não acessar dashboard USER.
[ ] USER não acessar dashboard STAFF.
[ ] Tokens não forem guardados em localStorage.
[ ] Refresh funcionar por cookie HttpOnly.
[ ] Logout limpar e revogar a sessão.
[ ] Site institucional estiver responsivo.
[ ] Formulário de contacto funcionar.
[ ] E-mail HTML e TXT funcionar.
[ ] Docker Compose funcionar.
[ ] veloma.app abrir o frontend.
[ ] api.veloma.app abrir a API.
[ ] /admin/ funcionar apenas no backend.
[ ] Swagger funcionar.
[ ] Healthchecks estiverem verdes.
[ ] Lint, typecheck e build passarem.
[ ] Não existir CustomUser.
[ ] Não existir NGINX.
[ ] Não existir módulo de negócio falso.

==================================================
33. ORDEM OBRIGATÓRIA DE ENTREGA
==================================================

FASE 1 — AUDITORIA

- Inspecionar projeto.
- Listar problemas reais.
- Não alterar arquitetura sem justificativa.

FASE 2 — CORE BACKEND

- Subir containers.
- Corrigir erros.
- Validar migrations.
- Validar Admin.
- Validar autenticação.
- Validar segurança.
- Validar e-mails.
- Executar testes.

FASE 3 — CONTRATO DA API

- Conferir OpenAPI.
- Documentar responses.
- Gerar tipos TypeScript.
- Não inventar endpoints.

FASE 4 — FRONTEND DE AUTENTICAÇÃO

- Criar BFF.
- Cookies HttpOnly.
- Fluxos completos.
- Proteção de rotas.
- Sessões.
- Perfil.
- Segurança.

FASE 5 — SITE INSTITUCIONAL

- Home.
- Sobre.
- Serviços.
- Como trabalhamos.
- FAQ.
- Contactos.
- Páginas legais.
- SEO.
- Acessibilidade.

FASE 6 — PRIMEIRA APP

- Criar app/website somente agora.
- Implementar contacto.
- Reutilizar EmailService.
- Adicionar Admin mínimo.
- Testar.

FASE 7 — DOCKER E COOLIFY

- Adicionar veloma-app.
- Healthcheck.
- Configuração de domínios.
- Traefik.
- Sem NGINX.

FASE 8 — VALIDAÇÃO FINAL

- Backend tests.
- Frontend lint.
- Typecheck.
- Build.
- E2E.
- Docker.
- Documentação.

==================================================
34. ENTREGA
==================================================

Ao concluir, entregar:

1. Projeto completo atualizado.
2. Frontend dentro de frontend/.
3. Backend preservado e corrigido.
4. docker-compose.yml atualizado.
5. .env.example atualizado.
6. frontend/.env.example.
7. Migrations.
8. Testes.
9. README.md atualizado.
10. Documentação de arquitetura.
11. Lista de endpoints.
12. Lista de variáveis.
13. Comandos de execução.
14. Configuração Coolify.
15. Credenciais de desenvolvimento documentadas sem expor segredos em produção.
16. Relatório objetivo do que foi alterado.
17. Lista de decisões técnicas.
18. Lista de limitações reais.
19. ZIP final do projeto, sem caches e sem node_modules.

==================================================
35. COMANDOS ESPERADOS
==================================================

Backend:

cd /Users/cosmeaf/projects/veloma

docker compose \
  -f docker-compose.yml \
  -f docker-compose.local.yml \
  up -d --build

docker exec -it veloma-api python manage.py check
docker exec -it veloma-api python manage.py migrate
docker exec -it veloma-api python manage.py bootstrap_veloma
docker exec -it veloma-api python manage.py test

Frontend:

cd /Users/cosmeaf/projects/veloma/frontend

npm install
npm run lint
npm run typecheck
npm run build
npm run dev

Projeto completo:

cd /Users/cosmeaf/projects/veloma

docker compose up -d --build

==================================================
36. COMPORTAMENTO ESPERADO DE VOCÊ
==================================================

- Trabalhe diretamente nos ficheiros.
- Não entregue somente exemplos.
- Não entregue somente arquitetura.
- Não crie ficheiros vazios.
- Não simule implementação.
- Não escreva TODO no lugar de código funcional.
- Não apague recursos existentes sem justificar.
- Não complique a estrutura.
- Não peça confirmação para cada etapa.
- Faça escolhas técnicas coerentes quando faltar detalhe menor.
- Documente qualquer suposição.
- Preserve o backend existente.
- Corrija falhas reais.
- Reutilize os serviços existentes.
- Seja económico em dependências e infraestrutura.
- Entregue código funcional, testado e organizado.
```
