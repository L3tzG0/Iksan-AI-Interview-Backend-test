erDiagram
    ROLES {
        int id PK
        string role_name
    }

    SCHOOLS {
        int id PK
        string school_name
    }

    MAJORS {
        int id PK
        string major_name
    }

    AUTH_USERS {
        uuid id PK "Managed by Supabase Auth"
        string email
        string encrypted_password "Managed by Supabase Auth"
        jsonb raw_user_meta_data
        timestamp created_at
    }

    USER_PROFILES {
        uuid id PK
        string email
        string full_name
        int role_id FK
        timestamp created_at
        timestamp updated_at
    }

    TEACHERS {
        int id PK
        uuid user_id FK
        int school_id FK
        timestamp created_at
        timestamp updated_at
    }

    CLASSES {
        int id PK
        string class_name
        string grade_level
        int homeroom_teacher_id FK
    }

    STUDENTS {
        int id PK
        uuid user_id FK
        int school_id FK
        int major_id FK
        int current_class_id FK
        timestamp created_at
        timestamp updated_at
    }

    SESSIONS {
        int id PK
        int student_id FK
        string status
        timestamp completed_at
        numeric total_score
        timestamp created_at
    }

    DOCUMENTS {
        int id PK
        int session_id FK
        text cleaned_text
    }

    SUMMARIES {
        int id PK
        int session_id FK
        text strength_text
        text areas_for_growth_text
    }

    DETAILED_FEEDBACKS {
        int id PK
        int session_id FK
        int question_order
        text question_text
        text answer_text
        text evaluation_text
        boolean is_correct
        numeric content_relevance_score
        numeric structure_score
        numeric fluency_score
        numeric confidence_score
        numeric overall_score
    }

    NEXT_STEPS {
        int id PK
        int session_id FK
        int next_step_order
        string title
        text description_text
    }

    AUTH_USERS ||--|| USER_PROFILES : "synced via trigger"
    ROLES ||--o{ USER_PROFILES : "assigned to"
    USER_PROFILES ||--o| TEACHERS : "may be"
    USER_PROFILES ||--o| STUDENTS : "may be"
    SCHOOLS ||--o{ TEACHERS : "employs"
    SCHOOLS ||--o{ STUDENTS : "has"
    MAJORS ||--o{ STUDENTS : "has"
    CLASSES ||--o{ STUDENTS : "contains"
    TEACHERS ||--o{ CLASSES : "homeroom for"
    STUDENTS ||--o{ SESSIONS : "takes"
    SESSIONS ||--o{ DOCUMENTS : "contains"
    SESSIONS ||--|| SUMMARIES : "has"
    SESSIONS ||--o{ DETAILED_FEEDBACKS : "has"
    SESSIONS ||--o{ NEXT_STEPS : "has"
