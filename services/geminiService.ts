
import { GoogleGenAI, Type } from "@google/genai";
import type { Question, Answer, InterviewReport, StudentSummary, StudentDetail } from '../types';

// IMPORTANT: This key is managed externally and is a hard requirement.
// Do not modify this line.
// Use a fallback empty string to prevent 'undefined' access errors if process.env is partially shimmed.
const API_KEY = process.env.API_KEY || "";

if (!API_KEY) {
    console.warn("API_KEY environment variable not set. API calls will fail.");
}

// Initialize AI client safely. 
const ai = new GoogleGenAI({ apiKey: API_KEY });

const questionGenerationSchema = {
    type: Type.ARRAY,
    items: {
        type: Type.OBJECT,
        properties: {
            id: { type: Type.INTEGER },
            text: { type: Type.STRING },
            type: { type: Type.STRING, enum: ['general', 'resume-based'] },
        },
        required: ['id', 'text', 'type'],
    },
};

const evaluationSchema = {
    type: Type.OBJECT,
    properties: {
        scores: {
            type: Type.OBJECT,
            properties: {
                contentRelevance: { type: Type.NUMBER, description: "Score from 0 to 10 based on meaningfulness" },
                structure: { type: Type.NUMBER, description: "Score from 0 to 10 based on STAR method usage" },
                fluency: { type: Type.NUMBER, description: "Score from 0 to 10 based on flow and grammar" },
                confidence: { type: Type.NUMBER, description: "Score from 0 to 10 based on tone and stability" },
            },
            required: ['contentRelevance', 'structure', 'fluency', 'confidence'],
        },
        summary: {
            type: Type.OBJECT,
            properties: {
                strengths: { type: Type.STRING, description: "A paragraph in Korean summarizing the user's strengths." },
                areasForGrowth: { type: Type.STRING, description: "A paragraph in Korean summarizing areas for improvement." },
            },
            required: ['strengths', 'areasForGrowth'],
        },
        detailedFeedback: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    question: { type: Type.STRING },
                    answer: { type: Type.STRING },
                    evaluation: { type: Type.STRING, description: "Constructive feedback in Korean. Encourage quantifying answers." },
                    isCorrect: { type: Type.BOOLEAN, description: "True if answer is good, false if poor." },
                    score: { type: Type.NUMBER, description: "Score from 1 to 10."}
                },
                required: ['question', 'answer', 'evaluation', 'isCorrect', 'score'],
            },
        },
        nextSteps: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    title: { type: Type.STRING },
                    description: { type: Type.STRING }
                },
                required: ['title', 'description']
            }
        }
    },
    required: ['scores', 'summary', 'detailedFeedback', 'nextSteps'],
};

export const generateQuestions = async (input: string | { data: string; mimeType: string }): Promise<Question[]> => {
    let contents: any;
    
    // Jobda / PDF Context for style
    const interviewContext = `
    참고할 면접 질문 유형 (Jobda 스타일 - 특성화고/직무 중심):
    1. 비전/목표 (Vision/Goals): 입사 후 포부, 5년/10년 후 모습, 직업관, 일의 목적.
    2. 조직적응력 (Organizational Adaptability): 상사와의 갈등 해결, 협력 경험, 야근/지방 근무 가능 여부.
    3. 창의성/돌발 (Spontaneous/Creativity): 붉은 벽돌의 5가지 용도, 서울의 중국집 매출 추산 등 논리적 사고.
    4. 가치관/인성 (Interests/Values): 존경하는 인물, 감명 깊은 영화, 스트레스 해소법.
    5. 직무 적합성 (Job Fit): 지원 동기, 직무 관련 강점, 전공과 직무의 연관성.
    `;

    const basePrompt = `
        당신은 특성화고 학생을 위한 전문 AI 면접 코치입니다.
        제공된 이력서 정보를 심층 분석하여 **전공(Major)**, **구체적인 경험(Experience)**, **지원 동기(Motivation)**를 파악하십시오.
        이를 바탕으로 한국어로 정확히 10개의 맞춤형 면접 질문을 생성하세요.
        
        다음 규칙을 엄격히 따르세요:
        1. **이력서/직무 기반 질문 (resume-based)**: 5개. 
           - 제출된 이력서에서 학생의 전공과 관련된 구체적인 프로젝트나 기술 스택을 언급하며 질문하세요.
           - 학생이 작성한 특정 경험(동아리, 실습, 자격증 등)에 대해 깊이 있는 질문을 하세요.
           - 지원 동기와 입사 후 포부를 묻는 질문을 포함하세요.
           - 질문은 매우 구체적이고 개인화되어야 합니다.
        2. **일반/인성 질문 (general)**: 5개. 위에서 제공한 '비전/목표', '조직적응력', '창의성' 등의 주제를 참고하여 생성하세요.
        3. 모든 질문은 한국어로 작성되어야 합니다.
        4. ID는 1부터 10까지 부여하세요.

        ${interviewContext}
    `;

    if (typeof input === 'string') {
        const prompt = `${basePrompt}\n\nResume Text:\n---\n${input}\n---`;
        contents = prompt;
    } else {
        contents = {
            parts: [
                { text: basePrompt },
                {
                    inlineData: {
                        data: input.data,
                        mimeType: input.mimeType,
                    },
                },
            ],
        };
    }

    const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: contents,
        config: {
            responseMimeType: 'application/json',
            responseSchema: questionGenerationSchema,
            temperature: 0.6,
        },
    });
    
    const jsonText = response.text.trim();
    return JSON.parse(jsonText) as Question[];
};


