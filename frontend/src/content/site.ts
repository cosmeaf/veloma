export const site = {
  name: 'Veloma',
  /** Nome comercial da plataforma digital apresentada aos clientes. */
  product: 'Veloma Digital',
  eyebrow: 'Veloma Contabilidade, agora é digital!',
  tagline: 'A sua contabilidade online, sem papéis e sem burocracia.',
  description:
    'Envie os seus documentos, acompanhe cada processo por protocolo e fale com a nossa equipa — tudo online, num só lugar, sempre à mão.',
  // Contactos institucionais reais (velomacontabilidade.com).
  email: 'geral@velomacontabilidade.com',
  phones: ['917 968 076', '932 426 691'],
  address: 'Rua Policarpo dos Anjos, 61 – LJ D/Q',
  hours: 'Seg. a Sex. · 09:00–13:00 e 14:00–18:00',
  social: {
    facebook: 'https://www.facebook.com/velomacontabilidade',
    instagram: 'https://www.instagram.com/velomacontabilidade',
    linkedin: 'https://www.linkedin.com/company/velomacontabilidade',
  },
  // Argumentos de venda da plataforma, na ótica do cliente.
  highlights: [
    {
      title: 'Documentos digitalizados',
      body: 'Deixe de trocar papéis e e-mails soltos. Envie, guarde e consulte tudo digitalizado, organizado e disponível quando precisar.',
    },
    {
      title: 'Acompanhe por protocolo',
      body: 'Cada pedido tem um número. Veja o estado em tempo real, do envio à conclusão, sem ter de ligar ou esperar por respostas.',
    },
    {
      title: 'Sem filas nem burocracia',
      body: 'Aceda a qualquer hora, do computador ou do telemóvel. Nós tratamos do resto, com a mesma equipa de sempre.',
    },
  ],
  steps: [
    { title: 'Recebe o convite', body: 'A Veloma envia-lhe um convite seguro, de uso único, para o e-mail da sua empresa.' },
    { title: 'Vê o que é preciso', body: 'Abrimos um protocolo e indicamos exatamente que documentos precisamos, sem margem para dúvidas.' },
    { title: 'Envia num clique', body: 'Carrega os ficheiros pela plataforma, com verificação automática de segurança em cada envio.' },
    { title: 'Acompanha ao vivo', body: 'Cada passo do processo fica registado e visível para si — sabe sempre em que ponto está.' },
  ],
  // Compromisso ambiental — digital significa menos papel.
  eco: {
    eyebrow: 'Compromisso ambiental',
    title: 'Menos papel, mais floresta.',
    body: 'Cada documento que trocamos online é papel que não se imprime. Ao passar para a Veloma Digital, junta-se a nós na redução do consumo de papel e no combate à desflorestação — a contabilidade da sua empresa passa a cuidar também do ambiente.',
    points: [
      'Menos impressões, menos árvores abatidas.',
      'Arquivo digital em vez de dossiês em papel.',
      'Menos deslocações para entregar documentos.',
    ],
  },
  // Serviços da Veloma (institucional).
  services: [
    {
      title: 'Contabilidade',
      body: 'Para pequenas e médias empresas e empresários em nome individual, com acompanhamento permanente.',
    },
    {
      title: 'Consultoria',
      body: 'Fiscal, de gestão e de negócios, para o ajudar a decidir no momento certo.',
    },
    {
      title: 'Recursos Humanos',
      body: 'Gestão de recursos humanos e apoio administrativo, sem sobrecarregar a sua equipa.',
    },
  ],
} as const;
