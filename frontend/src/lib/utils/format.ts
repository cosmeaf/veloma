// Brazil locale and timezone, so dates read the same regardless of the viewer's
// browser timezone (the backend stores UTC).
const TZ = 'America/Sao_Paulo';
const dateFormatter = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium', timeZone: TZ });
const dateTimeFormatter = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium', timeStyle: 'short', timeZone: TZ });

export function formatDate(value?: string | null): string {
  if (!value) return '—';
  return dateFormatter.format(new Date(value));
}

export function formatDateTime(value?: string | null): string {
  if (!value) return '—';
  return dateTimeFormatter.format(new Date(value));
}

export function formatBytes(bytes: number): string {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export const PROTOCOL_CATEGORIES: Record<string, string> = {
  monthly_accounting: 'Contabilidade mensal',
  vat: 'IVA',
  irc: 'IRC',
  irs: 'IRS',
  payroll: 'Processamento salarial',
  hr: 'Recursos humanos',
  company_opening: 'Abertura de empresa',
  company_closing: 'Encerramento de empresa',
  corporate_change: 'Alteração societária',
  tax: 'Fiscalidade',
  banking: 'Bancos',
  contracts: 'Contratos',
  document_request: 'Pedido documental',
  other: 'Outro',
};

export const PROTOCOL_STATUS: Record<string, string> = {
  draft: 'Rascunho',
  waiting_documents: 'Aguardando documentos',
  documents_received: 'Documentos recebidos',
  under_review: 'Em análise',
  action_required: 'Precisamos de informações',
  processing: 'Em processamento',
  completed: 'Concluído',
  cancelled: 'Cancelado',
  archived: 'Arquivado',
};

export const PRIORITIES: Record<string, string> = {
  low: 'Baixa',
  normal: 'Normal',
  high: 'Alta',
  urgent: 'Urgente',
};

export const REQUIREMENT_STATUS: Record<string, string> = {
  pending: 'Em falta',
  uploaded: 'Enviado',
  accepted: 'Aceite',
  rejected: 'Rejeitado',
  waived: 'Dispensado',
};

export const DOCUMENT_STATUS: Record<string, string> = {
  pending_upload: 'A aguardar envio',
  pending_scan: 'Em análise antivírus',
  clean: 'Analisado',
  infected: 'Bloqueado',
  quarantined: 'Em quarentena',
  rejected: 'Rejeitado',
  available: 'Disponível',
  archived: 'Arquivado',
};

export const INVITATION_STATUS: Record<string, string> = {
  pending: 'Pendente',
  accepted: 'Aceite',
  expired: 'Expirado',
  revoked: 'Revogado',
  cancelled: 'Cancelado',
};

export const MEMBER_ROLES: Record<string, string> = {
  owner: 'Titular',
  manager: 'Gestor',
  accounting: 'Contabilidade',
  employee: 'Colaborador',
  viewer: 'Consulta',
};

export const EVENT_LABELS: Record<string, string> = {
  protocol_created: 'Protocolo criado',
  protocol_updated: 'Protocolo atualizado',
  status_changed: 'Estado alterado',
  staff_assigned: 'Responsável atribuído',
  due_date_changed: 'Prazo alterado',
  document_requested: 'Documento solicitado',
  document_uploaded: 'Documento enviado',
  document_downloaded: 'Documento descarregado',
  document_replaced: 'Nova versão do documento',
  document_rejected: 'Documento rejeitado',
  folder_created: 'Pasta criada',
  comment_added: 'Comentário',
  internal_note_added: 'Nota interna',
  protocol_completed: 'Protocolo concluído',
  protocol_reopened: 'Protocolo reaberto',
  protocol_cancelled: 'Protocolo cancelado',
  protocol_archived: 'Protocolo arquivado',
};

export function label(map: Record<string, string>, key?: string | null): string {
  if (!key) return '—';
  return map[key] ?? key;
}
