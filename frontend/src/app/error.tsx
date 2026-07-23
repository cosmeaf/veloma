'use client';

import { ErrorScreen } from '@/components/error-screen';

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <ErrorScreen
      code="Erro"
      heading="Algo correu mal"
      message="Ocorreu um problema temporário. Pode tentar novamente."
      action={
        <button
          type="button"
          onClick={reset}
          className="bg-gold text-navy rounded-lg px-5 py-2.5 text-sm font-semibold"
        >
          Tentar novamente
        </button>
      }
    />
  );
}
