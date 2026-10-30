const { test, describe, before, after } = require('node:test');
const assert = require('node:assert');
const express = require('express');
const http = require('http');
const jwt = require('jsonwebtoken');
const { initDatabase, query } = require('../src/config/db');
const { seedAll } = require('../src/server');
const authRoutes = require('../src/routes/auth.routes');
const adminRoutes = require('../src/routes/admin.routes');
const { getJwtSecret } = require('../src/middleware/auth');

describe('Production Authentication Security Hardening Suite', () => {
  let server;
  let baseUrl;

  before(async () => {
    await initDatabase();
    if (seedAll) {
      await seedAll();
    }
    const app = express();
    app.use(express.json());
    app.use('/api/auth', authRoutes);
    app.use('/api/admin', adminRoutes);

    await new Promise((resolve) => {
      server = http.createServer(app);
      server.listen(0, '127.0.0.1', () => {
        const addr = server.address();
        baseUrl = `http://127.0.0.1:${addr.port}`;
        resolve();
      });
    });
  });

  after(async () => {
    if (server) {
      await new Promise((resolve, reject) => {
        server.close((err) => err ? reject(err) : resolve());
      });
    }
  });

  test('1. Citizen authenticates with correct individual password', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: '8788562103',
        password: '8788562103'
      })
    });
    assert.strictEqual(res.status, 200);
    const data = await res.json();
    assert.ok(data.token);
    assert.strictEqual(data.user.role, 'citizen');
  });

  test('2. Citizen authentication with wrong password returns 401', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: '8788562103',
        password: 'incorrect_password_citizen'
      })
    });
    assert.strictEqual(res.status, 401);
    const data = await res.json();
    assert.strictEqual(data.error, 'Invalid login credentials');
  });

  test('3. Department Head authenticates with individual password', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    assert.strictEqual(res.status, 200);
    const data = await res.json();
    assert.ok(data.token);
    assert.strictEqual(data.user.role, 'department_head');
    assert.ok(data.user.department_name);
  });

  test('4. Department Head with wrong password returns 401', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'wrong_password_dh'
      })
    });
    assert.strictEqual(res.status, 401);
  });

  test('5. City Admin authenticates with individual password', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'admin@nagarsetu.gov.in',
        password: 'admin@123'
      })
    });
    assert.strictEqual(res.status, 200);
    const data = await res.json();
    assert.ok(data.token);
    assert.strictEqual(data.user.role, 'city_admin');
  });

  test('6. City Admin with wrong password returns 401', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'admin@nagarsetu.gov.in',
        password: 'wrong_password_admin'
      })
    });
    assert.strictEqual(res.status, 401);
  });

  test('7. Password change: rejects request without authentication token', async () => {
    const res = await fetch(`${baseUrl}/api/auth/change-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        currentPassword: 'old',
        newPassword: 'new'
      })
    });
    assert.strictEqual(res.status, 401);
  });

  test('8. Password change: rejects when new password is too short (< 6 chars)', async () => {
    const loginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    const { token } = await loginRes.json();

    const changeRes = await fetch(`${baseUrl}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        currentPassword: 'head@123',
        newPassword: 'short'
      })
    });
    assert.strictEqual(changeRes.status, 400);
    const data = await changeRes.json();
    assert.ok(data.error.includes('6 characters'));
  });

  test('9. Password change: rejects when current password is wrong', async () => {
    const loginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    const { token } = await loginRes.json();

    const changeRes = await fetch(`${baseUrl}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        currentPassword: 'wrong_current_password',
        newPassword: 'newValidPassword123'
      })
    });
    assert.strictEqual(changeRes.status, 400);
    const data = await changeRes.json();
    assert.strictEqual(data.error, 'Current password is incorrect');
  });

  test('10. Password change: successfully updates password to unique credential', async () => {
    const loginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    const { token } = await loginRes.json();

    const changeRes = await fetch(`${baseUrl}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        currentPassword: 'head@123',
        newPassword: 'RahulPWD#2026Unique'
      })
    });
    assert.strictEqual(changeRes.status, 200);
    const changeData = await changeRes.json();
    assert.strictEqual(changeData.success, true);
    assert.strictEqual(changeData.user.must_change_password, false);

    // Verify login with new password succeeds
    const newLoginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'RahulPWD#2026Unique'
      })
    });
    assert.strictEqual(newLoginRes.status, 200);

    // Verify old password no longer works
    const oldLoginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    assert.strictEqual(oldLoginRes.status, 401);
  });

  test('11. Password reset workflow: request and execute reset token', async () => {
    // Request reset
    const forgotRes = await fetch(`${baseUrl}/api/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identifier: 'amit.sharma@nagarsetu.gov.in'
      })
    });
    assert.strictEqual(forgotRes.status, 200);
    const forgotData = await forgotRes.json();
    assert.strictEqual(forgotData.success, true);
    assert.ok(forgotData.resetToken, 'Must generate reset token in non-production');

    // Execute reset with token
    const resetRes = await fetch(`${baseUrl}/api/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: forgotData.resetToken,
        newPassword: 'AmitSAN#2026Private'
      })
    });
    assert.strictEqual(resetRes.status, 200);
    const resetData = await resetRes.json();
    assert.strictEqual(resetData.success, true);

    // Verify login with new password
    const loginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'amit.sharma@nagarsetu.gov.in',
        password: 'AmitSAN#2026Private'
      })
    });
    assert.strictEqual(loginRes.status, 200);
  });

  test('12. Password reset rejects invalid or already used tokens', async () => {
    const resetRes = await fetch(`${baseUrl}/api/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: 'invalid_or_expired_token_12345',
        newPassword: 'AnotherPassword#999'
      })
    });
    assert.strictEqual(resetRes.status, 400);
    const data = await resetRes.json();
    assert.strictEqual(data.error, 'Invalid or expired password reset token');
  });

  test('13. Expired JWT is rejected with 403 Forbidden', async () => {
    const secret = getJwtSecret();
    const expiredToken = jwt.sign(
      { id: 1, role: 'citizen' },
      secret,
      { expiresIn: '-10s' } // Expired 10 seconds ago
    );

    const res = await fetch(`${baseUrl}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${expiredToken}` }
    });
    assert.strictEqual(res.status, 403);
    const data = await res.json();
    assert.strictEqual(data.error, 'Invalid or expired token');
  });

  test('14. Tampered JWT signature is rejected with 403 Forbidden', async () => {
    const tamperedToken = jwt.sign(
      { id: 1, role: 'city_admin' },
      'wrong_untrusted_signing_secret_for_attack_attempt_only_12345',
      { expiresIn: '1h' }
    );

    const res = await fetch(`${baseUrl}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${tamperedToken}` }
    });
    assert.strictEqual(res.status, 403);
  });

  test('15. RBAC: Citizen cannot access Admin API (403 Forbidden)', async () => {
    const loginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: '8788562103',
        password: '8788562103'
      })
    });
    const { token } = await loginRes.json();

    const adminRes = await fetch(`${baseUrl}/api/admin/analytics`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    assert.strictEqual(adminRes.status, 403);
  });
});

