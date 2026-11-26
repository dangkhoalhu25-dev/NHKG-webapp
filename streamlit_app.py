import streamlit as st
import google.generativeai as genai

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

# 3. KẾT NỐI VỚI GOOGLE AI STUDIO (BỘ NÃO)
# Lưu ý: Sẽ cấu hình API Key bảo mật sau
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Chưa cấu hình API Key. Vui lòng thêm GEMINI_API_KEY vào phần Secrets.")

# Thiết lập "Đạo đức sư phạm" cho AI (System Instructions)
system_instruction = """
Bạn là một Giảng viên/Trợ lý học tập chuyên ngành Kỹ thuật Xây dựng (Nền móng, Sức bền vật liệu, Bê tông).
Nhiệm vụ của bạn là hướng dẫn sinh viên ĐH Lạc Hồng theo quy trình N.H.K.G.
QUY TẮC TỐI THƯỢNG:
1. KHÔNG BAO GIỜ giải hộ bài tập hay đưa ra đáp án tính toán cuối cùng.
2. Nếu sinh viên hỏi bài, hãy gợi ý các bước giải, gợi ý công thức và hỏi ngược lại sinh viên.
3. Luôn nhắc nhở sinh viên: "Hãy kiểm tra lại hệ số này trong TCVN 2737:2023 hoặc TCVN 10304:2014" hoặc "Hãy thử mô phỏng sơ đồ này trên Plaxis/SAP2000 để kiểm chứng".
"""

# Khởi tạo mô hình
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction
)

# 4. GIAO DIỆN CHAT (BƯỚC H)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Khung nhập câu hỏi
if is_verified:
    prompt = st.chat_input("Nhập câu hỏi (Ví dụ: Các bước kiểm tra lún móng băng?)")
    if prompt:
        # Hiển thị câu hỏi của SV
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Gọi AI trả lời
        response = model.generate_content(prompt)
        
        # Hiển thị câu trả lời của AI
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.warning("🔒 Khung Chat đã bị khóa. Bạn vui lòng tích vào ô Cam kết kiểm chứng ở thanh Menu bên trái (Bước K) để mở khóa tính năng hỏi AI.")