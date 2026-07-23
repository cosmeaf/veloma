"""Legal document versions and the acceptance-proof PDF builder.

The version strings must be bumped whenever the Terms or Privacy Policy text
changes (kept in sync with the frontend legal pages). Each acceptance stores the
versions the user actually agreed to, so the proof remains meaningful over time.
"""

import io

TERMS_VERSION = '2026-07-23'
PRIVACY_VERSION = '2026-07-23'

COMPANY_NAME = 'Veloma — Contabilidade e Consultoria Fiscal, Lda.'


def build_acceptance_pdf(*, acceptance, first_name='', last_name=''):
    """Renders a one-page A4 PDF proof of consent and returns the raw bytes.

    Includes the full digital evidence (RGPD accountability): who accepted, when,
    from where (IP, region), with which device, and which document versions.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 20 * mm
    y = height - 25 * mm

    def line(text, *, size=10, gap=6.5, bold=False):
        nonlocal y
        pdf.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        pdf.drawString(left, y, text)
        y -= gap * mm

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(left, y, 'Comprovativo de Aceitação')
    y -= 8 * mm
    pdf.setFont('Helvetica', 10)
    pdf.drawString(left, y, COMPANY_NAME)
    y -= 4 * mm
    pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
    pdf.line(left, y, width - left, y)
    y -= 10 * mm

    full_name = f'{first_name} {last_name}'.strip()
    accepted_at = acceptance.accepted_at.strftime('%Y-%m-%d %H:%M:%S %Z').strip() if acceptance.accepted_at else ''

    line('Documentos aceites', size=12, bold=True, gap=8)
    line(f'Termos e Condições — versão {acceptance.terms_version}')
    line(f'Política de Privacidade — versão {acceptance.privacy_version}')
    y -= 3 * mm

    line('Identificação', size=12, bold=True, gap=8)
    if full_name:
        line(f'Nome: {full_name}')
    line(f'E-mail: {acceptance.email_snapshot}')
    if acceptance.client_name_snapshot:
        line(f'Cliente: {acceptance.client_name_snapshot}')
    line(f'Contexto: {acceptance.get_context_display()}')
    y -= 3 * mm

    line('Prova digital', size=12, bold=True, gap=8)
    line(f'Data e hora (UTC): {accepted_at}')
    line(f'Endereço IP: {acceptance.ip_address or "—"}')
    location = ' · '.join(part for part in (acceptance.country_code, acceptance.region) if part) or '—'
    line(f'Localização aproximada: {location}')
    line(f'Dispositivo: {acceptance.device or "—"}')
    ua = (acceptance.user_agent or '')[:110]
    line(f'User-agent: {ua}')
    line(f'Referência: {acceptance.id}')

    y -= 8 * mm
    pdf.setFont('Helvetica-Oblique', 8)
    pdf.drawString(
        left,
        y,
        'Aceitação eletrónica simples registada ao abrigo do RGPD (UE 2016/679). Documento gerado automaticamente.',
    )

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
