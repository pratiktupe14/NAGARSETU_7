const { query } = require('../config/db');
const { notifyStatusChange } = require('./notificationService');
const { resolveDepartmentByCodeSync } = require('./departmentService');

function getCanonicalDepartment(val) {
  if (!val) return null;
  const canonical = resolveDepartmentByCodeSync(val);
  if (!canonical) return null;
  return {
    id: canonical.registry_id,
    code: canonical.code,
    name: canonical.name,
    uuid: canonical.id
  };
}

/**
 * Determine the best eligible field staff member based on NagarSetu priority rules:
 * 1. Correct department only (strictly isolated)
 * 2. Active eligible staff only
 * 3. Lowest active task count first
 * 4. Among equal workload, fair round-robin (oldest last_assigned_at)
 * 5. If still tied: better existing performance metric (SLA rate, completed tasks, lower overdue)
 * 6. If still tied: oldest last_assigned_at / ID tie-breaker
 *
 * @param {Array} staffList - Array of staff objects with metrics
 * @param {string} [priority] - Complaint priority ('Low' | 'Medium' | 'High' | 'Critical')
 * @returns {Object|null} Selected staff member or null if none eligible
 */
function selectBestStaff(staffList, priority = 'Medium') {
  if (!staffList || staffList.length === 0) return null;

  // Filter out any invalid / inactive staff defensively
  const eligible = staffList.filter((s) => {
    const status = (s.status || 'active').toLowerCase();
    const role = (s.role || '').toLowerCase();
    return status === 'active' && (role === 'service_staff' || role === 'staff');
  });

  if (eligible.length === 0) return null;

  // Sort candidate staff using exact priority rules
  eligible.sort((a, b) => {
    const aActive = Number(a.active_task_count || 0);
    const bActive = Number(b.active_task_count || 0);

    // Rule 1: Lowest active task count first
    if (aActive !== bActive) {
      return aActive - bActive;
    }

    // Rule 2: Among equal workload, fair round-robin via oldest last_assigned_at
    const aTime = a.last_assigned_at ? new Date(a.last_assigned_at).getTime() : 0;
    const bTime = b.last_assigned_at ? new Date(b.last_assigned_at).getTime() : 0;
    if (aTime !== bTime) {
      return aTime - bTime;
    }

    // Rule 3: Better existing performance metrics if tied
    const aSla = typeof a.sla_success_rate === 'number' ? a.sla_success_rate : 1.0;
    const bSla = typeof b.sla_success_rate === 'number' ? b.sla_success_rate : 1.0;
    if (aSla !== bSla) {
      return bSla - aSla;
    }

    const aCompleted = Number(a.completed_task_count || 0);
    const bCompleted = Number(b.completed_task_count || 0);
    if (aCompleted !== bCompleted) {
      return bCompleted - aCompleted;
    }

    const aOverdue = Number(a.overdue_task_count || 0);
    const bOverdue = Number(b.overdue_task_count || 0);
    if (aOverdue !== bOverdue) {
      return aOverdue - bOverdue;
    }

    return Number(a.id) - Number(b.id);
  });

  return eligible[0];
}

/**
 * Fetch eligible field staff for a given department along with real-time workload and performance
 *
 * @param {string|number} departmentId
 * @returns {Promise<Array>}
 */
async function getEligibleDepartmentStaff(departmentId) {
  if (!departmentId) return [];

  const canonicalDept = getCanonicalDepartment(departmentId);
  const deptNumericId = canonicalDept ? canonicalDept.id : Number(departmentId);
  const deptUuid = canonicalDept ? canonicalDept.uuid : String(departmentId);
  const deptCode = canonicalDept ? canonicalDept.code : '';

  // Query only active field service staff belonging strictly to this department
  const staffQuery = `
    SELECT u.id, u.name, u.email, u.mobile, u.role, u.department_id, u.status, u.last_assigned_at,
           (
             SELECT COUNT(DISTINCT c.id)
             FROM complaints c
             WHERE (c.assigned_staff_id = CAST(u.id AS TEXT) OR LOWER(c.assigned_staff_email) = LOWER(u.email) OR c.assigned_staff_name = u.name)
               AND c.status NOT IN ('Resolved', 'Closed', 'Completed', 'Rejected', 'Submitted')
               AND c.status IS NOT NULL
           ) as active_task_count,
           (
             SELECT COUNT(DISTINCT c.id)
             FROM complaints c
             WHERE (c.assigned_staff_id = CAST(u.id AS TEXT) OR LOWER(c.assigned_staff_email) = LOWER(u.email) OR c.assigned_staff_name = u.name)
               AND c.status = 'Resolved'
           ) as completed_task_count,
           (
             SELECT COUNT(DISTINCT c.id)
             FROM complaints c
             WHERE (c.assigned_staff_id = CAST(u.id AS TEXT) OR LOWER(c.assigned_staff_email) = LOWER(u.email) OR c.assigned_staff_name = u.name)
               AND (c.status = 'Overdue' OR (c.status NOT IN ('Resolved', 'Rejected') AND c.sla_deadline IS NOT NULL AND c.sla_deadline < CURRENT_TIMESTAMP))
           ) as overdue_task_count
    FROM users u
    WHERE (u.role = 'service_staff' OR u.role = 'staff')
      AND LOWER(COALESCE(u.status, 'active')) = 'active'
      AND (
        u.department_id = ?
        OR CAST(u.department_id AS TEXT) = ?
        OR u.department_id = ?
      )
  `;

  try {
    const res = await query(staffQuery, [
      deptNumericId,
      String(deptNumericId),
      deptUuid
    ]);
    let staffRows = res.rows || [];

    if (staffRows.length === 0) {
      try {
        const { getMemStore } = require('../config/db');
        const memStore = getMemStore ? getMemStore() : null;
        if (memStore && Array.isArray(memStore.users)) {
          staffRows = memStore.users.filter(u =>
            (u.role === 'service_staff' || u.role === 'staff') &&
            (u.status || 'active').toLowerCase() === 'active' &&
            (
              u.department_id === deptNumericId ||
              String(u.department_id) === String(deptNumericId) ||
              u.department_id === deptUuid
            )
          );
        }
      } catch (e) {}
    }

    // Calculate SLA success rate
    return staffRows.map((s) => {
      const active = Number(s.active_task_count || 0);
      const completed = Number(s.completed_task_count || 0);
      const overdue = Number(s.overdue_task_count || 0);
      const totalResolvedOrOverdue = completed + overdue;
      const slaRate = totalResolvedOrOverdue > 0 ? (completed / totalResolvedOrOverdue) : 1.0;

      return {
        ...s,
        active_task_count: active,
        completed_task_count: completed,
        overdue_task_count: overdue,
        sla_success_rate: slaRate
      };
    });
  } catch (err) {
    console.error('Error fetching eligible department staff:', err);
    return [];
  }
}

