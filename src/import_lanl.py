"""Download a bounded, chronological subset of real LANL authentication logs.

No rows, dates, device types or attack labels are generated. Host IDs remain
anonymized host IDs. The compressed prefix is cached for reproducibility.
Run explicitly: python -m src.import_lanl (network required once).
"""
import csv
import gzip
import hashlib
import json
import re
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://lanl.ma.ic.ac.uk/data/cyber1/'
AUTH_COLUMNS = ['time', 'user_id', 'destination_user', 'source_host',
                'destination_host', 'auth_type', 'logon_type', 'orientation', 'outcome']
END_SECONDS = 3 * 86400
MAX_USER_ID = 1000
MAX_BYTES = 512 * 1024 * 1024


def selected(fields):
    """Fixed ID cohort, independent of labels and of model predictions."""
    match = re.fullmatch(rb'U(\d+)@[^,]+', fields[1])
    return (match is not None and int(match[1]) <= MAX_USER_ID
            and fields[7] == b'LogOn' and fields[8] in (b'Success', b'Fail', b'Failure')
            and fields[3] != b'?' and fields[4] != b'?')


def main():
    folder = ROOT / 'data' / 'lanl'
    folder.mkdir(parents=True, exist_ok=True)
    red_path = folder / 'redteam.txt.gz'
    if not red_path.exists():
        with urllib.request.urlopen(BASE+'redteam.txt.gz', timeout=60) as response:
            red_path.write_bytes(response.read(1000000))
    with gzip.open(red_path, 'rt') as handle:
        red = {tuple(row) for row in csv.reader(handle)}
    prefix = folder / 'auth-prefix.gz.part'
    cached = prefix.stat().st_size if prefix.exists() else 0
    def blocks():
        if cached:
            with prefix.open('rb') as handle:
                while block := handle.read(1024*1024):
                    yield block
        request = urllib.request.Request(BASE+'auth.txt.gz', headers={
            'Range': f'bytes={cached}-{MAX_BYTES-1}'})
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 206:
                raise RuntimeError('Server must support bounded Range downloads.')
            if not response.headers.get('Content-Range','').startswith(f'bytes {cached}-'):
                raise RuntimeError('Unexpected download range.')
            with prefix.open('ab') as handle:
                while block := response.read(1024*1024):
                    handle.write(block); handle.flush()
                    yield block
    decoder = zlib.decompressobj(16+zlib.MAX_WBITS)
    pending = b''; scanned = 0; kept = 0; last = 0; consumed = 0; complete = False
    target = folder / 'auth_selected.csv'
    with target.with_suffix('.tmp').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['event_id', *AUTH_COLUMNS, 'redteam_label'])
        stream = blocks()
        try:
            for block in stream:
                consumed += len(block)
                lines = (pending + decoder.decompress(block)).split(b'\n')
                pending = lines.pop()
                for line in lines:
                    line = line.rstrip(b'\r')
                    if not line: continue
                    scanned += 1
                    stamp, user, _ = line.split(b',', 2)
                    last = int(stamp)
                    if last >= END_SECONDS:
                        complete = True; break
                    if not user.startswith(b'U'): continue
                    fields = line.split(b',')
                    if len(fields) != 9 or not selected(fields): continue
                    row = [f.decode('utf-8') for f in fields]
                    label = int((row[0],row[1],row[3],row[4]) in red)
                    writer.writerow([f'LANL-{scanned}',*row,label]); kept += 1
                if consumed % (16*1024*1024) == 0 or complete:
                    print(f'{consumed//1024//1024} MiB; scanned={scanned}; selected={kept}; second={last}', flush=True)
                if complete: break
        finally:
            stream.close()
    if not complete:
        raise RuntimeError('Download budget reached before the 3-day boundary. No dataset activated.')
    target.with_suffix('.tmp').replace(target)
    digest = hashlib.sha256()
    with prefix.open('rb') as handle:
        while block := handle.read(1024*1024): digest.update(block)
    manifest = dict(dataset='LANL Comprehensive, Multi-Source Cyber-Security Events',
        doi='10.17021/1179829', provenance='Real enterprise authentication logs, de-identified by LANL',
        official_page='https://csr.lanl.gov/data/cyber1/', mirror=BASE,
        citation='Alexander D. Kent, Comprehensive, Multi-Source Cybersecurity Events, 2015.',
        cohort='source user U1..U1000, all domains; LogOn; known source/destination hosts',
        start_seconds=1, end_seconds_exclusive=END_SECONDS, train_end_exclusive=2*86400,
        scanned_lines=scanned, selected_rows=kept, compressed_prefix_bytes=prefix.stat().st_size,
        compressed_prefix_sha256=digest.hexdigest(), selected_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        redteam_sha256=hashlib.sha256(red_path.read_bytes()).hexdigest(),
        label_policy='Exact (time, source user, source host, destination host) match. Zero means unannotated, not proven benign.',
        limitations=['Absolute calendar and timezone undisclosed; relative hour only.',
                    'No IP addresses or physical device types in authentication source.',
                    'Fixed early-ID cohort and first three days are not representative of all LANL.',
                    'Failures included by publisher only for users with a success somewhere in full dataset.'])
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=True,indent=2))

if __name__ == '__main__':
    main()
