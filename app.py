# =======================================================
# app.py: 문화유산 에이전트 (최종 수정 및 정리된 버전)
# =======================================================

# app.py 파일 내 get_openai_client 함수 수정

@st.cache_resource
def get_openai_client():
    
    # 💥💥 os.getenv() 대신 st.secrets 객체를 직접 사용합니다. 💥💥
    
    # 1. st.secrets 객체에서 API 키 값을 가져옵니다.
    #    (secrets는 [secrets] 섹션으로 정의했으므로, st.secrets["secrets"]를 통해 접근합니다.)
    try:
        # 키를 가져와서 양쪽 공백이나 줄바꿈 문자를 확실히 제거합니다.
        api_key = st.secrets["secrets"]["OPENAI_API_KEY"].strip()
    except KeyError:
        # st.secrets에 키가 정의되지 않았거나 섹션 이름이 잘못되었을 때
        st.error("오류: Streamlit Secrets에 [secrets] 섹션 또는 OPENAI_API_KEY가 누락되었습니다.")
        st.stop()
        
    # 2. 키 값이 비어 있는지 최종 확인
    if not api_key or not api_key.startswith("sk-"):
        st.error("오류: API 키 (OPENAI_API_KEY)의 값이 유효하지 않습니다.")
        st.stop()
        
    return OpenAI(api_key=api_key)
import streamlit as st
from openai import OpenAI
import json
import os
from dotenv import load_dotenv # 로컬 테스트용. Streamlit Cloud에서는 제거/주석 처리

# -------------------------------------------------------
# 1. LLM 클라이언트 초기화 (최상위 레벨)
# -------------------------------------------------------

@st.cache_resource
def get_openai_client():
    # Streamlit Cloud가 환경 변수를 로드한 후 실행
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("오류: API 키 (OPENAI_API_KEY)가 Streamlit Secrets에 설정되지 않았습니다.")
        st.stop()
        
    return OpenAI(api_key=api_key)

# -------------------------------------------------------
# 2. Tool 함수 정의 (최상위 레벨)
# -------------------------------------------------------

def get_heritage_text_record(location: str, structure_name: str) -> str:
    """ 특정 지역과 구조물의 이름을 기반으로 역사 기록 텍스트를 검색합니다. """
    if "경복궁 사정전" in structure_name:
        return json.dumps({
            "status": "success",
            "text_record": "사정전은 경복궁의 정전으로, 임금의 집무실이었다. 1917년 화재로 소실되었으나, 기록에 따르면 화려한 단청과 용마루가 특징적이었으며, 내부에는 온돌방이 있었다. 주변에는 회랑이 있었다.",
            "original_image_url": "https://example.com/damaged_original.jpg"
        })
    return json.dumps({"status": "error", "text_record": "관련 기록을 찾을 수 없습니다."})

def call_3d_restoration_api(description: str, location_data: str) -> str:
    """ 상세한 복원 묘사를 받아 3D 모델링 또는 복원 이미지를 생성하는 API를 호출합니다. """
    print(f"3D 복원 API 호출 중. 묘사: {description[:50]}...")
    return json.dumps({
        "status": "success",
        "restored_url": "https://example.com/restored_model_placeholder.jpg"
    })

# -------------------------------------------------------
# 3. Tool 스키마 및 딕셔너리 정의 (최상위 레벨)
# -------------------------------------------------------

tools = [
    {"type": "function", "function": {"name": "get_heritage_text_record", "description": "지역 및 구조물 이름을 사용하여 역사 기록 텍스트를 검색하고 원본 이미지 URL을 반환합니다.", "parameters": {"type": "object", "properties": {"location": {"type": "string"}, "structure_name": {"type": "string"}}, "required": ["structure_name"]}}},
    {"type": "function", "function": {"name": "call_3d_restoration_api", "description": "상세한 묘사를 기반으로 3D 모델 또는 복원 이미지를 생성하는 API를 호출하고 결과를 반환합니다.", "parameters": {"type": "object", "properties": {"description": {"type": "string"}, "location_data": {"type": "string"}}, "required": ["description", "location_data"]}}}
]
available_functions = {
    "get_heritage_text_record": get_heritage_text_record,
    "call_3d_restoration_api": call_3d_restoration_api,
}

# -------------------------------------------------------
# 4. 핵심 에이전트 실행 함수 (최상위 레벨)
# -------------------------------------------------------

def run_master_agent(user_prompt: str, location: str, structure_name: str):
    
    client = get_openai_client() # 클라이언트 객체 가져오기
    messages = [{"role": "user", "content": user_prompt}]
    tool_results = {}
    
    for _ in range(3):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        response_message = response.choices[0].message
        
        if not response_message.tool_calls:
            return response_message.content, tool_results
        
        messages.append(response_message)
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            st.info(f"에이전트가 외부 도구 호출: {function_name}")
            
            if function_name == "get_heritage_text_record":
                function_args['location'] = location
                function_args['structure_name'] = structure_name
            
            function_response = available_functions[function_name](**function_args)
            
            tool_results[function_name] = json.loads(function_response)
            messages.append({"tool_call_id": tool_call.id, "role": "tool", "content": function_response})
            
    final_response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return final_response.choices[0].message.content, tool_results


# -------------------------------------------------------
# 5. Streamlit UI 및 실행 로직 (최상위 레벨)
# -------------------------------------------------------

st.title("🌍 지역 문화유산 디지털 마스터 에이전트")
st.markdown("역사 기록을 분석하고 훼손된 문화유산을 디지털로 복원합니다.")

# 사이드바 (입력 영역)
with st.sidebar:
    st.header("문화유산 정보 입력")
    location = st.text_input("지역:", "서울 종로")
    structure_name = st.text_input("문화유산 이름/특징:", "경복궁 사정전")
    location_data = st.text_input("지형 데이터:", "평지")
    
    prompt = st.text_area(
        "AI 분석 및 복원 요청:",
        f"'{structure_name}'의 역사 기록을 검색하고, 그 기록을 바탕으로 복원할 때의 시각적인 묘사를 생성해 줘. 그리고 복원된 모습을 이미지로 시뮬레이션해 줘.",
        height=150
    )

# 메인 실행 버튼
if st.button("🔎 분석 및 복원 시뮬레이션 실행"):
    if structure_name and prompt:
        with st.spinner("AI 에이전트가 역사 기록을 검색하고 복원 명령을 생성 중입니다..."):
            
            # run_master_agent 함수 호출
            analysis_text, tool_results = run_master_agent(prompt, location, structure_name)
            
            # 결과 출력
            st.subheader("💡 에이전트 분석 결과 및 스토리텔링")
            st.write(analysis_text)
            
            if "get_heritage_text_record" in tool_results:
                record = tool_results["get_heritage_text_record"]
                if record.get("status") == "success":
                    st.subheader("📜 검색된 역사 기록")
                    st.code(record["text_record"], language='markdown')
                    
                    if "call_3d_restoration_api" in tool_results:
                        restored = tool_results["call_3d_restoration_api"]
                        if restored.get("status") == "success":
                            st.subheader("✨ 디지털 복원 시뮬레이션 결과")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text("원본 이미지 (기록에 의해 가정)")
                                st.image(record["original_image_url"], caption="훼손되거나 소실된 유산")
                            with col2:
                                st.text("AI 복원 시뮬레이션")
                                st.image(restored["restored_url"], caption="기록 기반 복원")
                            
    else:
        st.warning("문화유산 이름과 분석 요청을 입력해 주세요.")
