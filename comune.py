# Parti in comune dei lavori del radar (Austria, Slovacchia): scala di colori unica, proiezione Web Mercator, caricamento su dati.barbel.app.
# Le chiavi del server arrivano dalle variabili R2_ACCESS_KEY_ID e R2_SECRET_ACCESS_KEY (GitHub Actions) oppure, in locale, da dati/r2.txt.
import io, math, mimetypes, os

import numpy as np

# scala unica (come lib/radar.ts COLORI_DBZ): r, g, b, dBZ
UNI = np.array([[56, 0, 112, 4], [48, 0, 168, 8], [0, 0, 252, 12], [0, 108, 192, 16], [0, 160, 0, 20], [0, 188, 0, 24], [52, 216, 0, 28], [156, 220, 0, 32],
                [224, 220, 0, 36], [252, 176, 0, 40], [252, 132, 0, 44], [252, 88, 0, 48], [252, 0, 0, 52], [160, 0, 0, 56], [252, 252, 252, 60]], dtype=float)
R = 6378137.0
ACCOUNT = '4b123daabde3ddcbe8320e68a26bc5dc'
BUCKET = 'barbel-dati'


def merc_x(lng): return R * math.radians(lng)
def merc_y(lat): return R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
def inv_x(x): return np.degrees(np.asarray(x) / R)
def inv_y(y): return np.degrees(2 * np.arctan(np.exp(np.asarray(y) / R)) - math.pi / 2)


def griglia_merc(sud, nord, ovest, est, larghezza):
    """Coordinate (lng, lat) del centro di ogni pixel di un'immagine in Web Mercator che copre il riquadro."""
    x0, x1, y0, y1 = merc_x(ovest), merc_x(est), merc_y(sud), merc_y(nord)
    h = round(larghezza * (y1 - y0) / (x1 - x0))
    xs = x0 + (np.arange(larghezza) + 0.5) / larghezza * (x1 - x0)
    ys = y1 - (np.arange(h) + 0.5) / h * (y1 - y0)
    xx, yy = np.meshgrid(xs, ys)
    return inv_x(xx), inv_y(yy), h


def immagine_da_dbz(dbz, minimo=8.0, alfa=235):
    """dBZ (nan dove non c'e' pioggia) -> RGBA con il colore, della scala unica, di intensita' piu' vicina."""
    valido = np.isfinite(dbz) & (dbz >= minimo)
    d = np.where(valido, dbz, 0.0)
    idx = np.abs(d[..., None] - UNI[:, 3][None, None, :]).argmin(axis=2)
    img = np.zeros(dbz.shape + (4,), dtype=np.uint8)
    img[..., :3] = UNI[idx][..., :3].astype(np.uint8)
    img[..., 3] = np.where(valido, alfa, 0).astype(np.uint8)
    return img


def chiavi():
    a, b = os.environ.get('R2_ACCESS_KEY_ID'), os.environ.get('R2_SECRET_ACCESS_KEY')
    if a and b:
        return a.strip(), b.strip()
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'r2.txt')
    d = dict(r.split('=', 1) for r in io.open(p, encoding='utf-8').read().splitlines() if '=' in r)
    return d['ACCESS_KEY_ID'].strip(), d['SECRET_ACCESS_KEY'].strip()


def carica_cartella(cartella, prefisso):
    """Carica i file di una cartella in dati.barbel.app/<prefisso>/ (senza cache lunga: i radar cambiano a ogni giro)."""
    try:
        import truststore
        truststore.inject_into_ssl()
    except Exception:
        pass
    import boto3
    from botocore.config import Config
    a, b = chiavi()
    s3 = boto3.client('s3', endpoint_url='https://%s.r2.cloudflarestorage.com' % ACCOUNT, aws_access_key_id=a, aws_secret_access_key=b, region_name='auto',
                      config=Config(signature_version='s3v4', retries={'max_attempts': 5}))
    n = 0
    for f in sorted(os.listdir(cartella)):
        if not (f.endswith('.png') or f.endswith('.json')):
            continue
        tipo = 'application/json; charset=utf-8' if f.endswith('.json') else 'image/png'
        s3.put_object(Bucket=BUCKET, Key='%s/%s' % (prefisso, f), Body=open(os.path.join(cartella, f), 'rb').read(), ContentType=tipo, CacheControl='no-cache')
        n += 1
    return n