export const evaluateAnswers = async (questions: Question[], answers: Answer[]): Promise<InterviewReport> => {
    const interviewTranscript = questions.map(q => {
        const answer = answers.find(a => a.questionId === q.id);
        return `질문 ${q.id} (${q.type}): ${q.text}\n답변: ${answer ? answer.text : '(답변 없음)'}`;
    }).join('\n\n');

    const prompt = `
        당신은 AI 면접관입니다. 특성화고 학생의 모의 면접 결과를 평가하세요. 
        평가 언어는 **한국어**입니다.

        다음 4가지 차원에서 점수(0~10)를 매기고 상세 피드백을 제공하세요:

        1. **내용 관련성 (Content Relevance - 40%)**: 
           - 질문의 의도를 정확히 파악하고 의미 있는 답변을 했는가?
           - 핵심 키워드가 포함되었는가?
        
        2. **구조 (Structure - 30%)**:
           - STAR 기법 (상황, 과제, 행동, 결과)을 사용하여 논리적으로 답변했는가?
           - 서론-본론-결론이 명확한가?

        3. **유창성 (Fluency - 20%)**:
           - 문장이 자연스럽게 이어지는가?
           - 불필요한 추임새(음, 어, 그..)가 적은가?
           - 단답형이 아닌 충분한 길이로 답변했는가?

        4. **자신감 (Confidence Proxy - 10%)**:
           - 답변의 내용에서 확신과 열정이 느껴지는가?
           - (텍스트 분석) 망설임이나 자신감 없는 표현이 적은가?

        **중요 피드백 지침**:
        - 학생에게 **수치로 답변(Quantify)**하도록 적극 권장하세요. (예: "많이 팔았다" 대신 "매출을 20% 늘렸다"라고 표현하도록 조언)
        - 구체적인 개선 방안을 제시하세요.
        
        Transcript:
        ---
        ${interviewTranscript}
        ---
    `;

    const response = await ai.models.generateContent({
        model: 'gemini-2.5-pro',
        contents: prompt,
        config: {
            responseMimeType: 'application/json',
            responseSchema: evaluationSchema,
        },
    });

    const result = JSON.parse(response.text.trim()) as InterviewReport;
    
    // Calculate weighted total score
    const { contentRelevance, structure, fluency, confidence } = result.scores;
    const weightedScore = (contentRelevance * 0.4) + (structure * 0.3) + (fluency * 0.2) + (confidence * 0.1);
    result.totalScore = Number(weightedScore.toFixed(1));
    result.date = new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });

    return result;
};


// --- MOCK DATA ---

