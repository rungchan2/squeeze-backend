-- =====================================================
-- Sqeeze LMS Posts 테이블 안전한 마이그레이션 전략
-- =====================================================

-- 📊 현재 상황 분석:
-- - posts 테이블: 575개 레코드
-- - 모든 post에 content 존재 (HTML 형태)
-- - mission_type: 현재 "text" 타입만 사용
-- - 파일 업로드 없음 (file_url 모두 null)
-- - 팀 제출물: 2개만 존재

-- =====================================================
-- 1단계: 백업 및 준비 작업
-- =====================================================

-- 1-1. 전체 테이블 백업 생성
CREATE TABLE posts_backup_20250726 AS 
SELECT * FROM posts;

-- 1-2. 의존성 테이블 백업
CREATE TABLE user_points_backup_20250726 AS 
SELECT * FROM user_points;

CREATE TABLE team_points_backup_20250726 AS 
SELECT * FROM team_points;

CREATE TABLE comments_backup_20250726 AS 
SELECT * FROM comments;

CREATE TABLE likes_backup_20250726 AS 
SELECT * FROM likes;

-- 1-3. missions 테이블 현재 mission_type 값 확인
-- (현재 "text"로 되어 있으나 새로운 ENUM으로 변경 필요)
SELECT DISTINCT mission_type FROM missions;

-- =====================================================
-- 2단계: 새로운 ENUM 및 구조 생성
-- =====================================================

-- 2-1. mission_type ENUM 생성
CREATE TYPE mission_type AS ENUM (
    'essay',           -- 주관식 (기존 text 타입)
    'multiple_choice', -- 객관식
    'image_upload',    -- 이미지 제출
    'mixed'            -- 복합형
);

-- 2-2. Mission Questions 테이블 생성
CREATE TABLE mission_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL,
    question_text TEXT NOT NULL,
    question_type mission_type NOT NULL DEFAULT 'essay',
    question_order INTEGER NOT NULL DEFAULT 1,
    
    -- 객관식 관련 필드
    options JSONB, -- 객관식 선택지
    correct_answer TEXT, -- 정답
    
    -- 이미지 업로드 관련 필드
    max_images INTEGER DEFAULT 1,
    required_image BOOLEAN DEFAULT false,
    
    -- 공통 필드
    is_required BOOLEAN DEFAULT true,
    max_characters INTEGER,
    placeholder_text TEXT,
    points INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
);

-- RLS 활성화
ALTER TABLE mission_questions ENABLE ROW LEVEL SECURITY;

-- 인덱스 생성
CREATE INDEX idx_mission_questions_mission_id ON mission_questions(mission_id);
CREATE INDEX idx_mission_questions_order ON mission_questions(question_order);

-- =====================================================
-- 3단계: Posts 테이블 점진적 변경
-- =====================================================

-- 3-1. 새로운 컬럼들 추가 (NULL 허용으로 시작)
ALTER TABLE posts 
ADD COLUMN IF NOT EXISTS answers_data JSONB,
ADD COLUMN IF NOT EXISTS auto_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS manual_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_questions INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS answered_questions INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS completion_rate DECIMAL(5,2) DEFAULT 100.00;

-- 3-2. 인덱스 추가
CREATE INDEX idx_posts_answers_data ON posts USING GIN (answers_data);

-- =====================================================
-- 4단계: 데이터 마이그레이션 함수 생성
-- =====================================================

-- 4-1. 기존 missions 데이터를 위한 기본 질문 생성 함수
CREATE OR REPLACE FUNCTION create_default_questions_for_existing_missions()
RETURNS void AS $$
DECLARE
    mission_record RECORD;
    question_id UUID;
BEGIN
    -- 기존 모든 missions에 대해 기본 질문 생성
    FOR mission_record IN 
        SELECT id, name, description, points 
        FROM missions 
        WHERE NOT EXISTS (
            SELECT 1 FROM mission_questions WHERE mission_id = missions.id
        )
    LOOP
        -- 각 미션에 대해 기본 주관식 질문 생성
        INSERT INTO mission_questions (
            mission_id, 
            question_text, 
            question_type, 
            question_order, 
            max_characters,
            points,
            is_required
        ) VALUES (
            mission_record.id,
            COALESCE(mission_record.description, mission_record.name),
            'essay',
            1,
            5000, -- 충분한 글자 수
            COALESCE(mission_record.points, 0),
            true
        ) RETURNING id INTO question_id;
        
        RAISE NOTICE 'Created default question for mission: %', mission_record.name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 4-2. Posts 데이터 마이그레이션 함수
