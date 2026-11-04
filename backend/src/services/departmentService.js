/**
 * Canonical Department Service for NAGARSETU 3.1
 * Single Source of Truth for Department Resolution, UUID Mapping, and Lifecycle Integrity.
 * 
 * Never route by display-name strings.
 * Canonical resolution flow:
 *   AI (departmentCode: "PWD", departmentRegistryId: 1)
 *     ↓
 *   resolveDepartmentByCode("PWD")
 *     ↓
 *   Canonical departments table
 *     ↓
 *   Authoritative Database UUID ("8ed9f760-1314-427c-a515-c2a54d6df6d8")
 *     ↓
 *   complaints.department_id
 */

const { query } = require('../config/db');

// Authoritative Canonical Department Registry
const CANONICAL_DEPARTMENTS = [
  {
    id: '8ed9f760-1314-427c-a515-c2a54d6df6d8',
    code: 'PWD',
    name: 'Public Works Department',
    description: 'Road repairs, potholes, asphalt infrastructure, and civic road maintenance',
    registry_id: 1,
    status: 'active'
  },
  {
    id: '9cabc1f2-fd10-48dd-a5cb-01d05197de22',
    code: 'SAN',
    name: 'Sanitation & Waste Management',
    description: 'Garbage pickup, solid waste clearing, dumpsters, and public cleanliness',
    registry_id: 2,
    status: 'active'
  },
  {
    id: 'ead370cc-459c-44f0-899f-8a97f0928beb',
    code: 'WTR',
    name: 'Water Supply & Sewerage Board',
    description: 'Pipeline leakages, potable water mains, valve control, and water supply',
    registry_id: 3,
    status: 'active'
  },
  {
    id: 'ee73cb82-cc47-4333-b7d6-4491353c1354',
    code: 'DRN',
    name: 'Drainage & Sewage Department',
    description: 'Drainage blockage, sewage overflow, open drains, culverts, and storm channels',
    registry_id: 4,
    status: 'active'
  },
  {
    id: '31842723-23ac-490b-912b-9f6d9afbdfb3',
    code: 'ELE',
    name: 'Electrical & Street Lighting',
    description: 'Streetlight repair, electrical poles, transformer inspection, and public lighting',
    registry_id: 5,
    status: 'active'
  },
  {
    id: 'ae5e4d0c-996f-4d81-9528-d642664c93ae',
    code: 'TRF',
    name: 'Traffic Management Department',
    description: 'Traffic signal repairs, road signage, lane markings, and junction safety',
    registry_id: 6,
    status: 'active'
  },
  {
    id: '71542723-23ac-490b-912b-9f6d9afbdfb7',
    code: 'MNT',
    name: 'Maintenance Department',
    description: 'General civic facility repairs, building maintenance, public park upkeep, and asset management',
    registry_id: 7,
    status: 'active'
  }
];

// Fast in-memory lookup indexes
const CODE_INDEX = new Map();
const UUID_INDEX = new Map();
const REGISTRY_ID_INDEX = new Map();
const NAME_INDEX = new Map();

for (const d of CANONICAL_DEPARTMENTS) {
  CODE_INDEX.set(d.code.toUpperCase(), d);
  UUID_INDEX.set(d.id.toLowerCase(), d);
  REGISTRY_ID_INDEX.set(String(d.registry_id), d);
  REGISTRY_ID_INDEX.set(Number(d.registry_id), d);
  NAME_INDEX.set(d.name.toUpperCase(), d);
}

