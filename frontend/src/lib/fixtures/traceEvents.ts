import type { TraceEvent } from '../types'

// Ordered event log. Processing.tsx plays these back on a timer to simulate
// the real SSE stream — same shape, so swapping in the live stream later
// is a one-line change (see Processing.tsx).
export const sampleTraceEvents: TraceEvent[] = [
  { id: 'e1', agent: 'script_breakdown', status: 'running', message: 'Parsing screenplay structure...', timestamp: 't0' },
  { id: 'e2', agent: 'script_breakdown', status: 'done', message: 'Extracted 3 scenes, 3 distinct locations required', timestamp: 't1' },
  { id: 'e3', agent: 'location_grounding', status: 'running', message: 'Researching "abandoned warehouse, urban interior"...', timestamp: 't2' },
  { id: 'e4', agent: 'location_grounding', status: 'running', message: 'Researching "city rooftop, skyline sightline"...', timestamp: 't3' },
  { id: 'e5', agent: 'location_grounding', status: 'done', message: 'Found 3 grounded candidate locations', timestamp: 't4' },
  { id: 'e6', agent: 'logistics_risk', status: 'running', message: 'Scoring composite fit and checking for conflicts...', timestamp: 't5' },
  { id: 'e7', agent: 'logistics_risk', status: 'done', message: '1 scheduling conflict flagged, report ready', timestamp: 't6' },
]
