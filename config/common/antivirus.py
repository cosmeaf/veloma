import logging
import socket
import struct

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192


class ScanResult:
    CLEAN = 'clean'
    INFECTED = 'infected'
    ERROR = 'error'
    SKIPPED = 'skipped'

    def __init__(self, status, message=''):
        self.status = status
        self.message = message[:255]

    def __repr__(self):
        return f'<ScanResult {self.status}: {self.message}>'


class AntivirusService:
    """Minimal ClamAV client speaking the INSTREAM protocol over TCP.

    Implemented directly on top of sockets so the project keeps its current
    dependency set. When the scanner is unreachable the result is `error`; the
    caller decides whether that means quarantine (`require_antivirus`) or not.
    """

    @staticmethod
    def scan_stream(stream, *, host, port, timeout=30):
        if not host:
            return ScanResult(ScanResult.SKIPPED, 'No antivirus host is configured.')
        try:
            with socket.create_connection((host, port), timeout=timeout) as connection:
                connection.settimeout(timeout)
                connection.sendall(b'zINSTREAM\0')
                while True:
                    chunk = stream.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    connection.sendall(struct.pack('!L', len(chunk)) + chunk)
                connection.sendall(struct.pack('!L', 0))
                response = b''
                while b'\0' not in response:
                    received = connection.recv(4096)
                    if not received:
                        break
                    response += received
        except (OSError, socket.timeout) as exc:
            logger.warning('Antivirus scan failed. host=%s port=%s error=%s', host, port, exc)
            return ScanResult(ScanResult.ERROR, f'Scanner unavailable: {exc}')

        text = response.decode('utf-8', errors='replace').strip('\0').strip()
        if text.endswith('OK'):
            return ScanResult(ScanResult.CLEAN, text)
        if 'FOUND' in text:
            return ScanResult(ScanResult.INFECTED, text)
        return ScanResult(ScanResult.ERROR, text or 'Unexpected scanner response.')
