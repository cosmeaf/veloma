import { site } from '@/content/site';

/** Data da última revisão dos documentos legais (rever a cada alteração). */
export const legalUpdatedAt = '23 de julho de 2026';

/** Identificação do responsável pelo tratamento, reutilizada nos documentos. */
export const controller = `Veloma — Contabilidade e Consultoria Fiscal, Lda., com sede na ${site.address}, contactável através de ${site.email} ou ${site.phones.join(' / ')}`;

type Section = { heading: string; paragraphs: string[] };
export type LegalDocument = { slug: string; title: string; summary: string; sections: Section[] };

export const termos: LegalDocument = {
  slug: 'termos',
  title: 'Termos e Condições de Utilização',
  summary: 'Condições de acesso e utilização da plataforma Veloma Digital.',
  sections: [
    {
      heading: '1. Objeto',
      paragraphs: [
        'Os presentes Termos e Condições regulam o acesso e a utilização da plataforma Veloma Digital (a "Plataforma"), disponibilizada pela Veloma às empresas e clientes com quem mantém uma relação de prestação de serviços de contabilidade, consultoria e recursos humanos.',
        'Ao aceder e utilizar a Plataforma, o utilizador declara ter lido, compreendido e aceite integralmente estes Termos, bem como a Política de Privacidade e a Política de Cookies.',
      ],
    },
    {
      heading: '2. Acesso à conta',
      paragraphs: [
        'O acesso é exclusivamente por convite. A Veloma envia um convite de uso único para o endereço de e-mail da empresa cliente, que permite criar uma conta pessoal e intransmissível.',
        'O utilizador é responsável por manter a confidencialidade das suas credenciais e por todas as atividades realizadas na sua conta. Deve comunicar de imediato à Veloma qualquer utilização não autorizada.',
        'A Plataforma disponibiliza verificação em duas etapas, cuja ativação é recomendada para reforço da segurança da conta.',
      ],
    },
    {
      heading: '3. Utilização da Plataforma',
      paragraphs: [
        'A Plataforma destina-se ao envio, consulta e acompanhamento de documentos e processos (protocolos) relacionados com os serviços contratados. O utilizador compromete-se a utilizar a Plataforma apenas para fins lícitos e a não carregar conteúdos ilegais, ofensivos ou que violem direitos de terceiros.',
        'Todos os ficheiros enviados são sujeitos a análise automática de segurança. A Veloma reserva-se o direito de recusar ou colocar em quarentena ficheiros que não cumpram os requisitos técnicos ou de segurança.',
      ],
    },
    {
      heading: '4. Documentos e conservação',
      paragraphs: [
        'Os documentos enviados são conservados de forma versionada: cada substituição gera uma nova versão, mantendo-se as anteriores disponíveis. Os documentos e o histórico de cada processo são conservados pelos prazos legais aplicáveis à atividade contabilística e fiscal.',
        'Nenhum documento é eliminado fisicamente pela ação do utilizador; as operações de remoção correspondem a arquivo lógico, preservando a rastreabilidade.',
      ],
    },
    {
      heading: '5. Responsabilidade',
      paragraphs: [
        'A Veloma envida os melhores esforços para assegurar a disponibilidade e segurança da Plataforma, não garantindo, contudo, o funcionamento ininterrupto ou isento de erros.',
        'A Veloma não se responsabiliza por danos decorrentes de utilização indevida da conta pelo utilizador, nomeadamente pela partilha de credenciais.',
      ],
    },
    {
      heading: '6. Alterações',
      paragraphs: [
        'A Veloma pode alterar estes Termos a qualquer momento. As alterações relevantes serão comunicadas através da Plataforma ou por e-mail, sendo indicada a data da última revisão.',
      ],
    },
    {
      heading: '7. Lei aplicável e foro',
      paragraphs: [
        'Os presentes Termos regem-se pela lei portuguesa. Para a resolução de qualquer litígio emergente será competente o foro da comarca da sede da Veloma, com renúncia expressa a qualquer outro.',
      ],
    },
  ],
};

