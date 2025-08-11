# Sqeeze LMS Database Schema

This document provides a comprehensive overview of the Sqeeze LMS database schema, including all tables, relationships, and data types. This schema supports a learning management system with role-based access control, journey-based learning paths, mission assignments, team collaboration features, and centralized file management.

## Project Information
- **Database Type**: PostgreSQL (Supabase)
- **Project ID**: egptutozdfchliouephl
- **Region**: ap-northeast-2
- **Postgres Version**: 15.8.1.070

## Core Entities Overview

### Authentication & User Management
- **Organizations**: Multi-tenant organization structure
- **Profiles**: User profiles with role-based permissions
- **Role Access Code**: Access codes for role elevation

### Learning Structure
- **Journeys**: Learning paths/courses
- **Journey Weeks**: Weekly structure within journeys
- **Missions**: Individual assignments/tasks with enhanced question system
- **Mission Questions**: Structured questions for missions (NEW)
- **Journey Mission Instances**: Missions assigned to specific journey weeks
- **User Journeys**: User enrollment in journeys

### Content & Engagement
- **Posts**: Student submissions with enhanced answer structure (UPDATED)
- **Comments**: Post comments
- **Likes**: Post likes/reactions
- **Notifications**: User notifications

### Team Management
- **Teams**: Team structure within journeys
- **Team Members**: Team membership

### Points & Scoring
- **User Points**: Individual user points
- **Team Points**: Team-based points

### File Management (NEW)
- **Files**: Centralized file management system

### System Features
- **Bug Reports**: User-submitted bug reports
- **Email Queue**: Email notification queue
- **Subscriptions**: Push notification subscriptions
- **Blog**: Blog content management
- **Inquiry**: Business inquiry form data

---

## Detailed Table Schemas

### 1. Organizations

Multi-tenant organization structure for institutional data isolation.

₩₩₩sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Primary Key: `id` (UUID)
- Estimated Records: 18

---

### 2. Profiles

User profiles with role-based permissions and organization affiliation.

₩₩₩sql
CREATE TYPE role AS ENUM ('user', 'teacher', 'admin');

CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    first_name TEXT,
    last_name TEXT,
    organization_id UUID DEFAULT '6fb0bbe1-56ac-40fc-8725-ae302d6faac0'::uuid,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    profile_image TEXT,
    profile_image_file_id INTEGER,  -- NEW: FK to files table
    marketing_opt_in BOOLEAN NOT NULL DEFAULT false,
    privacy_agreed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    role role NOT NULL DEFAULT 'user',
    push_subscription TEXT,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (id) REFERENCES auth.users(id),
    FOREIGN KEY (profile_image_file_id) REFERENCES files(id)  -- NEW
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Primary Key: `id` (UUID, linked to auth.users)
- Role Hierarchy: user(1) → teacher(2) → admin(3)
- Organization-based data isolation
- **NEW**: Centralized file management for profile images
- Estimated Records: 354

**Role Enum Values:**
- `user`: Students (default)
- `teacher`: Teachers/instructors
- `admin`: System administrators

---

### 3. Role Access Code

Access codes for teacher/admin role assignment during signup.

