# Radar Austria e Slovacchia: lavoro automatico

Ogni 5 minuti GitHub Actions scarica i dati aperti (SHMÚ per la Slovacchia, GeoSphere Austria per l'Austria), li trasforma in immagini con la scala di colori unica di Barbel
e le pubblica su dati.barbel.app/radar/sk/ e radar/at/. L'app legge da li'.

Per provare a mano (con le chiavi in ../r2.txt):  python render_sk.py --carica   e   python render_at.py --carica

Dati: SHMÚ (CC BY 4.0, "Zdroj: SHMÚ"), GeoSphere Austria (CC BY 4.0, "Datenquelle: GeoSphere Austria").