export const privacidade: LegalDocument = {
  slug: 'privacidade',
  title: 'Política de Privacidade',
  summary: 'Como tratamos e protegemos os seus dados pessoais, ao abrigo do RGPD.',
  sections: [
    {
      heading: '1. Responsável pelo tratamento',
      paragraphs: [
        `O responsável pelo tratamento dos dados pessoais é a ${controller}.`,
        'Para questões relacionadas com a proteção de dados, incluindo o exercício dos seus direitos, pode contactar-nos através do e-mail indicado.',
      ],
    },
    {
      heading: '2. Dados que tratamos',
      paragraphs: [
        'Dados de identificação e contacto (nome, e-mail, empresa) fornecidos no convite e no registo.',
        'Dados de utilização e segurança: endereço IP, região aproximada, tipo de dispositivo e navegador, datas e horas de acesso, envios e descarregamentos.',
        'Documentos e informação carregados pelo utilizador no âmbito dos serviços contratados.',
      ],
    },
    {
      heading: '3. Finalidades e fundamentos',
      paragraphs: [
        'Prestação dos serviços contratados e gestão da relação contratual (execução de contrato).',
        'Cumprimento de obrigações legais, nomeadamente contabilísticas e fiscais (obrigação jurídica).',
        'Segurança da Plataforma, prevenção de fraude e registo de acessos (interesse legítimo).',
        'Envio de comunicações de serviço essenciais ao funcionamento da conta.',
      ],
    },
    {
      heading: '4. Registo de consentimento e aceitação',
      paragraphs: [
        'Quando aceita os Termos e Condições e a presente Política, registamos essa aceitação de forma comprovável, incluindo a data e hora, o endereço IP, a região aproximada e a versão dos documentos aceites, para efeitos de prova e cumprimento do princípio da responsabilidade (accountability).',
      ],
    },
    {
      heading: '5. Conservação',
      paragraphs: [
        'Os dados são conservados apenas pelo período necessário às finalidades acima e aos prazos legais de conservação aplicáveis à atividade contabilística e fiscal. Findos esses prazos, os dados são eliminados ou anonimizados.',
      ],
    },
    {
      heading: '6. Partilha e subcontratantes',
      paragraphs: [
        'Os dados podem ser tratados por subcontratantes que prestam serviços à Veloma (por exemplo, alojamento e envio de e-mail), sempre sob contrato e instruções que asseguram a proteção dos dados. Não vendemos dados pessoais a terceiros.',
      ],
    },
    {
      heading: '7. Os seus direitos',
      paragraphs: [
        'Nos termos do RGPD, tem direito de acesso, retificação, apagamento, limitação, portabilidade e oposição, bem como o direito de retirar o consentimento a qualquer momento, sem afetar a licitude do tratamento anterior.',
        'Pode exercer os seus direitos através do e-mail indicado. Tem ainda o direito de apresentar reclamação à Comissão Nacional de Proteção de Dados (CNPD).',
      ],
    },
    {
      heading: '8. Segurança',
      paragraphs: [
        'Aplicamos medidas técnicas e organizativas adequadas, incluindo controlo de acessos, cifragem de credenciais, análise de ficheiros e registo de atividade, para proteger os dados contra acesso não autorizado, perda ou destruição.',
      ],
    },
  ],
};

export const cookies: LegalDocument = {
  slug: 'cookies',
  title: 'Política de Cookies',
  summary: 'Que cookies utilizamos e como pode geri-los.',
  sections: [
    {
      heading: '1. O que são cookies',
      paragraphs: [
        'Cookies são pequenos ficheiros de texto guardados no seu dispositivo quando visita um site, que permitem reconhecer o navegador e assegurar funcionalidades essenciais.',
      ],
    },
    {
      heading: '2. Cookies que utilizamos',
      paragraphs: [
        'Cookies estritamente necessários: garantem o funcionamento da Plataforma, o início de sessão seguro e a manutenção da sessão. Não podem ser desativados sem comprometer o serviço.',
        'Não utilizamos cookies de publicidade nem partilhamos dados de navegação com redes publicitárias.',
      ],
    },
    {
      heading: '3. Gestão de cookies',
      paragraphs: [
        'Pode configurar o seu navegador para bloquear ou eliminar cookies. Note que a desativação de cookies necessários poderá impedir o acesso à área de cliente.',
        'Ao aceitar o aviso de cookies apresentado na Plataforma, regista a sua escolha, que pode alterar a qualquer momento limpando os dados do navegador.',
      ],
    },
  ],
};

export const legalDocuments = [termos, privacidade, cookies];
