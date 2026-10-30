-- ==============================================================================
-- NAGARSETU 3.1: SAFE & PERMANENT COMPLAINT DATA PURGE ACROSS ALL PORTALS
-- Target Supabase Project: ozeiymkbxtrqqdoxtmhm (https://ozeiymkbxtrqqdoxtmhm.supabase.co)
--
-- This script safely removes 100% of complaints and dependent history while
-- strictly preserving all user accounts, roles, departments, and heads.
-- It also installs the missing DELETE RLS policies so future admin deletes work.
-- ==============================================================================

BEGIN;

-- 1. Break self-referential foreign key cycles on complaints (duplicate_of_id)
UPDATE public.complaints
SET duplicate_of_id = NULL
WHERE duplicate_of_id IS NOT NULL;

-- 2. Safely delete dependent records across all known schema variants
DELETE FROM public.complaint_status_history;
DELETE FROM public.task_assignments;
DELETE FROM public.complaint_feedback;
DELETE FROM public.notifications WHERE complaint_id IS NOT NULL;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'recurring_issue_links') THEN
    EXECUTE 'DELETE FROM public.recurring_issue_links;';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'complaint_evidence_versions') THEN
    EXECUTE 'DELETE FROM public.complaint_evidence_versions;';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'assignments') THEN
    EXECUTE 'DELETE FROM public.assignments;';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'feedback') THEN
    EXECUTE 'DELETE FROM public.feedback;';
  END IF;
END $$;

-- 3. Delete parent complaints
DELETE FROM public.complaints;

-- 4. Install missing RLS DELETE policies for administrative roles
DROP POLICY IF EXISTS "Complaints delete policy" ON public.complaints;
CREATE POLICY "Complaints delete policy" ON public.complaints
  FOR DELETE TO authenticated
  USING (current_user_role() IN ('city_admin', 'admin', 'super_admin'));

DROP POLICY IF EXISTS "Complaint status history delete policy" ON public.complaint_status_history;
CREATE POLICY "Complaint status history delete policy" ON public.complaint_status_history
  FOR DELETE TO authenticated
  USING (current_user_role() IN ('city_admin', 'admin', 'super_admin'));

DROP POLICY IF EXISTS "Task assignments delete policy" ON public.task_assignments;
CREATE POLICY "Task assignments delete policy" ON public.task_assignments
  FOR DELETE TO authenticated
  USING (current_user_role() IN ('city_admin', 'admin', 'super_admin'));

DROP POLICY IF EXISTS "Complaint feedback delete policy" ON public.complaint_feedback;
CREATE POLICY "Complaint feedback delete policy" ON public.complaint_feedback
  FOR DELETE TO authenticated
  USING (current_user_role() IN ('city_admin', 'admin', 'super_admin'));

-- 5. Verification Checks within Transaction
DO $$
DECLARE
  v_complaints_count INT;
  v_history_count INT;
  v_tasks_count INT;
  v_feedback_count INT;
  v_users_count INT;
  v_depts_count INT;
  v_heads_count INT;
BEGIN
  SELECT COUNT(*) INTO v_complaints_count FROM public.complaints;
  SELECT COUNT(*) INTO v_history_count FROM public.complaint_status_history;
  SELECT COUNT(*) INTO v_tasks_count FROM public.task_assignments;
  SELECT COUNT(*) INTO v_feedback_count FROM public.complaint_feedback;
  
  SELECT COUNT(*) INTO v_users_count FROM public.users;
  SELECT COUNT(*) INTO v_depts_count FROM public.departments;
  SELECT COUNT(*) INTO v_heads_count FROM public.department_heads;

  IF v_complaints_count > 0 OR v_history_count > 0 OR v_tasks_count > 0 OR v_feedback_count > 0 THEN
    RAISE EXCEPTION 'Cleanup verification failed: % complaint records still remain! Rolling back.', v_complaints_count;
  END IF;

  IF v_users_count = 0 OR v_depts_count = 0 OR v_heads_count = 0 THEN
    RAISE EXCEPTION 'CRITICAL: Preserved core data was compromised! Rolling back.';
  END IF;

  RAISE NOTICE 'SUCCESS: All complaints wiped (0 remaining). Preserved: % users, % departments, % department heads.',
    v_users_count, v_depts_count, v_heads_count;
END $$;

COMMIT;
