import base64
import html
import time
from datetime import datetime, timedelta, timezone

import requests
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. CẤU HÌNH TRANG & ĐỒ HỌA GIAO DIỆN (CSS)
# ==========================================
st.set_page_config(
    page_title="Trợ lý N.H.K.G - ĐH Lạc Hồng",
    page_icon="🏗️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .hero-banner {
        background:
            linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px),
            linear-gradient(135deg, #0b2545 0%, #134074 55%, #1d5b9e 100%);
        background-size: 24px 24px, 24px 24px, 100% 100%;
        border-radius: 16px;
        padding: 22px 26px;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(11, 37, 69, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.14);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(245, 158, 11, 0.2);
        border: 1px solid #f59e0b;
        color: #fde68a;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.6px;
        padding: 4px 10px;
        border-radius: 999px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        margin: 0 0 6px 0;
        color: #ffffff;
        line-height: 1.25;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #dbeafe;
        margin: 0;
        line-height: 1.5;
    }
    .stepper-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .step-card {
        border-radius: 12px;
        padding: 14px 16px;
        border: 1.5px solid #e2e8f0;
        background: #f8fafc;
        color: #64748b;
    }
    .step-card.active {
        background: #eff6ff;
        border-color: #2563eb;
        color: #1e3a8a;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.14);
    }
    .step-card.done {
        background: #ecfdf5;
        border-color: #10b981;
        color: #065f46;
    }
    .step-tag {
        font-size: 11.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .step-name {
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .step-desc {
        font-size: 12.5px;
        opacity: 0.9;
    }
    .section-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #1d5b9e;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
        color: #0f172a;
    }
    .cert-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 2px solid #0f766e;
        border-radius: 14px;
        padding: 22px 26px;
        color: #0f172a;
        box-shadow: 0 8px 20px rgba(15, 118, 110, 0.1);
    }
    .cert-header {
        border-bottom: 2px dashed #cbd5e1;
        padding-bottom: 12px;
        margin-bottom: 14px;
    }
    .log-badge {
        display: inline-block;
        font-size: 11.5px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 999px;
        margin-right: 6px;
    }
    .badge-h { background: #dbeafe; color: #1e40af; }
    .badge-g { background: #d1fae5; color: #065f46; }
    @media (max-width: 768px) {
        .stepper-grid { grid-template-columns: repeat(2, 1fr); }
        .hero-svg { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. KẾT NỐI GEMINI API & GOOGLE SHEETS
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chưa cấu hình API Key. Vui lòng thêm GEMINI_API_KEY vào phần Secrets trên Streamlit Cloud.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL_NAME = "gemini-3.8-flash"
GSHEET_URL = st.secrets.get("GSHEET_WEBHOOK_URL", "").strip()

SYSTEM_INSTRUCTION_N = """
Bạn là Giảng viên/Trợ lý học tập chuyên ngành Kỹ thuật Xây dựng (Nền móng, Sức bền vật liệu, Kết cấu) tại Đại học Lạc Hồng.
Hiện sinh viên đang ở BƯỚC N (NHẬN DIỆN VẤN ĐỀ) trong quy trình N.H.K.G.
NHIỆM VỤ CỦA BẠN:
1. Nếu có ảnh đề bài/sơ đồ tính, hãy đọc kỹ và liệt kê ngắn gọn các dữ kiện đầu vào chính nhìn thấy trong ảnh.
2. Chỉ ra 2–3 khái niệm lý thuyết cốt lõi và Tiêu chuẩn Việt Nam (TCVN 2737:2023, TCVN 10304:2014, TCVN 9362:2012...) liên quan trực tiếp đến chỗ sinh viên đang bí.
3. Gợi ý 2 câu hỏi thông minh để sinh viên dùng ở Bước H tiếp theo.
QUY TẮC TUYỆT ĐỐI: KHÔNG giải bài tập, KHÔNG thế số tính toán, KHÔNG đưa ra đáp số cuối cùng.
"""

SYSTEM_INSTRUCTION_H = """
Bạn là Giảng viên/Trợ lý học tập chuyên ngành Kỹ thuật Xây dựng tại Đại học Lạc Hồng, hỗ trợ sinh viên ở BƯỚC H (HỎI) của quy trình N.H.K.G.
QUY TẮC TỐI THƯỢNG:
1. KHÔNG BAO GIỜ giải hộ bài tập hay đưa ra đáp số tính toán cuối cùng.
2. Chỉ hướng dẫn trình tự các bước giải, gợi ý công thức tổng quát, giải thích ý nghĩa vật lý và hỏi ngược lại sinh viên để kiểm tra mức độ hiểu bài.
3. Luôn nhắc sinh viên ở cuối câu trả lời phải sang Bước K để đối chiếu hệ số/công thức với TCVN mới nhất (VD: TCVN 2737:2023, TCVN 10304:2014, TCVN 9362:2012) hoặc mô phỏng kiểm chứng bằng Plaxis/SAP2000/Optum.
"""


def vn_now_str():
    vn_tz = timezone(timedelta(hours=7))
    return datetime.now(vn_tz).strftime("%d/%m/%Y %H:%M:%S")


def call_gemini(contents, system_instruction):
    """Gọi Gemini API có tự động thử lại khi gặp lỗi quá tải 503."""
    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_instruction),
            )
            return response.text, None
        except Exception as exc:
            last_error = str(exc)
            if "503" in last_error or "UNAVAILABLE" in last_error:
                time.sleep(2 * (attempt + 1))
            else:
                break
    return None, last_error


@st.cache_data(ttl=30, show_spinner=False)
def fetch_gsheet_logs(webhook_url):
    """Đọc danh sách nhật ký Hỏi - Đáp từ Google Sheets qua Apps Script."""
    if not webhook_url:
        return [], "Chưa cấu hình GSHEET_WEBHOOK_URL trong Secrets."
    try:
        resp = requests.get(webhook_url, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ok":
            return data.get("records", []), None
        return [], data.get("message", "Không đọc được dữ liệu từ Google Sheets.")
    except Exception as exc:
        return [], f"Không thể kết nối Google Sheets: {exc}"


def save_to_gsheet(buoc, cau_hoi="", phan_hoi_ai="", kiem_chung="", ket_luan=""):
    """Ghi tự động một dòng nhật ký về Google Sheets (không làm gián đoạn phiên học)."""
    if not GSHEET_URL:
        return False
    payload = {
        "thoi_gian": vn_now_str(),
        "buoc": buoc,
        "ho_ten": st.session_state.student_name.strip() or "Ẩn danh",
        "mssv": st.session_state.student_id.strip() or "Chua_nhap",
        "hoc_phan": st.session_state.course_name,
        "nhom_kho_khan": st.session_state.issue_type,
        "cau_hoi": cau_hoi,
        "phan_hoi_ai": phan_hoi_ai,
        "kiem_chung": kiem_chung,
        "ket_luan": ket_luan,
    }
    try:
        resp = requests.post(GSHEET_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            fetch_gsheet_logs.clear()
            return True
    except Exception:
        pass
    return False


# ==========================================
# 3. QUẢN LÝ TRẠNG THÁI (SESSION STATE)
# ==========================================
DEFAULTS = {
    "main_view": "practice",  # "practice" hoặc "library"
    "active_step": 1,
    "unlocked_step": 1,
    "student_name": "",
    "student_id": "",
    "course_name": "Đồ án Nền Móng",
    "problem_img_bytes": None,
    "problem_img_mime": None,
    "problem_img_name": None,
    "problem_text": "",
    "issue_type": "Hổng lý thuyết / Chưa biết chọn sơ đồ tính",
    "stuck_point": "",
    "n_ai_analysis": "",
    "messages": [],
    "k_check_tcvn": False,
    "k_check_quant": False,
    "k_check_sim": False,
    "k_note": "",
    "g_img_bytes": None,
    "g_img_mime": None,
    "g_img_name": None,
    "g_conclusion": "",
    "g_completed": False,
    "g_timestamp": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_session():
    for key, value in DEFAULTS.items():
        if key not in ("student_name", "student_id", "course_name", "main_view"):
            st.session_state[key] = value if not isinstance(value, list) else []
    st.session_state.main_view = "practice"
    st.rerun()


# ==========================================
# 4. THANH BÊN TRÁI (THÔNG TIN & CHUYỂN CHẾ ĐỘ)
# ==========================================
COURSE_LIST = [
    "Đồ án Nền Móng",
    "Cơ học Đất",
    "Kết cấu Bê tông Cốt thép",
    "Sức bền Vật liệu",
    "Kết cấu Thép / Khác",
]

with st.sidebar:
    st.markdown("### 🔀 Chức năng chính")
    c_nav1, c_nav2 = st.columns(2)
    with c_nav1:
        if st.button(
            "🏗️ Quy trình",
            type="primary" if st.session_state.main_view == "practice" else "secondary",
            use_container_width=True,
        ):
            st.session_state.main_view = "practice"
            st.rerun()
    with c_nav2:
        if st.button(
            "📚 Nhật ký",
            type="primary" if st.session_state.main_view == "library" else "secondary",
            use_container_width=True,
        ):
            st.session_state.main_view = "library"
            st.rerun()

    st.divider()
    st.markdown("### 🎓 Thông tin sinh viên")
    st.session_state.student_name = st.text_input(
        "Họ và tên", value=st.session_state.student_name, placeholder="VD: Nguyễn Văn A"
    )
    st.session_state.student_id = st.text_input(
        "Mã số sinh viên (MSSV)", value=st.session_state.student_id, placeholder="VD: 122000123"
    )
    st.session_state.course_name = st.selectbox(
        "Học phần / Đồ án",
        COURSE_LIST,
        index=COURSE_LIST.index(st.session_state.course_name)
        if st.session_state.course_name in COURSE_LIST
        else 0,
    )

    if st.session_state.main_view == "practice":
        st.divider()
        st.markdown("### 🧭 Tiến độ quy trình N.H.K.G")
        progress_val = 1.0 if st.session_state.g_completed else (st.session_state.unlocked_step - 1) / 4
        st.progress(progress_val, text=f"Hoàn thành {int(progress_val * 100)}%")

        step_labels = {
            1: "1. [N] Nhận diện vấn đề",
            2: "2. [H] Hỏi trợ lý AI",
            3: "3. [K] Kiểm chứng TCVN",
            4: "4. [G] Giải quyết & Minh chứng",
        }
        for s_num, s_label in step_labels.items():
            is_locked = s_num > st.session_state.unlocked_step
            prefix = (
                "🔒 "
                if is_locked
                else (
                    "✅ "
                    if (s_num < st.session_state.unlocked_step or (s_num == 4 and st.session_state.g_completed))
                    else "👉 "
                )
            )
            if st.button(
                f"{prefix}{s_label}",
                key=f"nav_btn_{s_num}",
                disabled=is_locked,
                use_container_width=True,
            ):
                st.session_state.active_step = s_num
                st.rerun()

        st.divider()
        if st.button("🔄 Làm bài tập mới (Reset)", use_container_width=True):
            reset_session()

    st.divider()
    if GSHEET_URL:
        st.caption("🟢 Đã bật tự động lưu nhật ký về Google Sheets.")
    else:
        st.caption("🟡 Chưa gắn GSHEET_WEBHOOK_URL trong Secrets.")

# ==========================================
# 5. BANNER ĐỒ HỌA CHUNG
# ==========================================
hero_svg = """
<svg class="hero-svg" width="124" height="88" viewBox="0 0 140 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="82" width="128" height="10" rx="3" fill="#F59E0B" fill-opacity="0.28" stroke="#FBBF24" stroke-width="1.8"/>
  <path d="M18 82L28 92M42 82L52 92M66 82L76 92M90 82L100 92M114 82L124 92" stroke="#FBBF24" stroke-width="1.4"/>
  <rect x="28" y="64" width="84" height="18" rx="2" fill="#38BDF8" fill-opacity="0.22" stroke="#7DD3FC" stroke-width="2"/>
  <rect x="54" y="20" width="32" height="44" rx="2" fill="#60A5FA" fill-opacity="0.25" stroke="#BAE6FD" stroke-width="2"/>
  <path d="M70 4V18M70 18L63 11M70 18L77 11" stroke="#FBBF24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="114" cy="26" r="14" fill="#10B981" fill-opacity="0.22" stroke="#34D399" stroke-width="2"/>
  <path d="M108 26L112.5 30.5L120.5 21.5" stroke="#6EE7B7" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

st.markdown(
    f"""
    <div class="hero-banner">
        <div>
            <div class="hero-badge">Khoa Kỹ thuật Công trình • ĐH Lạc Hồng</div>
            <h1 class="hero-title">TRỢ LÝ ẢO N.H.K.G – LÀM CHỦ AI TRONG ĐỒ ÁN XÂY DỰNG</h1>
            <p class="hero-subtitle">
                Hệ thống tự học có kiểm soát theo quy trình 4 bước: <b>Nhận diện</b> → <b>Hỏi</b> → <b>Kiểm chứng</b> → <b>Giải quyết</b>.<br>
                Tự động lưu nhật ký câu hỏi & kho minh chứng kiểm chứng TCVN để sinh viên tra cứu và học tập cùng nhau.
            </p>
        </div>
        {hero_svg}
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# CHẾ ĐỘ A: THƯ VIỆN HỎI - ĐÁP CỘNG ĐỒNG & NHẬT KÝ HỌC TẬP CÁ NHÂN
# =====================================================================
if st.session_state.main_view == "library":
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.subheader("📚 Kho Nhật ký Hỏi – Đáp & Kinh nghiệm kiểm chứng TCVN")
    with col_h2:
        if st.button("🔄 Tải mới dữ liệu", use_container_width=True):
            fetch_gsheet_logs.clear()
            st.rerun()

    records, err = fetch_gsheet_logs(GSHEET_URL)
    if err:
        st.warning(f"⚠️ {err}")
        st.info("Giảng viên cần dán đường dẫn Web App từ Google Apps Script vào mục `GSHEET_WEBHOOK_URL` trong Streamlit Secrets.")
        st.stop()

    mode = st.radio(
        "Chọn chế độ xem:",
        ["🌐 Thư viện chung của lớp (Ẩn danh để học cùng bạn)", "👤 Nhật ký cá nhân của tôi (Tra cứu theo MSSV)"],
        horizontal=True,
    )

    f1, f2, f3 = st.columns([1.2, 1.2, 1.6])
    with f1:
        filter_course = st.selectbox("Lọc theo học phần", ["Tất cả"] + COURSE_LIST)
    with f2:
        filter_type = st.selectbox(
            "Loại bản ghi",
            ["Tất cả", "Đã kiểm chứng TCVN (Bước G)", "Lượt Hỏi – Đáp AI (Bước H)"],
        )
    with f3:
        keyword = st.text_input("Tìm theo từ khóa", placeholder="VD: móng đơn, TCVN 2737, Plaxis, độ lún...")

    lookup_mssv = ""
    if mode.startswith("👤"):
        lookup_mssv = st.text_input(
            "Nhập chính xác MSSV của bạn để xem lịch sử cá nhân:",
            value=st.session_state.student_id,
            placeholder="VD: 122000123",
        ).strip()
        if not lookup_mssv:
            st.info("👆 Hãy nhập MSSV của bạn để tra cứu lại các câu hỏi và kết luận đã lưu.")
            st.stop()

    filtered = []
    kw = keyword.strip().lower()
    for rec in records:
        if filter_course != "Tất cả" and rec.get("hoc_phan") != filter_course:
            continue
        if filter_type == "Đã kiểm chứng TCVN (Bước G)" and rec.get("buoc") != "Hoan_Thanh_G":
            continue
        if filter_type == "Lượt Hỏi – Đáp AI (Bước H)" and rec.get("buoc") != "Hoi_Dap":
            continue
        if mode.startswith("👤") and rec.get("mssv", "").strip().lower() != lookup_mssv.lower():
            continue
        if kw:
            haystack = " ".join(
                [
                    rec.get("cau_hoi", ""),
                    rec.get("phan_hoi_ai", ""),
                    rec.get("kiem_chung", ""),
                    rec.get("ket_luan", ""),
                    rec.get("nhom_kho_khan", ""),
                ]
            ).lower()
            if kw not in haystack:
                continue
        filtered.append(rec)

    # Thống kê nhanh ngay trên giao diện
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng bản ghi phù hợp", len(filtered))
    m2.metric("Lượt Hỏi – Đáp AI", sum(1 for r in filtered if r.get("buoc") == "Hoi_Dap"))
    m3.metric("Bài đã kiểm chứng TCVN", sum(1 for r in filtered if r.get("buoc") == "Hoan_Thanh_G"))

    st.divider()
    if not filtered:
        st.info("Chưa có dữ liệu nhật ký nào khớp với bộ lọc hiện tại.")
    else:
        for idx, rec in enumerate(filtered):
            is_g = rec.get("buoc") == "Hoan_Thanh_G"
            tag_label = "✅ ĐÃ KIỂM CHỨNG TCVN (Bước G)" if is_g else "💬 HỎI – ĐÁP AI (Bước H)"
            short_q = (rec.get("cau_hoi") or "(Không có tiêu đề)").strip().replace("\n", " ")
            if len(short_q) > 95:
                short_q = short_q[:95] + "..."

            header_title = f"{tag_label} | {rec.get('hoc_phan', '')} — {short_q} ({rec.get('thoi_gian', '')})"
            with st.expander(header_title, expanded=(idx < 2)):
                badge_cls = "badge-g" if is_g else "badge-h"
                owner_info = (
                    f" • 👤 {html.escape(rec.get('ho_ten', ''))} ({html.escape(rec.get('mssv', ''))})"
                    if mode.startswith("👤")
                    else " • 👥 Chia sẻ ẩn danh"
                )
                st.markdown(
                    f'<span class="log-badge {badge_cls}">{tag_label}</span>'
                    f'<span style="font-size:13px; color:#475569;">'
                    f'Nhóm vấn đề: <b>{html.escape(rec.get("nhom_kho_khan", ""))}</b>{owner_info}</span>',
                    unsafe_allow_html=True,
                )

                if is_g:
                    st.markdown(f"**🎯 Điểm vướng mắc ban đầu [N]:** {rec.get('cau_hoi', '')}")
                    st.success(f"**🛡️ Nhật ký kiểm chứng TCVN & Mô phỏng [K]:**\n\n{rec.get('kiem_chung', '')}")
                    st.info(f"**✍️ Kết luận chuẩn hóa (1 Dòng) [G]:**\n\n{rec.get('ket_luan', '')}")
                else:
                    st.markdown(f"**❓ Câu hỏi của sinh viên:**\n\n{rec.get('cau_hoi', '')}")
                    st.markdown("**🤖 Gợi ý sư phạm từ Trợ lý N.H.K.G:**")
                    st.markdown(rec.get("phan_hoi_ai", ""))
    st.stop()

# =====================================================================
# CHẾ ĐỘ B: THỰC HÀNH QUY TRÌNH 4 BƯỚC N.H.K.G
# =====================================================================
steps_meta = [
    (1, "Bước N", "Nhận diện", "Tải ảnh đề & khoanh vùng chỗ bí"),
    (2, "Bước H", "Hỏi (Prompt)", "Hỏi phương pháp, không xin đáp án"),
    (3, "Bước K", "Kiểm chứng", "Đối chiếu TCVN & Plaxis/SAP2000"),
    (4, "Bước G", "Giải quyết", "Nộp minh chứng 1 Ảnh – 1 Dòng"),
]

stepper_html = '<div class="stepper-grid">'
for s_num, s_code, s_title, s_desc in steps_meta:
    if s_num < st.session_state.unlocked_step or (s_num == 4 and st.session_state.g_completed):
        cls, badge = "done", "✅ Đã hoàn thành"
    elif s_num == st.session_state.active_step:
        cls, badge = "active", "🔵 Đang thực hiện"
    elif s_num <= st.session_state.unlocked_step:
        cls, badge = "", "🔓 Đã mở khóa"
    else:
        cls, badge = "", "🔒 Đang khóa"

    stepper_html += f"""
    <div class="step-card {cls}">
        <div class="step-tag">{s_code} • {badge}</div>
        <div class="step-name">{s_title}</div>
        <div class="step-desc">{s_desc}</div>
    </div>
    """
stepper_html += "</div>"
st.markdown(stepper_html, unsafe_allow_html=True)

# ------------------------------------------
# BƯỚC 1: [N] NHẬN DIỆN VẤN ĐỀ + TẢI ẢNH ĐỀ
# ------------------------------------------
if st.session_state.active_step == 1:
    st.markdown(
        """
        <div class="section-box">
            <b>🎯 Yêu cầu mở khóa Bước N:</b> Tải lên ảnh chụp đề bài/bản vẽ (hoặc nhập tóm tắt đề) và tự chỉ rõ chỗ bạn đang vướng mắc.
            AI sẽ đọc đề bài để khoanh vùng kiến thức gốc và tiêu chuẩn liên quan, giúp bạn đặt câu hỏi chuẩn xác ở Bước H.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1.15], gap="large")

    with col_left:
        st.subheader("📷 1. Tải ảnh đề bài / sơ đồ tính")
        uploaded_problem = st.file_uploader(
            "Chọn ảnh chụp đề bài (PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"],
            key="uploader_step_n",
        )
        if uploaded_problem is not None:
            st.session_state.problem_img_bytes = uploaded_problem.getvalue()
            st.session_state.problem_img_mime = uploaded_problem.type
            st.session_state.problem_img_name = uploaded_problem.name

        if st.session_state.problem_img_bytes:
            st.image(
                st.session_state.problem_img_bytes,
                caption=f"Ảnh đề bài đã tải: {st.session_state.problem_img_name}",
                width=420,
            )
            if st.button("🗑️ Xóa ảnh đề bài này"):
                st.session_state.problem_img_bytes = None
                st.session_state.problem_img_mime = None
                st.session_state.problem_img_name = None
                st.rerun()
        else:
            st.info("Mẹo: Chụp rõ số liệu địa chất, tải trọng chân cột hoặc mặt cắt móng để AI nhận diện chính xác hơn.")

    with col_right:
        st.subheader("🧭 2. Tự khoanh vùng điểm vướng mắc")
        st.session_state.problem_text = st.text_area(
            "Nội dung đề bài bổ sung (tùy chọn nếu đã tải ảnh, bắt buộc nếu không tải ảnh)",
            value=st.session_state.problem_text,
            height=90,
            placeholder="VD: Móng đơn kích thước 2.4x2.8m đặt trên nền đất sét pha, tải trọng N = 1200 kN...",
        )
        issue_options = [
            "Hổng lý thuyết / Chưa biết chọn sơ đồ tính",
            "Chưa rõ công thức / Hệ số theo TCVN",
            "Bị kẹt ở bước tính toán trung gian",
            "Lỗi mô hình hóa trên Plaxis / SAP2000 / Optum",
        ]
        st.session_state.issue_type = st.selectbox(
            "Bạn đang gặp nhóm khó khăn nào?",
            issue_options,
            index=issue_options.index(st.session_state.issue_type)
            if st.session_state.issue_type in issue_options
            else 0,
        )
        st.session_state.stuck_point = st.text_area(
            "Mô tả cụ thể chỗ bạn đang bí (Bắt buộc ≥ 15 ký tự) *",
            value=st.session_state.stuck_point,
            height=110,
            placeholder="VD: Em chưa biết cách xác định chiều sâu vùng chịu nén Za khi tính lún theo phương pháp cộng lún từng lớp...",
        )

        if st.button("🔍 Phân tích đề bài & Xác nhận Bước N", type="primary", use_container_width=True):
            has_problem = bool(st.session_state.problem_img_bytes or st.session_state.problem_text.strip())
            if not has_problem:
                st.warning("⚠️ Bạn cần tải lên ít nhất 1 ảnh đề bài hoặc nhập nội dung đề bài.")
            elif len(st.session_state.stuck_point.strip()) < 15:
                st.warning("⚠️ Bạn hãy mô tả cụ thể hơn chỗ mình đang bí (ít nhất 15 ký tự).")
            else:
                n_prompt = (
                    f"Học phần: {st.session_state.course_name}\n"
                    f"Nhóm khó khăn: {st.session_state.issue_type}\n"
                    f"Nội dung đề bổ sung: {st.session_state.problem_text or 'Xem trong ảnh đính kèm'}\n"
                    f"Điểm sinh viên đang bí: {st.session_state.stuck_point}\n"
                    "Hãy phân tích Bước N (Nhận diện) theo đúng vai trò giảng viên gợi mở."
                )
                parts = [n_prompt]
                if st.session_state.problem_img_bytes:
                    parts.append(
                        types.Part.from_bytes(
                            data=st.session_state.problem_img_bytes,
                            mime_type=st.session_state.problem_img_mime or "image/jpeg",
                        )
                    )

                with st.spinner("🤖 Trợ lý N.H.K.G đang đọc ảnh đề bài và khoanh vùng kiến thức..."):
                    reply, err = call_gemini(parts, SYSTEM_INSTRUCTION_N)

                if reply:
                    st.session_state.n_ai_analysis = reply
                    st.session_state.unlocked_step = max(st.session_state.unlocked_step, 2)
                    st.rerun()
                elif err and ("503" in err or "UNAVAILABLE" in err):
                    st.warning("⏳ Máy chủ AI đang quá tải tạm thời. Bạn đợi 10–15 giây rồi bấm lại nhé!")
                else:
                    st.error(f"Lỗi kết nối AI: {err}")

    if st.session_state.n_ai_analysis:
        st.success("✅ Đã hoàn thành Bước N! Dưới đây là bản đồ kiến thức cần tập trung:")
        st.markdown(st.session_state.n_ai_analysis)
        if st.button("➡️ Tiếp tục sang Bước H (Hỏi trợ lý AI)", type="primary", use_container_width=True):
            st.session_state.active_step = 2
            st.rerun()

# ------------------------------------------
# BƯỚC 2: [H] HỎI (TỰ ĐỘNG LƯU LOG VỀ SHEETS)
# ------------------------------------------
elif st.session_state.active_step == 2:
    st.markdown(
        """
        <div class="section-box">
            <b>💬 Yêu cầu mở khóa Bước H:</b> Đặt câu hỏi tập trung vào <b>cách làm, trình tự tính và ý nghĩa công thức</b> (không xin đáp số).
            Mỗi lượt hỏi – đáp sẽ tự động lưu vào <b>Nhật ký học tập</b> để bạn xem lại bất cứ lúc nào.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📌 Xem lại đề bài & Nhận diện từ Bước N", expanded=False):
        c1, c2 = st.columns([1, 1.5])
        with c1:
            if st.session_state.problem_img_bytes:
                st.image(st.session_state.problem_img_bytes, width=320)
            if st.session_state.problem_text:
                st.write("**Đề bài:**", st.session_state.problem_text)
        with c2:
            st.write("**Điểm vướng mắc:**", st.session_state.stuck_point)
            st.markdown(st.session_state.n_ai_analysis)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
    if user_turns >= 1:
        st.success(f"Bạn đã trao đổi {user_turns} lượt với Trợ lý AI. Nếu đã nắm rõ phương pháp, hãy sang Bước K để kiểm chứng!")
        if st.button("🛡️ Đã nắm phương pháp → Chuyển sang Bước K (Kiểm chứng)", type="primary", use_container_width=True):
            st.session_state.unlocked_step = max(st.session_state.unlocked_step, 3)
            st.session_state.active_step = 3
            st.rerun()
    else:
        st.info("🔒 Hãy đặt ít nhất 1 câu hỏi về phương pháp giải bên dưới để mở khóa Bước K.")

    prompt = st.chat_input("Nhập câu hỏi về phương pháp (VD: Giải thích cách chia lớp phân tố khi tính lún?)")
    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        recent_history = "\n".join(
            f"{'Sinh viên' if m['role'] == 'user' else 'Trợ lý'}: {m['content']}"
            for m in st.session_state.messages[-6:]
        )
        full_prompt = (
            f"Bối cảnh Bước N ({st.session_state.course_name}):\n"
            f"- Đề bài: {st.session_state.problem_text or 'Xem ảnh đề bài đính kèm'}\n"
            f"- Điểm bí: {st.session_state.stuck_point}\n\n"
            f"Lịch sử trao đổi gần đây:\n{recent_history}\n\n"
            "Hãy trả lời câu hỏi mới nhất của sinh viên theo đúng quy tắc Bước H (gợi ý phương pháp, không giải hộ)."
        )
        parts = [full_prompt]
        if st.session_state.problem_img_bytes:
            parts.append(
                types.Part.from_bytes(
                    data=st.session_state.problem_img_bytes,
                    mime_type=st.session_state.problem_img_mime or "image/jpeg",
                )
            )

        with st.spinner("🤖 Trợ lý N.H.K.G đang soạn gợi ý sư phạm..."):
            reply, err = call_gemini(parts, SYSTEM_INSTRUCTION_H)

        if reply:
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_to_gsheet(buoc="Hoi_Dap", cau_hoi=prompt, phan_hoi_ai=reply)
            st.rerun()
        elif err and ("503" in err or "UNAVAILABLE" in err):
            st.warning("⏳ Máy chủ AI đang quá tải tạm thời. Bạn vui lòng đợi 10–15 giây rồi gửi lại câu hỏi nhé!")
        else:
            st.error(f"Lỗi kết nối AI: {err}")

# ------------------------------------------
# BƯỚC 3: [K] KIỂM CHỨNG QUA 3 MÀNG LỌC
# ------------------------------------------
elif st.session_state.active_step == 3:
    st.markdown(
        """
        <div class="section-box">
            <b>🛡️ Yêu cầu mở khóa Bước K (Màng lọc sống còn):</b> Không bao giờ tin tuyệt đối vào kết quả AI.
            Bạn phải đối chiếu qua đủ <b>3 màng lọc kỹ thuật</b> và ghi lại cụ thể điều mình đã kiểm tra (hoặc lỗi sai bắt được từ AI) để mở khóa Bước G.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### ⚖️ 1. Màng lọc Pháp lý")
        st.session_state.k_check_tcvn = st.checkbox(
            "Em đã đối chiếu công thức và hệ số với TCVN mới nhất (VD: TCVN 2737:2023, TCVN 10304:2014, TCVN 9362:2012).",
            value=st.session_state.k_check_tcvn,
        )
    with c2:
        st.markdown("#### 📐 2. Màng lọc Định lượng")
        st.session_state.k_check_quant = st.checkbox(
            "Em đã kiểm tra thứ nguyên (kN, m, kPa), bậc độ lớn và tính hợp lý vật lý của kết quả tính toán.",
            value=st.session_state.k_check_quant,
        )
    with c3:
        st.markdown("#### 💻 3. Màng lọc Mô phỏng")
        st.session_state.k_check_sim = st.checkbox(
            "Em đã kiểm chứng lại bằng tính tay độc lập hoặc chạy mô hình kiểm tra trên Plaxis / SAP2000 / Optum.",
            value=st.session_state.k_check_sim,
        )

    st.divider()
    st.session_state.k_note = st.text_area(
        "📝 Nhật ký kiểm chứng (Bắt buộc ≥ 20 ký tự): Ghi rõ mục TCVN đã tra cứu, giá trị đối chiếu hoặc lỗi sai phát hiện từ AI *",
        value=st.session_state.k_note,
        height=120,
        placeholder="VD: AI gợi ý hệ số tin cậy tải trọng theo TCVN 2737:1995 là 1.2, em đã tra lại Bảng 4 TCVN 2737:2023 và chỉnh lại; kiểm tra độ lún trên Plaxis ra 2.4 cm < [S] = 8 cm.",
    )

    all_checked = (
        st.session_state.k_check_tcvn
        and st.session_state.k_check_quant
        and st.session_state.k_check_sim
    )
    if st.button("✅ Xác nhận hoàn thành Bước K → Mở khóa Bước G", type="primary", use_container_width=True):
        if not all_checked:
            st.warning("⚠️ Bạn phải thực hiện và tích đủ cả 3 màng lọc (Pháp lý – Định lượng – Mô phỏng).")
        elif len(st.session_state.k_note.strip()) < 20:
            st.warning("⚠️ Hãy ghi chi tiết hơn nội dung bạn đã đối chiếu với TCVN hoặc phần mềm (ít nhất 20 ký tự).")
        else:
            st.session_state.unlocked_step = 4
            st.session_state.active_step = 4
            st.rerun()

# ------------------------------------------
# BƯỚC 4: [G] GIẢI QUYẾT & LƯU KẾT QUẢ KIỂM CHỨNG
# ------------------------------------------
elif st.session_state.active_step == 4:
    st.markdown(
        """
        <div class="section-box">
            <b>🎓 Yêu cầu Bước G (Luật "1 Ảnh – 1 Dòng"):</b> Tải lên <b>1 ảnh minh chứng</b> kèm <b>1 dòng kết luận</b> chuẩn theo TCVN.
            Kết quả kiểm chứng sẽ được lưu vào hệ thống thống kê và xuất <b>Phiếu Minh Chứng</b> để bạn nộp lên Canvas LMS.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_g1, col_g2 = st.columns([1, 1.2], gap="large")
    with col_g1:
        st.subheader("🖼️ 1 Ảnh minh chứng")
        evidence_file = st.file_uploader(
            "Tải ảnh chụp màn hình minh chứng (PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"],
            key="uploader_step_g",
        )
        if evidence_file is not None:
            st.session_state.g_img_bytes = evidence_file.getvalue()
            st.session_state.g_img_mime = evidence_file.type
            st.session_state.g_img_name = evidence_file.name

        if st.session_state.g_img_bytes:
            st.image(
                st.session_state.g_img_bytes,
                caption=f"Ảnh minh chứng: {st.session_state.g_img_name}",
                width=420,
            )

    with col_g2:
        st.subheader("✍️ 1 Dòng kết luận chuẩn hóa")
        st.session_state.g_conclusion = st.text_area(
            "Ghi ngắn gọn giải pháp cuối cùng sau khi đã kiểm chứng (≥ 15 ký tự) *",
            value=st.session_state.g_conclusion,
            height=130,
            placeholder="VD: Đã chỉnh lại hệ số độ tin cậy theo TCVN 2737:2023 và kiểm tra độ lún móng đơn S = 2.4 cm đạt điều kiện theo TCVN 9362:2012.",
        )

        if st.button("🏆 Hoàn tất quy trình & Xuất Phiếu Minh Chứng", type="primary", use_container_width=True):
            if not st.session_state.g_img_bytes:
                st.warning("⚠️ Bạn cần tải lên 1 ảnh minh chứng theo quy tắc '1 Ảnh – 1 Dòng'.")
            elif len(st.session_state.g_conclusion.strip()) < 15:
                st.warning("⚠️ Hãy viết rõ 1 dòng kết luận chuẩn hóa (ít nhất 15 ký tự).")
            else:
                st.session_state.g_timestamp = vn_now_str()
                st.session_state.g_completed = True
                save_to_gsheet(
                    buoc="Hoan_Thanh_G",
                    cau_hoi=st.session_state.stuck_point,
                    phan_hoi_ai=f"Hoàn tất sau {sum(1 for m in st.session_state.messages if m['role'] == 'user')} lượt hỏi AI",
                    kiem_chung=st.session_state.k_note,
                    ket_luan=st.session_state.g_conclusion,
                )
                st.rerun()

    if st.session_state.g_completed:
        st.divider()
        st.balloons()

        s_name = st.session_state.student_name.strip() or "(Chưa nhập họ tên ở thanh bên trái)"
        s_id = st.session_state.student_id.strip() or "Chua_nhap_MSSV"
        q_count = sum(1 for m in st.session_state.messages if m["role"] == "user")

        st.markdown(
            f"""
            <div class="cert-card">
                <div class="cert-header">
                    <h3 style="margin:0; color:#0f766e;">🏅 PHIẾU MINH CHỨNG TỰ HỌC QUY TRÌNH N.H.K.G</h3>
                    <div style="font-size:13px; color:#475569; margin-top:4px;">
                        Khoa Kỹ thuật Công trình – Trường Đại học Lạc Hồng | Thời gian hoàn tất: <b>{st.session_state.g_timestamp}</b>
                    </div>
                </div>
                <p><b>Sinh viên:</b> {html.escape(s_name)} &nbsp;|&nbsp; <b>MSSV:</b> {html.escape(s_id)} &nbsp;|&nbsp; <b>Học phần:</b> {html.escape(st.session_state.course_name)}</p>
                <p><b>[N] Điểm nhận diện vướng mắc:</b> {html.escape(st.session_state.stuck_point)}</p>
                <p><b>[H] Số lượt đặt câu hỏi phương pháp với AI:</b> {q_count} lượt</p>
                <p><b>[K] Nhật ký kiểm chứng TCVN & Mô phỏng:</b> {html.escape(st.session_state.k_note)}</p>
                <p><b>[G] Kết luận chuẩn hóa (1 Dòng):</b> {html.escape(st.session_state.g_conclusion)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        img_b64 = base64.b64encode(st.session_state.g_img_bytes).decode("utf-8")
        img_mime = st.session_state.g_img_mime or "image/png"
        report_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Phieu Minh Chung NHKG - {html.escape(s_id)}</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 820px; margin: 28px auto; color: #0f172a; line-height: 1.6; }}
  .box {{ border: 2px solid #0f766e; border-radius: 12px; padding: 24px 28px; }}
  h2 {{ color: #0f766e; margin-top: 0; }}
  .meta {{ color: #475569; font-size: 14px; border-bottom: 1px dashed #cbd5e1; padding-bottom: 10px; margin-bottom: 14px; }}
  img {{ max-width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; }}
</style>
</head>
<body>
  <div class="box">
    <h2>PHIẾU MINH CHỨNG TỰ HỌC QUY TRÌNH N.H.K.G</h2>
    <div class="meta">Khoa Kỹ thuật Công trình – Trường Đại học Lạc Hồng | Hoàn tất lúc: {st.session_state.g_timestamp}</div>
    <p><b>Sinh viên:</b> {html.escape(s_name)} &nbsp;|&nbsp; <b>MSSV:</b> {html.escape(s_id)} &nbsp;|&nbsp; <b>Học phần:</b> {html.escape(st.session_state.course_name)}</p>
    <p><b>1. [N] Nhận diện vấn đề:</b> {html.escape(st.session_state.stuck_point)}</p>
    <p><b>2. [H] Quá trình hỏi AI:</b> Đã thực hiện {q_count} lượt trao đổi định hướng phương pháp.</p>
    <p><b>3. [K] Kiểm chứng TCVN & Mô phỏng:</b> {html.escape(st.session_state.k_note)}</p>
    <p><b>4. [G] Kết luận chuẩn hóa (1 Dòng):</b> {html.escape(st.session_state.g_conclusion)}</p>
    <p><b>Ảnh minh chứng đính kèm (1 Ảnh):</b></p>
    <img src="data:{img_mime};base64,{img_b64}" alt="Anh minh chung NHKG" />
  </div>
</body>
</html>"""

        st.download_button(
            label="📥 Tải Phiếu Minh Chứng (.html) để nộp lên Canvas LMS",
            data=report_html.encode("utf-8"),
            file_name=f"Phieu_NHKG_{s_id}.html",
            mime="text/html",
            use_container_width=True,
        )