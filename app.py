# app.py 파일 내에 정의

import streamlit as st
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

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
