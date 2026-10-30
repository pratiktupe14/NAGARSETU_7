const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const dbPath = path.join(__dirname, '../../nagarsetu.sqlite');
const db = new sqlite3.Database(dbPath);

console.log('--- STARTING SQLITE COMPLAINT PURGE ---');

db.serialize(() => {
  db.run('PRAGMA foreign_keys = ON;');
  db.run('BEGIN TRANSACTION;');

  db.get('SELECT COUNT(*) as c FROM complaints;', (err, row) => {
    console.log('Before count (complaints):', row?.c);
  });

  db.run('DELETE FROM feedback;');
  db.run('DELETE FROM assignments;');
  db.run('DELETE FROM complaint_status_history;');
  db.run('DELETE FROM notifications WHERE complaint_id IS NOT NULL;');
  db.run('DELETE FROM recurring_issue_links;');
  db.run('DELETE FROM complaint_evidence_versions;');
  db.run('DELETE FROM blockchain_transactions;');
  db.run('DELETE FROM complaints;');

  db.run("DELETE FROM sqlite_sequence WHERE name IN ('complaints', 'assignments', 'complaint_status_history', 'feedback', 'task_assignments', 'blockchain_transactions');");

  db.run('COMMIT;', (err) => {
    if (err) {
      console.error('Commit error:', err);
      db.run('ROLLBACK;');
      return;
    }
    console.log('SQLite transaction committed successfully.');

    db.get('SELECT COUNT(*) as c FROM complaints;', (e, row) => {
      console.log('After count (complaints):', row?.c);
      
      db.get('SELECT COUNT(*) as u FROM users;', (e2, uRow) => {
        console.log('Preserved users count:', uRow?.u);
      });
      db.get('SELECT COUNT(*) as d FROM departments;', (e3, dRow) => {
        console.log('Preserved departments count:', dRow?.d);
      });
      db.get('SELECT COUNT(*) as dh FROM department_heads;', (e4, dhRow) => {
        console.log('Preserved department_heads count:', dhRow?.dh);
        
        db.run('VACUUM;', () => {
          console.log('VACUUM completed.');
          db.close();
        });
      });
    });
  });
});
