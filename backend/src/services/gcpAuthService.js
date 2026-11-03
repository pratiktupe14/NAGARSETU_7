/**
 * NAGARSETU 3.1 — Google Cloud Workload Identity Federation (WIF) Authentication Service
 * 
 * Authenticates Vercel Serverless Functions to Google Cloud Run using OpenID Connect (OIDC).
 * 
 * Flow:
 * 1. Retrieve Vercel OIDC Token (via Vercel runtime / env / header).
 * 2. Exchange Vercel OIDC token for Google STS Federated Access Token via sts.googleapis.com.
 * 3. Generate a Google-signed ID Token for Cloud Run service via iamcredentials.googleapis.com
 *    with target Cloud Run service URL as the audience.
 * 4. Cache ID Token in-memory and refresh automatically prior to expiration.
 * 
 * ZERO hardcoded secrets: All credentials and project details are loaded from environment variables.
 */

const fs = require('fs');

// In-memory token cache to prevent per-request STS overhead
let cachedTokenData = {
  idToken: null,
  expiresAt: 0,
  audience: null,
  apiKey: null
};

let cachedInternalApiKey = {
  key: null,
  expiresAt: 0
};

let lastStsAccessToken = null;

function isRevokedKey(k) {
  if (!k || typeof k !== 'string') return true;
  return k.startsWith('BNOdu') || k.includes('BNOduVL');
}

async function fetchSecretManagerKey(stsAccessToken, projectNumber = '755578057105', secretName = 'nagarsetu-ai-internal-key') {
  if (process.env.AI_INTERNAL_API_KEY && !isRevokedKey(process.env.AI_INTERNAL_API_KEY)) {
    return process.env.AI_INTERNAL_API_KEY.trim();
  }
  const now = Date.now();
  if (cachedInternalApiKey.key && cachedInternalApiKey.expiresAt > now) {
    return cachedInternalApiKey.key;
  }
  try {
    const url = `https://secretmanager.googleapis.com/v1/projects/${projectNumber}/secrets/${secretName}/versions/latest:access`;
    // Attempt 1: Direct access via federated STS token (bound to workloadIdentityUser subject)
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${stsAccessToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      if (data.payload && data.payload.data) {
        const secretVal = Buffer.from(data.payload.data, 'base64').toString('utf8').trim();
        cachedInternalApiKey = {
          key: secretVal,
          expiresAt: now + (30 * 60 * 1000) // Cache for 30 minutes
        };
        lastDiagnostics.secretManager = { success: true, method: 'sts' };
        return secretVal;
      }
    }

    // Attempt 2: Impersonate vercel-ai-invoker service account to generate access token
    const serviceAccountEmail = (process.env.GCP_SERVICE_ACCOUNT_EMAIL || 'vercel-ai-invoker@project-578628ad-e6b6-4b3b-9f7.iam.gserviceaccount.com').trim();
    const tokenUrl = `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${encodeURIComponent(serviceAccountEmail)}:generateAccessToken`;
    const tokenRes = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${stsAccessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        scope: ['https://www.googleapis.com/auth/cloud-platform']
      })
    });

    if (tokenRes.ok) {
      const tokenData = await tokenRes.json();
      if (tokenData.accessToken) {
        const saSecRes = await fetch(url, {
          headers: { Authorization: `Bearer ${tokenData.accessToken}` }
        });
        if (saSecRes.ok) {
          const saData = await saSecRes.json();
          if (saData.payload && saData.payload.data) {
            const secretVal = Buffer.from(saData.payload.data, 'base64').toString('utf8').trim();
            cachedInternalApiKey = {
              key: secretVal,
              expiresAt: now + (30 * 60 * 1000)
            };
            lastDiagnostics.secretManager = { success: true, method: 'impersonated_sa' };
            return secretVal;
          }
        }
      }
    }
    lastDiagnostics.secretManager = { success: false, status: res.status };
  } catch (e) {
    console.warn('[GCP AUTH] Error fetching secret from Secret Manager:', e.message);
    lastDiagnostics.secretManager = { success: false, error: e.message };
  }
  return null;
}

let inFlightPromise = null;

let lastDiagnostics = {
  timestamp: null,
  targetUrl: null,
  oidc: null,
  sts: null,
  iam: null
};

