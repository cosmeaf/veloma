import { ArrowRight, FileStack, ShieldCheck, Workflow } from 'lucide-react';
import Link from 'next/link';

import { VelomaLogomark, VelomaMark } from '@/components/brand';
import { site } from '@/content/site';

const ICONS = [Workflow, FileStack, ShieldCheck];

export default function HomePage() {
  return (
    <>
      <header className="border-b border-mist bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <VelomaMark />
          <Link
            href="/entrar"
            className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
          >
            Área de cliente
            <ArrowRight className="size-4" />
          </Link>
        </nav>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-20">
          <VelomaLogomark width={180} priority className="mb-8" />
          <p className="text-navy/55 text-sm font-medium">Área de cliente para escritórios de contabilidade</p>
          <h1 className="font-display mt-3 max-w-3xl text-4xl font-semibold tracking-tight text-balance text-navy sm:text-5xl">
            {site.tagline}
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-navy/70">{site.description}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/entrar"
              className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
            >
              Entrar na área de cliente
              <ArrowRight className="size-4" />
            </Link>
            <a
              href={`mailto:${site.email}`}
              className="inline-flex items-center rounded-lg border border-mist bg-white px-5 py-3 text-sm font-medium text-navy transition-colors hover:bg-mist/30"
            >
              Falar connosco
            </a>
          </div>
        </section>

        <section className="border-y border-mist bg-white">
          <div className="mx-auto grid max-w-6xl gap-8 px-6 py-16 sm:grid-cols-3">
            {site.highlights.map((item, index) => {
              const Icon = ICONS[index] ?? Workflow;
              return (
                <div key={item.title}>
                  <Icon className="size-5 text-navy" aria-hidden />
                  <h2 className="mt-3 text-base font-semibold text-navy">{item.title}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-navy/70">{item.body}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="font-display text-xl font-semibold tracking-tight text-navy">Como funciona</h2>
          <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {site.steps.map((step, index) => (
              <li key={step.title} className="rounded-xl border border-mist bg-white p-5">
                <span className="text-xs font-semibold text-navy/40">0{index + 1}</span>
                <h3 className="mt-2 text-sm font-semibold text-navy">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-navy/70">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="border-t border-mist bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-6 text-sm text-navy/55">
          <span>
            {site.name} · {new Date().getFullYear()}
          </span>
          <a href={`mailto:${site.email}`} className="hover:text-navy">
            {site.email}
          </a>
        </div>
      </footer>
    </>
  );
}
