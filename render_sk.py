# Radar della Slovacchia: dai file HDF5 (ODIM) del composito radar di SHMÚ (opendata.shmu.sk, CC BY 4.0) a immagini PNG in Web Mercator con la scala unica di Barbel.
# Le ultime 12 immagini (un'ora, una ogni 5 minuti), nessuna previsione. Pubblicate su dati.barbel.app/radar/sk/ con latest.json.
# Uso:  python render_sk.py [--carica]      Attribuzione richiesta: "Zdroj: SHMÚ".
import calendar, json, os, re, sys, time, urllib.request

import h5py
import numpy as np
from PIL import Image
from pyproj import Transformer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comune as C

BASE = 'https://opendata.shmu.sk/meteorology/weather/radar/composite/skcomp/zmax/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'sk')
LARGHEZZA = 1000
UA = {'User-Agent': 'BarbelApp/1.0 (hello@barbel.app)'}


def leggi(url, binario=False):
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    return d if binario else d.decode('utf-8', 'replace')


def ultimi_file(n=12):
    """I nomi delle ultime n immagini (oggi e, se servono, ieri), dalla piu' vecchia."""
    out = []
    for giorno in (time.strftime('%Y%m%d', time.gmtime()), time.strftime('%Y%m%d', time.gmtime(time.time() - 86400))):
        try:
            elenco = sorted(set(re.findall(r'T_PABV22_C_LZIB_(\d{14})\.hdf', leggi(BASE + giorno + '/'))))
        except Exception:
            continue
        out = [(giorno, e) for e in elenco] + out
        if len(out) >= n:
            break
    return out[-n:]


def main():
    os.makedirs(OUT, exist_ok=True)
    elenco = ultimi_file(12)
    if not elenco:
        print('SK: nessun file disponibile')
        sys.exit(1)
    griglia = None
    frames = []
    for giorno, stamp in elenco:
        tmp = os.path.join(OUT, 'sk.hdf')
        open(tmp, 'wb').write(leggi('%s%s/T_PABV22_C_LZIB_%s.hdf' % (BASE, giorno, stamp), True))
        f = h5py.File(tmp, 'r')
        w = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in f['where'].attrs.items()}
        q = f['dataset1/what'].attrs
        gain, offset = float(q['gain']), float(q['offset'])
        raw = np.array(f['dataset1/data1/data'][:], dtype=float)
        f.close()
        if griglia is None:
            sud, nord, ovest, est = float(w['LL_lat']), float(w['UL_lat']), float(w['UL_lon']), float(w['UR_lon'])
            LNG, LAT, H = C.griglia_merc(sud, nord, ovest, est, LARGHEZZA)
            tr = Transformer.from_crs('EPSG:4326', w['projdef'], always_xy=True)
            ulx, uly = tr.transform(float(w['UL_lon']), float(w['UL_lat']))
            sx, sy = tr.transform(LNG, LAT)
            ix = np.floor((sx - ulx) / float(w['xscale'])).astype(int)
            iy = np.floor((uly - sy) / float(w['yscale'])).astype(int)
            dentro = (ix >= 0) & (ix < int(w['xsize'])) & (iy >= 0) & (iy < int(w['ysize']))
            ix, iy = np.clip(ix, 0, int(w['xsize']) - 1), np.clip(iy, 0, int(w['ysize']) - 1)
            griglia = (sud, nord, ovest, est, H)
        r = raw[iy, ix]
        dbz = np.where(dentro & (r > 0) & (r < 255), r * gain + offset, np.nan)  # 0 = nessun eco, 255 = fuori copertura; il resto e dBZ
        nome = 'f%02d.png' % len(frames)
        Image.fromarray(C.immagine_da_dbz(dbz, minimo=8.0), 'RGBA').save(os.path.join(OUT, nome), optimize=True)
        ora = calendar.timegm(time.strptime(stamp, '%Y%m%d%H%M%S')) * 1000
        frames.append({'ora': ora, 'file': nome})
    os.remove(os.path.join(OUT, 'sk.hdf'))
    sud, nord, ovest, est, H = griglia
    meta = {'creato': int(time.time() * 1000), 'bounds': {'sud': sud, 'ovest': ovest, 'nord': nord, 'est': est}, 'px': {'w': LARGHEZZA, 'h': H}, 'frames': frames,
            'fonte': 'Zdroj: SHMÚ (CC BY 4.0), composito radar SKCOMP'}
    open(os.path.join(OUT, 'latest.json'), 'w', encoding='utf-8').write(json.dumps(meta))
    print('SK pronto:', len(frames), 'immagini', LARGHEZZA, 'x', H, '| ultimo istante', time.strftime('%H:%M UTC', time.gmtime(frames[-1]['ora'] / 1000)))
    if '--carica' in sys.argv:
        print('SK caricati', C.carica_cartella(OUT, 'radar/sk'), 'file')


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # il motivo si vede nelle annotazioni di GitHub (mai contiene le chiavi)
        print('::error::%s: %s' % (type(e).__name__, str(e)[:400]))
        sys.exit(1)