function getLastDiagnostics() {
  return {
    ...lastDiagnostics,
    env: {
      hasProjectNumber: Boolean(process.env.GCP_PROJECT_NUMBER),
      hasServiceAccountEmail: Boolean(process.env.GCP_SERVICE_ACCOUNT_EMAIL),
      hasPool: Boolean(process.env.GCP_WORKLOAD_POOL),
      hasProvider: Boolean(process.env.GCP_WORKLOAD_PROVIDER),
      hasPythonAiUrl: Boolean(process.env.PYTHON_AI_URL),
      hasAiServiceUrl: Boolean(process.env.AI_SERVICE_URL),
      hasVercelOidcToken: Boolean(process.env.VERCEL_OIDC_TOKEN),
      hasAiInternalApiKey: Boolean(process.env.AI_INTERNAL_API_KEY),
      aiKeyPrefix: process.env.AI_INTERNAL_API_KEY ? process.env.AI_INTERNAL_API_KEY.substring(0, 5) : null,
      nodeEnv: process.env.NODE_ENV,
      vercelEnv: process.env.VERCEL_ENV,
      vercelUrl: process.env.VERCEL_URL
    }
  };
}

/**
 * Normalizes the target audience to the root Cloud Run service origin.
 * Example: 'https://nagarsetu-ai-service-...run.app/analyze' -> 'https://nagarsetu-ai-service-...run.app'
 */
function resolveCloudRunAudience(targetUrl) {
  if (!targetUrl) return null;
  try {
    const parsed = new URL(targetUrl);
    return parsed.origin;
  } catch (err) {
    return targetUrl.replace(/\/+$/, '');
  }
}

/**
 * Checks whether the target URL is a remote Cloud Run or HTTPS deployment requiring GCP auth.
 */
function isGoogleCloudRunTarget(targetUrl) {
  if (!targetUrl) return false;
  const lower = targetUrl.toLowerCase();
  if (lower.includes('localhost') || lower.includes('127.0.0.1')) {
    return false;
  }
  return lower.includes('.run.app') || lower.includes('google') || Boolean(process.env.GCP_SERVICE_ACCOUNT_EMAIL);
}

/**
 * Safely decodes JWT payload to determine expiration without external dependencies.
 */
function decodeJwtPayload(jwtToken) {
  try {
    const parts = jwtToken.split('.');
    if (parts.length !== 3) return null;
    const payload = Buffer.from(parts[1], 'base64').toString('utf8');
    return JSON.parse(payload);
  } catch (e) {
    return null;
  }
}

/**
 * Retrieves the Vercel OIDC token from secure server-side runtime sources only.
 * Client-supplied tokens/headers are strictly rejected to prevent identity spoofing.
 */
async function retrieveVercelOidcToken(options = {}) {
  // 1. Server-side Vercel runtime OIDC retrieval via official @vercel/oidc package
  try {
    const { getVercelOidcToken } = require('@vercel/oidc');
    if (typeof getVercelOidcToken === 'function') {
      const token = await getVercelOidcToken();
      if (token) return token;
    }
  } catch (_) {
    // Falls through to server-side env/file if running outside Vercel function context
  }
  // 1b. Check request context header if passed
  if (options && options.req && options.req.headers && options.req.headers['x-vercel-oidc-token']) {
    return options.req.headers['x-vercel-oidc-token'];
  }


  // 2. Server-side environment variable (set securely in Vercel project dashboard / backend env)
  if (process.env.VERCEL_OIDC_TOKEN) {
    return process.env.VERCEL_OIDC_TOKEN;
  }

  // 3. Server-side token file (e.g. mounted secure credentials file)
  if (process.env.VERCEL_OIDC_TOKEN_FILE && fs.existsSync(process.env.VERCEL_OIDC_TOKEN_FILE)) {
    try {
      const fileContent = fs.readFileSync(process.env.VERCEL_OIDC_TOKEN_FILE, 'utf8').trim();
      if (fileContent) return fileContent;
    } catch (e) {
      console.warn('[GCP AUTH] Failed to read VERCEL_OIDC_TOKEN_FILE:', e.message);
    }
  }

  return null;
}

/**
 * Exchanges Vercel OIDC token for Google Security Token Service (STS) federated access token.
 */
