"""Portões do render v2 (2.4.5) — usados por engine/v2/produce.py e engine/assemble_languages.py.

- qa_blocking: lê o relatório do QA do makeshorts; no bloco, só a duração é dispensada (vale no vídeo inteiro).
- fingerprint/can_reuse: o recibo "rendered" só é reaproveitado se os insumos e os parâmetros forem os mesmos.
- build_problem: no reel, o build tem de ter passado no --strict; fora dele, fallback continua proibido.
"""
from pathlib import Path
import hashlib, json

DURATION_ITEM = 'duração'


def qa_blocking(report_path, ignore_duration):
    """Lista de itens que reprovam. Relatório ausente ou ilegível também reprova."""
    try:
        rep = json.loads(Path(report_path).read_text(encoding='utf-8'))
        checks = rep['checks']
    except (OSError, ValueError, KeyError, TypeError):
        return ['relatório do QA ausente ou ilegível']
    return [c['item'] for c in checks
            if c.get('status') == 'FALHA' and not (ignore_duration and c.get('item') == DURATION_ITEM)]


def fingerprint(project, params):
    """sha256 dos arquivos do bloco + parâmetros do render. O avatar (symlink, centenas de MB) entra por
    caminho, tamanho e mtime do alvo — trocar o MP4 do HeyGen muda a impressão sem ler o arquivo todo."""
    project = Path(project)
    h = hashlib.sha256(json.dumps(params, sort_keys=True).encode())
    for p in sorted(project.rglob('*')):
        rel = p.relative_to(project).as_posix()
        if p.is_symlink():
            t = p.resolve()
            st = t.stat() if t.exists() else None
            h.update(f'L {rel} {t} {st and st.st_size} {st and st.st_mtime_ns}\n'.encode())
        elif p.is_file():
            h.update(f'F {rel}\n'.encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def can_reuse(rec, out, fp):
    """Recibo antigo (sem impressão) não é reaproveitado: renderiza de novo, que é local e sem custo de HeyGen."""
    return bool(rec) and rec.get('status') == 'rendered' and rec.get('fingerprint') == fp and Path(out).exists()


def build_problem(report, reel):
    """Motivo para não renderizar o bloco, ou None."""
    if any('fallback' in w for w in report.get('warnings', [])):
        return 'cenas sem roteiro visual (fallback)'
    if reel:
        v = report.get('validation') or {}
        if not (v.get('strict') and v.get('ok')):
            return 'reel exige build aprovado no --strict (rode build_block.py N --strict e corrija os avisos)'
    return None
