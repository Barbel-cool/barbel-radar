# Radar pioggia DE / AT / SK - ricerca (verificata il 2026-10-12, UA BarbelApp/1.0)

## Tabella
| Paese | Fonte | Endpoint verificato | Copertura | Passi / previsione | Licenza | Attribuzione |
|---|---|---|---|---|---|---|
| DE | DWD WMS `dwd:Niederschlagsradar` (= RV, mm/h) | SI (PNG RGBA trasparente, 3857) | Germania + ~150 km oltre confine (180 km dal 24.11.2026). Austria solo ovest di ~14E (Tirolo, Salisburgo, Alta Austria ovest); Vienna, Slovacchia: NO. Cechia ovest parziale | 5 min; storico ~3 giorni; previsione +2 h (time esteso oltre "adesso") | DWD: riuso con CC BY 4.0 + Quellenvermerk (ex GeoNutzV, uso commerciale ok). Il testo esatto dei Nutzungsbedingungen non e' stato letto da pagina dedicata: da ricontrollare | "Datenquelle: Deutscher Wetterdienst, Radarkomposit RV" + "verändert" se ricolorato |
| AT | GeoSphere Nowcast `nowcast-v1-15min-1km` (INCA) | SI, ma NON immagini: GeoJSON/NetCDF numerico, griglia EPSG:31287 | Austria + bordo (45.5-49.5N, 8.1-17.7E) | 15 min, +3 h (12 passi, rr = mm/15 min); NESSUN passato radar (storico INCA solo 1 h) | CC BY 4.0 | "Datenquelle: GeoSphere Austria (CC BY 4.0)" |
| AT | WMS/WMTS/PNG radar GeoSphere | NO: non esiste nel data hub (solo radar singolo Hochficht) | - | - | - | - |
| SK | SHMU opendata `skcomp` | SI, ma HDF5 (ODIM) non PNG | Slovacchia (~46.05-50.7N, 13.6-23.79E per l'overlay del sito) | 5 min, nessuna previsione | CC BY 4.0 (README opendata.shmu.sk). I PNG del sito www.shmu.sk sono "proprieta' intellettuale SHMU": NON riusabili senza consenso | "Zdroj: SHMÚ (CC BY 4.0)" |
| EU | OPERA / MeteoGate Open Radar Data API | NO (richiede API key e termini non verificati) | Europa | 5-15 min | non confermata (storica: solo ricerca) | - |
| EU | RainViewer | verificato sulla pagina | globale | solo passato, zoom 7 | solo personale/educativo; commerciale su accordo. NON usare | - |
| EU | Open-Meteo `minutely_15` | SI (JSON) | Europa | 15 min, -1 h/+2 h, non immagini | CC BY 4.0 dati; API gratuita non commerciale (plan a pagamento per app commerciali) | "Weather data by Open-Meteo.com" |

## Esempi funzionanti
DE GetMap (200, image/png, 17 KB, non vuoto; 512x512 tutta la Germania):
https://maps.dwd.de/geoserver/ows?service=WMS&version=1.3.0&request=GetMap&layers=dwd:Niederschlagsradar&styles=&crs=EPSG:3857&format=image/png&transparent=true&width=512&height=512&bbox=162894,5729950,2085194,7602217&time=2026-10-12T14:40:00Z

- bbox massimo 3857: 162894,5729950,2085194,7602217. Layer alternativi: dwd:Radar_rv_product_1x1km_ger (stesso), dwd:Radar_wn-product_1x1km_ger (WN, analisi+previsione), dwd:Radar_wn-analysis_1x1km_ger (solo analisi). Radar_eucom_zeros e' solo una maschera no-data; il layer eucom-zhproduct NON e' nel GetCapabilities. Nessun composito europeo utile.
- TIME: ISO8601 `2026-10-12T14:40:00Z`, extent `inizio/fine/PT5M` (fine = ora + 2 h di previsione); REFERENCE_TIME = ora del run. Un TIME fuori extent (16:45) restituisce XML d'errore (text/xml), non immagine: controllare Content-Type.
- Legenda: ...&request=GetLegendGraphic&format=image/png&layer=dwd:Niederschlagsradar (200)
- Capabilities: https://maps.dwd.de/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities (~1 MB: leggere solo la dimensione time lato server)

AT metadata (ROUTE CORRETTA: /grid/**forecast**/, non /grid/nowcast/):
https://dataset.api.hub.geosphere.at/v1/grid/forecast/nowcast-v1-15min-1km/metadata
Dati puntuali/griglia GeoJSON (200):
https://dataset.api.hub.geosphere.at/v1/grid/forecast/nowcast-v1-15min-1km?parameters=rr&bbox=48.1,16.3,48.3,16.5&output_format=geojson
NetCDF tutta Austria (200, 750 KB, GET):
https://dataset.api.hub.geosphere.at/v1/grid/forecast/nowcast-v1-15min-1km?parameters=rr&bbox=45.5,8.1,49.5,17.7&output_format=netcdf&forecast_offset=0
Elenco dataset: https://dataset.api.hub.geosphere.at/v1/datasets ; docs: https://dataset.api.hub.geosphere.at/v1/docs/
Per avere immagini serve un renderer lato server (cron: NetCDF -> PNG 3857, come per CHMU).

SK file raw 5 min (HDF5, ~50 KB):
https://opendata.shmu.sk/meteorology/weather/radar/composite/skcomp/zmax/20261012/T_PABV22_C_LZIB_20261012144500.hdf
Prodotti: zmax, cappi2km, etop, pac01 (accumulo 1 h). Metadati/proiezione: .../composite/metadata/Radar_udaje_SHMU_SK.pdf (non letto).
(Solo informativo, NON usare: https://www.shmu.sk/api/v1/meteo/getradardata e https://www.shmu.sk/data/dataradary/data.cmax/cmax.kruh.20261012.1440.0.png, 800x550, ~3 giorni di storico, nessuna previsione; termini del sito restrittivi.)

Open-Meteo:
https://api.open-meteo.com/v1/forecast?latitude=48.2&longitude=16.37&minutely_15=precipitation&past_minutely_15=4&forecast_minutely_15=8&timezone=UTC

## Raccomandazione
- DE: usare WMS DWD direttamente (nessun server necessario); GetMap per bbox della vista, TIME ogni 5 min da -60 a +120. Attribuzione + nota "verändert" se si ricolora.
- AT: copertura radar immagini = solo il pezzo ovest dal DWD (fino a ~14E). Per il resto servono un job server (NetCDF GeoSphere nowcast -> PNG, solo futuro +3 h) oppure fallback Open-Meteo minutely_15 per punto. Nessun passato.
- SK: pipeline server da HDF5 opendata (CC BY 4.0) -> PNG 3857 ogni 5 min, nessuna previsione. Non usare i PNG del sito.
- Mai RainViewer. OPERA: da riverificare (chiave API, licenza).
- Incertezze: testo esatto licenza DWD/Open-Meteo e attribuzione AT non letti da pagina ufficiale dedicata; copertura AT/SK dedotta da immagine a bassa risoluzione e dai bound del sito.
