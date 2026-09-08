from datetime import datetime, date, time
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 페이지 설정
st.set_page_config(page_title="우리 아기 투약 & 체온 공유", page_icon="👶", layout="centered")

# ---------------------------------------------------------
# 디자인을 위한 커스텀 CSS (카드형 UI, 깔끔한 폰트 및 간격 조정)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    div.stForm {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 로그인 (비밀번호 설정)
# ---------------------------------------------------------
CORRECT_PASSWORD = "0318"  # 원하시는 비밀번호로 변경 가능

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("👶 우리 아기 투약 & 체온 기록")
    st.info("부부만 접속할 수 있도록 비밀번호를 입력해 주세요.")

    with st.form("login_form"):
        input_pw = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("로그인")

        if login_btn:
            if input_pw == CORRECT_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다. 다시 확인해 주세요.")
    st.stop()

# ---------------------------------------------------------
# 2. 구글 시트 연결 함수
# ---------------------------------------------------------
def init_google_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("아기체온기록").sheet1
    return sheet

# ---------------------------------------------------------
# 3. 메인 앱 화면
# ---------------------------------------------------------
st.title("👶 우리 아기 케어 기록장")
st.caption("✨ 남편과 실시간으로 연동되며 구글 시트에 안전하게 저장됩니다.")

try:
    sheet = init_google_sheet()
except Exception as e:
    st.error("구글 시트 연결에 실패했습니다. Streamlit Secrets 설정을 확인해 주세요.")
    st.stop()

# 입력 섹션 (카드 폼 안에서 작성)
with st.form("record_form", clear_on_submit=True):
    st.markdown("### 📝 새로운 기록 남기기")
    
    # 1. 날짜 및 시간을 최상단으로 배치
    col3, col4 = st.columns(2)
    with col3:
        record_date = st.date_input("📅 기록 날짜", value=date.today())
    with col4:
        record_time = st.time_input("⏰ 기록 시간", value=datetime.now().time())

    st.markdown("---")

    # 2. 체온 및 투약 종류
    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("🌡️ 체온 (°C)", min_value=35.0, max_value=42.0, value=37.5, step=0.1)
    with col2:
        medicine = st.selectbox("💊 투약 종류", ["없음", "아세트아미노펜", "이부프로펜/덱시부프로펜"])

    memo = st.text_input("💬 특이사항 / 메모", placeholder="예: 떡뻥 잘 먹음, 땀 많이 남")

    submitted = st.form_submit_button("💾 기록 저장하기")
    if submitted:
        combined_dt = datetime.combine(record_date, record_time)
        formatted_time = combined_dt.strftime("%m/%d %H:%M")
        
        # 구글 시트에 행 추가
        sheet.append_row([formatted_time, str(temp), medicine, memo])
        st.success("기록이 안전하게 저장되었습니다!")
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------
# 4. 실시간 기록장 및 삭제 기능
# ---------------------------------------------------------
st.subheader("📋 실시간 기록장")

try:
    # 전체 데이터를 가져옴 (각 행의 index 정보 활용을 위해 enumerate 사용)
    all_values = sheet.get_all_values()
    
    if len(all_values) <= 1:
        st.info("아직 기록이 없습니다. 위에서 체온과 투약을 기록해 보세요!")
    else:
        headers = all_values[0]  # ['시간', '체온', '투약종류', '메모']
        rows = all_values[1:]    # 실제 데이터들
        
        # 최신 기록이 위로 오도록 인덱스와 함께 역순 정렬
        indexed_rows = list(enumerate(rows, start=2)) # 실제 구글 시트 행 번호는 2부터 시작
        
        for sheet_row_idx, row in reversed(indexed_rows):
            time_val, temp_val, med_val, memo_val = row[0], row[1], row[2], row[3]
            
            # 카드 박스 형태로 이쁘게 출력
            with st.container():
                col_info, col_del = st.columns([5, 1])
                
                with col_info:
                    med_badge = f"💊 **{med_val}**" if med_val != "없음" else "✨ 투약 없음"
                    st.markdown(f"🗓️ **{time_val}** &nbsp;|&nbsp; 🌡️ **{temp_val}°C** &nbsp;|&nbsp; {med_badge}")
                    if memo_val:
                        st.caption(f"└ 📝 메모: {memo_val}")
                
                with col_del:
                    # 각 기록별 고유 삭제 버튼
                    if st.button("🗑️ 삭제", key=f"del_{sheet_row_idx}"):
                        sheet.delete_rows(sheet_row_idx)
                        st.success("기록이 삭제되었습니다.")
                        st.rerun()
                        
                st.markdown("---")

except Exception as e:
    st.warning("기록을 불러오는 중 문제가 발생했습니다.")

# 로그아웃 버튼
if st.sidebar.button("로그아웃"):
    st.session_state.authenticated = False
    st.rerun()
