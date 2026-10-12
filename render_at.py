# Radar dell'Austria: dalla previsione a breve (nowcast INCA, 1 km, ogni 15 minuti per 3 ore) di GeoSphere Austria (CC BY 4.0) a immagini PNG
# in Web Mercator con la scala di colori unica di Barbel, pubblicate su dati.barbel.app/radar/at/ con un file latest.json.
# Uso:  python render_at.py [--carica]      Attribuzione richiesta: "Datenquelle: GeoSphere Austria".
import calendar, json, os, sys, time, urllib.request

import h5py
import numpy as np
from PIL import Image
from pyproj import CRS, Transformer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comune as C

URL = 'https://dataset.api.hub.geosphere.at/v1/grid/forecast/nowcast-v1-15min-1km?parameters=rr&bbox=45.5,8.1,49.5,17.7&output_format=netcdf&forecast_offset=0'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'at')
LARGHEZZA = 900


def main():
    os.makedirs(OUT, exist_ok=True)
    rq = urllib.request.Request(URL, headers={'User-Agent': 'BarbelApp/1.0 (hello@barbel.app)'})
    tmp = os.path.join(OUT, 'nowcast.nc')
    open(tmp, 'wb').write(urllib.request.urlopen(rq, timeout=90).read())
    f = h5py.File(tmp, 'r')
    rr = np.array(f['rr'][:], dtype=float)  # (tempo, y, x), mm in 15 minuti
    lat, lon = np.array(f['lat'][:]), np.array(f['lon'][:])
    x, y = np.array(f['x'][:]), np.array(f['y'][:])
    tempo = np.array(f['time'][:])
    unita = f['time'].attrs['units']
    unita = unita.decode() if isinstance(unita, bytes) else str(unita)
    base = calendar.timegm(time.strptime(unita.split('since ')[1].strip(), '%Y-%m-%d %H:%M:%S'))  # secondi UTC
    lcc = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in f['lambert_conformal_conic'].attrs.items()}
    crs_src = CRS.from_cf(lcc)
    sud, nord, ovest, est = float(np.nanmin(lat)), float(np.nanmax(lat)), float(np.nanmin(lon)), float(np.nanmax(lon))
    LNG, LAT, H = C.griglia_merc(sud, nord, ovest, est, LARGHEZZA)
    sx, sy = Transformer.from_crs('EPSG:4326', crs_src, always_xy=True).transform(LNG, LAT)
    ix = np.rint((sx - x[0]) / (x[1] - x[0])).astype(int)
    iy = np.rint((sy - y[0]) / (y[1] - y[0])).astype(int)
    dentro = (ix >= 0) & (ix < len(x)) & (iy >= 0) & (iy < len(y))
    ix, iy = np.clip(ix, 0, len(x) - 1), np.clip(iy, 0, len(y) - 1)
    frames = []
    for k in range(rr.shape[0]):
        mm_ora = rr[k][iy, ix] * 4.0
        valido = dentro & np.isfinite(mm_ora) & (mm_ora >= 0.1)
        dbz = np.full(mm_ora.shape, np.nan)
        dbz[valido] = 10 * np.log10(200) + 16 * np.log10(mm_ora[valido])
        nome = 'f%02d.png' % k
        Image.fromarray(C.immagine_da_dbz(dbz, minimo=8.0), 'RGBA').save(os.path.join(OUT, nome), optimize=True)
        frames.append({'ora': (base + int(tempo[k]) * 60) * 1000, 'file': nome})
    meta = {'creato': int(time.time() * 1000), 'bounds': {'sud': sud, 'ovest': ovest, 'nord': nord, 'est': est}, 'px': {'w': LARGHEZZA, 'h': H}, 'frames': frames,
            'fonte': 'Datenquelle: GeoSphere Austria (CC BY 4.0), Nowcast INCA'}
    open(os.path.join(OUT, 'latest.json'), 'w', encoding='utf-8').write(json.dumps(meta))
    f.close()
    os.remove(tmp)
    print('AT pronto:', len(frames), 'immagini', LARGHEZZA, 'x', H, '| primo istante', time.strftime('%H:%M UTC', time.gmtime(frames[0]['ora'] / 1000)))
    if '--carica' in sys.argv:
        print('AT caricati', C.carica_cartella(OUT, 'radar/at'), 'file')


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # il motivo si vede nelle annotazioni di GitHub (mai contiene le chiavi)
        print('::error::%s: %s' % (type(e).__name__, str(e)[:400]))
        sys.exit(1)