// Canonical aliases & keyword mapping for robust routing
const DEPARTMENT_KEYWORD_RULES = [
  { code: 'WTR', keywords: ['WTR', 'WSSB', 'WATER', 'WATER SUPPLY', 'WATER SUPPLY & SEWERAGE BOARD', 'PIPELINE', 'PIPE', 'LEAK', 'LEAKAGE', 'POTABLE', 'WATER MAINS'] },
  { code: 'SAN', keywords: ['SAN', 'SWM', 'SANITATION', 'SANITATION & WASTE MANAGEMENT', 'WASTE', 'GARBAGE', 'SOLID WASTE', 'TRASH', 'DUMPSTER', 'CLEAN', 'CLEANLINESS'] },
  { code: 'DRN', keywords: ['DRN', 'DRAIN', 'DRAINAGE', 'DRAINAGE & SEWAGE DEPARTMENT', 'SEWAGE', 'SEWER', 'GUTTER', 'CULVERT', 'STORM CHANNEL', 'OVERFLOW'] },
  { code: 'PWD', keywords: ['PWD', 'PUBLIC WORKS', 'PUBLIC WORKS DEPARTMENT', 'ROAD', 'ROADS', 'POTHOLE', 'ASPHALT', 'PAVEMENT', 'BRIDGE', 'FOOTPATH'] },
  { code: 'ELE', keywords: ['ELE', 'ELECTRICAL', 'ELECTRICAL & STREET LIGHTING', 'ELECTRIC', 'STREETLIGHT', 'LIGHTING', 'POLE', 'TRANSFORMER'] },
  { code: 'TRF', keywords: ['TRF', 'TRAFFIC', 'TRAFFIC MANAGEMENT DEPARTMENT', 'SIGNAL', 'TRAFFIC SIGNAL', 'SIGNAGE', 'LANE MARKING'] },
  { code: 'MNT', keywords: ['MNT', 'MAINTENANCE', 'MAINTENANCE DEPARTMENT', 'CIVIC FACILITY', 'BUILDING MAINTENANCE', 'PUBLIC PARK', 'PARK UPKEEP'] }
];

function matchDepartmentByText(text) {
  if (!text) return null;
  const rawStr = String(text).trim();
  if (!rawStr) return null;
  const cleanCode = rawStr.toUpperCase();
  const lowerStr = rawStr.toLowerCase();

  // 1. Direct memory lookup
  if (CODE_INDEX.has(cleanCode)) return CODE_INDEX.get(cleanCode);
  if (REGISTRY_ID_INDEX.has(cleanCode)) return REGISTRY_ID_INDEX.get(cleanCode);
  if (UUID_INDEX.has(lowerStr)) return UUID_INDEX.get(lowerStr);
  if (NAME_INDEX.has(cleanCode)) return NAME_INDEX.get(cleanCode);

  // 2. Keyword & alias matching
  for (const rule of DEPARTMENT_KEYWORD_RULES) {
    for (const kw of rule.keywords) {
      if (cleanCode === kw || cleanCode.includes(kw) || lowerStr.includes(kw.toLowerCase())) {
        return CODE_INDEX.get(rule.code);
      }
    }
  }
  return null;
}

/**
 * Resolves canonical department by department code, UUID, name, or alias.
 * Authoritatively returns the database UUID, canonical code, and canonical name.
 * 
 * @param {string} code - Department code, ID, or name (e.g. "WTR", "Water Supply & Sewerage Board", 3)
 * @returns {Promise<{ id: string, code: string, name: string, status: string, registry_id: number }>}
 */
async function resolveDepartmentByCode(code) {
  if (!code) {
    const defaultDept = CANONICAL_DEPARTMENTS[0]; // PWD default
    return {
      id: defaultDept.id,
      code: defaultDept.code,
      name: defaultDept.name,
      status: defaultDept.status,
      registry_id: defaultDept.registry_id
    };
  }

  const rawStr = String(code).trim();
  const cleanCode = rawStr.toUpperCase();

  // 1. Fast memory match (code, UUID, registry_id, name, keywords)
  const memHit = matchDepartmentByText(rawStr);
  if (memHit) {
    return {
      id: memHit.id,
      code: memHit.code,
      name: memHit.name,
      status: memHit.status,
      registry_id: memHit.registry_id
    };
  }

  // 2. Query authoritative database departments table
  try {
    const res = await query(
      `SELECT id, code, name, status, description, registry_id 
       FROM departments 
       WHERE UPPER(code) = ? OR id = ? OR CAST(registry_id AS TEXT) = ? OR UPPER(name) = ? OR UPPER(name) LIKE ?
       LIMIT 1`,
      [cleanCode, rawStr, cleanCode, cleanCode, `%${cleanCode}%`]
    );

    if (res.rows && res.rows.length > 0) {
      const row = res.rows[0];
      const matchedCanonical = CODE_INDEX.get((row.code || '').toUpperCase()) || UUID_INDEX.get(String(row.id).toLowerCase());
      return {
        id: String(row.id),
        code: String(row.code || matchedCanonical?.code || cleanCode),
        name: String(row.name || matchedCanonical?.name || 'Municipal Department'),
        status: String(row.status || 'active'),
        registry_id: Number(row.registry_id || matchedCanonical?.registry_id || 1)
      };
    }
  } catch (err) {
    console.warn('[DEPARTMENT_RESOLVER] DB lookup note:', err.message);
  }

  // 3. Default fallback to PWD
  const fallback = CANONICAL_DEPARTMENTS[0];
  return {
    id: fallback.id,
    code: fallback.code,
    name: fallback.name,
    status: fallback.status,
    registry_id: fallback.registry_id
  };
}

