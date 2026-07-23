```text
VELOMA — CICLO DE VIDA DO UTILIZADOR

ÁREA RESPONSÁVEL

config/authentication/
├── convites
├── criação de conta por convite
├── ativação
├── desativação
├── exclusão lógica
├── reativação
├── sessões
├── tokens
├── OTP
└── auditoria da conta
```

## 1. Não alterar o User do Django

Continuaremos usando:

```python
from django.contrib.auth.models import User
```

Não criar:

```text
- CustomUser
- AUTH_USER_MODEL
- campos adicionais no User
- model alternativo de utilizador
```

Para guardar informações sobre desativação e exclusão lógica, será usado um model relacionado:

```text
AccountLifecycle
├── user
├── deactivated_at
├── deactivated_by
├── deactivation_reason
├── archived_at
├── archived_by
├── archive_reason
├── last_reactivated_at
└── updated_at
```

Esse model não substitui o `User`. Apenas regista o ciclo de vida da conta.

---

## 2. Ação: Desativar

A desativação é temporária e reversível.

```text
DESATIVAR UTILIZADOR

├── user.is_active = False
├── revogar todas as sessões
├── bloquear access e refresh tokens
├── cancelar OTPs pendentes
├── cancelar password reset pendente
├── impedir novo login
├── manter utilizador visível no Admin
├── manter todos os documentos
├── manter todos os protocolos
├── manter comentários e auditorias
└── permitir reativação posterior
```

O utilizador continuará aparecendo como:

```text
Estado: Desativado
```

Não será ocultado das listas administrativas.

---

## 3. Ação: Excluir

“Excluir” será uma **exclusão lógica**, não uma remoção física do banco.

```text
EXCLUIR UTILIZADOR

├── user.is_active = False
├── AccountLifecycle.archived_at = data atual
├── AccountLifecycle.archived_by = administrador
├── revogar todas as sessões
├── invalidar tokens
├── cancelar OTPs
├── cancelar convites pendentes
├── impedir qualquer autenticação
├── ocultar das listas operacionais
├── preservar protocolos
├── preservar documentos
├── preservar comentários
├── preservar tickets
├── preservar auditoria
└── manter visível somente no filtro "Arquivados" do Admin
```

Na interface, o estado será:

```text
Estado: Excluído
```

Mas tecnicamente continuará armazenado para manter integridade contabilística, histórica e jurídica.

---

## 4. Diferença entre as duas ações

```text
DESATIVAR
├── temporário
├── continua visível
├── pode ser reativado normalmente
└── usado para suspensão, saída temporária ou bloqueio

EXCLUIR
├── exclusão lógica
├── fica oculto das operações normais
├── aparece somente em "Arquivados"
├── preserva todo o histórico
└── restauração somente por administrador autorizado
```

Não haverá botão de exclusão física no frontend nem no Django Admin.

---

## 5. Django Admin

Na área `AUTHENTICATION`, o administrador verá:

```text
AUTHENTICATION
├── Users
├── Client Invitations
├── Client Members
├── Authentication Activity
├── OTP Challenges
├── Password Reset Grants
├── User Sessions
├── Access Blocks
├── Security Events
└── Archived Accounts
```

Na listagem de utilizadores:

```text
AÇÕES

├── Desativar contas selecionadas
├── Excluir e arquivar contas selecionadas
├── Reativar contas selecionadas
└── Restaurar contas arquivadas
```

As duas ações principais visíveis serão:

```text
Desativar
Excluir
```

`Reativar` e `Restaurar` ficam disponíveis somente para administradores autorizados.

A ação nativa:

```text
Delete selected users
```

deve ser removida do Admin.

Também deve ser bloqueada a exclusão física na página individual do utilizador.

Isso não altera o Django internamente. Apenas impede uma operação perigosa no `ModelAdmin`.

---

## 6. Política correta de relacionamentos

Não usar `CASCADE` indiscriminadamente.

### Dados temporários de autenticação

Podem usar `CASCADE` caso uma remoção física controlada aconteça:

```text
User
├── OTPChallenge
├── PasswordResetGrant
└── UserSession
```

Exemplo:

```python
user = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
)
```

### Dados históricos e contabilísticos

Nunca devem desaparecer junto com o utilizador:

