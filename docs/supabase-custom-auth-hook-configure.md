## Detail of supabase custom auth hook config


function:

```sql
DECLARE
  user_id uuid;
  profile_record RECORD;
  claims jsonb;
BEGIN
  -- 사용자 ID 가져오기
  user_id = (event->>'user_id')::uuid;
  claims = event->'claims';
  
  -- 사용자 프로필 정보 조회
  SELECT 
    role, 
    first_name, 
    last_name, 
    organization_id,
    email,
    id,
    profile_image
  INTO profile_record
  FROM public.profiles
  WHERE id = user_id;
  
  -- 프로필 정보가 있으면 JWT에 추가
  IF profile_record IS NOT NULL THEN
    -- app_metadata에 역할 및 조직 정보 추가
    claims = jsonb_set(
      claims,
      '{app_metadata}',
      jsonb_build_object(
        'role', profile_record.role,
        'organization_id', profile_record.organization_id,
        'profile_id', profile_record.id
      )
    );
    
    -- user_metadata에 개인 정보 추가
    claims = jsonb_set(
      claims,
      '{user_metadata}',
      jsonb_build_object(
        'first_name', profile_record.first_name,
        'last_name', profile_record.last_name,
        'email', profile_record.email,
        'profile_image', profile_record.profile_image
      )
    );
  END IF;
  
  -- 수정된 claims 반환
  RETURN jsonb_build_object('claims', claims);
END;

```

trigger:

```sql
-- Grant access to function to supabase_auth_admin
grant execute on function public.custom_access_token_hook to supabase_auth_admin;

-- Grant access to schema to supabase_auth_admin
grant usage on schema public to supabase_auth_admin;

-- Revoke function permissions from authenticated, anon and public
revoke execute on function public.custom_access_token_hook from authenticated, anon, public;
```