let mockStudentList: StudentSummary[] = [
    { id: '1', name: '김민호', major: '자동화기계', latestScore: 42, improvement: 15, completed: true, schoolName: '이리공업고등학교', grade: 3 },
    { id: '2', name: '박지윤', major: '전기제어', latestScore: 85, improvement: 10, completed: true, schoolName: '이리공업고등학교', grade: 3 },
    { id: '3', name: '이서준', major: '스마트팩토리', latestScore: 65, improvement: -5, completed: false, schoolName: '이리공업고등학교', grade: 3 },
    { id: '4', name: '최혜원', major: '조리제빵', latestScore: 92, improvement: 20, completed: true, schoolName: '이리공업고등학교', grade: 2 },
    { id: '5', name: '정우성', major: '기계설계', latestScore: 80, improvement: 5, completed: true, schoolName: '전북기계공업고등학교', grade: 3 },
];

// Helper to generate a mock report (Generic)
const createMockReport = (score: number, name: string, date: string): InterviewReport => ({
    date: date,
    scores: {
        contentRelevance: score > 80 ? 9 : 7,
        structure: score > 80 ? 8 : 6,
        fluency: score > 80 ? 9 : 7,
        confidence: score > 80 ? 8 : 6
    },
    totalScore: score / 10,
    summary: {
        strengths: `${name} 학생은 직무에 대한 이해도가 높고 경험을 구체적으로 설명할 수 있습니다. 특히 프로젝트 성과를 수치로 제시한 점이 인상적입니다.`,
        areasForGrowth: "답변의 구조가 다소 느슨할 때가 있습니다. STAR 기법을 더 엄격하게 적용하여 서론-본론-결론을 명확히 하면 좋겠습니다."
    },
    detailedFeedback: [
        {
            question: "본인의 강점은 무엇인가요?",
            answer: "저는 꼼꼼함이 강점입니다. 실수를 잘 안 합니다.",
            evaluation: "강점을 언급했지만 구체적인 사례가 부족합니다. 어떤 프로젝트에서 꼼꼼함으로 문제를 예방했는지 설명해보세요.",
            isCorrect: true,
            score: 7
        },
        {
            question: "어려움을 극복한 경험을 말해주세요.",
            answer: "프로젝트 마감기한이 짧아서 힘들었지만, 밤새서 열심히 해서 끝냈습니다.",
            evaluation: "열정은 좋지만, 단순히 '열심히'보다는 시간 관리를 어떻게 했는지, 팀원과 어떻게 협력했는지 구체적인 방법론(Action)이 필요합니다.",
            isCorrect: true,
            score: 6
        }
    ],
    nextSteps: [
        { title: "STAR 기법 훈련", description: "상황-과제-행동-결과 구조로 답변 작성하기 연습" },
        { title: "모의 면접 반복", description: "다양한 질문에 대해 즉흥적으로 답변하는 연습 필요" }
    ]
});

