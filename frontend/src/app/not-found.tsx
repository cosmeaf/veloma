import Link from 'next/link';

import { ErrorScreen } from '@/components/error-screen';

export default function NotFound() {
  return (
    <ErrorScreen
      code="404"
      heading="Página não encontrada"
      message="A página que procura não existe ou foi movida."
      action={
        <Link href="/" className="bg-gold text-navy rounded-lg px-5 py-2.5 text-sm font-semibold">
          Voltar ao início
        </Link>
      }
    />
  );
}
