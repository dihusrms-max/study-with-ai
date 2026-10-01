import streamlit as st
import pandas as pd
import plotly.express as px
from langchain.messages import SystemMessage,HumanMessage,AIMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_model():
    return init_chat_model("openai:gpt-6-luna", reasoning_effort="none")



st.set_page_config(page_title="챗봇", 
                   page_icon="🤖", 
                   layout="wide")

# 모델 로드 -> 사용자마다 다를 필요가 없다 -> 캐시에 저장
# cache : 데이터(표,숫자,리스트) -> 미리 가져올 사용
# cache_resurce -> 모델, DB 연결, 에이전트 와 같은 한번 만들어서사용
# 계속 재사용한ㄴ 객체 -> resource에 저장

# 대화 내용이 누적
if "messages" not in st.session_state:
    st.session_state['messages']=[] # 초기화

for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

question = st.chat_input("질문해주세용")
    
if question :
    with st.chat_message("user"):
        st.markdown(question)
    # 질문한 내역을 저장 -> msessages에 저장
    st.session_state['messages'].append({'role':'user','content':question})
    with st.chat_message('assistant'):
            answer = get_model().invoke(st.session_state['messages'])
            st.markdown(answer.text)

            st.session_state['messages'].append({'role':'assistant','content': answer.content})



