from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="우리 아기 투약 & 체온 공유", page_icon="👶")

# ---------------------------------------------------------
# 1. 로그인 (비밀번호 설정)
# ---------------------------------------------------------
CORRECT_PASSWORD = "1234"  # 원하시는 비밀번호로 변경하세요

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
# 2. 구글 시트 연결 함수 (Streamlit Secrets 활용)
# ---------------------------------------------------------
def init_google_sheet():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  # Streamlit Secrets에 저장된 서비스 계정 키를 불러옵니다.
  creds_dict = dict(st.secrets["gcp_service_account"])
  creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
  client = gspread.authorize(creds)
  # 구글 시트 제목을 정확히 입력해주세요
  sheet = client.open("아기체온기록").sheet1
  return sheet


# ---------------------------------------------------------
# 3. 메인 앱 화면
# ---------------------------------------------------------
st.title("👶 우리 아기 투약 & 체온 실시간 공유")
st.caption("구글 시트와 연동되어 기록이 영구 저장됩니다.")

try:
  sheet = init_google_sheet()
except Exception as e:
  st.error(
      "구글 시트 연결에 실패했습니다. Streamlit Secrets 설정(지정된 시트 이름"
      " 및 키)을 확인해 주세요."
  )
  st.stop()

# 입력 섹션
with st.form("record_form", clear_on_submit=True):
  col1, col2 = st.columns(2)
  with col1:
    temp = st.number_input(
        "체온 (°C)", min_value=35.0, max_value=42.0, value=37.5, step=0.1
    )
  with col2:
    medicine = st.selectbox(
        "투약 종류", ["없음", "아세트아미노펜", "이부프로펜/덱시부프로펜"]
    )

  memo = st.text_input(
      "특이사항 / 메모", placeholder="예: 떡뻥 잘 먹음, 땀 많이 남"
  )

  submitted = st.form_submit_button("기록 저장하기")
  if submitted:
    current_time = datetime.now().strftime("%m/%d %H:%M")
    # 구글 시트에 행 추가
    sheet.append_row([current_time, str(temp), medicine, memo])
    st.success("기록이 구글 시트에 안전하게 저장되었습니다!")
    st.rerun()

st.divider()

# ---------------------------------------------------------
# 4. 구글 시트에서 기록 불러와서 보여주기
# ---------------------------------------------------------
st.subheader("📋 실시간 기록장")

try:
  # 시트의 모든 데이터를 가져옴 (1행 제목 제외하고 최신순 정렬)
  rows = sheet.get_all_records()
  if not rows:
    st.info("아직 기록이 없습니다. 위에서 체온과 투약을 기록해 보세요!")
  else:
    # 최신 기록이 위로 오도록 뒤집기
    for item in reversed(rows):
      med_badge = (
          f"💊 {item['투약종류']}" if item["투약종류"] != "없음" else ""
      )
      st.markdown(
          f"**[{item['시간']}]** 체온: **{item['체온']}°C** {med_badge}"
      )
      if item["메모"]:
        st.caption(f"📝 메모: {item['메모']}")
      st.markdown("---")
except Exception as e:
  st.warning("기록을 불러오는 중 문제가 발생했습니다.")

# 로그아웃 버튼
if st.sidebar.button("로그아웃"):
  st.session_state.authenticated = False
  st.rerun()