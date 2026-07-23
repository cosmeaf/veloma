export const site = {
  name: 'Veloma',
  tagline: 'Contabilidade acompanhada, documentos no sítio certo.',
  description:
    'Área de cliente para escritórios de contabilidade: pedidos organizados por protocolo, documentos versionados e histórico completo de cada processo.',
  email: 'geral@veloma.app',
  highlights: [
    {
      title: 'Pedidos com protocolo',
      body: 'Cada solicitação tem número público, responsável, prazo e estado. Nada se perde em trocas de e-mail.',
    },
    {
      title: 'Documentos versionados',
      body: 'Cada substituição cria uma nova versão. As anteriores permanecem disponíveis e auditáveis.',
    },
    {
      title: 'Acesso controlado',
      body: 'Contas só por convite, sessões revogáveis e registo de cada acesso, envio e descarregamento.',
    },
  ],
  steps: [
    { title: 'Convite', body: 'O escritório envia um convite de uso único para o e-mail da empresa.' },
    { title: 'Pedido', body: 'A equipa abre um protocolo e indica exatamente que documentos são precisos.' },
    { title: 'Envio', body: 'A empresa envia os ficheiros pela área de cliente, com análise antivírus automática.' },
    { title: 'Acompanhamento', body: 'Cada alteração de estado fica registada e visível para ambas as partes.' },
  ],
} as const;
