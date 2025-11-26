    -- ============================================================================
-- SEED DUMMY DATA
-- Note: This script assumes you have already created users via Supabase Auth
-- Users must be registered through the authentication system first, then
-- their UUIDs can be used here to create related records.
-- ============================================================================

-- IMPORTANT: Replace these UUIDs with actual user IDs from your auth.users table
-- You can get them by querying: SELECT id, email FROM auth.users;
-- Or register users through the /api/v1/auth/register endpoint first

-- 1. Insert Roles
INSERT INTO roles (id, role_name) VALUES 
(1, 'admin'),
(2, 'teacher'),
(3, 'student')
ON CONFLICT (role_name) DO NOTHING;

-- 2. Insert Schools
INSERT INTO schools (id, school_name) VALUES 
(1, '이리공업고등학교'),
(2, '전북기계공업고등학교')
ON CONFLICT (school_name) DO NOTHING;

-- 3. Insert Majors
INSERT INTO majors (id, major_name) VALUES 
(1, '전기전자과'),
(2, '전기제어'),
(3, '자동화기계'),
(4, '스마트팩토리'),
(5, '조리제빵'),
(6, '기계설계'),
(7, '소프트웨어과')
ON CONFLICT (major_name) DO NOTHING;

-- ============================================================================
-- MANUAL STEP REQUIRED: Register Users via Auth API First!
-- ============================================================================
-- Before running the rest of this script, register users through the API:
--
-- Example registration requests:
-- 
-- POST /api/v1/auth/register
-- {
--   "email": "teacher@elice.io",
--   "password": "SecurePass123!",
--   "full_name": "김교사",
--   "role_id": 2
-- }
--
-- POST /api/v1/auth/register
-- {
--   "email": "student@elice.io",
--   "password": "SecurePass123!",
--   "full_name": "이학생",
--   "role_id": 3
-- }
--
-- ... (register all 7 users similarly)
--
-- After registration, get the UUIDs:
-- SELECT id, email, full_name FROM public.user_profiles ORDER BY email;
--
-- Then update the variables below with the actual UUIDs
-- ============================================================================

-- STEP 1: Declare variables for user UUIDs (Update these with actual values!)
DO $$
DECLARE
    teacher_uuid UUID := '00000000-0000-0000-0000-000000000001'::UUID;  -- Replace with actual UUID for teacher@elice.io
    student1_uuid UUID := '00000000-0000-0000-0000-000000000002'::UUID; -- Replace with actual UUID for student@elice.io
    student2_uuid UUID := '00000000-0000-0000-0000-000000000003'::UUID; -- Replace with actual UUID for minho@example.com
    student3_uuid UUID := '00000000-0000-0000-0000-000000000004'::UUID; -- Replace with actual UUID for jiyoon@example.com
    student4_uuid UUID := '00000000-0000-0000-0000-000000000005'::UUID; -- Replace with actual UUID for seojun@example.com
    student5_uuid UUID := '00000000-0000-0000-0000-000000000006'::UUID; -- Replace with actual UUID for hyewon@example.com
    student6_uuid UUID := '00000000-0000-0000-0000-000000000007'::UUID; -- Replace with actual UUID for woosung@example.com