```text
User
├── AuthenticationActivity
├── SecurityEvent
├── ClientMember
├── Protocol
├── ProtocolEvent
├── ProtocolComment
├── Document
├── DocumentVersion
├── EmailDeliveryLog
└── DownloadAudit
```

Usar:

```python
user = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
)
```

Ou, em relacionamentos críticos:

```python
user = models.ForeignKey(
    User,
    on_delete=models.PROTECT,
)
```

---

## 7. Política recomendada por entidade

```text
OTPChallenge.user
└── CASCADE

PasswordResetGrant.user
└── CASCADE

UserSession.user
└── CASCADE

AuthenticationActivity.user
└── SET_NULL

SecurityEvent.user
└── SET_NULL

ClientMember.user
└── PROTECT

ClientInvitation.invited_by
└── SET_NULL

ClientInvitation.accepted_by
└── SET_NULL

Protocol.created_by
└── SET_NULL

Protocol.assigned_to
└── SET_NULL

ProtocolComment.author
└── SET_NULL

ProtocolEvent.performed_by
└── SET_NULL

Document.uploaded_by
└── SET_NULL

DocumentVersion.uploaded_by
└── SET_NULL

EmailDeliveryLog.created_by
└── SET_NULL
```

Como o utilizador não será fisicamente apagado, essas políticas funcionam principalmente como proteção contra erro administrativo ou execução indevida via shell.

---

## 8. Snapshot histórico

Para preservar a identificação mesmo que a conta seja arquivada futuramente:

```text
ProtocolComment
├── author
├── author_name_snapshot
└── author_email_snapshot

ProtocolEvent
├── performed_by
├── actor_name_snapshot
└── actor_email_snapshot

Document
├── uploaded_by
├── uploader_name_snapshot
└── uploader_email_snapshot
```

Assim o histórico continuará legível mesmo que o utilizador seja anonimizado futuramente.

---

## 9. Exclusão de cliente ou empresa

A mesma regra deve ser aplicada ao cliente contabilístico.

```text
CLIENTE DESATIVADO

├── membros não conseguem entrar
├── novos uploads são bloqueados
├── protocolos ficam somente leitura
├── documentos continuam disponíveis ao staff
└── histórico permanece intacto
```

```text
CLIENTE EXCLUÍDO

├── exclusão lógica
├── ocultado das listas normais
├── membros desativados
├── convites cancelados
├── protocolos preservados
├── documentos preservados
├── auditoria preservada
└── disponível no filtro "Clientes arquivados"
```

Nunca apagar fisicamente uma empresa que tenha:

```text
- protocolos
- documentos
- obrigações
- comentários
- membros
- auditorias
```

---

## 10. Serviço centralizado

Nenhuma view, serializer ou Admin deverá executar essas operações diretamente.

Usar um serviço único:

```python
AccountLifecycleService.deactivate(
    user=user,
    performed_by=request.user,
    reason="Contrato suspenso",
)

AccountLifecycleService.archive(
    user=user,
    performed_by=request.user,
    reason="Cliente encerrado",
)

AccountLifecycleService.reactivate(
    user=user,
    performed_by=request.user,
)

AccountLifecycleService.restore(
    user=user,
    performed_by=request.user,
)
```

O serviço será responsável por:

```text
├── alterar is_active
├── atualizar AccountLifecycle
├── revogar sessões
├── invalidar tokens
├── cancelar OTPs
├── cancelar resets
├── cancelar convites
├── gerar AuthenticationActivity
├── gerar SecurityEvent
├── enviar e-mail quando configurado
└── executar tudo dentro de transação
```

Usar:

```python
from django.db import transaction

@transaction.atomic
def archive(...):
    ...
```

---

## 11. Regra final

```text
EXCLUSÃO FÍSICA
└── proibida pela aplicação e pelo Admin

DESATIVAÇÃO
└── bloqueia temporariamente, mas mantém visível

EXCLUSÃO LÓGICA
└── bloqueia, arquiva e oculta, preservando todo o histórico
```

Convites, contas, sessões e ciclo de vida ficam dentro de:

```text
config/authentication/
```

Protocolos, documentos, pastas e pedidos ficam dentro de:

```text
app/client_portal/
```

Eles se relacionam com a autenticação, mas não devem ficar misturados nela. Autenticação controla **quem pode entrar**; o portal controla **o que o cliente e o staff fazem depois de entrar**.

```
```