const detailedKimMinHoReport: InterviewReport = {
    date: '2024년 3월 15일',
    scores: {
        contentRelevance: 4,
        structure: 3,
        fluency: 5,
        confidence: 2
    },
    totalScore: 4.2,
    summary: {
        strengths: "9번 문항에 대한 답변에서 보여주셨듯이, 자신의 장기적인 비전과 목표를 매우 체계적이고 논리적으로 설명하는 뛰어난 역량을 갖추고 계십니다. 'π자형 인재'라는 구체적인 목표와 함께 AI, DevOps, 커뮤니케이션 능력 등 다방면의 노력을 구체적인 기술 스택과 경험을 바탕으로 제시한 점이 매우 인상적입니다. 준비된 질문에 대해서는 깊이 있는 사고와 명확한 표현이 가능하다는 큰 잠재력을 보여주셨습니다.",
        areasForGrowth: "전반적으로 면접에 대한 준비가 더 필요해 보입니다. 대부분의 질문에 '모르겠습니다', '대박'과 같은 단답형 또는 무응답으로 일관하여 지원자의 경험과 역량을 전혀 파악하기 어려웠습니다. 특히 이력서 기반의 구체적인 경험을 묻는 질문에 답변하지 못하는 것은 치명적일 수 있습니다. 면접은 자신의 경험을 바탕으로 역량을 증명하는 자리임을 인지하고, 모든 질문에 성실하고 구체적으로 답변하는 연습이 시급합니다. STAR 기법을 활용하여 자신의 프로젝트 경험을 구조화하고, 예상 질문에 대한 답변을 미리 준비하는 훈련이 반드시 필요합니다."
    },
    detailedFeedback: [
        {
            question: "MindVerse 웹사이트 프로젝트에서 MongoDB 스키마를 Mongoose를 사용하여 3개 설계하고 구현하셨는데, 이 과정에서 데이터 무결성과 효율성을 어떻게 확보하셨는지 구체적인 예를 들어 설명해 주십시오.",
            answer: "대박",
            evaluation: "질문의 의도에 전혀 부합하지 않는 답변입니다. 데이터 무결성과 효율성은 백엔드 개발자로서 매우 중요한 역량입니다. 스키마 설계 시 고려했던 제약 조건(Validation), 인덱싱(Indexing) 전략, 또는 정규화/비정규화 결정 과정 등을 구체적으로 설명해야 합니다. 면접관에게 예의를 갖추고 성실하게 답변하는 태도 또한 평가의 중요한 요소임을 명심하세요.",
            isCorrect: false,
            score: 1
        },
        {
            question: "Academic Service Chatbot 프로젝트에서 LSTM 모델을 활용한 챗봇의 인도네시아어 질문 견고성을 높이기 위해 데이터 증강 기법(역번역 및 동의어 대체)을 적용하셨습니다. 이 기법을 적용하기 전후의 성능 변화와 그 과정에서 겪었던 어려움은 무엇이었습니까?",
            answer: "대박",
            evaluation: "질문의 핵심인 '성능 변화'와 '어려움'에 대해 전혀 답변하지 못했습니다. 프로젝트 경험을 묻는 질문에는 STAR 기법(상황-과제-행동-결과)을 적용하여 답변하는 것이 효과적입니다. '데이터 부족이라는 문제 상황, 역번역 기법을 적용하여 학습 데이터 양을 2배로 늘렸고, 그 결과 F1-score가 0.75에서 0.82로 약 9% 향상되었습니다.' 와 같이 구체적인 수치를 포함하여 성과를 보여주어야 합니다.",
            isCorrect: false,
            score: 1
        },
        {
            question: "Selena - Seller Financial Tracking App 프로젝트에서 Autoencoder를 사용하여 불규칙한 지출을 자동으로 감지하는 이상 감지 모델을 개발하셨습니다. 이 모델의 설계 과정에서 어떤 종류의 데이터를 활용했고, 실제 이상 지출을 얼마나 정확하게 탐지할 수 있었는지 설명해 주십시오.",
            answer: "정말 감사합니다",
            evaluation: "질문에 대한 답변이 이루어지지 않았습니다. 사용한 데이터셋의 특징(시계열 데이터, 결제 로그 등)과 모델의 성능 지표(Precision, Recall 등)를 구체적으로 언급해야 합니다. 면접 중 답변하기 어려운 질문을 받았을 때는 '잠시 생각할 시간을 주시겠습니까?'라고 양해를 구하거나, 아는 부분까지만이라도 논리적으로 설명하려는 노력을 보여주는 것이 좋습니다.",
            isCorrect: false,
            score: 1
        },
        {
            question: "개발자로서 장기적인 비전이나 목표가 있다면 무엇이며, 그 목표를 달성하기 위해 현재 어떤 노력을 하고 있습니까?",
            answer: "1. 장기적인 비전 (Long-Term Vision) 저의 최종 목표는 **T자형 인재**를 넘어, **π자형 인재**와 같이 깊은 전문 분야(AI/ML 통합 및 프론트엔드 사용자 경험)를 두루 갖추고, 이들을 아우르는 시스템 설계 능력을 확보하는 것입니다. 기술적 목표: 복잡한 시스템의 설계(Architecture) 및 **확장성(Scalability)**을 책임지며, 특히 AI 모델과 같은 최신 기술을 안정적으로 서비스에 통합하는 전문가가 되는 것입니다. 가치 창출 목표: 개발 프로세스의 처음부터 끝까지 참여하여, 기술적 요구사항을 비즈니스 목표로 정확히 번역하고, 사용자에게 가장 효율적인 경험을 제공하는 솔루션을 제시하는 리더가 되는 것입니다. 2. 현재 달성을 위한 노력 (Current Efforts) 저는 현재 이러한 비전을 달성하기 위해 다음과 같은 세 가지 영역에서 노력을 집중하고 있습니다. 1. 깊은 전문성 확보 (Vertical Depth) AI 모델 통합 실습: 단순히 라이브러리를 사용하는 것을 넘어, React 프론트엔드 환경에서 Gemini API와 같은 AI 모델을 직접 통합하고 데이터를 처리하는 경험을 쌓고 있습니다. 이를 통해 지능적인 기능이 사용자 인터페이스에 매끄럽게 녹아들도록 구현하는 노하우를 습득하고 있습니다. 핵심 기술 심화: 서비스의 성능과 직결되는 TypeScript 및 비동기 처리 로직의 이해도를 높이는 데 시간을 투자하고 있습니다. 2. 서비스 운영 및 확장성 이해 (Horizontal Breadth & DevOps) CI/CD 환경 구축: 개발한 코드가 실제 서비스로 배포되는 전체 과정을 이해하기 위해 GitLab CI/CD 파이프라인을 직접 설정하고 관리하는 경험을 쌓았습니다. 배포 실패 요인을 분석하고 안정성을 확보하는 능력을 길렀습니다. Baas(Backend as a Service) 활용: Supabase와 같은 서버리스 백엔드 솔루션을 도입하여, 데이터베이스 설계부터 인증(Authentication)까지 백엔드 시스템을 빠르게 구성하고 확장하는 능력을 연습하고 있습니다. 이는 Full-Stack 아키텍처를 이해하는 데 필수적인 과정입니다. 3. 결과 기반의 사고 및 소통 훈련 가치 측정: 제가 개발하는 기능이 사용자 경험이나 비즈니스 목표에 어떤 긍정적인 변화를 주는지(예: 사용자 이탈률 감소, 효율 증가) 측정하고 결과를 분석하는 훈련을 합니다. 기술 번역: 비기술 직군에게 복잡한 기술적 의사결정을 명료하고 설득력 있게 설명할 수 있도록 문서를 작성하고 소통하는 연습을 지속하여, 팀 전체의 목표 달성에 기여할 수 있도록 노력하고 있습니다.",
            evaluation: "매우 훌륭한 답변입니다. 질문의 의도를 정확히 파악하고, 자신의 장기적인 비전과 이를 달성하기 위한 현재의 구체적인 노력을 논리적으로 잘 설명했습니다. 'π자형 인재'라는 명확한 목표와 함께 AI, DevOps, 커뮤니케이션 능력 등 다방면의 노력을 구체적인 기술 스택과 경험을 바탕으로 제시한 점이 매우 인상적입니다. 이러한 답변 방식은 다른 질문에도 동일하게 적용할 필요가 있습니다.",
            isCorrect: true,
            score: 9.5
        }
    ],
    nextSteps: [
        {
            title: "면접 기본 태도 및 답변 준비",
            description: "모든 면접 질문에는 성실하고 진솔한 답변을 해야 합니다. '모르겠다'거나 무응답으로 일관하기보다는, 질문의 의도를 파악하고 자신이 아는 범위 내에서 최대한 설명하려는 노력이 필요합니다. 본인의 이력서와 자기소개서를 바탕으로 예상 질문 리스트를 만들고, 각 질문에 대해 1분 내외로 답변하는 연습을 반복하세요."
        },
        {
            title: "STAR 기법을 활용한 경험 정리",
            description: "자신이 수행한 모든 프로젝트 경험을 STAR 기법(Situation-상황, Task-과제, Action-행동, Result-결과)에 따라 문서로 정리해보세요. 이 구조에 맞춰 이야기하면 훨씬 논리적이고 설득력 있는 답변을 할 수 있습니다. 특히 'Action'과 'Result' 부분에서 자신의 역할과 기여도를 구체적으로 드러내는 것이 중요합니다."
        },
        {
            title: "성과를 구체적인 수치로 표현하기",
            description: "자신의 성과를 이야기할 때 '성능을 개선했다'와 같이 추상적인 표현 대신, '응답 속도를 30% 단축했다', '정확도를 85%에서 92%로 7%p 향상시켰다'처럼 구체적인 숫자를 제시하는 연습을 하세요. 수치화된 결과는 자신의 기여도를 객관적으로 증명해주어 답변의 신뢰도를 크게 높여줍니다."
        }
    ]
};

