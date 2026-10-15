import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="🏘️",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 함수 (캐싱 적용으로 로딩 속도 향상)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 데이터셋 URL (ZIP 압축 파일 형태의 CSV)
    url = "https://raw.githubusercontent.com/koloramax-goedu/seowonhs-data/main/population_ts_yearly_gender.zip"
    
    # 판다스로 CSV 데이터 읽어오기
    df = pd.read_csv(url)
    
    # 데이터셋 내 가장 최신 연도 추출 및 필터링
    latest_year = int(df['연도'].max())
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 실행
try:
    df, latest_year = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 메인 화면 타이틀
# -----------------------------------------------------------------------------
st.title("🏘️ 우리 동네 인구 피라미드")
st.markdown(f"**{latest_year}년 최신 데이터**를 기준으로 지역별 연령 및 성별 인구 구조를 살펴봅니다. ☀️")
st.divider()

# -----------------------------------------------------------------------------
# 4. 상단 드롭다운 3개 (시·도 ➔ 시·군·구 ➔ 읍·면·동 선택)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

# 1단계: 시·도 선택
sido_list = sorted(df['시도'].dropna().unique())
with col1:
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 2단계: 선택한 시·도에 해당하는 시·군·구 선택
filtered_sido_df = df[df['시도'] == selected_sido]
sigungu_list = sorted(filtered_sido_df['시군구'].dropna().unique())
with col2:
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 3단계: 선택한 시·군·구에 해당하는 읍·면·동 선택
filtered_sigungu_df = filtered_sido_df[filtered_sido_df['시군구'] == selected_sigungu]
dong_list = sorted(filtered_sigungu_df['동'].dropna().unique())
with col3:
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# -----------------------------------------------------------------------------
# 5. 선택한 지역 데이터 연산 (인구수, 평균연령, 고령화율)
# -----------------------------------------------------------------------------
# 최종 선택된 동의 데이터 필터링
target_df = filtered_sigungu_df[filtered_sigungu_df['동'] == selected_dong]

# 컬럼명에서 숫자(나이)만 추출하는 함수
def get_age_num(col_name):
    clean_str = col_name.replace('남_', '').replace('여_', '').replace('세', '').replace(' 이상', '').strip()
    try:
        return int(clean_str)
    except ValueError:
        return 0

# '남_'으로 시작하는 컬럼을 나이 순서대로 정렬 (0세 -> 100세 이상)
male_cols = sorted([col for col in df.columns if col.startswith('남_')], key=get_age_num)
female_cols = [col.replace('남_', '여_') for col in male_cols]
age_labels = [col.replace('남_', '') for col in male_cols]
age_numbers = [get_age_num(col) for col in male_cols]

# 선택 지역의 남/여 인구 수 수집
male_values = target_df[male_cols].sum().values
female_values = target_df[female_cols].sum().values
total_values = male_values + female_values

# ① 총인구
total_pop = int(total_values.sum())

# ② 평균연령 (가중평균 계산)
if total_pop > 0:
    weighted_age_sum = sum(pop * age for pop, age in zip(total_values, age_numbers))
    avg_age = weighted_age_sum / total_pop
else:
    avg_age = 0.0

# ③ 유소년(0~14세) 및 고령인구(65세 이상)
youth_pop = sum(pop for pop, age in zip(total_values, age_numbers) if age <= 14)
elderly_pop = sum(pop for pop, age in zip(total_values, age_numbers) if age >= 65)

# 고령화율 (%)
elderly_rate = (elderly_pop / total_pop * 100) if total_pop > 0 else 0.0
# 유소년 비율 (%)
youth_rate = (youth_pop / total_pop * 100) if total_pop > 0 else 0.0

# -----------------------------------------------------------------------------
# 6. 상단 지표 카드 3개 (총인구, 평균연령, 고령화율)
# -----------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"### 📊 **{selected_sido} {selected_sigungu} {selected_dong}** 주요 지표")

card_col1, card_col2, card_col3 = st.columns(3)

# 지표 카드 1: 총인구
card_col1.metric(
    label="👥 총인구",
    value=f"{total_pop:,} 명"
)

# 지표 카드 2: 평균연령
card_col2.metric(
    label="🎂 평균연령",
    value=f"{avg_age:.1f} 세"
)

# 지표 카드 3: 고령화율 (20% 이상일 경우 주의 표시)
if elderly_rate >= 20.0:
    card_col3.metric(
        label="👵 고령화율 (65세 이상)",
        value=f"{elderly_rate:.1f}%",
        delta="⚠️ 초고령사회 (20% 이상)",
        delta_color="inverse"
    )
