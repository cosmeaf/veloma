import {
  ArrowRight,
  Calculator,
  Check,
  ClipboardList,
  Clock,
  FileStack,
  Leaf,
  MapPin,
  Phone,
  ScanLine,
  ShieldCheck,
  TrendingUp,
  Users,
} from 'lucide-react';
import Link from 'next/link';

import { VelomaLogomark, VelomaMark } from '@/components/brand';
import { SiteFooter } from '@/components/site-footer';
import { site } from '@/content/site';

const HIGHLIGHT_ICONS = [ScanLine, ClipboardList, Clock];
const SERVICE_ICONS = [Calculator, TrendingUp, Users];

export default function HomePage() {
  return (
    <>
      {/* Navy hero carries the brand; the rest of the page stays light. */}
      <div className="bg-navy text-ivory">
        <header className="border-b border-white/10">
          <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <VelomaMark tone="dark" />
            <Link
              href="/entrar"
              className="bg-gold text-navy hover:bg-gold-high inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            >
              Área de cliente
              <ArrowRight className="size-4" />
            </Link>
          </nav>
        </header>

        <section className="mx-auto max-w-6xl px-6 pt-16 pb-20">
          <VelomaLogomark tone="dark" width={190} priority className="mb-8" />
          <p className="text-gold-high text-sm font-medium tracking-wide uppercase">{site.eyebrow}</p>
          <h1 className="font-display text-ivory mt-3 max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            {site.tagline}
          </h1>
          <p className="text-ivory/75 mt-5 max-w-2xl text-lg">{site.description}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/entrar"
              className="bg-gold text-navy hover:bg-gold-high inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-medium transition-colors"
            >
              Entrar na área de cliente
              <ArrowRight className="size-4" />
            </Link>
            <a
              href={`mailto:${site.email}`}
              className="text-ivory inline-flex items-center rounded-lg border border-white/25 px-5 py-3 text-sm font-medium transition-colors hover:bg-white/10"
            >
              Falar connosco
            </a>
          </div>
        </section>
      </div>

      <main className="flex-1">
        {/* O que a plataforma resolve, na ótica do cliente. */}
        <section className="border-b border-mist bg-white">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <p className="text-gold-sun text-sm font-medium">Porquê a {site.product}</p>
            <h2 className="font-display text-navy mt-2 max-w-2xl text-2xl font-semibold tracking-tight">
              A relação com o seu contabilista, sem papéis e sem esperas.
            </h2>
            <div className="mt-10 grid gap-8 sm:grid-cols-3">
              {site.highlights.map((item, index) => {
                const Icon = HIGHLIGHT_ICONS[index] ?? ScanLine;
                return (
                  <div key={item.title}>
                    <span className="bg-navy inline-flex size-9 items-center justify-center rounded-lg">
                      <Icon className="text-gold size-4.5" aria-hidden />
                    </span>
                    <h3 className="text-navy mt-3 text-base font-semibold">{item.title}</h3>
                    <p className="text-navy/70 mt-2 text-sm leading-relaxed">{item.body}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Passo a passo do processo digital. */}
        <section className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="font-display text-navy text-xl font-semibold tracking-tight">Como funciona</h2>
          <p className="text-navy/60 mt-2 max-w-2xl text-sm">
            Do convite à conclusão, todo o processo acontece online e fica registado.
          </p>
          <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {site.steps.map((step, index) => (
              <li key={step.title} className="border-mist rounded-xl border bg-white p-5">
                <span className="text-gold-sun font-display text-lg font-semibold">0{index + 1}</span>
                <h3 className="text-navy mt-2 text-sm font-semibold">{step.title}</h3>
                <p className="text-navy/70 mt-1.5 text-sm leading-relaxed">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Faixa de sustentabilidade — digital = menos papel. */}
        <section className="bg-emerald-900 text-emerald-50">
          <div className="mx-auto grid max-w-6xl items-center gap-10 px-6 py-16 lg:grid-cols-2">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-medium tracking-wide text-emerald-100 uppercase">
                <Leaf className="size-3.5" aria-hidden />
                {site.eco.eyebrow}
              </span>
              <h2 className="font-display mt-4 text-2xl font-semibold tracking-tight sm:text-3xl">{site.eco.title}</h2>
              <p className="mt-3 max-w-md text-sm leading-relaxed text-emerald-100/85">{site.eco.body}</p>
            </div>
            <ul className="space-y-3">
              {site.eco.points.map((point) => (
                <li key={point} className="flex items-start gap-3 rounded-xl bg-emerald-800/40 px-4 py-3">
                  <span className="mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-emerald-400/25">
                    <Check className="size-3.5 text-emerald-100" aria-hidden />
                  </span>
                  <span className="text-sm text-emerald-50">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Serviços institucionais da Veloma. */}
        <section className="border-y border-mist bg-white">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <p className="text-gold-sun text-sm font-medium">O que fazemos</p>
            <h2 className="font-display text-navy mt-2 text-2xl font-semibold tracking-tight">
              Uma equipa comprometida com o sucesso dos seus clientes.
            </h2>
            <div className="mt-10 grid gap-6 sm:grid-cols-3">
              {site.services.map((service, index) => {
                const Icon = SERVICE_ICONS[index] ?? Calculator;
                return (
                  <div key={service.title} className="border-mist rounded-xl border bg-white p-6">
                    <span className="bg-mist/70 inline-flex size-9 items-center justify-center rounded-lg">
                      <Icon className="text-navy size-4.5" aria-hidden />
                    </span>
                    <h3 className="text-navy mt-3 text-base font-semibold">{service.title}</h3>
                    <p className="text-navy/70 mt-2 text-sm leading-relaxed">{service.body}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Segurança + contacto, para fechar. */}
        <section className="mx-auto max-w-6xl px-6 py-16">
          <div className="grid gap-10 lg:grid-cols-2">
            <div>
              <span className="bg-navy inline-flex size-9 items-center justify-center rounded-lg">
                <ShieldCheck className="text-gold size-4.5" aria-hidden />
              </span>
              <h2 className="font-display text-navy mt-3 text-xl font-semibold tracking-tight">
                Os seus documentos, protegidos.
              </h2>
              <p className="text-navy/70 mt-2 max-w-md text-sm leading-relaxed">
                O acesso é apenas por convite, cada envio passa por análise de segurança e fica registada cada consulta,
                envio e descarregamento. Nada é apagado — o histórico de cada processo mantém-se sempre disponível.
              </p>
              <div className="mt-5 flex items-center gap-2">
                <FileStack className="text-navy/40 size-4.5" aria-hidden />
                <span className="text-navy/60 text-sm">Documentos versionados e auditáveis</span>
              </div>
            </div>

            <div className="border-mist rounded-xl border bg-white p-6">
              <h2 className="font-display text-navy text-base font-semibold">Fale connosco</h2>
              <ul className="mt-4 space-y-3 text-sm">
                <li className="flex items-start gap-3">
                  <MapPin className="text-gold-sun mt-0.5 size-4.5 shrink-0" aria-hidden />
                  <span className="text-navy/75">{site.address}</span>
                </li>
                <li className="flex items-start gap-3">
                  <Phone className="text-gold-sun mt-0.5 size-4.5 shrink-0" aria-hidden />
                  <span className="text-navy/75">{site.phones.join(' · ')}</span>
                </li>
                <li className="flex items-start gap-3">
                  <Clock className="text-gold-sun mt-0.5 size-4.5 shrink-0" aria-hidden />
                  <span className="text-navy/75">{site.hours}</span>
                </li>
              </ul>
              <a
                href={`mailto:${site.email}`}
                className="bg-navy text-ivory hover:bg-navy-soft mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
              >
                {site.email}
                <ArrowRight className="size-4" />
              </a>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </>
  );
}