let mockStudentDetailData: { [key: string]: StudentDetail } = {
    '1': {
        id: '1',
        name: '김민호',
        major: '자동화기계',
        schoolName: '이리공업고등학교',
        grade: 3,
        report: detailedKimMinHoReport,
        history: [detailedKimMinHoReport, createMockReport(65, '김민호', '2024년 3월 10일')]
    },
    '2': {
        id: '2',
        name: '박지윤',
        major: '전기제어',
        schoolName: '이리공업고등학교',
        grade: 3,
        report: createMockReport(85, '박지윤', '2024년 3월 14일'),
        history: [createMockReport(85, '박지윤', '2024년 3월 14일')]
    },
    '3': {
        id: '3',
        name: '이서준',
        major: '스마트팩토리',
        schoolName: '이리공업고등학교',
        grade: 3,
        history: []
    },
    '4': {
        id: '4',
        name: '최혜원',
        major: '조리제빵',
        schoolName: '이리공업고등학교',
        grade: 2,
        report: createMockReport(92, '최혜원', '2024년 3월 12일'),
        history: [createMockReport(92, '최혜원', '2024년 3월 12일')]
    },
    '5': {
        id: '5',
        name: '정우성',
        major: '기계설계',
        schoolName: '전북기계공업고등학교',
        grade: 3,
        report: createMockReport(80, '정우성', '2024년 3월 11일'),
        history: [createMockReport(80, '정우성', '2024년 3월 11일')]
    }
};

