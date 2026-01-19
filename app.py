import streamlit as st
import requests
import json

# --- CONFIGURATION ---
# This grabs the key from Streamlit's secure vault
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API Key not found. Please set it in Streamlit Secrets.")
    st.stop()

API_URL = "https://lightning.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.5-flash-lite-preview-06-17"

# --- PAGE SETUP ---
st.set_page_config(page_title="Помощник сообщений", page_icon="💬", layout="centered")

# --- SESSION STATE ---
if "api_result" not in st.session_state:
    st.session_state.api_result = None

# --- CSS FOR CARDS ---
st.markdown("""
<style>
    .stTextArea textarea {font-size: 16px;}
    .card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #4e4e4e;
    }
    .card-header {
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 8px;
        color: #fff;
    }
    .card-content {
        color: #e0e0e0;
        font-family: sans-serif;
    }
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- API FUNCTION ---
def get_ai_response(prompt_text):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_instruction = """
    You are a Russian messaging assistant. 
    Output ONLY valid JSON.
    Always return a JSON object with exactly these 4 keys: 
    "formal", "friendly", "humorous", "brief".
    All values must be in Russian.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.85
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- HELPER: PROMPT BUILDER ---
def build_prompt(mode_selection, text_input):
    if mode_selection == "Предложить варианты ответа":
        return f"""
        The user received this message: "{text_input}"
        Generate 4 distinct replies in Russian:
        1. Formal (Business)
        2. Friendly (Casual)
        3. Humorous (Witty)
        4. Brief (Direct)
        Return JSON format: {{ "formal": "...", "friendly": "...", "humorous": "...", "brief": "..." }}
        """
    elif mode_selection == "Ответ на историю переписки":
        return f"""
        Chat history:
        ---
        {text_input}
        ---
        Generate 4 distinct replies to the LAST message in Russian:
        1. Formal
        2. Friendly
        3. Humorous
        4. Brief
        Return JSON format: {{ "formal": "...", "friendly": "...", "humorous": "...", "brief": "..." }}
        """
    else: 
        return f"""
        The user wrote this draft: "{text_input}"
        Rewrite/Paraphrase this draft into 4 distinct Russian versions:
        1. Formal (Polite/Business)
        2. Friendly (Natural)
        3. Humorous (Fun)
        4. Brief (Short)
        Return JSON format: {{ "formal": "...", "friendly": "...", "humorous": "...", "brief": "..." }}
        """

# --- MAIN APP INTERFACE ---

st.title("💬 Помощник сообщений")

mode = st.radio(
    "Что нужно сделать?",
    [
        "Предложить варианты ответа", 
        "Ответ на историю переписки", 
        "Улучшить мой черновик"
    ]
)

user_input = ""
if mode == "Предложить варианты ответа":
    user_input = st.text_area("Вставьте входящее сообщение:", height=150, placeholder="Например: Ты где?")
elif mode == "Ответ на историю переписки":
    user_input = st.text_area("Вставьте историю переписки:", height=200, placeholder="- Привет\n- Как дела?")
else:
    user_input = st.text_area("Вставьте ваш черновик:", height=150, placeholder="Например: я буду поже")

if st.button("🚀 Начать обработку", type="primary"):
    if not user_input.strip():
        st.warning("Введите текст!")
    else:
        with st.spinner("Думаю..."):
            prompt = build_prompt(mode, user_input)
            st.session_state.api_result = get_ai_response(prompt)
            st.rerun()

if st.session_state.api_result:
    result = st.session_state.api_result
    st.markdown("---")

    if "error" in result:
        st.error(f"Error: {result['error']}")
    elif "choices" in result:
        try:
            content = result["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)

            st.success("Готово! Вот варианты:")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">👔 Официально</div>
                    <div class="card-content">{data.get('formal', '...')}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">🤝 Дружески</div>
                    <div class="card-content">{data.get('friendly', '...')}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">😄 С юмором</div>
                    <div class="card-content">{data.get('humorous', '...')}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">⚡ Коротко</div>
                    <div class="card-content">{data.get('brief', '...')}</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("")
            if st.button("🔄 Перегенерировать (Попробовать еще раз)"):
                with st.spinner("Генерирую новые варианты..."):
                    prompt = build_prompt(mode, user_input)
                    st.session_state.api_result = get_ai_response(prompt)
                    st.rerun()

        except Exception as e:
            st.error("Ошибка формата данных. Нажмите 'Перегенерировать'.")