CREATE OR REPLACE FUNCTION migrate_posts_to_new_structure()
RETURNS void AS $$
DECLARE
    post_record RECORD;
    question_id UUID;
    migration_count INTEGER := 0;
BEGIN
    -- 기존 posts 데이터를 새 구조로 변환
    FOR post_record IN 
        SELECT id, content, mission_instance_id, score, created_at, updated_at
        FROM posts 
        WHERE answers_data IS NULL
        ORDER BY created_at
    LOOP
        -- 해당 미션의 첫 번째 질문 ID 찾기
        SELECT mq.id INTO question_id
        FROM journey_mission_instances jmi
        JOIN mission_questions mq ON jmi.mission_id = mq.mission_id
        WHERE jmi.id = post_record.mission_instance_id
        ORDER BY mq.question_order
        LIMIT 1;
        
        -- answers_data JSON 구조 생성
        UPDATE posts 
        SET 
            answers_data = jsonb_build_object(
                'answers', jsonb_build_array(
                    jsonb_build_object(
                        'question_id', question_id,
                        'question_order', 1,
                        'answer_type', 'essay',
                        'answer_text', post_record.content,
                        'selected_option', null,
                        'image_urls', ARRAY[]::text[],
                        'is_correct', null,
                        'points_earned', COALESCE(post_record.score, 0)
                    )
                ),
                'submission_metadata', jsonb_build_object(
                    'total_questions', 1,
                    'answered_questions', CASE 
                        WHEN post_record.content IS NOT NULL AND post_record.content != '' THEN 1 
                        ELSE 0 
                    END,
                    'submission_time', post_record.created_at,
                    'last_modified', post_record.updated_at
                )
            ),
            manual_score = COALESCE(post_record.score, 0),
            total_questions = 1,
            answered_questions = CASE 
                WHEN post_record.content IS NOT NULL AND post_record.content != '' THEN 1 
                ELSE 0 
            END,
            completion_rate = CASE 
                WHEN post_record.content IS NOT NULL AND post_record.content != '' THEN 100.00 
                ELSE 0.00 
            END
        WHERE id = post_record.id;
        
        migration_count := migration_count + 1;
        
        -- 진행 상황 로그 (100개마다)
        IF migration_count % 100 = 0 THEN
            RAISE NOTICE 'Migrated % posts', migration_count;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Migration completed. Total posts migrated: %', migration_count;
END;
$$ LANGUAGE plpgsql;

-- 4-3. missions 테이블 mission_type 업데이트 함수
CREATE OR REPLACE FUNCTION update_missions_type()
RETURNS void AS $$
BEGIN
    -- 기존 "text" 타입을 "essay"로 변경
    UPDATE missions 
    SET mission_type = 'essay'::text 
    WHERE mission_type = 'text';
    
    -- mission_type 컬럼을 ENUM으로 변경
    ALTER TABLE missions 
    ALTER COLUMN mission_type TYPE mission_type 
    USING CASE 
        WHEN mission_type = 'text' THEN 'essay'::mission_type
        ELSE 'essay'::mission_type
    END;
    
    -- 기본값 설정
    ALTER TABLE missions 
    ALTER COLUMN mission_type SET DEFAULT 'essay';
    
    RAISE NOTICE 'missions.mission_type updated to ENUM';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5단계: 검증 함수들
-- =====================================================

-- 5-1. 마이그레이션 검증 함수
CREATE OR REPLACE FUNCTION validate_migration()
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- 1. 전체 post 수 확인
    RETURN QUERY
    SELECT 
        'Post Count Check'::TEXT,
        CASE 
            WHEN (SELECT COUNT(*) FROM posts) = (SELECT COUNT(*) FROM posts_backup_20250726)
            THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('Original: %s, Current: %s', 
            (SELECT COUNT(*) FROM posts_backup_20250726),
            (SELECT COUNT(*) FROM posts)
        );
    
    -- 2. answers_data 생성 확인
    RETURN QUERY
    SELECT 
        'Answers Data Check'::TEXT,
        CASE 
            WHEN (SELECT COUNT(*) FROM posts WHERE answers_data IS NOT NULL) = (SELECT COUNT(*) FROM posts)
            THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('Posts with answers_data: %s / %s', 
            (SELECT COUNT(*) FROM posts WHERE answers_data IS NOT NULL),
            (SELECT COUNT(*) FROM posts)
        );
    
    -- 3. 기본 질문 생성 확인
    RETURN QUERY
    SELECT 
        'Mission Questions Check'::TEXT,
        CASE 
            WHEN (SELECT COUNT(*) FROM mission_questions) >= (SELECT COUNT(*) FROM missions)
            THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        format('Questions: %s, Missions: %s', 
            (SELECT COUNT(*) FROM mission_questions),
            (SELECT COUNT(*) FROM missions)
        );
    
    -- 4. 점수 데이터 일관성 확인
    RETURN QUERY
    SELECT 
        'Score Consistency Check'::TEXT,
        CASE 
            WHEN (
                SELECT COUNT(*) FROM posts p1 
                JOIN posts_backup_20250726 p2 ON p1.id = p2.id 
                WHERE COALESCE(p1.score, 0) != COALESCE(p2.score, 0)
            ) = 0
            THEN 'PASS'::TEXT
            ELSE 'FAIL'::TEXT
        END,
        'Score data consistency between original and migrated';
