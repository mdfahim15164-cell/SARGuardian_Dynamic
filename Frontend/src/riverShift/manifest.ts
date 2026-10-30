export type RiverShiftReport = {
  schema_version: number;
  engine: string;
  analysis_type: string;
  source: Record<string, unknown>;
  inputs?: Record<string, unknown>;
  reference?: Record<string, unknown>;
  method?: Record<string, unknown>;
  confusion_matrix?: Record<string, unknown>;
  metrics: Record<string, number | null>;
  quality: {
    status: string;
    warnings?: string[];
    [key: string]: unknown;
  };
  outputs?: Record<string, unknown>;
};

export type RiverShiftGeoJSON = {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    properties?: Record<string, unknown>;
    geometry: {
      type: string;
      coordinates: unknown;
    };
  }>;
};

export function parseRiverShiftReport(value: unknown): RiverShiftReport {
  if (!value || typeof value !== 'object') {
    throw new Error('Result JSON must be an object.');
  }
  const candidate = value as Record<string, unknown>;
  if (candidate.schema_version !== 1 || candidate.engine !== 'RiverShift') {
    throw new Error('Unsupported result. Expected schema_version 1 and engine RiverShift.');
  }
  const validTypes = [
    'flood_inundation_screening',
    'river_morphology_screening',
    'classification_validation',
    'bankline_migration',
  ];
  if (typeof candidate.analysis_type !== 'string' || !validTypes.includes(candidate.analysis_type)) {
    throw new Error('Unsupported RiverShift analysis type.');
  }
  if (!candidate.source || typeof candidate.source !== 'object') {
    throw new Error('Result is missing its satellite source provenance.');
  }
  if (!candidate.metrics || typeof candidate.metrics !== 'object') {
    throw new Error('Result is missing its metrics object.');
  }
  if (!candidate.quality || typeof candidate.quality !== 'object') {
    throw new Error('Result is missing its quality status.');
  }
  const quality = candidate.quality as Record<string, unknown>;
  if (typeof quality.status !== 'string' || !quality.status.trim()) {
    throw new Error('Result quality.status is required.');
  }
  const metrics: Record<string, number | null> = {};
  for (const [key, raw] of Object.entries(candidate.metrics as Record<string, unknown>)) {
    if (raw === null) metrics[key] = null;
    else if (typeof raw === 'number' && Number.isFinite(raw)) metrics[key] = raw;
    else throw new Error('Metric ' + key + ' is not finite or null.');
  }

  return {
    schema_version: 1,
    engine: 'RiverShift',
    analysis_type: candidate.analysis_type,
    source: candidate.source as Record<string, unknown>,
    inputs: candidate.inputs as Record<string, unknown> | undefined,
    reference: candidate.reference as Record<string, unknown> | undefined,
    method: candidate.method as Record<string, unknown> | undefined,
    confusion_matrix: candidate.confusion_matrix as Record<string, unknown> | undefined,
    metrics,
    quality: quality as RiverShiftReport['quality'],
    outputs: candidate.outputs as Record<string, unknown> | undefined,
  };
}

export function parseRiverShiftGeoJSON(value: unknown): RiverShiftGeoJSON {
  if (!value || typeof value !== 'object') throw new Error('GeoJSON must be an object.');
  const candidate = value as Record<string, unknown>;
  if (candidate.type !== 'FeatureCollection' || !Array.isArray(candidate.features)) {
    throw new Error('Expected a GeoJSON FeatureCollection.');
  }
  for (const feature of candidate.features) {
    if (!feature || typeof feature !== 'object') throw new Error('Invalid GeoJSON feature.');
    const item = feature as Record<string, unknown>;
    if (item.type !== 'Feature' || !item.geometry || typeof item.geometry !== 'object') {
      throw new Error('Every GeoJSON item must have a geometry and Feature type.');
    }
  }
  return candidate as RiverShiftGeoJSON;
}