/**
 * Automatically assign a complaint to the best eligible staff member
 *
 * @param {string|number} complaintId
 * @param {string|number} departmentId
 * @param {Object} [options]
 * @returns {Promise<{ assigned: boolean, staff: Object|null, reason?: string }>}
 */
async function autoAssignComplaint(complaintId, departmentId, options = {}) {
  try {
    if (!complaintId || !departmentId) {
      return { assigned: false, staff: null, reason: 'MISSING_PARAMS' };
    }

    const { priority = 'Medium', citizenId = null, departmentName = null } = options;

    const eligibleStaff = await getEligibleDepartmentStaff(departmentId);
    if (!eligibleStaff || eligibleStaff.length === 0) {
      return { assigned: false, staff: null, reason: 'NO_ELIGIBLE_STAFF' };
    }

    const chosenStaff = selectBestStaff(eligibleStaff, priority);
    if (!chosenStaff) {
      return { assigned: false, staff: null, reason: 'NO_STAFF_SELECTED' };
    }

    // 1. Assign complaint in complaints table
    const updateComplaintSql = `
      UPDATE complaints
      SET status = 'Staff Assigned',
          assigned_staff_id = ?,
          assigned_staff_name = ?,
          assigned_staff_email = ?,
          assigned_by = 'system_auto_assign',
          assigned_by_name = 'Automated Dispatch System',
          assigned_at = CURRENT_TIMESTAMP,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = ? OR CAST(id AS TEXT) = ?
    `;
    await query(updateComplaintSql, [
      String(chosenStaff.id),
      chosenStaff.name,
      chosenStaff.email || '',
      complaintId,
      String(complaintId)
    ]);

    // 2. Insert into assignments and task_assignments tables
    const insertAssignSql = `
      INSERT INTO assignments (complaint_id, staff_id, assigned_by, assigned_at)
      VALUES (?, ?, 'system_auto_assign', CURRENT_TIMESTAMP)
    `;
    await query(insertAssignSql, [complaintId, chosenStaff.id]).catch((aErr) => {
      console.warn('Assignment table insert note:', aErr.message);
    });

    const insertTaskAssignSql = `
      INSERT INTO task_assignments (complaint_id, staff_id, assigned_by, created_at)
      VALUES (?, ?, 'system_auto_assign', CURRENT_TIMESTAMP)
    `;
    await query(insertTaskAssignSql, [complaintId, chosenStaff.id]).catch(() => {});

    // 3. Update staff member's last_assigned_at for fair round-robin rotation
    const updateStaffSql = `
      UPDATE users
      SET last_assigned_at = CURRENT_TIMESTAMP
      WHERE id = ? OR CAST(id AS TEXT) = ?
    `;
    await query(updateStaffSql, [chosenStaff.id, String(chosenStaff.id)]).catch(() => {});

    // 4. Record status history
    try {
      const dept = departmentName || 'Municipal Operations';
      await query(
        `INSERT INTO complaint_status_history (complaint_id, status, remark, department, updated_by) VALUES (?, ?, ?, ?, ?)`,
        [
          complaintId,
          'Staff Assigned',
          `Auto-assigned to field staff ${chosenStaff.name} (${chosenStaff.active_task_count} active tasks).`,
          dept,
          'Automated Dispatch System'
        ]
      );
    } catch (hErr) {}

    // 5. Notify status change
    if (citizenId) {
      await notifyStatusChange(complaintId, 'Staff Assigned', citizenId).catch(() => {});
    }

    return {
      assigned: true,
      staff: {
        id: chosenStaff.id,
        name: chosenStaff.name,
        email: chosenStaff.email,
        department_id: chosenStaff.department_id,
        active_task_count: chosenStaff.active_task_count
      }
    };
  } catch (err) {
    console.error('Error in autoAssignComplaint:', err);
    // Never fail complaint creation even if auto-assignment errors
    return { assigned: false, staff: null, reason: err.message };
  }
}

module.exports = {
  selectBestStaff,
  getEligibleDepartmentStaff,
  autoAssignComplaint
};