else:
    card_col3.metric(
        label="👵 고령화율 (65세 이상)",
        value=f"{elderly_rate:.1f}%"
    )

# 고령화율 20% 초과 시 추가 주의 메시지 배너 표시
if elderly_rate >= 20.0:
    st.warning(f"⚠️ **주의:** **{selected_dong}**은(는) 65세 이상 인구 비율이 **{elderly_rate:.1f}%**로 **초고령사회 기준(20% 이상)**을 넘었습니다.")

st.divider()

# -----------------------------------------------------------------------------
# 7. Plotly 가로 막대 그래프 (인구 피라미드) 생성
# -----------------------------------------------------------------------------

# 남자는 왼쪽 방향 표시를 위해 인구수를 음수로 변환
male_neg_values = [-val for val in male_values]

fig = go.Figure()

# 남자 데이터 막대 (왼쪽)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_neg_values,
    name='남성',
    orientation='h',
    marker_color='#4A90E2',   # 차분한 푸른색
    customdata=male_values,    # 툴팁에 표시할 양수 실제 값
    hovertemplate='<b>%{y}</b><br>남성 인구: %{customdata:,}명<extra></extra>'
))

# 여자 데이터 막대 (오른쪽)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_values,
    name='여성',
    orientation='h',
    marker_color='#FF6B6B',   # 따뜻한 분홍색
    customdata=female_values,
    hovertemplate='<b>%{y}</b><br>여성 인구: %{customdata:,}명<extra></extra>'
))

# X축 눈금 설정 (음수 값을 양수 레이블로 보정)
max_val = max(max(male_values, default=0), max(female_values, default=0))
if max_val == 0:
    max_val = 100

tick_step = max(1, int(max_val / 4))
tick_vals = list(range(-tick_step * 4, tick_step * 5, tick_step))
tick_text = [f"{abs(v):,}" for v in tick_vals]

# -----------------------------------------------------------------------------
# 축 레이아웃 고정 설정
# - categoryorder='array' 및 categoryarray=age_labels를 설정하여
#   0세가 맨 아래, 100세 이상이 맨 위에 위치하도록 순서 고정
# -----------------------------------------------------------------------------
fig.update_layout(
    title=dict(
        text=f"<b>{selected_dong} 연령별 인구 피라미드 ({latest_year}년)</b>",
        font=dict(size=20)
    ),
    xaxis=dict(
        title="인구 수 (명)",
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_text,
        zeroline=True,
        zerolinecolor='#888888',
        zerolinewidth=1.5
    ),
    yaxis=dict(
        title="나이",
        type='category',
        categoryorder='array',
        categoryarray=age_labels  # '0세'가 맨 아래, '100세 이상'이 맨 위에 배치
    ),
    barmode='relative',
    bargap=0.1,
    height=850,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(l=60, r=40, t=80, b=40)
)

# Plotly 그래프 화면 출력
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 8. 피라미드 하단 자동 한 줄 설명
# -----------------------------------------------------------------------------
st.subheader("❓ 이 동네는 아이가 많은 편인가요, 어르신이 많은 편인가요?")

# 아이(0~14세) 비율 vs 어르신(65세 이상) 비율 비교 및 자동 문구 생성
if youth_rate > elderly_rate:
    insight_text = (
        f"💡 **분석 결과:** **{selected_dong}**은(는) 유소년 인구(0~14세) 비율이 **{youth_rate:.1f}%**로 "
        f"고령 인구(65세 이상, **{elderly_rate:.1f}%**)보다 높아 **아이가 상대적으로 많은 젊은 동네**입니다. 🎈"
    )
elif elderly_rate > youth_rate:
    insight_text = (
        f"💡 **분석 결과:** **{selected_dong}**은(는) 고령 인구(65세 이상) 비율이 **{elderly_rate:.1f}%**로 "
        f"유소년 인구(0~14세, **{youth_rate:.1f}%**)보다 높아 **어르신이 상대적으로 많은 동네**입니다. 🍵"
    )
else:
    insight_text = (
        f"💡 **분석 결과:** **{selected_dong}**은(는) 유소년 인구(**{youth_rate:.1f}%**)와 "
        f"고령 인구(**{elderly_rate:.1f}%**)의 비율이 서로 비슷한 균형적인 동네입니다. ⚖️"
    )

st.info(insight_text)
