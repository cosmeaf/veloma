'use client';

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="pt-PT">
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#20193B',
          color: '#FFFEF0',
          fontFamily: 'ui-sans-serif, system-ui, Segoe UI, Arial, sans-serif',
          textAlign: 'center',
          padding: '32px 16px',
        }}
      >
        <div>
          <div style={{ letterSpacing: '.18em', textTransform: 'uppercase', color: '#F3D994', fontWeight: 700, fontSize: 14 }}>
            Veloma
          </div>
          <h1 style={{ fontFamily: 'Georgia, serif', fontSize: 26, margin: '16px 0 10px' }}>Algo correu mal</h1>
          <p style={{ color: 'rgba(255,254,240,.65)', maxWidth: 420, margin: '0 auto 22px' }}>
            Ocorreu um problema temporário. Pode tentar novamente.
          </p>
          <button
            type="button"
            onClick={reset}
            style={{ background: '#D69508', color: '#20193B', border: 0, borderRadius: 8, padding: '11px 20px', fontWeight: 600, cursor: 'pointer' }}
          >
            Tentar novamente
          </button>
        </div>
      </body>
    </html>
  );
}
