import { useMemo, useState, type FormEvent } from 'react';
import type { User } from 'firebase/auth';
import {
  searchRiverShiftGCOVCatalog,
  type RiverShiftCatalogResponse,
  type RiverShiftMaturity,
} from '../../src/api/riverShift';
import './river-shift.css';

type RiverShiftPageProps = {
  user: User;
  onHome: () => void;
  onSignOut: () => void;
};

function parsePolygonWkt(value: string): number[][] {
  const match = value.trim().match(/^POLYGON\s*\(\(\s*(.*?)\s*\)\)$/i);
  if (!match) throw new Error('Enter one WKT POLYGON using longitude latitude pairs.');

  const points = match[1].split(',').map((pair) => {
    const values = pair.trim().split(/\s+/).map(Number);
    if (values.length !== 2 || values.some((item) => !Number.isFinite(item))) {
      throw new Error('Each polygon point must contain exactly two numeric values: longitude latitude.');
    }
    return values;
  });

  if (points.length < 4) throw new Error('The polygon needs at least three vertices and a repeated closing point.');
  const first = points[0];
  const last = points[points.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    throw new Error('The final polygon point must repeat the first point to close the AOI.');
  }
  return points;
}

function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return 'Not reported';
  return `${(bytes / (1024 ** 3)).toFixed(2)} GiB`;
}

