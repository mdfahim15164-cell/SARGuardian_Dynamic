import type { User } from 'firebase/auth';

const configuredApiUrl = (import.meta.env.VITE_SARGUARDIAN_API_URL as string | undefined)?.trim();
const API_BASE = (configuredApiUrl || 'http://localhost:8000').replace(/\/+$/, '');

export type RiverShiftMaturity = 'PROVISIONAL' | 'BETA';

export type RiverShiftCatalogScene = {
  granule_name: string;
  product_id?: string | null;
  product_type: string;
  data_maturity?: string | null;
  catalogue_maturity_filter: RiverShiftMaturity;
  maturity_evidence: 'product_metadata' | 'ASF query filter only';
  start_time?: string | null;
  stop_time?: string | null;
  flight_direction?: string | null;
  relative_orbit?: string | number | null;
  path_number?: string | number | null;
  frame_number?: string | number | null;
  acquisition_mode?: string | null;
  polarization?: string | null;
  polarization_mode?: string | null;
  frequency?: string | null;
  crid?: string | null;
  url?: string | null;
  size_bytes?: number | null;
};

export type RiverShiftCatalogResponse = {
  dataset: 'NISAR';
  processing_level: 'GCOV';
  requested_maturity_filter: RiverShiftMaturity;
  start_date: string;
  end_date: string;
  aoi_area_km2: number;
  result_count: number;
  limit: number;
  truncated_possible: boolean;
  catalogue_only: true;
  data_downloaded: false;
  scientific_analysis_performed: false;
  scenes: RiverShiftCatalogScene[];
  warnings: string[];
  user_notice: string;
};

export type RiverShiftCatalogRequest = {
  coordinates: number[][];
  startDate: string;
  endDate: string;
  dataMaturity: RiverShiftMaturity;
  maxResults: number;
};

export async function searchRiverShiftGCOVCatalog(
  input: RiverShiftCatalogRequest,
  user: Pick<User, 'getIdToken'> | null,
): Promise<RiverShiftCatalogResponse> {
  if (!user) throw new Error('Sign in before searching the NISAR archive.');

  let token: string;
  try {
    token = await user.getIdToken();
  } catch {
    throw new Error('Could not obtain the Firebase sign-in token. Sign in again and retry.');
  }
  if (!token) throw new Error('Could not obtain the Firebase sign-in token. Sign in again and retry.');

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/river-shift/catalog/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        coordinates: input.coordinates,
        start_date: input.startDate,
        end_date: input.endDate,
        data_maturity: input.dataMaturity,
        max_results: input.maxResults,
      }),
    });
  } catch {
    throw new Error('Could not reach the SARGuardian API. Check your connection and backend URL.');
  }

  const payload = await response.json().catch(() => ({})) as { detail?: string; message?: string };
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || `GCOV catalogue search failed (${response.status}).`);
  }
  return payload as RiverShiftCatalogResponse;
}