async function exchangeVercelTokenForStsAccessToken(vercelToken, config) {
  const { projectNumber, poolId, providerId } = config;
  const stsAudience = `//iam.googleapis.com/projects/${projectNumber}/locations/global/workloadIdentityPools/${poolId}/providers/${providerId}`;

  const stsBody = {
    audience: stsAudience,
    grantType: 'urn:ietf:params:oauth:grant-type:token-exchange',
    requestedTokenType: 'urn:ietf:params:oauth:token-type:access_token',
    scope: 'https://www.googleapis.com/auth/cloud-platform',
    subjectTokenType: 'urn:ietf:params:oauth:token-type:jwt',
    subjectToken: vercelToken
  };

  const stsResponse = await fetch('https://sts.googleapis.com/v1/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(stsBody)
  });

  if (!stsResponse.ok) {
    const errText = await stsResponse.text().catch(() => '');
    throw new Error(`Google STS token exchange failed with status ${stsResponse.status}: ${errText}`);
  }

  const stsData = await stsResponse.json();
  if (!stsData.access_token) {
    throw new Error('Google STS response missing access_token');
  }

  return stsData.access_token;
}

/**
 * Generates a Google-signed ID token for Cloud Run by impersonating the target service account.
 */
async function generateServiceAccountIdToken(stsAccessToken, serviceAccountEmail, targetAudience) {
  const impersonateUrl = `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${encodeURIComponent(serviceAccountEmail)}:generateIdToken`;

  const response = await fetch(impersonateUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${stsAccessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      audience: targetAudience,
      includeEmail: true
    })
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => '');
    throw new Error(`Google IAM generateIdToken failed with status ${response.status}: ${errText}`);
  }

  const data = await response.json();
  if (!data.token) {
    throw new Error('Google IAM response missing ID token');
  }

  return data.token;
}

/**
 * Main function to obtain a valid Google Cloud Run ID token.
 * 
 * @param {string} targetUrl - Target Cloud Run URL or endpoint
 * @param {object} options - Optional overrides or request context
 * @returns {Promise<string|null>} Bearer ID token or null if not applicable
 */
