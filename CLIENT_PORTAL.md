```text
PROMPT — NOVO MÓDULO CLIENT PORTAL DA VELOMA

Atue como arquiteto de software e programador sénior especializado em Django, Django REST Framework, Next.js, PostgreSQL, Redis, Celery, MinIO, segurança, auditoria e sistemas de gestão documental.

Trabalhe diretamente no projeto existente:

/Users/cosmeaf/projects/veloma

DOMÍNIOS

Frontend:
https://veloma.app

Backend:
https://api.veloma.app

Django Admin:
https://api.veloma.app/admin/

==================================================
1. OBJETIVO
==================================================

Criar o primeiro módulo de negócio da Veloma:

app/client_portal/

O módulo será uma Área de Membro para um escritório de contabilidade.

O sistema permitirá:

1. Staff cadastrar clientes.
2. Staff enviar convites de acesso.
3. Cliente aceitar o convite e criar a conta.
4. Cliente preencher os seus dados contabilísticos de Portugal.
5. Staff criar pedidos ou protocolos.
6. Cliente enviar documentos dentro dos protocolos.
7. Staff organizar, analisar, enviar e descarregar documentos.
8. Cliente acompanhar o andamento de cada pedido.
9. Cliente e staff comunicarem dentro do protocolo.
10. Todo acesso, alteração, upload e download gerar auditoria.
11. Contas poderem ser desativadas ou excluídas logicamente.
12. Nenhum documento, protocolo ou histórico ser apagado acidentalmente.

Não criar vários apps Django.

Criar somente:

app/client_portal/

Internamente, organizar o módulo por responsabilidades.

==================================================
2. REGRAS QUE NÃO PODEM SER QUEBRADAS
==================================================

Não criar CustomUser.

Não configurar AUTH_USER_MODEL.

Não substituir User, Group ou Permission do Django.

Continuar utilizando:

django.contrib.auth.models.User
django.contrib.auth.models.Group
django.contrib.auth.models.Permission

Não alterar internamente o funcionamento do Django Admin.

Não duplicar o sistema de autenticação existente.

Não criar novo sistema JWT.

Não criar novo serviço de e-mail.

Não criar novo serviço de MinIO se já existir uma abstração reutilizável.

Não colocar protocolos, documentos e pastas dentro de config/authentication.

Não apagar fisicamente utilizadores, clientes, protocolos, documentos, comentários ou auditorias.

Não utilizar CASCADE em dados históricos ou contabilísticos.

Não criar microserviços.

Não adicionar NGINX.

Não criar frontend com dados simulados.

Não criar endpoints que não sejam realmente implementados.

==================================================
3. SEPARAÇÃO ENTRE CORE E MÓDULO
==================================================

O projeto deve manter esta divisão:

veloma/
├── config/
│   ├── authentication/
│   ├── iam/
│   ├── security/
│   └── common/
│
└── app/
    └── client_portal/

Responsabilidades:

config/authentication/
- Login.
- OTP.
- Password reset.
- JWT.
- Sessões.
- Criação de User.
- Ativação de conta.
- Desativação de conta.
- Exclusão lógica da conta.
- Revogação de sessões.
- Ciclo de vida do utilizador.

config/iam/
- Groups nativos.
- Permissions nativas.
- RBAC.
- STAFF.
- USER.
- Permissões de acesso.

config/security/
- IP.
- User-Agent.
- Dispositivo.
- País.
- Rate limit.
- Bloqueios.
- Auditoria de segurança.
- IP Intelligence.

config/common/
- Serviço de e-mail.
- Vendors SMTP.
- Celery.
- MinIO.
- Respostas da API.
- Exceções.
- Serviços reutilizáveis.

app/client_portal/
- Clientes contabilísticos.
- Membros.
- Convites.
- Protocolos.
- Documentos.
- Pastas.
- Comentários.
- Histórico operacional.
- Dashboard do staff.
- Dashboard do cliente.

==================================================
4. REGISTO SOMENTE POR CONVITE
==================================================

Desativar o registo público.

O endpoint público de register não deve permitir a criação direta de contas.

Configuração:

public_registration_enabled = false

Uma conta USER somente poderá ser criada através de um convite válido.

Fluxo:

STAFF
    │
    ▼
Cadastra o cliente
    │
    ▼
Envia convite para um e-mail
    │
    ▼
Cliente recebe link de uso único
    │
    ▼
Cliente valida o convite
    │
    ▼
Cliente completa os dados
    │
    ▼
config/authentication cria o User nativo
    │
    ▼
app/client_portal cria o ClientMember
    │
    ▼
Cliente entra na Área de Membro

O convite deverá possuir:

- UUID público.
- Token secreto aleatório.
- Hash do token armazenado.
- E-mail convidado.
- Cliente associado.
- Função do membro.
- Staff responsável pelo convite.
- Data de criação.
- Data de expiração.
- Data de aceitação.
- Data de revogação.
- Estado.
- Número de reenvios.
- Último envio.
- IP de aceitação.
- User-Agent de aceitação.

Estados:

pending
accepted
expired
revoked
cancelled

O token deve ser:

- Aleatório.
- Opaco.
- De alta entropia.
- De uso único.
- Armazenado somente como hash.
- Invalidado após a utilização.
- Invalidado após revogação.
- Invalidado após a expiração.

Link:

https://veloma.app/convite/aceitar?token=TOKEN_OPACO

Não colocar ID do cliente ou ID do utilizador no link.

==================================================
5. ACEITAÇÃO DO CONVITE
==================================================

Tela frontend:

/convite/aceitar

Primeiro, validar o token no backend.

Depois solicitar:

- first_name
- last_name
- email bloqueado ou somente leitura
- password
- password2
- telefone
- cargo ou função
- aceitação dos termos
- aceitação da política de privacidade

O backend deverá:

1. Validar o convite.
2. Confirmar que não expirou.
3. Confirmar que não foi utilizado.
4. Confirmar que não foi revogado.
5. Confirmar que o e-mail ainda não possui conta incompatível.
6. Normalizar o e-mail.
7. Criar o User nativo do Django.
8. Definir username igual ao e-mail.
9. Definir email igual ao e-mail.
10. Adicionar o User ao Group USER.
11. Criar o ClientMember.
12. Marcar o convite como accepted.
13. Registar IP e User-Agent.
14. Criar evento de auditoria.
15. Enviar confirmação por EmailService.
16. Executar tudo dentro de transaction.atomic.

Não duplicar a criação de utilizador.

Usar um serviço existente ou criar um serviço reutilizável dentro de config/authentication.

==================================================
6. CLIENTE CONTABILÍSTICO
==================================================

Criar o model Client.

Client representa a empresa, entidade ou profissional acompanhado pela Veloma.

Campos sugeridos:

Client
- id UUID.
- legal_name.
- commercial_name.
- nif.
- entity_type.
- activity_code.
- activity_description.
- email.
- phone.
- website.
- address_line.
- postal_code.
- city.
- district.
- country.
- accounting_period_start.
- accounting_period_end.
- assigned_staff.
- status.
- is_active.
- archived_at.
- archived_by.
- archive_reason.
- created_at.
- updated_at.

Tipos de entidade configuráveis:

- Sociedade por quotas.
- Sociedade unipessoal.
- Empresário em nome individual.
- Trabalhador independente.
- Associação.
- Fundação.
- Condomínio.
- Outro.

Não fixar toda a lógica em choices imutáveis se os tipos precisarem ser administrados no futuro.

NIF:

- Guardar como string.
- Não converter para inteiro.
- Validar formato.
- Criar restrição de unicidade quando aplicável.
- Permitir exceção administrativa documentada quando necessário.

==================================================
7. MEMBROS DO CLIENTE
==================================================

Criar ClientMember.

Uma empresa pode ter vários utilizadores.

ClientMember
- id UUID.
- client.
- user.
- role.
- position.
- phone.
- preferred_language.
- can_upload.
- can_download.
- can_view_protocols.
- can_comment.
- can_manage_members.
- status.
- joined_at.
- deactivated_at.
- archived_at.
- created_at.
- updated_at.

Restrições:

- Um utilizador não pode possuir dois vínculos ativos idênticos com o mesmo cliente.
- Um utilizador pode pertencer a mais de um cliente quando autorizado.
- A API deve sempre filtrar dados pelos ClientMembers do utilizador.
- Nunca confiar no client_id enviado pelo frontend sem validar o vínculo.

Funções sugeridas:

owner
manager
accounting
employee
viewer

Não confundir essas funções com os Groups globais STAFF e USER.

==================================================
8. GRUPOS E PERMISSÕES
==================================================

Usar Groups nativos:

STAFF_MANAGER
STAFF
USER

STAFF_MANAGER:

- Vê todos os clientes.
- Convida membros.
- Atribui staff.
- Cria protocolos.
- Reabre protocolos.
- Arquiva clientes.
- Restaura clientes.
- Consulta auditoria completa.

STAFF:

- Vê somente clientes atribuídos ou permitidos.
- Cria e atualiza protocolos autorizados.
- Solicita documentos.
- Faz upload e download.
- Adiciona comentários públicos.
- Adiciona notas internas.
- Altera estados permitidos.

USER:

- Vê somente clientes aos quais pertence.
- Vê protocolos autorizados.
- Faz upload de documentos.
- Descarrega documentos disponibilizados.
- Envia comentários públicos.
- Acompanha o andamento.
- Não vê notas internas.

O Django Admin utiliza is_staff=True e não deve usar esses dashboards.

==================================================
9. PROTOCOLOS
==================================================

Criar Protocol.

O protocolo representa um pedido contabilístico, uma solicitação ou um processo.

Não criar um protocolo para cada ficheiro.

Um protocolo pode conter vários documentos.

Campos:

Protocol
- id UUID.
- number.
- client.
- created_by.
- assigned_to.
- title.
- description.
- category.
- priority.
- status.
- competence_month.
- competence_year.
- due_date.
- started_at.
- completed_at.
- closed_at.
- cancelled_at.
- archived_at.
- created_at.
- updated_at.

Número público:

VEL-2026-000001

Não expor ID sequencial.

Gerar o número de forma segura contra concorrência.

Categorias sugeridas:

- Contabilidade mensal.
- IVA.
- IRC.
- IRS.
- Processamento salarial.
- Recursos humanos.
- Abertura de empresa.
- Encerramento de empresa.
- Alteração societária.
- Fiscalidade.
- Bancos.
- Contratos.
- Pedido documental.
- Outro.

Estados internos:

draft
waiting_documents
documents_received
under_review
action_required
processing
completed
cancelled
archived

Estados mostrados ao cliente:

- Aguardando documentos.
- Documentos recebidos.
- Em análise.
- Precisamos de informações.
- Em processamento.
- Concluído.
- Cancelado.

Criar transições válidas.

Não permitir alteração arbitrária de qualquer estado para qualquer estado.

Exemplo:

draft
→ waiting_documents

waiting_documents
→ documents_received
→ cancelled

documents_received
→ under_review
→ action_required

under_review
→ action_required
→ processing
→ completed

action_required
→ documents_received
→ under_review

processing
→ completed
→ action_required

completed
→ archived
→ reaberto somente por STAFF_MANAGER

==================================================
10. HISTÓRICO DO PROTOCOLO
==================================================

Criar ProtocolEvent.

Campos:

- protocol.
- event_type.
- actor.
- actor_name_snapshot.
- actor_email_snapshot.
- old_value.
- new_value.
- metadata.
- IP.
- User-Agent.
- created_at.

Eventos:

protocol_created
protocol_updated
status_changed
staff_assigned
due_date_changed
document_requested
document_uploaded
document_downloaded
document_replaced
document_rejected
folder_created
comment_added
internal_note_added
protocol_completed
protocol_reopened
protocol_cancelled
protocol_archived

O cliente vê um histórico simplificado.

O staff vê o histórico completo.

Eventos históricos devem ser somente leitura.

==================================================
11. COMENTÁRIOS
==================================================

Criar ProtocolComment.

Campos:

- id UUID.
- protocol.
- author.
- author_name_snapshot.
- author_email_snapshot.
- message.
- visibility.
- is_edited.
- edited_at.
- archived_at.
- created_at.
- updated_at.

Visibilidade:

public
- Visível para cliente e staff.

internal
- Visível somente para staff.

O frontend nunca deve receber comentários internal numa resposta destinada a USER.

Não confiar somente em ocultação visual.

Filtrar no queryset e serializer.

Não permitir HTML arbitrário.

Guardar texto puro ou Markdown estritamente sanitizado.

==================================================
12. ESTRUTURA DE PASTAS
==================================================

Criar ClientFolder.

A estrutura será lógica e armazenada no PostgreSQL.

Campos:

- id UUID.
- client.
- protocol opcional.
- parent opcional.
- name.
- slug.
- folder_type.
- year opcional.
- month opcional.
- created_by.
- archived_at.
- created_at.
- updated_at.

Estrutura inicial sugerida:

Clientes/
└── Nome do cliente/
    ├── 2026/
    │   ├── 01_Janeiro/
    │   │   ├── Compras/
    │   │   ├── Vendas/
    │   │   ├── Bancos/
    │   │   ├── Recibos/
    │   │   └── Outros/
    │   └── ...
    ├── Contratos/
    ├── Fiscal/
    ├── Recursos_Humanos/
    └── Documentos_Permanentes/

Não criar essa estrutura como diretórios físicos locais.

O MinIO deve usar chaves técnicas.

Exemplo:

clients/{client_uuid}/protocols/{protocol_uuid}/documents/{document_uuid}/versions/{version_uuid}

Nunca utilizar diretamente nomes de clientes na chave permanente.

==================================================
13. DOCUMENTOS
==================================================

Criar Document.

Campos:

- id UUID.
- client.
- protocol.
- folder.
- title.
- original_name.
- current_version.
- category.
- status.
- visibility.
- uploaded_by.
- uploader_name_snapshot.
- uploader_email_snapshot.
- archived_at.
- created_at.
- updated_at.

Estados:

pending_upload
pending_scan
clean
infected
quarantined
rejected
available
archived

Visibilidade:

client_and_staff
staff_only
client_only quando houver necessidade válida

Criar DocumentVersion.

Campos:

- id UUID.
- document.
- version_number.
- storage_key.
- original_name.
- content_type.
- detected_mime_type.
- size.
- checksum_sha256.
- uploaded_by.
- uploader_name_snapshot.
- uploader_email_snapshot.
- scan_status.
- scan_message.
- change_reason.
- created_at.

Nunca substituir fisicamente a versão anterior.

Cada substituição cria nova versão.

Não permitir colisões de nome.

Não confiar em extensão.

==================================================
14. UPLOAD SEGURO
==================================================

Tipos iniciais permitidos:

PDF
XML
CSV
XLS
XLSX
DOC
DOCX
JPG
JPEG
PNG
ZIP

Configurar pelo Admin:

- Tipos permitidos.
- Tamanho máximo.
- Quantidade máxima por protocolo.
- Permitir ZIP.
- Exigir antivírus.
- Tempo de URL assinada.
- Retenção de quarentena.

Fluxo:

1. Validar autorização.
2. Validar tamanho.
3. Validar nome.
4. Validar extensão.
5. Detetar MIME real.
6. Calcular SHA-256.
7. Verificar duplicação.
8. Armazenar em área temporária ou quarentena.
9. Criar DocumentVersion.
10. Enviar scan para Celery.
11. Executar antivírus.
12. Se clean, disponibilizar.
13. Se infected, manter em quarentena.
14. Gerar evento.
15. Notificar staff ou cliente.

Adicionar ClamAV ao Docker Compose:

veloma-clamav

Não servir documentos infectados.

Não executar macros.

Não extrair ZIP automaticamente sem proteção contra:

- Zip Slip.
- Zip bomb.
- Profundidade excessiva.
- Número excessivo de ficheiros.
- Tamanho descompactado excessivo.

Na primeira versão, ZIP pode ser armazenado e analisado, sem extração automática.

==================================================
15. MINIO
==================================================

Utilizar o MinIO existente.

Regras:

- Bucket privado.
- Nenhum ficheiro público.
- Credenciais somente no backend.
- Frontend nunca recebe credenciais MinIO.
- Download somente após validação de permissão.
- Usar URL assinada com validade curta.
- Registar todo download.
- Não utilizar URL permanente.
- Não expor Console MinIO publicamente em produção.
- Criar buckets automaticamente quando necessário.

Serviço reutilizável:

StorageService.upload(...)
StorageService.download_url(...)
StorageService.delete(...)
StorageService.copy(...)
StorageService.exists(...)
StorageService.metadata(...)

Não espalhar chamadas diretas ao SDK do MinIO por views e serializers.

==================================================
16. DOWNLOAD
==================================================

Fluxo:

1. Frontend solicita download ao backend.
2. Backend valida autenticação.
3. Backend valida vínculo com o cliente.
4. Backend valida permissão no documento.
5. Backend valida scan_status=clean.
6. Backend cria URL assinada curta.
7. Backend cria DownloadAudit.
8. Frontend utiliza a URL.
9. URL expira automaticamente.

Criar DownloadAudit:

- document.
- version.
- user.
- user_name_snapshot.
- client.
- IP.
- User-Agent.
- created_at.

==================================================
17. SOLICITAÇÃO DE DOCUMENTOS
==================================================

Staff deve poder criar uma lista de documentos solicitados dentro do protocolo.

Criar ProtocolRequirement.

Campos:

- protocol.
- title.
- description.
- category.
- required.
- due_date.
- status.
- fulfilled_by_document.
- created_by.
- completed_at.
- created_at.

Estados:

pending
uploaded
accepted
rejected
waived

Exemplo:

Protocolo:
Documentos mensais — Julho/2026

Itens solicitados:

[ ] Extrato bancário
[ ] Faturas de compra
[ ] Faturas de venda
[ ] Recibos
[ ] Comprovativos de pagamento

O cliente deve conseguir visualizar claramente o que falta.

==================================================
18. PAINEL DO CLIENTE
==================================================

Criar rotas frontend:

/dashboard
/dashboard/protocolos
/dashboard/protocolos/[id]
/dashboard/documentos
/dashboard/empresa
/dashboard/membros
/dashboard/perfil
/dashboard/seguranca
/dashboard/sessoes

Dashboard:

- Protocolos em aberto.
- Aguardando documentos.
- Em análise.
- Ação necessária.
- Concluídos.
- Últimas atualizações.
- Próximos prazos.
- Documentos solicitados.

Detalhe do protocolo:

- Número.
- Título.
- Categoria.
- Estado.
- Prazo.
- Responsável.
- Linha do tempo.
- Lista de documentos solicitados.
- Upload.
- Documentos enviados.
- Documentos disponibilizados.
- Comentários públicos.
- Histórico simplificado.

Não mostrar:

- Notas internas.
- Logs técnicos.
- IPs.
- User-Agents.
- Risco.
- Dados de outros clientes.
- Documentos staff_only.

==================================================
19. PAINEL DO STAFF
==================================================

Criar rotas:

/staff
/staff/clientes
/staff/clientes/[id]
/staff/clientes/[id]/membros
/staff/convites
/staff/protocolos
/staff/protocolos/[id]
/staff/documentos
/staff/perfil
/staff/seguranca
/staff/sessoes

Dashboard:

- Novos protocolos.
- Aguardando análise.
- Aguardando cliente.
- Atrasados.
- Ação necessária.
- Concluídos recentemente.
- Uploads pendentes de scan.
- Ficheiros em quarentena.
- Convites pendentes.
- Convites expirados.

Clientes:

- Criar cliente.
- Editar cliente.
- Desativar cliente.
- Excluir logicamente cliente.
- Restaurar cliente.
- Atribuir staff.
- Listar membros.
- Enviar convite.
- Revogar convite.

Protocolos:

- Criar.
- Editar.
- Atribuir responsável.
- Alterar estado.
- Definir prioridade.
- Definir prazo.
- Solicitar documentos.
- Adicionar comentário público.
- Adicionar nota interna.
- Enviar documentos.
- Concluir.
- Reabrir com permissão.
- Arquivar.

Documentos:

- Navegar por cliente.
- Navegar por ano.
- Navegar por competência.
- Navegar por pasta.
- Upload.
- Download.
- Versionar.
- Mover.
- Classificar.
- Rejeitar.
- Arquivar.
- Consultar histórico.

==================================================
20. DESATIVAÇÃO E EXCLUSÃO LÓGICA
==================================================

Existirão duas ações reais:

DESATIVAR
EXCLUIR

Desativar:

- Temporário.
- Reversível.
- Mantém visível.
- user.is_active=False.
- Revoga todas as sessões.
- Invalida tokens.
- Cancela OTPs.
- Cancela resets.
- Impede login.
- Mantém documentos.
- Mantém protocolos.
- Mantém auditoria.

Excluir:

- Exclusão lógica.
- user.is_active=False.
- Arquiva a conta.
- Oculta das listas normais.
- Revoga sessões.
- Invalida tokens.
- Cancela OTPs.
- Cancela resets.
- Cancela convites pendentes.
- Preserva documentos.
- Preserva protocolos.
- Preserva comentários.
- Preserva auditoria.
- Mostra somente no filtro Arquivados.
- Restauração somente por administrador autorizado.

Não criar botão de exclusão física.

Remover a ação nativa:

Delete selected users

Bloquear exclusão física individual no Admin.

==================================================
21. ACCOUNT LIFECYCLE
==================================================

Criar AccountLifecycle relacionado ao User nativo.

Campos:

- user.
- status.
- deactivated_at.
- deactivated_by.
- deactivation_reason.
- archived_at.
- archived_by.
- archive_reason.
- restored_at.
- restored_by.
- updated_at.

Estados:

active
deactivated
archived

Criar serviço:

AccountLifecycleService.deactivate(...)
AccountLifecycleService.archive(...)
AccountLifecycleService.reactivate(...)
AccountLifecycleService.restore(...)

O serviço deve:

- Usar transaction.atomic.
- Alterar user.is_active.
- Revogar sessões.
- Invalidar tokens.
- Cancelar OTPs.
- Cancelar resets.
- Cancelar convites.
- Criar AuthenticationActivity.
- Criar SecurityEvent.
- Criar auditoria no client_portal.
- Enviar e-mail configurável.
- Nunca apagar o User.

==================================================
22. CLIENT LIFECYCLE
==================================================

Cliente também possui:

active
deactivated
archived

Desativar cliente:

- Bloquear novos logins dos membros relacionados, conforme configuração.
- Bloquear novos uploads.
- Bloquear criação de protocolos.
- Manter dados visíveis ao staff.
- Manter protocolos em leitura.
- Manter documentos.
- Permitir reativação.

Excluir cliente:

- Exclusão lógica.
- Arquivar cliente.
- Arquivar vínculos ativos.
- Desativar membros.
- Cancelar convites.
- Preservar protocolos.
- Preservar documentos.
- Preservar comentários.
- Preservar auditoria.
- Ocultar das listas normais.
- Permitir restauração autorizada.

Criar ClientLifecycleService.

==================================================
23. POLÍTICA DE ON_DELETE
==================================================

Não usar CASCADE em dados históricos.

Usar:

OTPChallenge.user
- CASCADE.

PasswordResetGrant.user
- CASCADE.

UserSession.user
- CASCADE.

AuthenticationActivity.user
- SET_NULL.

SecurityEvent.user
- SET_NULL.

ClientMember.user
- PROTECT.

ClientMember.client
- PROTECT.

ClientInvitation.invited_by
- SET_NULL.

ClientInvitation.accepted_by
- SET_NULL.

Protocol.client
- PROTECT.

Protocol.created_by
- SET_NULL.

Protocol.assigned_to
- SET_NULL.

ProtocolComment.author
- SET_NULL.

ProtocolEvent.actor
- SET_NULL.

Document.uploaded_by
- SET_NULL.

DocumentVersion.uploaded_by
- SET_NULL.

DownloadAudit.user
- SET_NULL.

Não depender somente dessas proteções.

A exclusão física deve ser bloqueada nos serviços, API e Admin.

==================================================
24. ADMIN DO DJANGO
==================================================

Manter o Admin enxuto.

O core continua organizado em:

AUTHENTICATION
CONFIGURATION

O novo módulo deve aparecer como:

CLIENT PORTAL

Entradas:

- Clients.
- Client members.
- Invitations.
- Protocols.
- Documents.
- Folders.

Não mostrar cada tabela auxiliar como entrada independente.

Usar inlines e filtros.

Exemplo:

Protocol Admin
- Dados principais.
- Requirements inline.
- Comments inline com cuidado.
- Events somente leitura.
- Documents relacionados.
- Filtros por estado, cliente, staff, categoria e prazo.
- Pesquisa por número, título, NIF e cliente.

Document Admin
- Metadados.
- Versões inline somente leitura.
- Scan status.
- Download controlado.
- Quarentena.
- Auditoria.

Client Admin
- Dados.
- Membros inline.
- Convites inline.
- Staff atribuído.
- Protocolos relacionados.
- Desativar.
- Excluir logicamente.
- Restaurar.

Logs, eventos e versões devem ser read-only.

==================================================
25. NOTIFICAÇÕES E E-MAILS
==================================================

Reutilizar EmailService existente.

Finalidades:

client_invitation
client_invitation_reminder
client_invitation_accepted
client_account_deactivated
client_account_archived
client_account_restored
protocol_created
protocol_status_changed
documents_requested
document_uploaded
document_available
document_rejected
staff_public_comment
client_public_comment
client_action_required
protocol_completed
protocol_reopened

Criar templates diretamente em:

templates/emails/

Sem subpastas.

Exemplos:

client_invitation.html
client_invitation.txt
protocol_created.html
protocol_created.txt
documents_requested.html
documents_requested.txt
document_uploaded.html
document_uploaded.txt
protocol_completed.html
protocol_completed.txt

Não fixar nomes no serviço de e-mail.

Configurar pelo EmailTemplate no Admin.

==================================================
26. CELERY
==================================================

Utilizar Celery para:

- Envio de convites.
- Reenvio de convites.
- Lembrete de convites.
- Scan antivírus.
- Processamento de metadados.
- Cálculo de checksum em ficheiros grandes quando necessário.
- Notificações.
- Limpeza de uploads temporários.
- Expiração de convites.
- Limpeza de URLs temporárias, se aplicável.
- Retenção e arquivamento.
- Alertas de protocolos atrasados.

Utilizar Celery Beat para:

- Marcar convites expirados.
- Enviar lembretes.
- Localizar protocolos atrasados.
- Limpar ficheiros temporários.
- Aplicar políticas de retenção.
- Reprocessar scans falhados com limite.

Não executar tarefas pesadas durante a request.

==================================================
27. ENDPOINTS DA API
==================================================

Criar endpoints reais e documentados.

Convites:

POST   /api/client-portal/invitations/
GET    /api/client-portal/invitations/
GET    /api/client-portal/invitations/{id}/
POST   /api/client-portal/invitations/{id}/resend/
POST   /api/client-portal/invitations/{id}/revoke/
POST   /api/client-portal/invitations/validate/
POST   /api/client-portal/invitations/accept/

Clientes:

GET    /api/client-portal/clients/
POST   /api/client-portal/clients/
GET    /api/client-portal/clients/{id}/
PATCH  /api/client-portal/clients/{id}/
POST   /api/client-portal/clients/{id}/deactivate/
POST   /api/client-portal/clients/{id}/archive/
POST   /api/client-portal/clients/{id}/restore/

Membros:

GET    /api/client-portal/clients/{client_id}/members/
GET    /api/client-portal/members/{id}/
PATCH  /api/client-portal/members/{id}/
POST   /api/client-portal/members/{id}/deactivate/
POST   /api/client-portal/members/{id}/archive/
POST   /api/client-portal/members/{id}/restore/

Protocolos:

GET    /api/client-portal/protocols/
POST   /api/client-portal/protocols/
GET    /api/client-portal/protocols/{id}/
PATCH  /api/client-portal/protocols/{id}/
POST   /api/client-portal/protocols/{id}/transition/
POST   /api/client-portal/protocols/{id}/assign/
POST   /api/client-portal/protocols/{id}/complete/
POST   /api/client-portal/protocols/{id}/reopen/
POST   /api/client-portal/protocols/{id}/archive/
GET    /api/client-portal/protocols/{id}/timeline/

Requirements:

GET    /api/client-portal/protocols/{id}/requirements/
POST   /api/client-portal/protocols/{id}/requirements/
PATCH  /api/client-portal/requirements/{id}/

Comentários:

GET    /api/client-portal/protocols/{id}/comments/
POST   /api/client-portal/protocols/{id}/comments/
PATCH  /api/client-portal/comments/{id}/
POST   /api/client-portal/comments/{id}/archive/

Pastas:

GET    /api/client-portal/folders/
POST   /api/client-portal/folders/
GET    /api/client-portal/folders/{id}/
PATCH  /api/client-portal/folders/{id}/
POST   /api/client-portal/folders/{id}/move/
POST   /api/client-portal/folders/{id}/archive/

Documentos:

GET    /api/client-portal/documents/
POST   /api/client-portal/documents/upload/
GET    /api/client-portal/documents/{id}/
POST   /api/client-portal/documents/{id}/new-version/
POST   /api/client-portal/documents/{id}/move/
POST   /api/client-portal/documents/{id}/archive/
POST   /api/client-portal/documents/{id}/reject/
POST   /api/client-portal/documents/{id}/download/
GET    /api/client-portal/documents/{id}/versions/

Não criar DELETE físico.

Utilizar ações explícitas:

deactivate
archive
restore
revoke

==================================================
28. SERIALIZERS E SEGURANÇA
==================================================

Não usar um serializer gigante.

Separar:

- List serializer.
- Detail serializer.
- Create serializer.
- Update serializer.
- Action serializer.

Nunca aceitar diretamente:

- created_by.
- uploaded_by.
- assigned staff sem permissão.
- client arbitrário.
- status arbitrário.
- storage_key.
- checksum.
- scan_status.
- event actor.
- archive metadata.

Esses campos devem ser definidos pelo backend.

Utilizar selectors ou query services para consultas complexas.

Utilizar services para mutações de negócio.

Views devem permanecer finas.

==================================================
29. FRONTEND
==================================================

Utilizar o frontend Next.js existente.

Criar features:

src/features/client-portal/
├── clients/
├── invitations/
├── members/
├── protocols/
├── requirements/
├── folders/
├── documents/
├── comments/
└── timeline/

Criar componentes reutilizáveis:

- ProtocolStatusBadge.
- ProtocolTimeline.
- DocumentUploader.
- UploadProgress.
- DocumentList.
- DocumentVersionList.
- FolderTree.
- RequirementChecklist.
- CommentThread.
- InternalNote.
- InvitationForm.
- MemberList.
- ClientSelector.
- AssignedStaffSelector.
- ConfirmActionDialog.
- ArchiveReasonDialog.

Upload:

- Drag and drop.
- Seleção manual.
- Progresso.
- Cancelamento.
- Erro individual.
- Limite visual.
- Tipos permitidos.
- Estado de scan.
- Não considerar disponível antes do backend confirmar.

==================================================
30. AUDITORIA
==================================================

Registar:

- Convite criado.
- Convite enviado.
- Convite reenviado.
- Convite revogado.
- Convite aceite.
- Cliente criado.
- Cliente alterado.
- Cliente desativado.
- Cliente arquivado.
- Cliente restaurado.
- Membro criado.
- Membro desativado.
- Protocolo criado.
- Estado alterado.
- Documento solicitado.
- Upload iniciado.
- Upload concluído.
- Scan concluído.
- Documento rejeitado.
- Documento descarregado.
- Documento versionado.
- Comentário criado.
- Nota interna criada.
- Sessão revogada.
- Conta desativada.
- Conta arquivada.
- Conta restaurada.

Não registar:

- Password.
- OTP.
- Tokens.
- Cookies.
- SMTP password.
- Conteúdo integral de documentos.
- Conteúdo sensível desnecessário.

==================================================
31. DOCKER
==================================================

Estrutura esperada:

veloma-rc
├── veloma-app
├── veloma-api
├── veloma-postgres
├── veloma-redis
├── veloma-celery
├── veloma-celery-beat
├── veloma-minio
├── veloma-minio-init
└── veloma-clamav

Não criar NGINX.

Coolify utiliza Traefik.

Domínios:

veloma.app
→ veloma-app

api.veloma.app
→ veloma-api

PostgreSQL, Redis, Celery, MinIO e ClamAV devem permanecer internos.

==================================================
32. MIGRAÇÕES
==================================================

Criar migrações limpas.

Não apagar migrações existentes.

Não editar migrações antigas já aplicadas.

Executar:

python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations --check
python manage.py check

Criar índices para:

- Client.nif.
- Client.status.
- Client.archived_at.
- ClientInvitation.email.
- ClientInvitation.status.
- ClientInvitation.expires_at.
- ClientMember.client.
- ClientMember.user.
- Protocol.number.
- Protocol.client.
- Protocol.status.
- Protocol.assigned_to.
- Protocol.due_date.
- Document.client.
- Document.protocol.
- Document.folder.
- Document.status.
- DocumentVersion.checksum_sha256.
- ProtocolEvent.created_at.

==================================================
33. TESTES
==================================================

Criar testes backend para:

Convites:
- Criar convite.
- Reenviar.
- Revogar.
- Expirar.
- Aceitar.
- Aceitar duas vezes.
- Token inválido.
- E-mail já existente.
- Staff sem permissão.
- USER tentando convidar.

Clientes:
- Criar.
- Editar.
- Desativar.
- Arquivar.
- Restaurar.
- USER acessando outro cliente.
- Staff sem atribuição.

Membros:
- Criar por convite.
- Desativar.
- Arquivar.
- Restaurar.
- Evitar vínculo duplicado.

Protocolos:
- Criar.
- Transições válidas.
- Transições inválidas.
- Atribuir staff.
- Filtrar por cliente.
- USER vendo somente seus protocolos.
- Nota interna invisível ao USER.
- Concluir.
- Reabrir.
- Arquivar.

Documentos:
- Upload válido.
- Tipo inválido.
- MIME falso.
- Tamanho excedido.
- Scan clean.
- Scan infected.
- Quarentena.
- Download autorizado.
- Download negado.
- Versionamento.
- Checksum.
- Auditoria.
- Documento de outro cliente.

Ciclo de vida:
- Desativar conta.
- Arquivar conta.
- Restaurar conta.
- Revogar sessões.
- Preservar protocolos.
- Preservar documentos.
- Preservar comentários.
- Proibir exclusão física.

Frontend:
- Aceitar convite.
- Dashboard USER.
- Dashboard STAFF.
- Upload.
- Progresso.
- Protocolo.
- Comentário.
- Nota interna.
- Arquivo indisponível durante scan.
- Sessão expirada.
- Acesso cruzado bloqueado.

==================================================
34. ORDEM DE IMPLEMENTAÇÃO
==================================================

FASE 1

- Auditar o core existente.
- Executar testes.
- Confirmar que autenticação está funcional.
- Não criar o módulo antes disso.

FASE 2

- Criar app/client_portal.
- Configurar AppConfig.
- Criar models.
- Criar migrações.
- Criar Admin.

FASE 3

- Implementar AccountLifecycle.
- Implementar ClientLifecycle.
- Bloquear exclusão física.
- Implementar convites.

FASE 4

- Implementar clientes.
- Implementar membros.
- Implementar permissões.

FASE 5

- Implementar protocolos.
- Implementar requisitos.
- Implementar comentários.
- Implementar timeline.

FASE 6

- Implementar pastas.
- Implementar documentos.
- Implementar versões.
- Implementar MinIO.
- Implementar ClamAV.
- Implementar downloads assinados.

FASE 7

- Implementar notificações.
- Criar templates HTML e TXT.
- Implementar Celery e Beat.

FASE 8

- Implementar frontend STAFF.
- Implementar frontend USER.
- Implementar upload e navegação.

FASE 9

- Executar testes.
- Executar lint.
- Executar typecheck.
- Executar build.
- Executar Docker.
- Corrigir falhas.

==================================================
35. CRITÉRIOS DE ACEITE
==================================================

O módulo somente estará concluído quando:

[ ] Não existir registo público.
[ ] Staff conseguir enviar convite.
[ ] Convite possuir expiração e uso único.
[ ] Cliente conseguir aceitar o convite.
[ ] User nativo ser criado corretamente.
[ ] ClientMember ser criado corretamente.
[ ] Cliente conseguir completar o perfil.
[ ] Staff conseguir criar protocolo.
[ ] Protocolo possuir número público.
[ ] Staff conseguir solicitar documentos.
[ ] Cliente conseguir fazer upload.
[ ] Upload gerar Document e DocumentVersion.
[ ] Upload passar por scan.
[ ] Ficheiro infectado ficar em quarentena.
[ ] Download exigir autorização.
[ ] Download gerar auditoria.
[ ] Cliente acompanhar andamento.
[ ] Cliente enviar comentário público.
[ ] Staff adicionar nota interna.
[ ] USER não visualizar nota interna.
[ ] Staff navegar por clientes, pastas e documentos.
[ ] Documentos possuírem versões.
[ ] Utilizador poder ser desativado.
[ ] Utilizador poder ser arquivado.
[ ] Utilizador poder ser restaurado.
[ ] Cliente poder ser desativado.
[ ] Cliente poder ser arquivado.
[ ] Nenhum histórico ser apagado.
[ ] Exclusão física estar bloqueada.
[ ] Nenhum DELETE físico existir na API.
[ ] Todos os testes passarem.
[ ] Docker Compose subir corretamente.
[ ] Frontend build passar.
[ ] Django check passar.
[ ] Migrações estarem limpas.

==================================================
36. ENTREGA
==================================================

Entregar:

1. Código completo do módulo.
2. Models.
3. Migrações.
4. Services.
5. Selectors.
6. Serializers.
7. Views.
8. Permissions.
9. URLs.
10. Admin.
11. Tasks Celery.
12. Templates HTML e TXT.
13. Integração MinIO.
14. Integração ClamAV.
15. Frontend STAFF.
16. Frontend USER.
17. Testes backend.
18. Testes frontend.
19. Docker Compose atualizado.
20. .env.example atualizado.
21. README atualizado.
22. Documentação dos endpoints.
23. Documentação dos fluxos.
24. Relatório de decisões técnicas.
25. ZIP final sem caches, node_modules ou ficheiros temporários.

Não entregar somente exemplos.

Não deixar TODO no lugar de implementação.

Não criar ficheiros vazios.

Não simular testes.

Não afirmar que algo funciona sem executar a validação disponível.

Preservar integralmente o core existente e implementar o novo módulo de forma desacoplada, segura, auditável e reutilizável.
```