END;
$$ LANGUAGE plpgsql;

-- 5-2. 샘플 데이터 조회 함수
CREATE OR REPLACE FUNCTION get_migration_samples(sample_count INTEGER DEFAULT 5)
RETURNS TABLE (
    post_id UUID,
    original_content TEXT,
    new_answers_data JSONB,
    original_score INTEGER,
    new_manual_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        LEFT(pb.content, 100),
        p.answers_data,
        pb.score,
        p.manual_score
    FROM posts p
    JOIN posts_backup_20250726 pb ON p.id = pb.id
    ORDER BY p.created_at DESC
    LIMIT sample_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6단계: 실행 스크립트 (순서대로 실행)
-- =====================================================

-- 실행 순서:
/*
1. 백업 생성
   SELECT 'Backup created' as step;

2. 기본 질문 생성
   SELECT create_default_questions_for_existing_missions();

3. missions 테이블 타입 업데이트
   SELECT update_missions_type();

4. posts 데이터 마이그레이션
   SELECT migrate_posts_to_new_structure();

5. 검증 실행
   SELECT * FROM validate_migration();

6. 샘플 확인
   SELECT * FROM get_migration_samples(10);
*/

-- =====================================================
-- 7단계: 롤백 스크립트 (문제 발생 시 사용)
-- =====================================================

CREATE OR REPLACE FUNCTION rollback_migration()
RETURNS void AS $$
BEGIN
    -- posts 테이블 복원
    DROP TABLE IF EXISTS posts;
    CREATE TABLE posts AS SELECT * FROM posts_backup_20250726;
    
    -- 기본키 복원
    ALTER TABLE posts ADD PRIMARY KEY (id);
    
    -- 외래키 복원
    ALTER TABLE posts ADD CONSTRAINT posts_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES profiles(id);
    ALTER TABLE posts ADD CONSTRAINT posts_mission_instance_id_fkey 
        FOREIGN KEY (mission_instance_id) REFERENCES journey_mission_instances(id);
    
    -- 새 테이블들 제거
    DROP TABLE IF EXISTS mission_questions;
    DROP TYPE IF EXISTS mission_type;
    
    RAISE NOTICE 'Rollback completed';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8단계: 정리 스크립트 (마이그레이션 완료 후 실행)
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_migration()
RETURNS void AS $$
BEGIN
    -- content 컬럼 제거 (선택사항 - 신중하게 결정)
    -- ALTER TABLE posts DROP COLUMN content;
    
    -- 백업 테이블 제거 (충분히 검증 후)
    -- DROP TABLE posts_backup_20250726;
    -- DROP TABLE user_points_backup_20250726;
    -- DROP TABLE team_points_backup_20250726;
    -- DROP TABLE comments_backup_20250726;
    -- DROP TABLE likes_backup_20250726;
    
    RAISE NOTICE 'Cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9단계: RLS 정책 생성
-- =====================================================

-- mission_questions RLS 정책
CREATE POLICY "Users can view mission questions" ON mission_questions
    FOR SELECT USING (true);

CREATE POLICY "Teachers can manage mission questions" ON mission_questions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() 
            AND role IN ('teacher', 'admin')
        )
    );

-- =====================================================
-- 10단계: 성능 최적화
-- =====================================================

-- 통계 업데이트
ANALYZE posts;
ANALYZE mission_questions;

-- 추가 인덱스 (필요시)
-- CREATE INDEX idx_posts_completion_rate ON posts(completion_rate);
-- CREATE INDEX idx_posts_manual_score ON posts(manual_score);

-- =====================================================
-- 마이그레이션 실행 체크리스트
-- =====================================================

/*
□ 1. 백업 생성 완료
□ 2. 기본 질문 생성 완료  
□ 3. missions 타입 업데이트 완료
□ 4. posts 마이그레이션 완료
□ 5. 검증 통과
□ 6. 샘플 데이터 확인
□ 7. API 테스트 완료
□ 8. 사용자 테스트 완료
□ 9. 정리 작업 완료
□ 10. 문서 업데이트 완료
*/