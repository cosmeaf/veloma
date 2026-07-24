/**
 * Client-facing release notes — the "Novidades e correções" map.
 *
 * This file is the single source of truth for the app version: the newest entry
 * (first in the array) is the current release, read by `APP_VERSION`. When you
 * ship, add an entry at the top and bump `package.json` to match — nothing else
 * needs to change.
 *
 * Text is written for the client (pt-PT), not as raw commit messages.
 */

/** A change is tagged so the page can colour it. */
export type ChangeType = 'new' | 'improved' | 'fix';

export type ReleaseChange = {
  type: ChangeType;
  text: string;
};

export type Release = {
  /** Semantic version, e.g. "1.2.0". */
  version: string;
  /** ISO date (YYYY-MM-DD) of the release. */
  date: string;
  /** Short headline for the release. */
  title: string;
  changes: ReleaseChange[];
};

export const CHANGE_LABELS: Record<ChangeType, string> = {
  new: 'Novo',
  improved: 'Melhorado',
  fix: 'Corrigido',
};

/** Newest first. */
export const CHANGELOG: Release[] = [
  {
    version: '1.2.0',
    date: '2026-07-24',
    title: 'Explorador de ficheiros nos protocolos',
    changes: [
      { type: 'new', text: 'Os ficheiros de cada protocolo passam a aparecer numa vista tipo Explorador/Dropbox, igual à área de Documentos.' },
      { type: 'improved', text: 'A página do protocolo ficou mais limpa: os ficheiros ao centro e as ações, pedidos e histórico numa coluna à parte.' },
      { type: 'improved', text: 'Só se mostram os campos preenchidos (prazo, competência, conclusão) — deixou de haver informação vazia.' },
      { type: 'fix', text: 'O histórico deixou de repetir cada envio duas vezes — cada ficheiro aparece uma só vez.' },
    ],
  },
  {
    version: '1.1.0',
    date: '2026-07-24',
    title: 'Envios automáticos e notificações',
    changes: [
      { type: 'new', text: 'A lista de ficheiros atualiza-se sozinha assim que um envio termina.' },
      { type: 'new', text: 'Notificações com aviso sonoro; pode marcá-las como lidas ou apagá-las.' },
      { type: 'improved', text: 'O Explorador mostra o nome do cliente na raiz, em vez de "Raiz".' },
    ],
  },
  {
    version: '1.0.0',
    date: '2026-07-23',
    title: 'Lançamento em homologação',
    changes: [
      { type: 'new', text: 'Explorador de documentos estilo Dropbox, com pastas e histórico recolhível.' },
      { type: 'new', text: 'Envio de documentos por protocolo, com observação e descarga segura.' },
      { type: 'improved', text: 'Segurança: verificação em duas etapas (2FA) com aviso claro e o histórico a mostrar o último acesso.' },
    ],
  },
];

/** Current application version, derived from the newest release. */
export const APP_VERSION = CHANGELOG[0].version;