BEGIN
    
    -- 4. Insert Teachers
    INSERT INTO teachers (id, user_id) VALUES (1, teacher_uuid)
    ON CONFLICT (user_id) DO NOTHING;

    -- 5. Insert Classes
    INSERT INTO classes (id, class_name, grade_level, homeroom_teacher_id) VALUES 
    (1, '3학년 1반', '3', 1),
    (2, '2학년 1반', '2', NULL),
    (3, '3학년 2반', '3', NULL)
    ON CONFLICT (id) DO NOTHING;

    -- 6. Insert Students
    INSERT INTO students (id, user_id, school_id, major_id, current_class_id) VALUES 
    (1, student1_uuid, 1, 2, 1),
    (2, student2_uuid, 1, 3, 1),
    (3, student3_uuid, 1, 2, 1),
    (4, student4_uuid, 1, 4, 1),
    (5, student5_uuid, 1, 5, 2),
    (6, student6_uuid, 2, 6, 3)
    ON CONFLICT (user_id) DO NOTHING;

    -- 7. Insert Sessions (Interview History)
    -- Session 1: Kim Minho (Latest - Detailed) - 2024-03-15
    INSERT INTO sessions (id, student_id, status, completed_at, total_score, created_at) VALUES 
    (1, 2, 'completed', '2024-03-15 14:00:00', 4.2, '2024-03-15 13:30:00')
    ON CONFLICT (id) DO NOTHING;

    -- Session 2: Kim Minho (History) - 2024-03-10
    INSERT INTO sessions (id, student_id, status, completed_at, total_score, created_at) VALUES 
    (2, 2, 'completed', '2024-03-10 10:00:00', 6.5, '2024-03-10 09:30:00')
    ON CONFLICT (id) DO NOTHING;

    -- Session 3: Park Jiyoon - 2024-03-14
    INSERT INTO sessions (id, student_id, status, completed_at, total_score, created_at) VALUES 
    (3, 3, 'completed', '2024-03-14 11:00:00', 8.5, '2024-03-14 10:30:00')
    ON CONFLICT (id) DO NOTHING;

    -- Session 4: Choi Hyewon - 2024-03-12
    INSERT INTO sessions (id, student_id, status, completed_at, total_score, created_at) VALUES 
    (4, 5, 'completed', '2024-03-12 15:00:00', 9.2, '2024-03-12 14:30:00')
    ON CONFLICT (id) DO NOTHING;

    -- Session 5: Jung Woosung - 2024-03-11
    INSERT INTO sessions (id, student_id, status, completed_at, total_score, created_at) VALUES 
    (5, 6, 'completed', '2024-03-11 16:00:00', 8.0, '2024-03-11 15:30:00')
    ON CONFLICT (id) DO NOTHING;

    -- 8. Insert Summaries
    INSERT INTO summaries (id, session_id, strength_text, areas_for_growth_text) VALUES 
    (1, 1, '9번 문항에 대한 답변에서 보여주셨듯이, 자신의 장기적인 비전과 목표를 매우 체계적이고 논리적으로 설명하는 뛰어난 역량을 갖추고 계십니다. ''π자형 인재''라는 구체적인 목표와 함께 AI, DevOps, 커뮤니케이션 능력 등 다방면의 노력을 구체적인 기술 스택과 경험을 바탕으로 제시한 점이 매우 인상적입니다.', '전반적으로 면접에 대한 준비가 더 필요해 보입니다. 대부분의 질문에 ''모르겠습니다'', ''대박''과 같은 단답형 또는 무응답으로 일관하여 지원자의 경험과 역량을 전혀 파악하기 어려웠습니다. 특히 이력서 기반의 구체적인 경험을 묻는 질문에 답변하지 못하는 것은 치명적일 수 있습니다.'),
    (2, 2, '김민호 학생은 직무에 대한 이해도가 높고 경험을 구체적으로 설명할 수 있습니다. 특히 프로젝트 성과를 수치로 제시한 점이 인상적입니다.', '답변의 구조가 다소 느슨할 때가 있습니다. STAR 기법을 더 엄격하게 적용하여 서론-본론-결론을 명확히 하면 좋겠습니다.'),
    (3, 3, '박지윤 학생은 직무에 대한 이해도가 높고 경험을 구체적으로 설명할 수 있습니다.', '답변의 구조가 다소 느슨할 때가 있습니다.'),
    (4, 4, '최혜원 학생은 직무에 대한 이해도가 높고 경험을 구체적으로 설명할 수 있습니다.', '답변의 구조가 다소 느슨할 때가 있습니다.'),
    (5, 5, '정우성 학생은 직무에 대한 이해도가 높고 경험을 구체적으로 설명할 수 있습니다.', '답변의 구조가 다소 느슨할 때가 있습니다.')
    ON CONFLICT (session_id) DO NOTHING;

    -- 9. Insert Detailed Feedbacks (with new score columns)
    -- Session 1: Kim Minho's detailed feedback
    INSERT INTO detailed_feedbacks (session_id, question_order, question_text, answer_text, evaluation_text, is_correct, content_relevance_score, structure_score, fluency_score, confidence_score, overall_score) VALUES 
    (1, 1, 'MindVerse 웹사이트 프로젝트에서 MongoDB 스키마를 Mongoose를 사용하여 3개 설계하고 구현하셨는데, 이 과정에서 데이터 무결성과 효율성을 어떻게 확보하셨는지 구체적인 예를 들어 설명해 주십시오.', '대박', '질문의 의도에 전혀 부합하지 않는 답변입니다. 데이터 무결성과 효율성은 백엔드 개발자로서 매우 중요한 역량입니다.', false, 1.0, 1.0, 1.0, 1.0, 1.0),
    (1, 2, 'Academic Service Chatbot 프로젝트에서 LSTM 모델을 활용한 챗봇의 인도네시아어 질문 견고성을 높이기 위해 데이터 증강 기법을 적용하셨습니다. 성과와 어려움은 무엇이었습니까?', '대박', '질문의 핵심인 ''성능 변화''와 ''어려움''에 대해 전혀 답변하지 못했습니다.', false, 1.0, 1.0, 1.0, 1.0, 1.0),
    (1, 3, 'Selena - Seller Financial Tracking App 프로젝트에서 Autoencoder를 사용하여 불규칙한 지출을 자동으로 감지하는 이상 감지 모델을 개발하셨습니다. 설계 과정과 정확도는 어떠했습니까?', '정말 감사합니다', '질문에 대한 답변이 이루어지지 않았습니다. 사용한 데이터셋의 특징과 모델의 성능 지표를 구체적으로 언급해야 합니다.', false, 1.0, 1.0, 1.0, 1.0, 1.0),
    (1, 4, '개발자로서 장기적인 비전이나 목표가 있다면 무엇이며, 그 목표를 달성하기 위해 현재 어떤 노력을 하고 있습니까?', '1. 장기적인 비전 (Long-Term Vision) 저의 최종 목표는 **T자형 인재**를 넘어, **π자형 인재**와 같이...', '매우 훌륭한 답변입니다. 질문의 의도를 정확히 파악하고, 자신의 장기적인 비전과 이를 달성하기 위한 현재의 구체적인 노력을 논리적으로 잘 설명했습니다.', true, 9.5, 9.0, 9.5, 9.0, 9.5)
    ON CONFLICT DO NOTHING;

    -- Session 2: Generic feedbacks for Kim Minho (history)
    INSERT INTO detailed_feedbacks (session_id, question_order, question_text, answer_text, evaluation_text, is_correct, content_relevance_score, structure_score, fluency_score, confidence_score, overall_score) VALUES 
    (2, 1, '본인의 강점은 무엇인가요?', '저는 꼼꼼함이 강점입니다. 실수를 잘 안 합니다.', '강점을 언급했지만 구체적인 사례가 부족합니다.', true, 7.0, 6.0, 7.0, 6.5, 6.5),
    (2, 2, '어려움을 극복한 경험을 말해주세요.', '프로젝트 마감기한이 짧아서 힘들었지만, 밤새서 열심히 해서 끝냈습니다.', '열정은 좋지만, 구체적인 방법론(Action)이 필요합니다.', true, 6.0, 5.5, 7.0, 6.0, 6.0)
    ON CONFLICT DO NOTHING;

    -- Session 3: Park Jiyoon feedbacks
    INSERT INTO detailed_feedbacks (session_id, question_order, question_text, answer_text, evaluation_text, is_correct, content_relevance_score, structure_score, fluency_score, confidence_score, overall_score) VALUES 
    (3, 1, '자기소개를 해주세요.', '안녕하세요, 전기제어과 3학년 박지윤입니다. 저는 PLC 프로그래밍에 관심이 많고, 관련 자격증도 취득했습니다.', '자기소개가 간결하고 핵심을 잘 전달했습니다.', true, 8.5, 8.0, 9.0, 8.5, 8.5),
    (3, 2, '왜 이 분야를 선택했나요?', '아버지가 전기 기술자이셔서 어릴 때부터 관심이 있었고, 실습 수업에서 회로를 직접 만들어보면서 더 확신이 생겼습니다.', '개인적 동기와 경험을 잘 연결했습니다.', true, 8.5, 8.5, 8.5, 8.5, 8.5)
    ON CONFLICT DO NOTHING;

    -- Session 4: Choi Hyewon feedbacks
    INSERT INTO detailed_feedbacks (session_id, question_order, question_text, answer_text, evaluation_text, is_correct, content_relevance_score, structure_score, fluency_score, confidence_score, overall_score) VALUES 
    (4, 1, '조리제빵과를 선택한 이유는?', '요리는 사람들에게 행복을 주는 일이라고 생각합니다. 특히 디저트를 만들 때 창의성을 발휘할 수 있어서 좋습니다.', '명확한 동기와 열정이 느껴지는 좋은 답변입니다.', true, 9.0, 9.0, 9.5, 9.0, 9.2),
    (4, 2, '가장 자신 있는 요리는?', '마카롱입니다. 온도와 습도에 민감해서 실패도 많이 했지만, 반복 연습으로 성공률을 90% 이상으로 높였습니다.', '구체적인 수치와 노력 과정을 잘 설명했습니다.', true, 9.5, 9.0, 9.0, 9.5, 9.2)
    ON CONFLICT DO NOTHING;

    -- Session 5: Jung Woosung feedbacks
    INSERT INTO detailed_feedbacks (session_id, question_order, question_text, answer_text, evaluation_text, is_correct, content_relevance_score, structure_score, fluency_score, confidence_score, overall_score) VALUES 
    (5, 1, '기계설계에서 가장 중요한 것은?', '정확성이라고 생각합니다. 0.1mm의 오차도 전체 제품에 영향을 줄 수 있기 때문입니다.', '핵심을 잘 짚었고 이유도 명확합니다.', true, 8.0, 8.0, 8.0, 8.0, 8.0),
    (5, 2, 'CAD 프로그램 사용 경험은?', 'AutoCAD와 SolidWorks를 사용해봤습니다. 특히 SolidWorks로 기어박스 모델링을 한 경험이 있습니다.', '구체적인 프로그램명과 경험을 언급했습니다.', true, 8.0, 8.0, 8.0, 8.0, 8.0)
    ON CONFLICT DO NOTHING;

    -- 10. Insert Next Steps (with next_step_order)
    -- Session 1: Kim Minho Latest
    INSERT INTO next_steps (session_id, next_step_order, title, description_text) VALUES 
    (1, 1, '면접 기본 태도 및 답변 준비', '모든 면접 질문에는 성실하고 진솔한 답변을 해야 합니다.'),
    (1, 2, 'STAR 기법을 활용한 경험 정리', '자신이 수행한 모든 프로젝트 경험을 STAR 기법에 따라 문서로 정리해보세요.'),
    (1, 3, '성과를 구체적인 수치로 표현하기', '자신의 성과를 이야기할 때 구체적인 숫자를 제시하는 연습을 하세요.')
    ON CONFLICT DO NOTHING;

    -- Session 2: Kim Minho History
    INSERT INTO next_steps (session_id, next_step_order, title, description_text) VALUES 
    (2, 1, 'STAR 기법 훈련', '상황-과제-행동-결과 구조로 답변 작성하기 연습'),
    (2, 2, '모의 면접 반복', '다양한 질문에 대해 즉흥적으로 답변하는 연습 필요')
    ON CONFLICT DO NOTHING;

    -- Session 3: Park Jiyoon
    INSERT INTO next_steps (session_id, next_step_order, title, description_text) VALUES 
    (3, 1, '기술 면접 준비', 'PLC 관련 기술 질문에 대비하여 이론과 실습 경험을 정리하세요.'),
    (3, 2, '자격증 활용법', '취득한 자격증이 실무에서 어떻게 활용되는지 구체적으로 설명할 수 있도록 준비하세요.')
    ON CONFLICT DO NOTHING;

    -- Session 4: Choi Hyewon
    INSERT INTO next_steps (session_id, next_step_order, title, description_text) VALUES 
    (4, 1, '포트폴리오 정리', '만든 디저트 사진과 레시피를 체계적으로 정리하세요.'),
    (4, 2, '트렌드 파악', '최신 디저트 트렌드와 기법을 지속적으로 학습하세요.')
    ON CONFLICT DO NOTHING;

    -- Session 5: Jung Woosung
    INSERT INTO next_steps (session_id, next_step_order, title, description_text) VALUES 
    (5, 1, 'CAD 실력 향상', '다양한 부품 모델링 연습을 통해 실력을 더 키우세요.'),
    (5, 2, '제조 공정 이해', '설계한 부품이 실제로 어떻게 제조되는지 공정을 이해하세요.')
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Seed data inserted successfully!';
    RAISE NOTICE 'Note: User UUIDs need to be updated with actual values from auth.users';
    
END $$;

-- ============================================================================
-- ALTERNATIVE APPROACH: Seed with actual registered users
-- ============================================================================
-- If you prefer to query actual UUIDs from user_profiles, use this instead:
--
-- DO $$
-- DECLARE
--     teacher_uuid UUID;
--     student1_uuid UUID;
--     student2_uuid UUID;
--     -- ... declare other UUIDs
-- BEGIN
--     -- Get actual UUIDs from user_profiles
--     SELECT id INTO teacher_uuid FROM user_profiles WHERE email = 'teacher@elice.io';
--     SELECT id INTO student1_uuid FROM user_profiles WHERE email = 'student@elice.io';
--     SELECT id INTO student2_uuid FROM user_profiles WHERE email = 'minho@example.com';
--     -- ... get other UUIDs
--     
--     -- Check if UUIDs were found
--     IF teacher_uuid IS NULL THEN
--         RAISE EXCEPTION 'User teacher@elice.io not found. Please register users first.';
--     END IF;
--     
--     -- Then insert data using the retrieved UUIDs
--     -- ... (same INSERT statements as above)
-- END $$;
-- ============================================================================