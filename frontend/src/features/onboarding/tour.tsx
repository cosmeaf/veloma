'use client';

import { ArrowLeft, ArrowRight, Compass, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button, cn } from '@/components/ui';

type Step = {
  /** `data-tour` value of the element to highlight, when there is one. */
  anchor?: string;
  title: string;
  body: string;
};

const STEPS: Step[] = [
  {
    title: 'Bem-vindo à sua área de cliente',
    body: 'Aqui acompanha tudo o que troca com o escritório: pedidos, documentos e mensagens. Um minuto e fica a conhecer.',
  },
  {
    anchor: 'resumo',
    title: 'Resumo',
    body: 'A primeira vista mostra quantos pedidos aguardam documentos, quais estão em análise e o que precisa da sua ação.',
  },
  {
    anchor: 'pedidos',
    title: 'Pedidos',
    body: 'Cada pedido tem um número próprio, como VEL-2026-000003. Lá dentro vê a lista do que falta enviar, envia ficheiros e fala com a equipa.',
  },
  {
    anchor: 'documentos',
    title: 'Documentos',
    body: 'As pastas funcionam como no explorador do computador. Os envios são feitos num único ficheiro .zip com os documentos do período.',
  },
  {
    anchor: 'empresa',
    title: 'Empresa',
    body: 'Os dados da sua empresa e quem tem acesso a esta área. Para alterar, fale com o escritório.',
  },
  {
    anchor: 'seguranca',
    title: 'Segurança',
    body: 'Veja as sessões abertas, termine as que não reconhece e altere a palavra-passe quando quiser.',
  },
  {
    title: 'É tudo',
    body: 'Pode rever esta visita quando quiser, no botão "Visita guiada" no topo.',
  },
];

const STORAGE_KEY = 'veloma:tour:client:v1';
const HIGHLIGHT = ['outline-3', 'outline-gold-sun', 'outline-offset-2', 'rounded-lg'];

/**
 * Guided tour of the client area.
 *
 * Runs once per browser and can be replayed from the header. Only a
 * "seen" flag is stored — no personal data.
 */
export function ClientTour() {
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (window.localStorage.getItem(STORAGE_KEY) !== 'done') setOpen(true);
  }, []);

  // Highlights the sidebar entry the current step talks about.
  useEffect(() => {
    if (!open) return;
    const anchor = STEPS[index]?.anchor;
    const element = anchor ? document.querySelector<HTMLElement>(`[data-tour="${anchor}"]`) : null;
    element?.classList.add(...HIGHLIGHT);
    element?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    return () => element?.classList.remove(...HIGHLIGHT);
  }, [open, index]);

  const close = useCallback(() => {
    window.localStorage.setItem(STORAGE_KEY, 'done');
    setOpen(false);
    setIndex(0);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close();
      if (event.key === 'ArrowRight') setIndex((current) => Math.min(current + 1, STEPS.length - 1));
      if (event.key === 'ArrowLeft') setIndex((current) => Math.max(current - 1, 0));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, close]);

  if (!open) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          setIndex(0);
          setOpen(true);
        }}
      >
        <Compass className="size-4" aria-hidden />
        <span className="hidden sm:inline">Visita guiada</span>
      </Button>
    );
  }

  const step = STEPS[index];
  const last = index === STEPS.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center" role="dialog" aria-modal="true">
      <button type="button" aria-label="Fechar visita" className="bg-navy/50 absolute inset-0" onClick={close} />

      <div className="border-mist relative w-full max-w-md rounded-xl border bg-white p-6 shadow-xl">
        <button
          type="button"
          onClick={close}
          aria-label="Fechar visita"
          className="text-navy/40 hover:text-navy absolute top-4 right-4"
        >
          <X className="size-4" />
        </button>

        <p className="text-gold-sun text-xs font-semibold tracking-wider uppercase">
          Passo {index + 1} de {STEPS.length}
        </p>
        <h2 className="font-display text-navy mt-2 text-xl font-semibold">{step.title}</h2>
        <p className="text-navy/70 mt-2 text-sm leading-relaxed">{step.body}</p>

        <div className="mt-6 flex items-center justify-between gap-3">
          <div className="flex gap-1" aria-hidden>
            {STEPS.map((item, position) => (
              <span
                key={item.title}
                className={cn('h-1.5 w-4 rounded-full', position === index ? 'bg-navy' : 'bg-mist')}
              />
            ))}
          </div>
          <div className="flex gap-2">
            {index > 0 ? (
              <Button variant="secondary" size="sm" onClick={() => setIndex(index - 1)}>
                <ArrowLeft className="size-4" aria-hidden />
                Anterior
              </Button>
            ) : null}
            {last ? (
              <Button size="sm" onClick={close}>
                Começar
              </Button>
            ) : (
              <Button size="sm" onClick={() => setIndex(index + 1)}>
                Seguinte
                <ArrowRight className="size-4" aria-hidden />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
