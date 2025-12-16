erDiagram
    roles {
        bigint id PK
        text role_name "UNIQUE"
    }

    schools {
        bigint id PK
        text school_name "UNIQUE"
        char_3 school_number "UNIQUE; nullable; assigned via function"
    }

    majors {
        bigint id PK
        text major_name "UNIQUE"
        char_4 major_number "UNIQUE; nullable; assigned via function"
    }

    auth_users {
        uuid id PK "auth.users (Supabase-managed)"
        text email
        jsonb raw_user_meta_data
        timestamptz created_at
    }

    user_profiles {
        uuid id PK "FK -> auth.users(id)"
        text full_name
        text email "UNIQUE"
        bigint role_id FK "nullable; ON DELETE SET NULL"
        timestamptz created_at
        timestamptz updated_at
    }

    teachers {
        bigint id PK
        uuid user_id FK "UNIQUE"
        bigint school_id FK "nullable; ON DELETE SET NULL"
        timestamptz created_at
        timestamptz updated_at
    }

    classes {
        bigint id PK
        text class_name
        int grade_level "CHECK (1,2,3)"
    }

    students {
        bigint id PK
        text student_id "UNIQUE; generated student identifier"
        uuid user_id FK "UNIQUE"
        bigint school_id FK "NOT NULL"
        bigint major_id FK "NOT NULL"
        bigint current_class_id FK "NOT NULL"
        text stored_password "nullable; hashed for display"
        timestamptz created_at
        timestamptz updated_at
    }

    student_number_tracking {
        bigint id PK
        bigint school_id FK
        bigint major_id FK
        int last_student_number
        timestamptz created_at
        timestamptz updated_at
    }

    sessions {
        bigint id PK
        bigint student_id FK
        text status
        timestamptz completed_at
        numeric total_score "NUMERIC(3,1); 0..10"
        timestamptz created_at
    }

    documents {
        bigint id PK
        bigint session_id FK
        text cleaned_text
    }

    summaries {
        bigint id PK
        bigint session_id FK "UNIQUE"
        text strength_text
        text areas_for_growth_text
    }

    detailed_feedbacks {
        bigint id PK
        bigint session_id FK
        int question_order
        text question_text
        text answer_text
        text evaluation_text
        boolean is_correct "DEFAULT FALSE"
        numeric content_relevance_score "NUMERIC(3,1); 0..10"
        numeric structure_score "NUMERIC(3,1); 0..10"
        numeric fluency_score "NUMERIC(3,1); 0..10"
        numeric confidence_score "NUMERIC(3,1); 0..10"
        numeric overall_score "NUMERIC(3,1); 0..10"
    }

    next_steps {
        bigint id PK
        bigint session_id FK
        int next_step_order
        text title "NOT NULL"
        text description_text
    }

    LANGCHAIN_PG_COLLECTION {
        uuid uuid PK
        varchar name
        json cmetadata
    }
    
    LANGCHAIN_PG_EMBEDDING {
        varchar id PK
        uuid collection_id FK
        vector embedding
        varchar document
        jsonb cmetadata
    }
    
    auth_users ||--|| user_profiles : "synced via trigger"
    roles ||--o{ user_profiles : "assigned to"
    user_profiles ||--o| teachers : "may be"
    user_profiles ||--o| students : "may be"
    schools ||--o{ teachers : "employs"
    schools ||--o{ students : "has"
    majors ||--o{ students : "has"
    classes ||--o{ students : "contains"
    schools ||--o{ student_number_tracking : "tracks"
    majors ||--o{ student_number_tracking : "tracks"
    students ||--o{ sessions : "takes"
    sessions ||--o{ documents : "contains"
    sessions ||--|| summaries : "has"
    sessions ||--o{ detailed_feedbacks : "has"
    sessions ||--o{ next_steps : "has"
