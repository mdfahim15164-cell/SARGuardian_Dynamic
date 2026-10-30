import { useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { importLibrary, setOptions } from '@googlemaps/js-api-loader';
import type { RiverShiftGeoJSON, RiverShiftReport } from '../riverShift/manifest';
import { parseRiverShiftGeoJSON, parseRiverShiftReport } from '../riverShift/manifest';
import './river-shift.css';

type Props = { onHome: () => void };

type CatalogueProduct = {
  granule_name: string;
  product_type: 'GCOV';
  maturity: 'BETA' | 'PROVISIONAL' | 'UNKNOWN';
  download_url?: string | null;
  start_time_utc?: string | null;
  stop_time_utc?: string | null;
  flight_direction?: string | null;
  relative_orbit?: string | null;
  cycle?: string | null;
  frame?: string | null;
  bandwidth_mode?: string | null;
  polarization_code?: string | null;
  main_band_polarization?: string | null;
  size_mb?: number | null;
};

type CatalogueResponse = {
  mode: 'catalogue_only';
  status: 'ready' | 'no_data' | 'upstream_error';
  message: string;
  data_downloaded: false;
  scientific_analysis_performed: false;
  product_count: number;
  products: CatalogueProduct[];
  warnings: string[];
  query: Record<string, unknown>;
};

const API_BASE = ((import.meta.env.VITE_SARGUARDIAN_API_URL as string | undefined) || 'http://localhost:8000')
  .trim()
  .replace(/\/+$/, '');
const GOOGLE_MAPS_KEY = (import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined) || '';
let mapsConfigured = false;

function parseWktPolygon(wkt: string): [number, number][] {
  const normalized = wkt.trim();
  if (!/^POLYGON\s*\(\(/i.test(normalized) || !/\)\)\s*$/.test(normalized)) {
    throw new Error('AOI must be a single-ring POLYGON WKT.');
  }
  const body = normalized.replace(/^POLYGON\s*\(\(/i, '').replace(/\)\)\s*$/, '');
  const coordinates = body.split(',').map((pair) => {
    const values = pair.trim().split(/\s+/).map(Number);
    if (values.length !== 2 || !Number.isFinite(values[0]) || !Number.isFinite(values[1])) {
      throw new Error('AOI has an invalid longitude/latitude pair.');
    }
    if (values[0] < -180 || values[0] > 180 || values[1] < -90 || values[1] > 90) {
      throw new Error('AOI coordinate is outside WGS84 longitude/latitude limits.');
    }
    return [values[0], values[1]] as [number, number];
  });
  if (coordinates.length < 4) throw new Error('AOI needs 3 vertices plus a closing coordinate.');
  const first = coordinates[0];
  const last = coordinates[coordinates.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    throw new Error('AOI polygon must repeat its first coordinate at the end.');
  }
  return coordinates;
}

function formatDate(value?: string | null): string {
  if (!value) return 'Not supplied';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toISOString().slice(0, 10);
}

function metricLabel(key: string): string {
  const names: Record<string, string> = {
    baseline_water_area_km2: 'Baseline water area',
    peak_water_area_km2: 'Peak water area',
    post_event_water_area_km2: 'Post-event water area',
    newly_water_covered_area_km2: 'New water coverage',
    water_area_change_percent: 'Water-area change',
    persistent_erosion_candidate_area_ha: 'Erosion candidates',
    persistent_deposition_candidate_area_ha: 'Deposition candidates',
    net_candidate_land_change_ha: 'Net candidate land change',
    symmetric_boundary_distance_mean_m: 'Mean boundary distance',
    symmetric_boundary_distance_p95_m: 'P95 boundary distance',
    accuracy: 'Accuracy',
    precision_user_accuracy: 'Precision',
    recall_producer_accuracy: 'Recall',
    f1_score: 'F1 score',
    intersection_over_union: 'Intersection over Union',
    cohen_kappa: 'Cohen’s kappa',
    area_bias_percent: 'Area bias',
  };
  return names[key] || key.replaceAll('_', ' ');
}

function metricUnit(key: string): string {
  if (key.includes('km2')) return 'km²';
  if (key.includes('_ha')) return 'ha';
  if (key.endsWith('_m')) return 'm';
  if (key.includes('percent')) return '%';
  return '';
}

function metricText(key: string, value: number | null): string {
  if (value === null) return 'Unavailable';
  const digits = key.includes('percent') ? 1 : key.includes('area') || key.endsWith('_ha') || key.includes('km2') ? 3 : 3;
  return value.toFixed(digits);
}

function ReportPanel({ report }: { report: RiverShiftReport }) {
  const warnings = report.quality.warnings || [];
  const title = report.analysis_type === 'flood_inundation_screening'
    ? 'Flood inundation screening'
    : report.analysis_type === 'river_morphology_screening'
      ? 'River morphology screening'
      : 'Classification validation';
  const source = report.source;
  return (
    <section className="rs-panel">
      <div className="rs-section-heading">
        <div><p className="rs-kicker">IMPORTED SCIENTIFIC RESULT</p><h2>{title}</h2></div>
        <span className="rs-quality">{report.quality.status.replaceAll('_', ' ')}</span>
      </div>
      <div className="rs-provenance">
        <span>Mission: <strong>{String(source.mission || 'Not stated')}</strong></span>
        <span>Product: <strong>{String(source.product || 'Not stated')}</strong></span>
        <span>Maturity: <strong>{String(source.maturity || 'Not stated')}</strong></span>
        <span>Frequency: <strong>{String(source.frequency || 'Not stated')}</strong></span>
        <span>Term: <strong>{String(source.covariance_term || 'Not stated')}</strong></span>
      </div>
      <div className="rs-metric-grid">
        {Object.entries(report.metrics).map(([key, value]) => (
          <article className="rs-metric" key={key}>
            <span>{metricLabel(key)}</span>
            <strong>{metricText(key, value)} <small>{metricUnit(key)}</small></strong>
          </article>
        ))}
      </div>
      {report.reference && (
        <div className="rs-reference">
          Reference: <strong>{String(report.reference.source || 'Not stated')}</strong>
          <span>{String(report.reference.date || 'Date not stated')}</span>
          <p>{String(report.reference.method || 'Reference method not stated')}</p>
        </div>
      )}
      {warnings.length > 0 && (
        <div className="rs-warning-list">
          <strong>Scientific interpretation and limitations</strong>
          {warnings.map((warning, index) => <p key={index}>• {warning}</p>)}
        </div>
      )}
    </section>
  );
}

export function RiverShiftPage({ onHome }: Props) {
  const [aoiWkt, setAoiWkt] = useState('');
  const [startDate, setStartDate] = useState('2026-06-17');
  const [endDate, setEndDate] = useState('2026-10-31');
  const [maturity, setMaturity] = useState<'BETA' | 'PROVISIONAL' | 'ALL'>('PROVISIONAL');
  const [polarization, setPolarization] = useState('');
  const [direction, setDirection] = useState('');
  const [catalogue, setCatalogue] = useState<CatalogueResponse | null>(null);
  const [catalogueBusy, setCatalogueBusy] = useState(false);
  const [catalogueError, setCatalogueError] = useState('');
  const [report, setReport] = useState<RiverShiftReport | null>(null);
  const [reportError, setReportError] = useState('');
  const [geoJSON, setGeoJSON] = useState<RiverShiftGeoJSON | null>(null);
  const [geoJSONError, setGeoJSONError] = useState('');
  const [mapError, setMapError] = useState('');
  const mapElement = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<google.maps.Map | null>(null);

  const searchCatalogue = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCatalogueError('');
    setCatalogue(null);
    setCatalogueBusy(true);
    try {
      const coordinates = parseWktPolygon(aoiWkt);
      const response = await fetch(API_BASE + '/api/river-shift/catalog/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          coordinates,
          start_date: startDate,
          end_date: endDate,
          maturity,
          main_band_polarization: polarization || null,
          flight_direction: direction || null,
          max_results: 100,
        }),
      });
      const payload = await response.json() as CatalogueResponse | { detail?: string };
      if (!response.ok) {
        const detail = 'detail' in payload && payload.detail ? payload.detail : 'Catalogue request failed (' + response.status + ').';
        throw new Error(detail);
      }
      setCatalogue(payload as CatalogueResponse);
    } catch (error) {
      setCatalogueError(error instanceof Error ? error.message : 'Could not search the ASF catalogue.');
    } finally {
      setCatalogueBusy(false);
    }
  };

  const loadReport = async (file?: File) => {
    if (!file) return;
    setReportError('');
    setReport(null);
    try {
      const payload = JSON.parse(await file.text()) as unknown;
      setReport(parseRiverShiftReport(payload));
    } catch (error) {
      setReportError(error instanceof Error ? error.message : 'Could not read the result JSON.');
    }
  };

  const loadGeoJSON = async (file?: File) => {
    if (!file) return;
    setGeoJSONError('');
    setGeoJSON(null);
    try {
      const payload = JSON.parse(await file.text()) as unknown;
      setGeoJSON(parseRiverShiftGeoJSON(payload));
    } catch (error) {
      setGeoJSONError(error instanceof Error ? error.message : 'Could not read the GeoJSON.');
    }
  };

  useEffect(() => {
    if (!GOOGLE_MAPS_KEY || !mapElement.current) {
      if (!GOOGLE_MAPS_KEY) setMapError('Google Maps API key is not configured. The GeoJSON download remains available for QGIS.');
      return;
    }
    let cancelled = false;
    if (!mapsConfigured) {
      setOptions({ key: GOOGLE_MAPS_KEY, v: 'weekly' });
      mapsConfigured = true;
    }
    importLibrary('maps').then((mapsLibrary) => {
      if (cancelled || !mapElement.current) return;
      const maps = mapsLibrary as google.maps.MapsLibrary;
      const map = mapInstance.current || new maps.Map(mapElement.current, {
        center: { lat: 25.2, lng: 89.6 },
        zoom: 9,
        mapTypeId: 'satellite',
        streetViewControl: false,
        mapTypeControl: true,
        fullscreenControl: true,
      });
      mapInstance.current = map;
      map.data.forEach((feature) => map.data.remove(feature));
      if (geoJSON) {
        map.data.addGeoJson(geoJSON as unknown as object);
        map.data.setStyle((feature) => {
          const name = String(feature.getProperty('class') || feature.getProperty('change_type') || '').toLowerCase();
          const colour = name.includes('erosion') ? '#f07462'
            : name.includes('deposition') ? '#5fd7a5'
              : '#53b9f4';
          return { fillColor: colour, strokeColor: colour, fillOpacity: 0.30, strokeWeight: 2 };
        });
        const bounds = new google.maps.LatLngBounds();
        map.data.forEach((feature) => {
          const geometry = feature.getGeometry();
          if (geometry) geometry.forEachLatLng((point) => bounds.extend(point));
        });
        if (!bounds.isEmpty()) map.fitBounds(bounds);
      }
    }).catch((error: unknown) => {
      if (!cancelled) setMapError(error instanceof Error ? error.message : 'Google Maps could not be loaded.');
    });
    return () => { cancelled = true; };
  }, [geoJSON]);

  const resultType = useMemo(() => report ? report.analysis_type.replaceAll('_', ' ') : 'No result imported', [report]);

  return (
    <main className="river-shift-page">
      <header className="rs-header">
        <button className="rs-back" onClick={onHome} type="button">← SARGuardian</button>
        <div className="rs-brand">
          <span className="rs-brand-mark">RS</span>
          <div><strong>RiverShift</strong><small>FLOOD & RIVER CHANGE INTELLIGENCE</small></div>
        </div>
        <span className="rs-challenge-tag">NASA SPACE APPS 2026 · DANCING WITH THE SARS</span>
      </header>

      <section className="rs-hero">
        <div>
          <p className="rs-kicker">NISAR-POWERED SURFACE CHANGE MONITORING</p>
          <h1>Track the river.<br /><em>Measure the change.</em></h1>
          <p className="rs-intro">
            Discover real NISAR GCOV acquisitions, inspect reproducible RiverShift analysis reports,
            and compare observed floodwater and persistent river-change candidates.
          </p>
          <div className="rs-hero-tags">
            <span>NASA-ISRO NISAR</span><span>GCOV · L-BAND</span><span>ASF DAAC</span>
          </div>
        </div>
        <div className="rs-hero-visual" aria-hidden="true">
          <div className="rs-river-contour rs-contour-one" />
          <div className="rs-river-contour rs-contour-two" />
          <div className="rs-river-contour rs-contour-three" />
          <div className="rs-river-dot rs-dot-one" /><div className="rs-river-dot rs-dot-two" /><div className="rs-river-dot rs-dot-three" />
          <span>RIVER SYSTEM<br />CHANGE OBSERVATORY</span>
        </div>
      </section>

      <section className="rs-workspace-grid">
        <div className="rs-panel">
          <div className="rs-section-heading">
            <div><p className="rs-kicker">01 · DATA DISCOVERY</p><h2>Find NISAR GCOV acquisitions</h2></div>
            <span className="rs-chip">LIVE ASF CATALOGUE</span>
          </div>
          <p className="rs-muted">
            Search metadata from the ASF DAAC archive. This action does not download products or run scientific analysis.
          </p>
          <form onSubmit={searchCatalogue} className="rs-form">
            <label className="rs-field rs-field-full">
              <span>Study area · WGS84 Polygon WKT</span>
              <textarea value={aoiWkt} onChange={(event) => setAoiWkt(event.target.value)}
                placeholder="Paste a closed POLYGON ((longitude latitude, ...)) from ASF Vertex."
                rows={4} required />
              <small>Coordinates are longitude, latitude. Use the exact same AOI for every selected acquisition.</small>
            </label>
            <div className="rs-fields-two">
              <label className="rs-field"><span>Start date</span><input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required /></label>
              <label className="rs-field"><span>End date</span><input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} required /></label>
              <label className="rs-field"><span>Processing maturity</span>
                <select value={maturity} onChange={(event) => setMaturity(event.target.value as typeof maturity)}>
                  <option value="PROVISIONAL">PROVISIONAL</option><option value="BETA">BETA</option><option value="ALL">ALL (audit only)</option>
                </select>
              </label>
              <label className="rs-field"><span>Frequency A polarization</span>
                <select value={polarization} onChange={(event) => setPolarization(event.target.value)}>
                  <option value="">Any</option><option value="VV">VV</option><option value="VV+VH">VV + VH</option>
                  <option value="HH">HH</option><option value="HH+HV">HH + HV</option><option value="HH+VV">HH + VV</option>
                  <option value="HH+HV+VH+VV">Full quad-pol</option><option value="LH+LV">LH + LV</option><option value="RH+RV">RH + RV</option>
                </select>
              </label>
              <label className="rs-field rs-field-full"><span>Orbit direction</span>
                <select value={direction} onChange={(event) => setDirection(event.target.value)}>
                  <option value="">Any direction</option><option value="ASCENDING">Ascending</option><option value="DESCENDING">Descending</option>
                </select>
              </label>
            </div>
            <button className="rs-primary-button" type="submit" disabled={catalogueBusy}>
              {catalogueBusy ? 'Searching ASF…' : 'Search GCOV archive'}
            </button>
            {catalogueError && <p className="rs-error" role="alert">{catalogueError}</p>}
          </form>
          {catalogue && (
            <div className="rs-catalogue-result">
              <div className="rs-result-summary"><strong>{catalogue.product_count} product(s)</strong><span>{catalogue.message}</span></div>
              <div className="rs-info-banner">Catalogue discovery only · Data downloaded: No · Scientific analysis: Not performed</div>
              {catalogue.warnings.map((warning, index) => <p className="rs-warning-inline" key={index}>{warning}</p>)}
              {catalogue.products.length > 0 && (
                <div className="rs-table-wrap">
                  <table className="rs-table">
                    <thead><tr><th>Acquisition</th><th>Track / frame</th><th>Mode / pol.</th><th>Maturity</th><th>Product</th></tr></thead>
                    <tbody>
                      {catalogue.products.map((product) => (
                        <tr key={product.granule_name}>
                          <td>{formatDate(product.start_time_utc)}</td>
                          <td>{product.flight_direction || '—'}<small>R{product.relative_orbit || '—'} · F{product.frame || '—'}</small></td>
                          <td>{product.bandwidth_mode || '—'}<small>{product.main_band_polarization || product.polarization_code || '—'}</small></td>
                          <td><span className={'rs-maturity rs-' + product.maturity.toLowerCase()}>{product.maturity}</span></td>
                          <td>{product.download_url
                            ? <a href={product.download_url} target="_blank" rel="noreferrer">Open ASF product ↗</a>
                            : <span>URL unavailable</span>}
                            <small>{product.granule_name}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

        <aside className="rs-panel rs-pipeline-panel">
          <p className="rs-kicker">02 · SCIENTIFIC WORKFLOW</p>
          <h2>From radar to evidence</h2>
          <ol className="rs-pipeline">
            <li><b>Discover</b><span>Find actual NISAR GCOV products in ASF DAAC.</span></li>
            <li><b>Prepare</b><span>Inspect HDF5, check maturity, extract the same diagonal term and clip the same AOI.</span></li>
            <li><b>Detect</b><span>Screen open water on comparable pre-event, flood-period and post-event observations.</span></li>
            <li><b>Measure</b><span>Quantify water coverage and persistent land/water transitions.</span></li>
            <li><b>Validate</b><span>Compare against an independent reference and report F1/IoU.</span></li>
          </ol>
          <a className="rs-doc-link" href="https://nisar-docs.asf.alaska.edu/gcov/" target="_blank" rel="noreferrer">NISAR GCOV product guide ↗</a>
          <a className="rs-doc-link" href="https://docs.asf.alaska.edu/api/keywords/" target="_blank" rel="noreferrer">ASF Search API documentation ↗</a>
          <a className="rs-doc-link" href="https://nisar-docs.asf.alaska.edu/availability-overview/" target="_blank" rel="noreferrer">NISAR data availability & maturity ↗</a>
        </aside>
      </section>

      <section className="rs-panel rs-results-panel">
        <div className="rs-section-heading">
          <div><p className="rs-kicker">03 · RESULTS EXPLORER</p><h2>Inspect reproducible outputs</h2></div>
          <span className="rs-chip">NO SYNTHETIC METRICS</span>
        </div>
        <p className="rs-muted">
          Run the documented CLI scripts in tools/river_shift, then import their result JSON and GeoJSON here.
          Catalogue rows are never presented as measured flood or erosion results.
        </p>
        <div className="rs-upload-grid">
          <label className="rs-upload"><span>Import result JSON</span><small>Flood, morphology or validation report</small>
            <input type="file" accept=".json,application/json" onChange={(event) => void loadReport(event.target.files?.[0])} />
          </label>
          <label className="rs-upload"><span>Import change GeoJSON</span><small>Erosion, deposition or new-water polygons</small>
            <input type="file" accept=".geojson,.json,application/geo+json,application/json" onChange={(event) => void loadGeoJSON(event.target.files?.[0])} />
          </label>
        </div>
        {reportError && <p className="rs-error" role="alert">{reportError}</p>}
        {geoJSONError && <p className="rs-error" role="alert">{geoJSONError}</p>}
        {report && <ReportPanel report={report} />}
        <section className="rs-map-section">
          <div className="rs-section-heading"><div><p className="rs-kicker">GEOSPATIAL OUTPUT</p><h3>Change map</h3></div></div>
          {mapError && <p className="rs-warning-inline">{mapError}</p>}
          <div className="rs-map" ref={mapElement} role="img" aria-label="Satellite basemap with imported RiverShift GeoJSON change polygons" />
          {geoJSON && <p className="rs-muted">{geoJSON.features.length} GeoJSON feature(s) loaded. Use the layer and date legend from the source report when interpreting polygons.</p>}
        </section>
        {!report && <div className="rs-empty-state"><strong>{resultType}</strong><p>No scientific result is loaded. Run a script and import its JSON report; no demo measurement is shown here.</p></div>}
      </section>

      <footer className="rs-footer">
        <span>SARGuardian · RiverShift</span><span>Open science · Reproducible processing · Evidence before claims</span>
      </footer>
    </main>
  );
}