₩₩₩sql
CREATE TABLE role_access_code (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role role NOT NULL,
    code UUID DEFAULT gen_random_uuid(),
    expiry_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Used for role elevation during user registration
- Supports expiry dates for time-limited access
- Estimated Records: 1

---

### 4. Journeys

Learning paths/courses with start and end dates.

₩₩₩sql
CREATE TABLE journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    date_start DATE,
    date_end DATE,
    image_url TEXT,
    image_file_id INTEGER,  -- NEW: FK to files table
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (image_file_id) REFERENCES files(id)  -- NEW
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Course/learning path management
- Optional date ranges for course scheduling
- **NEW**: Centralized file management for journey images
- Estimated Records: 16

---

### 5. User Journeys

User enrollment and participation in journeys.

₩₩₩sql
CREATE TABLE user_journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    journey_id UUID NOT NULL,
    role_in_journey TEXT DEFAULT 'user',
    joined_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (user_id) REFERENCES profiles(id),
    FOREIGN KEY (journey_id) REFERENCES journeys(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ❌
- Junction table for user-journey relationships
- Supports different roles within journeys
- Tracks enrollment date
- Estimated Records: 356

---

### 6. Journey Weeks

Weekly structure within journeys for organized learning progression.

₩₩₩sql
CREATE TABLE journey_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL,
    name TEXT NOT NULL,
    week_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (journey_id) REFERENCES journeys(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Organizes journey content by weeks
- Sequential week numbering
- Estimated Records: 56

---

### 7. Missions (UPDATED)

Individual assignments/tasks with enhanced mission types.

₩₩₩sql
CREATE TYPE mission_type AS ENUM (
    'essay',           -- 주관식
    'multiple_choice', -- 객관식
    'image_upload',    -- 이미지 제출
    'mixed'            -- 복합형
);

CREATE TABLE missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    mission_type mission_type NOT NULL DEFAULT 'essay',  -- UPDATED: Now ENUM
    points INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Reusable mission templates
- **UPDATED**: Enhanced mission types (essay, multiple_choice, image_upload, mixed)
- Point-based scoring system
- Estimated Records: 71

---

### 8. Mission Questions (NEW)

Structured questions for missions supporting various question types.

₩₩₩sql
CREATE TABLE mission_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL,
    question_text TEXT NOT NULL,
    question_type mission_type NOT NULL DEFAULT 'essay',
    question_order INTEGER NOT NULL DEFAULT 1,
    
    -- 객관식 관련 필드
    options JSONB, -- 객관식 선택지 저장
    correct_answer TEXT, -- 정답 (객관식인 경우)
    
    -- 이미지 업로드 관련 필드
    max_images INTEGER DEFAULT 1, -- 최대 이미지 개수
    required_image BOOLEAN DEFAULT false, -- 이미지 필수 여부
    
    -- 공통 필드
    is_required BOOLEAN DEFAULT true,
    max_characters INTEGER, -- 주관식 답변 최대 글자 수
    placeholder_text TEXT, -- 입력 가이드
    points INTEGER DEFAULT 0, -- 문항별 점수
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- **NEW**: Supports multiple question types per mission
- **NEW**: Objective questions with automatic grading
- **NEW**: Image upload questions
- **NEW**: Mixed-type questions
- Estimated Records: 71

---

### 9. Journey Mission Instances

Missions assigned to specific journey weeks with scheduling and status tracking.

₩₩₩sql
CREATE TYPE mission_status AS ENUM ('not_started', 'in_progress', 'submitted', 'completed', 'rejected');

CREATE TABLE journey_mission_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_week_id UUID NOT NULL,
    mission_id UUID NOT NULL,
    release_date TIMESTAMPTZ,
    expiry_date TIMESTAMPTZ,
    status mission_status DEFAULT 'not_started',
    journey_id UUID,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (journey_week_id) REFERENCES journey_weeks(id),
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Links missions to specific weeks in journeys
- Release and expiry date scheduling
- Status tracking for mission lifecycle
- Estimated Records: 100

**Mission Status Values:**
- `not_started`: Mission not yet begun
- `in_progress`: Mission currently being worked on
- `submitted`: Mission submitted for review
- `completed`: Mission successfully completed
- `rejected`: Mission submission rejected

---

### 10. Teams

Team structure within journeys for collaborative learning.

₩₩₩sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (journey_id) REFERENCES journeys(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ❌
- Journey-specific team organization
- Estimated Records: 3

---

### 11. Team Members

Team membership with leadership roles.

₩₩₩sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL,
    user_id UUID NOT NULL,
    is_leader BOOLEAN DEFAULT false,
    joined_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (user_id) REFERENCES profiles(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ❌
- Leadership designation support
- Membership tracking
- Estimated Records: 9

---

### 12. Posts (MAJOR UPDATE)

Student submissions with enhanced structured answer system.

₩₩₩sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_instance_id UUID,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    team_id UUID,
    title TEXT NOT NULL,
    content TEXT,  -- Legacy field maintained for compatibility
    file_url TEXT, -- Legacy field maintained for compatibility
    attachment_file_id INTEGER,  -- NEW: FK to files table
    
    -- NEW: Enhanced answer system
    answers_data JSONB,  -- Structured answer data
    auto_score INTEGER DEFAULT 0,  -- Automatic grading score
    manual_score INTEGER DEFAULT 0,  -- Manual grading score
    total_questions INTEGER DEFAULT 1,  -- Total number of questions
    answered_questions INTEGER DEFAULT 1,  -- Number of answered questions
    completion_rate DECIMAL(5,2) DEFAULT 100.00,  -- Completion percentage
    
    -- Existing fields
    score INTEGER,  -- Legacy field (auto_score + manual_score)
    view_count INTEGER NOT NULL DEFAULT 0,
    is_hidden BOOLEAN NOT NULL DEFAULT false,
    is_team_submission BOOLEAN DEFAULT false,
    achievement_status TEXT DEFAULT 'pending' CHECK (achievement_status = ANY (ARRAY['pending', 'achieved', 'not_achieved'])),
    team_points INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    journey_id UUID,
    
    FOREIGN KEY (mission_instance_id) REFERENCES journey_mission_instances(id),
    FOREIGN KEY (user_id) REFERENCES profiles(id),
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (journey_id) REFERENCES journeys(id),
    FOREIGN KEY (attachment_file_id) REFERENCES files(id)  -- NEW
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- **MAJOR UPDATE**: Structured JSON-based answer system
- **NEW**: Support for multiple questions per mission
- **NEW**: Automatic and manual scoring separation
- **NEW**: Completion rate tracking
- **NEW**: Centralized file management for attachments
- Supports both individual and team submissions
- Achievement status tracking
- View count analytics
- Content moderation (is_hidden)
- Estimated Records: 576

**answers_data JSON Structure:**
₩₩₩json
{
  "answers": [
    {
      "question_id": "uuid",
      "question_order": 1,
      "answer_type": "essay|multiple_choice|image_upload",
      "answer_text": "주관식 답변 내용",
      "selected_option": "객관식 선택 답변",
      "image_urls": ["url1", "url2"],
      "is_correct": true/false/null,
      "points_earned": 5
    }
  ],
  "submission_metadata": {
    "total_questions": 3,
    "answered_questions": 3,
    "submission_time": "2025-01-01T10:00:00Z",
    "last_modified": "2025-01-01T11:00:00Z"
  }
}
₩₩₩

**Achievement Status Values:**
- `pending`: Awaiting review
- `achieved`: Successfully completed
- `not_achieved`: Did not meet requirements

---

### 13. Comments

Comments on posts for discussion and feedback.

₩₩₩sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES profiles(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Threaded discussion support
- Estimated Records: 114

---

### 14. Likes

Like/reaction system for posts.

₩₩₩sql
CREATE TABLE likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES profiles(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Simple like/unlike functionality
- Estimated Records: 79

---

### 15. Notifications

User notification system with rich content support.

₩₩₩sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receiver_id UUID NOT NULL,
    type TEXT NOT NULL,
    message VARCHAR NOT NULL,
    link TEXT,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    notification_json TEXT,
    
    FOREIGN KEY (receiver_id) REFERENCES profiles(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Rich notification content via JSON
- Read status tracking
- Deep linking support
- Estimated Records: 37

---

### 16. User Points

Individual user points tracking for missions and posts.

₩₩₩sql
CREATE TABLE user_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL,
    mission_instance_id UUID NOT NULL,
    post_id UUID,
    total_points INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (mission_instance_id) REFERENCES journey_mission_instances(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ❌
- Links points to specific missions and posts
- Supports cumulative scoring
- Estimated Records: 528

---

### 17. Team Points

Team-based points for collaborative missions.

₩₩₩sql
CREATE TABLE team_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL,
    mission_instance_id UUID NOT NULL,
    post_id UUID,
    total_points INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (mission_instance_id) REFERENCES journey_mission_instances(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ❌
- Team-based scoring system
- Links to specific missions and posts
- Estimated Records: 1

---

### 18. Files (NEW)

Centralized file management system for all uploaded content.

₩₩₩sql
CREATE TYPE file_type AS ENUM (
    'image',        -- 이미지 파일 (jpg, png, gif, etc.)
    'file'          -- 일반 파일 (pdf, doc, zip, etc.)
);

CREATE TABLE files (
    id SERIAL PRIMARY KEY,                    -- Simple integer ID
    
    -- File basic information
    original_name TEXT NOT NULL,             -- Original filename
    url TEXT NOT NULL,                       -- Supabase Storage URL
    file_type file_type NOT NULL,            -- File type (image/file)
    
    -- File metadata
    file_size BIGINT,                        -- File size in bytes
    mime_type TEXT,                          -- MIME type
    
    -- Upload information
    uploaded_by UUID,                        -- User who uploaded
    uploaded_at TIMESTAMPTZ DEFAULT now(),   -- Upload timestamp
    
    -- Status management
    is_active BOOLEAN DEFAULT true,          -- Active status for soft delete
    
    -- Foreign keys
    FOREIGN KEY (uploaded_by) REFERENCES profiles(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- **NEW**: Centralized file storage and management
- **NEW**: Simple integer-based ID system for FK references
- **NEW**: File metadata tracking (size, type, upload date)
- **NEW**: Soft delete functionality
- Estimated Records: 98

---

### 19. Bug Reports

User-submitted bug reports with status tracking.

₩₩₩sql
CREATE TABLE bug_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL DEFAULT auth.uid(),
    title TEXT NOT NULL,
    description TEXT,
    file_url TEXT,  -- Legacy field maintained
    attachment_file_id INTEGER,  -- NEW: FK to files table
    status TEXT DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (user_id) REFERENCES profiles(id),
    FOREIGN KEY (attachment_file_id) REFERENCES files(id)  -- NEW
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- File attachment support for screenshots
- **NEW**: Centralized file management
- Status tracking for resolution
- Estimated Records: 6

---

### 20. Email Queue

Email notification queue for background processing.

₩₩₩sql
CREATE TABLE email_queue (
    id SERIAL PRIMARY KEY,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    content_ref_id UUID,
    created_at TIMESTAMPTZ DEFAULT now(),
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMPTZ,
    status_code INTEGER,
    response TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Background email processing
- Retry mechanism with error tracking
- Status and response logging
- Estimated Records: 20

---

### 21. Subscriptions

Push notification subscription management.

₩₩₩sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    notification_json TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    FOREIGN KEY (user_id) REFERENCES profiles(id)
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Push notification subscription data
- JSON-based subscription configuration
- Estimated Records: 4

---

### 22. Blog

Blog content management system.

₩₩₩sql
CREATE TABLE blog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    subtitle TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    image_url TEXT DEFAULT 'https://picsum.photos/980/540',  -- Legacy field
    image_file_id INTEGER,  -- NEW: FK to files table
    
    FOREIGN KEY (image_file_id) REFERENCES files(id)  -- NEW
);
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Rich content blog system
- **NEW**: Centralized file management for blog images
- Default placeholder images
- Estimated Records: 4

---

### 23. Inquiry

Business inquiry form data for academy automation consultation.

₩₩₩sql
CREATE TABLE inquiry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL COMMENT '신청자 이름',
    phone TEXT NOT NULL COMMENT '신청자 전화번호',
    automation_needs TEXT NOT NULL COMMENT '자동화하고 싶은 내용',
    current_tools TEXT COMMENT '현재 사용 중인 업무 툴',
    tool_issues TEXT COMMENT '사용 중인 툴의 문제점',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now() COMMENT '문의 생성 시각',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now() COMMENT '문의 수정 시각',
    status TEXT DEFAULT 'pending' CHECK (status = ANY (ARRAY['pending', 'processing', 'completed', 'cancelled'])) COMMENT '상담 처리 상태',
    notes TEXT COMMENT '관리자 메모'
) COMMENT '학원 자동화 상담 신청 정보';
₩₩₩

**Key Features:**
- RLS Enabled: ✅
- Business inquiry management
- Status workflow tracking
- Admin notes support
- Estimated Records: 4

**Status Values:**
- `pending`: New inquiry awaiting processing
- `processing`: Currently being handled
- `completed`: Successfully completed
- `cancelled`: Cancelled inquiry

---

## Database Relationships

### Primary Relationships

1. **Organizations → Profiles**: One-to-many (multi-tenant structure)
2. **Journeys → Journey Weeks**: One-to-many (weekly organization)
3. **Journey Weeks → Journey Mission Instances**: One-to-many (mission scheduling)
4. **Missions → Journey Mission Instances**: One-to-many (mission templates)
5. **Missions → Mission Questions**: One-to-many (structured questions) **NEW**
6. **Users → User Journeys**: Many-to-many via junction table
7. **Journeys → Teams**: One-to-many (team organization)
8. **Teams → Team Members**: One-to-many (team membership)
9. **Posts → Comments**: One-to-many (discussion threads)
10. **Posts → Likes**: One-to-many (engagement tracking)

### File Management Relationships (NEW)

- **Files → Profiles**: One-to-many (profile images)
- **Files → Journeys**: One-to-many (journey images)
- **Files → Blog**: One-to-many (blog images)
- **Files → Posts**: One-to-many (post attachments)
- **Files → Bug Reports**: One-to-many (bug report attachments)

### Points System Relationships

- **User Points**: Links profiles to mission instances and posts
- **Team Points**: Links teams to mission instances and posts

### Notification Relationships

- **Notifications**: Direct user targeting
- **Subscriptions**: Push notification management
- **Email Queue**: Background email processing

---

## Row Level Security (RLS)

The following tables have RLS enabled for security:

✅ **RLS Enabled:**
- organizations
- profiles
- role_access_code
- journeys
- journey_weeks
- missions
- mission_questions **NEW**
- journey_mission_instances
- posts
- comments
- likes
- notifications
- files **NEW**
- bug_reports
- email_queue
- subscriptions
- blog
- inquiry

❌ **RLS Disabled:**
- user_journeys
- teams
- team_members
- user_points
- team_points

---

## Key Features

### 1. Multi-Tenancy
- Organization-based data isolation
- Default organization fallback

### 2. Role-Based Access Control
- Three-tier role hierarchy (user → teacher → admin)
- Access code system for role elevation
- JWT token-based authentication

### 3. Enhanced Learning Path Management (UPDATED)
- Journey-based course structure
- Weekly organization of content
- **NEW**: Advanced mission system with multiple question types
- **NEW**: Structured answer system with JSON storage
- **NEW**: Automatic grading for objective questions

### 4. Flexible Mission System (MAJOR UPDATE)
- **NEW**: Support for essay, multiple choice, image upload, and mixed questions
- **NEW**: Multiple questions per mission
- **NEW**: Structured question templates with metadata
- **NEW**: Automatic scoring for objective questions
- Reusable mission templates
- Instance-based scheduling
- Status tracking throughout lifecycle

### 5. Team Collaboration
- Journey-specific teams
- Leadership roles
- Team-based submissions and scoring

### 6. Engagement Features
- Comments and likes on posts
- View count tracking
- Achievement status system

### 7. Points & Gamification (UPDATED)
- Individual and team points
- **NEW**: Separate automatic and manual scoring
- **NEW**: Question-level point distribution
- Mission-based scoring
- Post-based rewards

### 8. Centralized File Management (NEW)
- **NEW**: Unified file storage system
- **NEW**: File metadata tracking (size, type, upload date)
- **NEW**: Soft delete functionality
- **NEW**: Integration across all content types
- **NEW**: Legacy URL field compatibility

### 9. Communication System
- Rich notifications with JSON payloads
- Push notification subscriptions
- Email queue for background processing

### 10. Content Management (UPDATED)
- **NEW**: Centralized file management system
- **NEW**: Enhanced post submission with structured answers
- Blog system for announcements
- Content moderation capabilities

### 11. Business Features
- Bug reporting system with file attachments
- Inquiry management for business leads
- Analytics tracking via view counts

---

## Development Guidelines

### Authentication Flow
1. Users sign up with email/password or social login
2. Profile completion required for social users
3. Role assignment via access codes
4. Organization selection during signup
5. JWT token management for session handling

### Data Access Patterns
- Use organization_id for multi-tenant filtering
- Implement role checks for sensitive operations
- Leverage RLS policies for row-level security
- Use journey_id for course-specific data isolation

### Enhanced Mission System (UPDATED)
- **NEW**: Create structured questions using `mission_questions` table
- **NEW**: Support multiple question types per mission
- **NEW**: Use JSON structure in `posts.answers_data` for submissions
- **NEW**: Implement automatic grading for objective questions
- **NEW**: Track completion rates and progress

### File Management System (NEW)
- **NEW**: Use `upload_file()` function for new file uploads
- **NEW**: Reference files using `file_id` fields
- **NEW**: Maintain backward compatibility with legacy URL fields
- **NEW**: Implement soft delete using `is_active` flag

### Points System (UPDATED)
- User points track individual progress
- Team points support collaborative scoring
- **NEW**: Separate automatic scoring (objective questions) and manual scoring
- **NEW**: Question-level point distribution
- Both link to specific mission instances and posts
- Consider aggregation for leaderboards

### Mission Lifecycle (UPDATED)
1. **Template Creation**: Create reusable mission in `missions` table
2. **Question Setup**: Create structured questions in `mission_questions` table **NEW**
3. **Scheduling**: Create instance in `journey_mission_instances`
4. **Release**: Set `release_date` for availability
5. **Submission**: Users create posts with structured `answers_data` JSON **NEW**
6. **Auto-Grading**: System automatically scores objective questions **NEW**
7. **Manual Evaluation**: Teachers review and score subjective answers **NEW**
8. **Completion**: Update mission status to completed

---

## Migration History

### Version 2.0 - Enhanced Mission & File System (2025-01-26)

#### Posts Table Migration
- **Purpose**: Enable support for multiple question types and structured answers
- **Changes**: 
  - Added `answers_data` JSONB field for structured submissions
  - Added `auto_score`, `manual_score` separation
  - Added completion tracking fields
  - Migrated 575 existing posts to new structure
- **Backward Compatibility**: Original `content` field maintained

#### File Management System
- **Purpose**: Centralize file storage and management
- **Changes**:
  - Created `files` table with integer ID system
  - Added file reference fields to all relevant tables
  - Migrated 98 existing files (79 profile images, 16 journey images, 3 bug report files)
- **Backward Compatibility**: Original URL fields maintained

#### Mission Question System
- **Purpose**: Support diverse assignment types and automatic grading
- **Changes**:
  - Created `mission_questions` table
  - Enhanced `mission_type` from TEXT to ENUM
  - Generated 71 default questions for existing missions
- **Features**: Essay, multiple choice, image upload, and mixed question types

---

This schema supports a comprehensive learning management system with enterprise features, team collaboration, gamification, enhanced file management, and robust access control. The multi-tenant architecture allows for organization-based data isolation while maintaining a shared system for efficiency.