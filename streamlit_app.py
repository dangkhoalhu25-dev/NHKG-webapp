import streamlit as st
from google import genai
from google.genai import types

# 1. CẤU HÌNH GIAO DIỆN WEB
st.set_page_config(page_title="Trợ lý N.H.K.G - ĐH Lạc Hồng", page_icon="🏗️", layout="centered")

st.title("🏗️ Trợ lý ảo N.H.K.G - Hỗ trợ Đồ án Xây dựng")
st.markdown("""
**Chào mừng bạn đến với Hệ thống tự học chủ động Khoa Kỹ thuật Công trình.**
*Hệ thống yêu cầu bạn phải tuân thủ Quy trình 4 bước: Nhận diện - Hỏi - Kiểm chứng - Giải quyết.*
""")

# 2. KHU VỰC BẮT BUỘC: CAM KẾT KIỂM CHỨNG (BƯỚC K)
st.sidebar.header("⚠️ BƯỚC K: BẮT BUỘC")
st.sidebar.info("Để sử dụng AI, bạn phải cam kết thực hiện quy trình kiểm chứng.")
is_verified = st.sidebar.checkbox("Em cam kết sẽ đối chiếu kết quả của AI với TCVN và phần mềm Plaxis/SAP2000.")

# 3. KẾT NỐI VỚI GOOGLE AI STUDIO (SDK MỚI)
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chưa cấu hình API Key. Vui lòng thêm GEMINI_API_KEY vào phần Secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

system_instruction = """
Bạn là một Giảng viên/Trợ lý học tập chuyên ngành Kỹ thuật Xây dựng (Nền móng, Sức bền vật liệu, Bê tông).
Nhiệm vụ của bạn là hướng dẫn sinh viên ĐH Lạc Hồng theo quy trình N.H.K.G.
QUY TẮC TỐI THƯỢNG:
1. KHÔNG BAO GIỜ giải hộ bài tập hay đưa ra đáp án tính toán cuối cùng.
2. Nếu sinh viên hỏi bài, hãy gợi ý các bước giải, gợi ý công thức và hỏi ngược lại sinh viên.
3. Luôn nhắc nhở sinh viên: "Hãy kiểm tra lại hệ số này trong TCVN 2737:2023 hoặc TCVN 10304:2014" hoặc "Hãy thử mô phỏng sơ đồ này trên Plaxis/SAP2000 để kiểm chứng".
"""

# 4. GIAO DIỆN CHAT (BƯỚC H)
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if is_verified:
    prompt = st.chat_input("Nhập câu hỏi (Ví dụ: Các bước kiểm tra lún móng băng?)")
    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
            reply = response.text
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Chi tiết lỗi từ Gemini API: {e}")
else:
    st.warning("🔒 Khung Chat đã bị khóa. Bạn vui lòng tích vào ô Cam kết kiểm chứng ở thanh Menu bên trái (Bước K) để mở khóa tính năng hỏi AI.")