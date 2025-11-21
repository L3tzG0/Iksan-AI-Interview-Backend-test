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

    USERS {
        int id PK
        string full_name
        string email
        string password_hash
        int role_id
        timestamp created_at
        timestamp updated_at
    }

    TEACHERS {
        int user_id PK
    }

    CLASSES {
        int id PK
        string class_name
        string grade_level
        int homeroom_teacher_id
    }

    STUDENTS {
        int id PK
        int user_id
        int school_id
        int major_id
        int current_class_id
    }

    SESSIONS {
        int id PK
        int student_id
        string status
        timestamp completed_at
        numeric total_score
        timestamp created_at
    }

    DOCUMENTS {
        int id PK
        int session_id
        text raw_text
        string document_path
        timestamp processed_at
    }

    SCORES {
        int id PK
        int session_id
        numeric content_relevance_score
        numeric structure_score
        numeric fluency_score
        numeric confidence_score
        numeric overall_score
    }

    SUMMARIES {
        int id PK
        int session_id
        text strength_text
        text areas_for_growth_text
    }

    DETAILED_FEEDBACKS {
        int id PK
        int session_id
        int question_order
        text question_text
        text answer_text
        text evaluation_text
        boolean is_correct
        numeric score
        text transcript
        string audio_path
    }

    NEXT_STEPS {
        int id PK
        int session_id
        string title
        text description_text
    }

    ROLES ||--o{ USERS : "assigned to"
    USERS ||--|| TEACHERS : "may be"
    USERS ||--|| STUDENTS : "may be"
    SCHOOLS ||--o{ STUDENTS : "has"
    MAJORS ||--o{ STUDENTS : "has"
    CLASSES ||--o{ STUDENTS : "contains"
    TEACHERS ||--o{ CLASSES : "homeroom for"
    STUDENTS ||--o{ SESSIONS : "takes"
    SESSIONS ||--o{ DOCUMENTS : "contains"
    SESSIONS ||--|| SCORES : "has"
    SESSIONS ||--|| SUMMARIES : "has"
    SESSIONS ||--o{ DETAILED_FEEDBACKS : "has"
    SESSIONS ||--o{ NEXT_STEPS : "has"