export const saveInterviewReportForStudent = (studentId: string, report: InterviewReport) => {
    // For the demo, if the student doesn't exist in mock data (e.g. dynamic sign up), 
    // we just skip saving to the static list or create a temp entry locally.
    // In a real app, this would save to DB.
    let studentSummary = mockStudentList.find(s => s.id === studentId);
    let studentDetail = mockStudentDetailData[studentId];

    if (!studentDetail) {
        // Create transient detail for demo
        studentDetail = {
            id: studentId,
            name: 'Demo Student',
            major: '소프트웨어',
            schoolName: 'Demo School',
            grade: 3,
            history: []
        };
        mockStudentDetailData[studentId] = studentDetail;
    }

    if (!studentSummary) {
         // Create transient summary for demo
         studentSummary = {
            id: studentId,
            name: 'Demo Student',
            major: '소프트웨어',
            schoolName: 'Demo School',
            grade: 3,
            latestScore: 0,
            improvement: 0,
            completed: false
         };
         mockStudentList.push(studentSummary);
    }

    const newOverallScore = report.totalScore * 10; // Convert 0-10 to 0-100
    const oldScore = studentSummary.latestScore;
    const improvement = oldScore > 0 ? Math.round(((newOverallScore - oldScore) / oldScore) * 100) : 0;
    
    studentSummary.latestScore = Math.round(newOverallScore);
    studentSummary.improvement = isFinite(improvement) ? improvement : 0;
    studentSummary.completed = true;

    studentDetail.report = report;
    studentDetail.history.unshift(report); // Add to history
};


export const getTeacherDashboardData = async (): Promise<StudentSummary[]> => {
    await new Promise(res => setTimeout(res, 500));
    return JSON.parse(JSON.stringify(mockStudentList));
};

export const getStudentDetails = async (studentId: string): Promise<StudentDetail> => {
    await new Promise(res => setTimeout(res, 500));
    const studentData = mockStudentDetailData[studentId];
    if (!studentData) {
        // Return a default empty student for demo if not found
        return {
            id: studentId,
            name: '학생',
            major: '전공',
            schoolName: '학교',
            grade: 1,
            history: []
        };
    }
    return JSON.parse(JSON.stringify(studentData));
};
