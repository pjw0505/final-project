# app.py 파일 내에 정의

import streamlit as st
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# app.py 파일 상단 (import문 바로 아래)

# from dotenv import load_dotenv # 이 라인은 Streamlit Cloud에서는 주석 처리하거나 제거해야 합니다.

# --- LLM 클라이언트를 안전하게 초기화하는 함수 ---
@st.cache_resource

def get_openai_client():
    # Streamlit Cloud가 환경 변수를 로드한 후 이 함수가 실행됩니다.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("오류: API 키 (OPENAI_API_KEY)가 Streamlit Secrets에 설정되지 않았습니다.")
        st.stop() # 키가 없으면 앱 실행을 중단합니다.
        
    return OpenAI(api_key=api_key)

# app.py 파일에 추가해야 할 run_master_agent 함수

def run_master_agent(user_prompt: str, location: str, structure_name: str):
    
    # 1. 안전하게 초기화된 클라이언트 객체를 가져옵니다.
    client = get_openai_client()
    
    # 2. Tool 함수들과 LLM이 사용할 변수들을 정의합니다.
    available_functions = {
        "get_heritage_text_record": get_heritage_text_record,
        "call_3d_restoration_api": call_3d_restoration_api,
    }
    # (주의: tools는 파일 상단에 정의된 전역 변수여야 합니다.)
    
    messages = [{"role": "user", "content": user_prompt}]
    tool_results = {}
    
    # 3. LLM과 Tools 간의 대화 루프 (최대 3회 반복)
    for _ in range(3):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        
        response_message = response.choices[0].message
        
        # 최종 분석 결과 텍스트가 나왔는지 확인
        if not response_message.tool_calls:
            return response_message.content, tool_results
        
        # 4. Tool Call 실행 (MCP 핵심 로직)
        messages.append(response_message)
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            st.info(f"에이전트가 외부 도구 호출: {function_name}")
            
            # 함수 실행
            if function_name == "get_heritage_text_record":
                function_args['location'] = location
                function_args['structure_name'] = structure_name
            
            function_response = available_functions[function_name](**function_args)
            
            # 5. Tool 실행 결과를 저장하고 LLM에게 전달하여 최종 응답을 유도
            tool_results[function_name] = json.loads(function_response)
            messages.append(
                {"tool_call_id": tool_call.id, "role": "tool", "content": function_response}
            )
            
    # 루프 종료 후 최종 응답 반환
    final_response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return final_response.choices[0].message.content, tool_results

# client = get_openai_client() # 이제 이 client 객체는 함수를 호출해서 얻습니다.
load_dotenv()
# OpenAI API 키는 환경 변수에서 로드됩니다.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 1. Tool(Function) 정의: Mock 데이터 및 API 대체 함수 ---

def get_heritage_text_record(location: str, structure_name: str) -> str:
    """
    특정 지역과 구조물의 이름을 기반으로 문화유산 포털에서 관련 역사 기록 텍스트를 검색합니다.
    """
    # 실제 구현 시: 공공데이터포털의 문화재 정보를 호출하는 requests 코드가 들어갑니다.
    if "경복궁 사정전" in structure_name:
        return json.dumps({
            "status": "success",
            "text_record": "사정전은 경복궁의 정전으로, 임금의 집무실이었다. 1917년 화재로 소실되었으나, 기록에 따르면 화려한 단청과 용마루가 특징적이었으며, 내부에는 온돌방이 있었다. 주변에는 회랑이 있었다.",
            "original_image_url": "https://example.com/damaged_original.jpg" # 원본 이미지 URL (가정)
        })
    return json.dumps({"status": "error", "text_record": "관련 기록을 찾을 수 없습니다."})

def call_3d_restoration_api(description: str, location_data: str) -> str:
    """
    상세한 복원 묘사(description)와 지리 정보(location_data)를 받아 3D 모델링 또는 복원 이미지를 생성하는 외부 AI API를 호출합니다.
    """
    # 실제 구현 시: 3D 모델링 API (예: Blender API 래퍼, 또는 DALL-E/Midjourney의 고급 프롬프트) 호출 코드가 들어갑니다.
    print(f"3D 복원 API 호출 중. 묘사: {description[:50]}...")
    
    # Mock 복원 결과 URL 반환
    return json.dumps({
        "status": "success", 
        "restored_url": "https://example.com/restored_model_placeholder.jpg" 
    })

# LLM에게 제공할 최종 Tool 스키마 목록
tools = [
    # get_heritage_text_record 스키마 정의 (이전 예시와 유사하게)
    {
        "type": "function",
        "function": {
            "name": "get_heritage_text_record",
            "description": "지역 및 구조물 이름을 사용하여 역사 기록 텍스트를 검색하고 원본 이미지 URL을 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "문화유산이 위치했던 지역"},
                    "structure_name": {"type": "string", "description": "문화유산의 이름 또는 특징"},
                },
                "required": ["structure_name"],
            },
        },
    },
    # call_3d_restoration_api 스키마 정의
    {
        "type": "function",
        "function": {
            "name": "call_3d_restoration_api",
            "description": "상세한 묘사를 기반으로 3D 모델 또는 복원 이미지를 생성하는 API를 호출하고 결과를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "복원할 구조물의 상세한 시각적 묘사"},
                    "location_data": {"type": "string", "description": "지리 정보, 지형적 특징 (예: 경사진 언덕 위, 강 옆)"},
                },
                "required": ["description", "location_data"],
            },
        },
    },
]

available_functions = {
    "get_heritage_text_record": get_heritage_text_record,
    "call_3d_restoration_api": call_3d_restoration_api,
}