export function RiverShiftPage({ user, onHome, onSignOut }: RiverShiftPageProps) {
  const [aoiWkt, setAoiWkt] = useState('');
  const [startDate, setStartDate] = useState('2026-06-17');
  const [endDate, setEndDate] = useState('');
  const [maturity, setMaturity] = useState<RiverShiftMaturity>('PROVISIONAL');
  const [maxResults, setMaxResults] = useState('100');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RiverShiftCatalogResponse | null>(null);

  const dateRangeValid = useMemo(
    () => Boolean(startDate && endDate && startDate <= endDate),
    [startDate, endDate],
  );

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);

    let coordinates: number[][];
    try {
      coordinates = parsePolygonWkt(aoiWkt);
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : 'Invalid AOI polygon.');
      return;
    }
    if (!dateRangeValid) {
      setError('Select a valid date range. End date must not be before start date.');
      return;
    }

    const max = Number(maxResults);
    if (!Number.isInteger(max) || max < 1 || max > 500) {
      setError('Maximum results must be an integer between 1 and 500.');
      return;
    }

    setLoading(true);
    try {
      const response = await searchRiverShiftGCOVCatalog({
        coordinates,
        startDate,
        endDate,
        dataMaturity: maturity,
        maxResults: max,
      }, user);
      setResult(response);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : 'GCOV catalogue search failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="river-shift-page">
      <header className="rs-header">
        <button className="rs-brand" type="button" onClick={onHome} aria-label="Back to SARGuardian home">
          <span className="rs-brand-mark" aria-hidden="true">RS</span>
          <span><strong>SARGuardian</strong><small>RIVERSHIFT ENGINE</small></span>
        </button>
        <div className="rs-header-actions">
          <span className="rs-user">{user.displayName || user.email || 'Signed in'}</span>
          <button type="button" className="rs-quiet-button" onClick={onHome}>All engines</button>
          <button type="button" className="rs-quiet-button" onClick={onSignOut}>Sign out</button>
        </div>
      </header>

      <main className="rs-main">
        <section className="rs-hero">
          <div className="rs-kicker">NASA SPACE APPS 2026 · DANCING WITH THE SARS</div>
          <div className="rs-title-row">
            <div>
              <h1>River<span>Shift</span></h1>
              <p className="rs-subtitle">Flood &amp; River Change Intelligence</p>
            </div>
            <span className="rs-status-pill">PILOT · DATA AUDIT</span>
          </div>
          <p className="rs-intro">
            Track river inundation and persistent channel changes using repeat-pass NISAR radar observations.
            Start by checking whether comparable GCOV scenes exist for your study area.
          </p>
        </section>

        <section className="rs-workflow-strip" aria-label="RiverShift processing stages">
          <div className="rs-stage rs-stage-current"><span>01</span><div><strong>Data availability</strong><small>Current step</small></div></div>
          <div className="rs-stage"><span>02</span><div><strong>GCOV processing</strong><small>Next</small></div></div>
          <div className="rs-stage"><span>03</span><div><strong>Change analysis</strong><small>Planned</small></div></div>
          <div className="rs-stage"><span>04</span><div><strong>Validation</strong><small>Required</small></div></div>
        </section>

        <section className="rs-layout">
          <form className="rs-panel rs-search-panel" onSubmit={handleSearch}>
            <div className="rs-panel-heading">
              <div><span className="rs-eyebrow">PHASE 2.1</span><h2>NISAR GCOV data audit</h2></div>
              <span className="rs-step-number">01</span>
            </div>
            <p className="rs-panel-description">
              Search the actual ASF archive before choosing an event or writing a classifier for it.
              This request checks metadata only.
            </p>

            <label className="rs-field">
              <span>Study area · WKT Polygon</span>
              <textarea
                value={aoiWkt}
                onChange={(event) => setAoiWkt(event.target.value)}
                placeholder="POLYGON ((longitude latitude, longitude latitude, longitude latitude, longitude latitude))"
                rows={5}
                required
              />
              <small>Use WGS84 longitude/latitude order. The final coordinate must repeat the first coordinate.</small>
            </label>

            <div className="rs-form-grid">
              <label className="rs-field">
                <span>Start date</span>
                <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required />
              </label>
              <label className="rs-field">
                <span>End date</span>
                <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} required />
              </label>
            </div>

            <div className="rs-form-grid">
              <label className="rs-field">
                <span>NISAR data maturity</span>
                <select value={maturity} onChange={(event) => setMaturity(event.target.value as RiverShiftMaturity)}>
                  <option value="PROVISIONAL">PROVISIONAL</option>
                  <option value="BETA">BETA</option>
                </select>
              </label>
              <label className="rs-field">
                <span>Maximum products</span>
                <select value={maxResults} onChange={(event) => setMaxResults(event.target.value)}>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                  <option value="250">250</option>
                  <option value="500">500</option>
                </select>
              </label>
            </div>

            {error && <div className="rs-alert rs-alert-error" role="alert">{error}</div>}
            <button className="rs-primary-button" type="submit" disabled={loading}>
              {loading ? 'Searching ASF catalogue…' : 'Search NISAR GCOV archive'}
            </button>
            <div className="rs-source-note">
              Source: <a href="https://nisar-docs.asf.alaska.edu/asf-search/" target="_blank" rel="noreferrer">ASF NISAR Search documentation</a>
              {' · '}
              <a href="https://nisar-docs.asf.alaska.edu/gcov/" target="_blank" rel="noreferrer">GCOV product guide</a>
            </div>
          </form>

          <aside className="rs-panel rs-purpose-panel">
            <span className="rs-eyebrow">WHY THIS COMES FIRST</span>
            <h2>Prove the data exists before claiming a change.</h2>
            <p>
              A river comparison needs observations that can be compared scientifically. RiverShift records
              the granule, acquisition time, orbit direction and data maturity before any pixel-level analysis.
            </p>
            <div className="rs-guardrail">
              <strong>Scientific guardrail</strong>
              <p>Do not mix BETA and PROVISIONAL products in one change stack. Processing changes can look like surface changes.</p>
            </div>
            <div className="rs-data-types">
              <div><span className="rs-dot rs-dot-blue" /><span><strong>GCOV</strong><small>Primary backscatter / inundation input</small></span></div>
              <div><span className="rs-dot rs-dot-teal" /><span><strong>Sentinel-2</strong><small>Supporting interpretation / reference</small></span></div>
              <div><span className="rs-dot rs-dot-amber" /><span><strong>FFWC</strong><small>Independent river-stage context</small></span></div>
            </div>
          </aside>
        </section>

        {result && (
          <section className="rs-panel rs-results-panel" aria-live="polite">
            <div className="rs-panel-heading">
              <div><span className="rs-eyebrow">LIVE ASF RESPONSE</span><h2>Catalogue results</h2></div>
              <span className={result.result_count ? 'rs-result-count' : 'rs-result-count rs-result-zero'}>
                {result.result_count} products
              </span>
            </div>
            <div className="rs-result-summary">
              <div><small>AOI area</small><strong>{result.aoi_area_km2.toFixed(2)} km²</strong></div>
              <div><small>Product</small><strong>{result.processing_level}</strong></div>
              <div><small>Maturity</small><strong>{result.data_maturity}</strong></div>
              <div><small>Search window</small><strong>{result.start_date} → {result.end_date}</strong></div>
            </div>
            {result.result_count === 0 ? (
              <div className="rs-empty-results">
                No matching GCOV products were returned for this request. This is a real catalogue response, not a failed processing run.
                Widen the observation window or re-check the AOI and available data maturity.
              </div>
            ) : (
              <div className="rs-table-wrap">
                <table className="rs-table">
                  <thead><tr><th>Granule</th><th>Acquisition</th><th>Direction</th><th>Path / Frame</th><th>Polarization</th><th>File size</th></tr></thead>
                  <tbody>
                    {result.scenes.map((scene) => (
                      <tr key={scene.granule_name}>
                        <td><strong>{scene.granule_name}</strong><small>{scene.product_type} · {scene.data_maturity}</small></td>
                        <td>{scene.start_time || 'Not reported'}</td>
                        <td>{scene.flight_direction || 'Not reported'}</td>
                        <td>{scene.path_number ?? '—'} / {scene.frame_number ?? '—'}</td>
                        <td>{scene.polarization || 'Not reported'}</td>
                        <td>{formatBytes(scene.size_bytes)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {result.warnings.map((warning) => <p className="rs-warning" key={warning}>• {warning}</p>)}
            <p className="rs-result-disclaimer">{result.user_notice}</p>
          </section>
        )}

        <section className="rs-footnote">
          <strong>What this screen does not do:</strong> It does not download HDF5 files, classify water, calculate flood area,
          measure erosion or produce a warning. Those steps are deliberately separate and will only be enabled after
          a compatible GCOV time series and validation reference are available.
        </section>
      </main>
    </div>
  );
}

function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return 'Not reported';
  return `${(bytes / (1024 ** 3)).toFixed(2)} GiB`;
}
