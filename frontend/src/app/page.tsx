import { ArrowRight, FileStack, ShieldCheck, Workflow } from 'lucide-react';
import Link from 'next/link';

import { VelomaLogomark, VelomaMark } from '@/components/brand';
import { site } from '@/content/site';

const ICONS = [Workflow, FileStack, ShieldCheck];

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
          <p className="text-gold-high text-sm font-medium">Área de cliente para escritórios de contabilidade</p>
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
        <section className="border-b border-mist bg-white">
          <div className="mx-auto grid max-w-6xl gap-8 px-6 py-16 sm:grid-cols-3">
            {site.highlights.map((item, index) => {
              const Icon = ICONS[index] ?? Workflow;
              return (
                <div key={item.title}>
                  <span className="bg-navy inline-flex size-9 items-center justify-center rounded-lg">
                    <Icon className="text-gold size-4.5" aria-hidden />
                  </span>
                  <h2 className="text-navy mt-3 text-base font-semibold">{item.title}</h2>
                  <p className="text-navy/70 mt-2 text-sm leading-relaxed">{item.body}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="font-display text-navy text-xl font-semibold tracking-tight">Como funciona</h2>
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
      </main>

      <footer className="bg-navy text-ivory/70">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-6 text-sm">
          <VelomaMark tone="dark" />
          <a href={`mailto:${site.email}`} className="hover:text-ivory">
            {site.email}
          </a>
        </div>
      </footer>
    </>
  );
}
