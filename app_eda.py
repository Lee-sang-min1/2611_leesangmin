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
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
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
        # -----------------------
        # Bike-Sharing Demand EDA
        # -----------------------
        st.title("📊 Bike-Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환"
        ])

        # 1) 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터를 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.

            **절차**:
            1. 데이터 구조 및 기초 통계 확인  
            2. 결측치/중복치 등 품질 체크  
            3. datetime 특성 추출  
            4. 주요 변수 시각화  
            5. 변수 간 상관관계 분석  
            6. 이상치 탐지 및 제거  
            7. 로그 변환  
            """)

        # 2) 데이터셋 설명
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"""
            - **train.csv**: 2011–2012년의 시간대별 자전거 대여 기록  
            - 관측치 수: {df.shape[0]}개  
            - 주요 변수: datetime, season, holiday, workingday, weather, temp, atemp, humidity, windspeed, casual, registered, count
            """)
            buf = io.StringIO()
            df.info(buf=buf); st.text(buf.getvalue())
            st.subheader("기초 통계량"); st.dataframe(df.describe())
            st.subheader("샘플 데이터"); st.dataframe(df.head())

        # 3) 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("📥 데이터 로드 & 품질 체크")
            missing = df.isnull().sum(); st.bar_chart(missing)
            dupes = df.duplicated().sum(); st.write(f"- 중복 행: {dupes}개")

        # 4) Datetime 특성 추출
        with tabs[3]:
            st.header("🕒 Datetime 특성 추출")
            df['year']      = df['datetime'].dt.year
            df['month']     = df['datetime'].dt.month
            df['day']       = df['datetime'].dt.day
            df['hour']      = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek
            st.dataframe(df[['datetime','year','month','day','hour','dayofweek']].head())

        # 5) 시각화
        with tabs[4]:
            st.header("📈 시각화")
            fig1, ax1 = plt.subplots(); sns.pointplot(x='hour', y='count', hue='workingday', data=df, ax=ax1)
            ax1.set_xlabel("Hour"); ax1.set_ylabel("Count"); st.pyplot(fig1)
            # (이하 생략—원하시는 차트 그대로 유지)

        # 6) 상관관계 분석
        with tabs[5]:
            st.header("🔗 상관관계 분석")
            cols = ['temp','atemp','casual','registered','humidity','windspeed','count']
            corr = df[cols].corr()
            st.dataframe(corr)
            fig2, ax2 = plt.subplots(figsize=(6,5)); sns.heatmap(corr, annot=True, fmt=".2f", ax=ax2); st.pyplot(fig2)

        # 7) 이상치 제거
        with tabs[6]:
            st.header("🚫 이상치 제거")
            m, s = df['count'].mean(), df['count'].std()
            thresh = m + 3*s
            st.write(f"평균={m:.1f}, 표준편차={s:.1f}, 이상치 기준>{thresh:.1f}")
            df_no = df[df['count'] <= thresh]
            st.write(f"- 제거 전: {df.shape[0]} / 제거 후: {df_no.shape[0]}")

        # 8) 로그 변환
        with tabs[7]:
            st.header("🔄 로그 변환")
            fig3, axes = plt.subplots(1,2,figsize=(10,4))
            sns.histplot(df['count'], kde=True, ax=axes[0]); axes[0].set_title("Original")
            df['log_count'] = np.log1p(df['count'])
            sns.histplot(df['log_count'], kde=True, ax=axes[1]); axes[1].set_title("Log+1")
            st.pyplot(fig3)

        # --------------------------------------------
        # 추가: 지역별 인구 분석 EDA (별도 pop_tabs 정의)
        # --------------------------------------------
        st.markdown("---")
        st.header("📈 지역별 인구 분석 EDA")

        pop = pd.read_csv("population_trends.csv")
        pop = pop.rename(columns={"연도":"Year","지역":"Region","인구":"Population"})

        pop_tabs = st.tabs([
            "9. 품질 체크",
            "10. 전국 추이",
            "11. 변화량 순위",
            "12. 증감률 상위",
            "13. 누적 영역"
        ])

        # 9) 품질 체크
        with pop_tabs[0]:
            st.subheader("🔍 품질 체크")
            st.write("결측치:", pop.isnull().sum().to_dict())
            st.write("중복 행:", int(pop.duplicated().sum()))

        # 10) 전국 추이
        with pop_tabs[1]:
            st.subheader("📈 연도별 전국 인구 추이")
            tot = pop.groupby("Year")["Population"].sum().reset_index().set_index("Year")
            st.line_chart(tot, height=300)

        # 11) 변화량 순위
        with pop_tabs[2]:
            st.subheader("📊 변화량 순위 (직전 vs 최종)")
            yrs = sorted(pop["Year"].unique())
            if len(yrs)>=2:
                p, l = yrs[-2], yrs[-1]
                piv = pop.pivot(index="Region",columns="Year",values="Population")
                d = (piv[l]-piv[p]).sort_values(ascending=False)
                st.bar_chart(d, height=300)
            else:
                st.info("연도 데이터 2개 필요")

        # 12) 증감률 상위
        with pop_tabs[3]:
            st.subheader("🏆 증감률 상위 5개 지역")
            tmp = pop.copy()
            tmp["pct_change"] = tmp.groupby("Region")["Population"].pct_change()*100
            top5 = tmp.nlargest(5,"pct_change")[["Region","Year","pct_change"]]
            st.table(top5.style.format({"pct_change":"{:.2f}%"}))

        # 13) 누적 영역
        with pop_tabs[4]:
            st.subheader("🌐 누적 영역 그래프")
            ar = pop.pivot(index="Year",columns="Region",values="Population").fillna(0)
            st.area_chart(ar, height=300)




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