/**
 * Synchronous resolver for token verification / middleware
 */
function resolveDepartmentByCodeSync(code) {
  if (!code) return CANONICAL_DEPARTMENTS[0];
  const found = matchDepartmentByText(code);
  return found || CANONICAL_DEPARTMENTS[0];
}

/**
 * Authoritatively resolves the canonical department for a complaint based on:
 * 1. Complaint Category (Primary deterministic signal)
 * 2. Title & Description keywords (Water leakage, pipe burst, drainage, garbage, etc.)
 * 3. AI prediction metadata
 * 4. Explicit department input (if non-contradictory)
 * 
 * Guarantees:
 * - Water complaints always route to WTR ('ead370cc-459c-44f0-899f-8a97f0928beb')
 * - Drainage complaints always route to DRN ('ee73cb82-cc47-4333-b7d6-4491353c1354')
 * - Garbage complaints always route to SAN ('9cabc1f2-fd10-48dd-a5cb-01d05197de22')
 * - Road complaints route to PWD ('8ed9f760-1314-427c-a515-c2a54d6df6d8')
 * - Never silently defaults water to PWD.
 */
function resolveDepartmentForComplaint(params = {}) {
  const category = String(params.category || '').trim();
  const title = String(params.title || '').trim();
  const description = String(params.description || '').trim();
  const department = String(params.department || '').trim();
  const department_name = String(params.department_name || '').trim();
  const department_code = String(params.department_code || '').trim().toUpperCase();
  const department_id = String(params.department_id || '').trim();
  const ai_category = String(params.ai_category || '').trim();
  const ai_specific_issue = String(params.ai_specific_issue || '').trim();

  const catLower = category.toLowerCase();
  const titleLower = title.toLowerCase();
  const descLower = description.toLowerCase();

  // PRIORITY RULE 1: WATER SUPPLY & SEWERAGE BOARD (WTR)
  // Water category, water-related titles, or water pipeline descriptions
  const isWater =
    catLower === 'water' ||
    catLower === 'water supply' ||
    catLower.includes('water') ||
    titleLower.includes('water') ||
    titleLower.includes('pipe') ||
    titleLower.includes('leak') ||
    titleLower.includes('burst') ||
    titleLower.includes('potable') ||
    titleLower.includes('contamination') ||
    descLower.includes('water leak') ||
    descLower.includes('pipe leak') ||
    descLower.includes('pipeline') ||
    descLower.includes('water supply') ||
    descLower.includes('potable water') ||
    descLower.includes('contaminated water') ||
    descLower.includes('water connection') ||
    department_code === 'WTR' ||
    department_id === '3' ||
    department_id.toLowerCase() === 'ead370cc-459c-44f0-899f-8a97f0928beb' ||
    (department || department_name).toLowerCase().includes('water supply');

  const isDrainageSpecific =
    catLower.includes('drain') ||
    catLower.includes('sewag') ||
    catLower.includes('sewer') ||
    titleLower.includes('blocked drain') ||
    titleLower.includes('drain blockage') ||
    titleLower.includes('sewer overflow') ||
    titleLower.includes('gutter') ||
    titleLower.includes('culvert');

  if (isWater && (!isDrainageSpecific || catLower.includes('water'))) {
    return CODE_INDEX.get('WTR') || CANONICAL_DEPARTMENTS[2];
  }

  // PRIORITY RULE 2: DRAINAGE & SEWAGE DEPARTMENT (DRN)
  if (
    isDrainageSpecific ||
    department_code === 'DRN' ||
    department_id === '4' ||
    department_id === '7' ||
    department_id.toLowerCase() === 'ee73cb82-cc47-4333-b7d6-4491353c1354' ||
    (department || department_name).toLowerCase().includes('drainage') ||
    descLower.includes('blocked drain') ||
    descLower.includes('drainage clog') ||
    descLower.includes('sewage overflow')
  ) {
    return CODE_INDEX.get('DRN') || CANONICAL_DEPARTMENTS[3];
  }

  // PRIORITY RULE 3: SANITATION & WASTE MANAGEMENT (SAN)
  const isSanitation =
    catLower.includes('sanitat') ||
    catLower.includes('waste') ||
    catLower.includes('garbage') ||
    titleLower.includes('garbage') ||
    titleLower.includes('trash') ||
    titleLower.includes('waste') ||
    titleLower.includes('dump') ||
    titleLower.includes('dustbin') ||
    descLower.includes('garbage accumulation') ||
    descLower.includes('overflowing bin') ||
    department_code === 'SAN' ||
    department_id === '2' ||
    department_id.toLowerCase() === '9cabc1f2-fd10-48dd-a5cb-01d05197de22' ||
    (department || department_name).toLowerCase().includes('sanitation');

  if (isSanitation) {
    return CODE_INDEX.get('SAN') || CANONICAL_DEPARTMENTS[1];
  }

  // PRIORITY RULE 4: ELECTRICAL & STREET LIGHTING (ELE)
  const isElectrical =
    catLower.includes('electric') ||
    catLower.includes('light') ||
    titleLower.includes('street light') ||
    titleLower.includes('streetlight') ||
    titleLower.includes('electric') ||
    titleLower.includes('transformer') ||
    department_code === 'ELE' ||
    department_id === '5' ||
    department_id.toLowerCase() === '31842723-23ac-490b-912b-9f6d9afbdfb3';

  if (isElectrical) {
    return CODE_INDEX.get('ELE') || CANONICAL_DEPARTMENTS[4];
  }

  // PRIORITY RULE 5: TRAFFIC MANAGEMENT DEPARTMENT (TRF)
  const isTraffic =
    catLower.includes('traffic') ||
    titleLower.includes('traffic signal') ||
    titleLower.includes('road sign') ||
    department_code === 'TRF' ||
    department_id === '6' ||
    department_id.toLowerCase() === 'ae5e4d0c-996f-4d81-9528-d642664c93ae';

  if (isTraffic) {
    return CODE_INDEX.get('TRF') || CANONICAL_DEPARTMENTS[5];
  }

  // PRIORITY RULE 6: PUBLIC WORKS DEPARTMENT (PWD) - Roads, Potholes, Footpaths
  const isRoad =
    catLower.includes('road') ||
    catLower.includes('pothole') ||
    titleLower.includes('pothole') ||
    titleLower.includes('road damage') ||
    titleLower.includes('asphalt') ||
    titleLower.includes('footpath') ||
    descLower.includes('pothole') ||
    descLower.includes('road surface') ||
    department_code === 'PWD' ||
    department_id === '1' ||
    department_id.toLowerCase() === '8ed9f760-1314-427c-a515-c2a54d6df6d8' ||
    (department || department_name).toLowerCase().includes('public works');

  if (isRoad) {
    return CODE_INDEX.get('PWD') || CANONICAL_DEPARTMENTS[0];
  }

  // PRIORITY RULE 7: MAINTENANCE DEPARTMENT (MNT)
  const isMaintenance =
    catLower.includes('maintenance') ||
    titleLower.includes('park') ||
    titleLower.includes('garden') ||
    titleLower.includes('facility') ||
    department_code === 'MNT' ||
    department_id === '7' ||
    department_id.toLowerCase() === '71542723-23ac-490b-912b-9f6d9afbdfb7';

  if (isMaintenance) {
    return CODE_INDEX.get('MNT') || CANONICAL_DEPARTMENTS[6];
  }

  // Check raw inputs
  const rawInput = department_code || (department_id && department_id.length <= 4 ? department_id : null) || department || department_name;
  if (rawInput) {
    const matched = matchDepartmentByText(rawInput);
    if (matched) return matched;
  }

  // Default to general maintenance rather than silently defaulting to PWD
  return CODE_INDEX.get('MNT') || CANONICAL_DEPARTMENTS[0];
}

/**
 * Gets all canonical departments
 */
function getAllCanonicalDepartments() {
  return [...CANONICAL_DEPARTMENTS];
}

module.exports = {
  CANONICAL_DEPARTMENTS,
  resolveDepartmentByCode,
  resolveDepartmentByCodeSync,
  resolveDepartmentForComplaint,
  getAllCanonicalDepartments
};
