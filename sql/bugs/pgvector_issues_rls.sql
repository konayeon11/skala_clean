-- 이슈 소유자(또는 조직/팀) 식별자
ALTER TABLE issues ADD COLUMN IF NOT EXISTS owner_id integer NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_issues_owner ON issues(owner_id);

-- Row Level Security 활성화
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
-- (선택) 강제: 슈퍼유저 외 모든 세션에 RLS 강제
ALTER TABLE issues FORCE ROW LEVEL SECURITY;

-- 세션 변수(app.user_id)에 따라 행 필터링
DROP POLICY IF EXISTS policy_issues_by_owner ON issues;
CREATE POLICY policy_issues_by_owner
  ON issues
  USING ( owner_id = current_setting('app.user_id', true)::int );

-- INSERT 시에도 본인 소유만 넣도록 체크(선택)
DROP POLICY IF EXISTS policy_issues_insert ON issues;
CREATE POLICY policy_issues_insert
  ON issues FOR INSERT
  WITH CHECK ( owner_id = current_setting('app.user_id', true)::int );