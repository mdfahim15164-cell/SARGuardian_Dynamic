import { describe, expect, it } from 'vitest';
import { parseRiverShiftReport } from './manifest';

describe('RiverShift result manifest', () => {
  it('accepts a signed bankline migration result with provenance and QA status', () => {
    const result = parseRiverShiftReport({
      schema_version: 1,
      engine: 'RiverShift',
      analysis_type: 'bankline_migration',
      source: { mission: 'NISAR', product: 'GCOV', maturity: 'PROVISIONAL' },
      inputs: { positive_direction_label: 'toward_channel' },
      method: { measurement: 'signed_chainage_difference_along_user_supplied_transects' },
      metrics: {
        mean_signed_displacement_m: 12.5,
        mean_net_rate_m_per_year: 49.7,
        valid_transect_count: 4,
        invalid_transect_count: 1
      },
      quality: {
        status: 'TRANSECT_MEASURED_REQUIRES_BANKLINE_VALIDATION',
        warnings: ['Digitised banklines require independent review.']
      }
    });
    expect(result.analysis_type).toBe('bankline_migration');
    expect(result.metrics.mean_signed_displacement_m).toBe(12.5);
    expect(result.inputs?.positive_direction_label).toBe('toward_channel');
  });

  it('rejects a report with a non-finite metric', () => {
    expect(() => parseRiverShiftReport({
      schema_version: 1,
      engine: 'RiverShift',
      analysis_type: 'bankline_migration',
      source: { mission: 'NISAR' },
      metrics: { mean_signed_displacement_m: Number.NaN },
      quality: { status: 'INVALID' }
    })).toThrow('not finite or null');
  });
});
