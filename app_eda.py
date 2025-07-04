import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Population Trends 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population Trends 데이터셋**  
                - 제공처: 통계청 등 공공기관  
                - 설명: 2008년부터 전국 및 광역자치단체별 인구, 출생아 수, 사망자 수를 연도별로 기록한 데이터  
                - 주요 변수:  
                  - `Year`: 연도 (YYYY)  
                  - `Region`: 지역명 (광역자치단체)  
                  - `Population`: 연도별 인구 수 (명)  
                  - `Births`: 해당 연도 출생아 수 (명)  
                  - `Deaths`: 해당 연도 사망자 수 (명)  
                """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        import streamlit as st
        import pandas as pd
        import numpy as np

        # ────────────────────────────────────────────────────
        # 1) 지역별 인구 분석 EDA
        # ────────────────────────────────────────────────────

        st.title("📊 지역별 인구 분석 EDA")

        # 로컬에 올려둔 population_trends.csv 파일을 바로 읽어옵니다.
        pop = pd.read_csv("population_trends.csv")

        # 한글 컬럼명을 영어로 바꿔 줍니다.
        pop = pop.rename(columns={
            "연도": "Year",
            "지역": "Region",
            "인구": "Population",
            "출생아수(명)": "Births",
            "사망자수(명)": "Deaths"
        })

        # 연도 컬럼을 datetime 타입으로 변환
        pop["Year"] = pd.to_datetime(pop["Year"], format="%Y")

        # 탭 정의: A~E
        tabs = st.tabs([
            "A. 품질 체크",
            "B. 전국 추이",
            "C. 변화량 순위",
            "D. 증감률 상위",
            "E. 누적 영역"
        ])

        # A) 품질 체크
        with tabs[0]:
            st.header("🔍 품질 체크")
            st.write("결측치 개수:", pop.isnull().sum().to_dict())
            st.write("중복 행 개수:", int(pop.duplicated().sum()))

        # B) 전국 인구 추이
        with tabs[1]:
            st.header("🌐 전국 인구 추이")
            national = pop.loc[pop["Region"] == "전국", ["Year", "Population"]]
            national = national.set_index("Year")
            st.line_chart(national["Population"])

        # C) 변화량 순위 (최근 2년)
        with tabs[2]:
            st.header("📊 최근 2년 인구 변화량 순위")
            pivot = pop.pivot(index="Region", columns="Year", values="Population")
            years = sorted(pivot.columns)
            if len(years) >= 2:
                diff = pivot[years[-1]] - pivot[years[-2]]
                st.bar_chart(diff.sort_values(ascending=False) / 1_000,
                             use_container_width=True)
            else:
                st.info("연도 데이터가 2개 이상 필요합니다.")

        # D) 증감률 상위 5개
        with tabs[3]:
            st.header("📈 연도별 인구 증감률 상위 5개 (년도별)")

    # 1) 0 → NaN 으로 바꿔서 pct_change 계산 (inf 방지)
            tmp = pop.copy()
            tmp["Population"].replace(0, np.nan, inplace=True)
            tmp["pct_change"] = tmp.groupby("Region")["Population"].pct_change() * 100

    # 2) 연도 목록을 정렬해서 가져오기 (처음 연도는 변화량이 없으므로 제외)
            years = sorted(tmp["Year"].dt.year.unique())
            target_years = years[1:]  # 2번째 연도부터 시작

    # 3) 연도별로 탑5 뽑아내기
            for yr in target_years:
                st.subheader(f"{yr}년 증감률 상위 5개")
        # 해당 연도만 뽑아서 pct_change 기준 내림차순 정렬
                df_yr = tmp[tmp["Year"].dt.year == yr].dropna(subset=["pct_change"])
                top5 = df_yr.nlargest(5, "pct_change")[["Region", "pct_change"]]

        # % 포맷팅
                top5["pct_change"] = top5["pct_change"].map(lambda x: f"{x:.2f}%")
        
        # 테이블 출력
                st.table(top5.reset_index(drop=True))
        
        # E) 누적 영역 그래프
        with tabs[4]:
            st.header("📑 누적 영역 그래프")
            area_df = pop.pivot(index="Year", columns="Region", values="Population").fillna(0)
            st.area_chart(area_df)

# ─────────────────────────────────────────────────────────────────
# 스크립트 맨 아래에, 페이지 객체 생성/실행
# ─────────────────────────────────────────────────────────────────




# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