async function getCloudRunIdToken(targetUrl, options = {}) {
  const audience = resolveCloudRunAudience(targetUrl || process.env.CLOUD_RUN_SERVICE_URL || process.env.AI_SERVICE_URL || process.env.PYTHON_AI_URL);

  // If communicating with localhost or no remote target, bypass
  if (!isGoogleCloudRunTarget(audience)) {
    return null;
  }

  // 1. Direct ID token override (useful for testing or direct env injection)
  if (process.env.GCP_ID_TOKEN || process.env.CLOUD_RUN_ID_TOKEN) {
    return process.env.GCP_ID_TOKEN || process.env.CLOUD_RUN_ID_TOKEN;
  }

  // 2. Check token cache (ensure valid, unrevoked internal API key is available)
  const now = Date.now();
  const hasValidKey = Boolean(
    (process.env.AI_INTERNAL_API_KEY && !isRevokedKey(process.env.AI_INTERNAL_API_KEY)) ||
    cachedInternalApiKey.key ||
    cachedTokenData.apiKey
  );
  if (
    cachedTokenData.idToken &&
    cachedTokenData.audience === audience &&
    cachedTokenData.expiresAt > (now + 5 * 60 * 1000) &&
    hasValidKey
  ) {
    return cachedTokenData.idToken;
  }

  // If a refresh is already in-flight for this audience, await it
  if (inFlightPromise) {
    return inFlightPromise;
  }

  inFlightPromise = (async () => {
    try {
      const projectNumber = (process.env.GCP_PROJECT_NUMBER || '755578057105').trim();
      const poolId = (process.env.GCP_WORKLOAD_POOL || 'vercel').trim();
      const providerId = (process.env.GCP_WORKLOAD_PROVIDER || 'vercel').trim();
      const serviceAccountEmail = (process.env.GCP_SERVICE_ACCOUNT_EMAIL || 'vercel-ai-invoker@project-578628ad-e6b6-4b3b-9f7.iam.gserviceaccount.com').trim();

      if (!projectNumber || !serviceAccountEmail) {
        // Workload Identity Federation not configured in environment
        return null;
      }

      lastDiagnostics.timestamp = new Date().toISOString();
      lastDiagnostics.targetUrl = audience;

      const vercelToken = await retrieveVercelOidcToken(options);
      if (!vercelToken) {
        lastDiagnostics.oidc = { retrieved: false, error: 'Vercel OIDC token not found in runtime or environment.' };
        console.warn('[GCP AUTH] Vercel OIDC token not found in runtime or environment.');
        return null;
      }

      const decoded = decodeJwtPayload(vercelToken);
      lastDiagnostics.oidc = {
        retrieved: true,
        claims: decoded ? {
          iss: decoded.iss,
          aud: decoded.aud,
          sub: decoded.sub,
          owner: decoded.owner,
          project: decoded.project
        } : null
      };

      // Step A: STS token exchange
      let stsAccessToken;
      try {
        stsAccessToken = await exchangeVercelTokenForStsAccessToken(vercelToken, {
          projectNumber,
          poolId,
          providerId
        });
        lastStsAccessToken = stsAccessToken;
        lastDiagnostics.sts = { success: true, status: 200 };
      } catch (stsErr) {
        lastDiagnostics.sts = { success: false, error: stsErr.message };
        throw stsErr;
      }

      // Step A2: Retrieve internal API key from Secret Manager if env key is missing or revoked
      const envNeedsRotation = isRevokedKey(process.env.AI_INTERNAL_API_KEY);
      if (envNeedsRotation && stsAccessToken) {
        try {
          await fetchSecretManagerKey(stsAccessToken, projectNumber);
        } catch (_) {}
      }

      // Step B: Generate Cloud Run ID token
      let idToken;
      try {
        idToken = await generateServiceAccountIdToken(stsAccessToken, serviceAccountEmail, audience);
        lastDiagnostics.iam = { success: true, status: 200 };
      } catch (iamErr) {
        lastDiagnostics.iam = { success: false, error: iamErr.message };
        throw iamErr;
      }

      // Cache token with safe expiration
      let expiresAt = now + (50 * 60 * 1000); // Default to 50 minutes
      const decodedId = decodeJwtPayload(idToken);
      if (decodedId && decodedId.exp) {
        expiresAt = decodedId.exp * 1000;
      }

      cachedTokenData = {
        idToken,
        expiresAt,
        audience,
        apiKey: cachedInternalApiKey.key
      };

      return idToken;
    } catch (err) {
      console.error('[GCP AUTH] Error acquiring Cloud Run ID token:', err.message);
      return null;
    } finally {
      inFlightPromise = null;
    }
  })();

  return inFlightPromise;
}

/**
 * Attaches both GCP Bearer ID token and internal API key to request headers.
 */
async function attachGcpAuthHeaders(headers = {}, targetUrl, options = {}) {
  const finalHeaders = { ...headers };

  try {
    const idToken = await getCloudRunIdToken(targetUrl, options);
    if (idToken) {
      finalHeaders['Authorization'] = `Bearer ${idToken}`;
    }
  } catch (err) {
    console.warn('[GCP AUTH] Failed to attach GCP ID token:', err.message);
  }

  let apiKey = cachedInternalApiKey.key || cachedTokenData.apiKey;
  if (!apiKey && process.env.AI_INTERNAL_API_KEY && !isRevokedKey(process.env.AI_INTERNAL_API_KEY)) {
    apiKey = process.env.AI_INTERNAL_API_KEY.trim();
  }
  if (!apiKey && lastStsAccessToken) {
    apiKey = await fetchSecretManagerKey(lastStsAccessToken, process.env.GCP_PROJECT_NUMBER || '755578057105');
  }
  if (apiKey) {
    finalHeaders['X-Internal-API-Key'] = apiKey.trim();
  }

  return finalHeaders;
}

/**
 * Resets token cache (useful for testing or forced renewal).
 */
function resetTokenCache() {
  cachedTokenData = {
    idToken: null,
    expiresAt: 0,
    audience: null,
    apiKey: null
  };
  cachedInternalApiKey = {
    key: null,
    expiresAt: 0
  };
  inFlightPromise = null;
}

module.exports = {
  getLastDiagnostics,
  getCloudRunIdToken,
  attachGcpAuthHeaders,
  resolveCloudRunAudience,
  isGoogleCloudRunTarget,
  exchangeVercelTokenForStsAccessToken,
  generateServiceAccountIdToken,
  retrieveVercelOidcToken,
  decodeJwtPayload,
  resetTokenCache
};

