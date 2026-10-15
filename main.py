import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 (따뜻하고 직관적인 구성)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="🏘️",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 함수 (캐싱을 적용하여 데이터 로딩 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 데이터셋 URL (ZIP 압축 파일 형태의 CSV)
    url = "https://raw.githubusercontent.com/koloramax-goedu/seowonhs-data/main/population_ts_yearly_gender.zip"
    
    # 판다스 read_csv는 zip 파일 안의 csv를 자동으로 감지해서 불러옵니다.
    df = pd.read_csv(url)
    
    # 데이터셋 내 가장 최신 연도를 자동으로 파악 후 최신 연도 데이터만 필터링
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
# 3. 메인 화면 타이틀 영역
# -----------------------------------------------------------------------------
st.title("🏘️ 우리 동네 인구 피라미드")
st.markdown(f"**{latest_year}년 최신 데이터**를 기준으로 지역별 연령 및 성별 인구 구조를 살펴봅니다. ☀️")
st.divider()

# -----------------------------------------------------------------------------
# 4. 상단 드롭다운 3개 (시·도 ➔ 시·군·구 ➔ 읍·면·동 릴레이 선택)
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
# 5. 선택한 지역 데이터 처리 및 나이순 컬럼 정렬
# -----------------------------------------------------------------------------
# 최종 선택된 동의 데이터 필터링
target_df = filtered_sigungu_df[filtered_sigungu_df['동'] == selected_dong]

# 컬럼명에서 숫자(나이)만 추출하여 0세부터 100세 이상까지 올바른 순서로 정렬하는 키 함수
def get_age_key(col_name):
    clean_str = col_name.replace('남_', '').replace('여_', '').replace('세', '').replace(' 이상', '').strip()
    try:
        return int(clean_str)
    except ValueError:
        return 999

# '남_'으로 시작하는 컬럼을 나이 순서대로 정렬 (0세 -> 100세 이상)
male_cols = sorted([col for col in df.columns if col.startswith('남_')], key=get_age_key)
# 해당 남자 컬럼에 대응하는 여자 컬럼 리스트 생성
female_cols = [col.replace('남_', '여_') for col in male_cols]
# Y축 표시용 나이 라벨 리스트 생성 ('0세', '1세', ..., '100세 이상')
age_labels = [col.replace('남_', '') for col in male_cols]

# 선택 지역의 남/여 인구 수 추출 (여러 행일 경우 대비해 sum 처리)
male_values = target_df[male_cols].sum().values
female_values = target_df[female_cols].sum().values

# -----------------------------------------------------------------------------
# 6. 요약 인구 카드 (총 인구, 남성, 여성)
# -----------------------------------------------------------------------------
total_male = int(male_values.sum())
total_female = int(female_values.sum())
total_pop = total_male + total_female

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"### 📊 **{selected_sido} {selected_sigungu} {selected_dong}** 인구 수치")

m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("총 인구", f"{total_pop:,} 명")
m_col2.metric("남성 인구", f"{total_male:,} 명")
m_col3.metric("여성 인구", f"{total_female:,} 명")

st.divider()

# -----------------------------------------------------------------------------
# 7. Plotly 가로 막대 그래프 (인구 피라미드) 생성
# -----------------------------------------------------------------------------

# 남자는 왼쪽 방향 표시를 위해 인구수를 음수로 변환
male_neg_values = [-val for val in male_values]

fig = go.Figure()

# 남자 데이터 막대 (왼쪽 방향)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_neg_values,
    name='남성',
    orientation='h',
    marker_color='#4A90E2',   # 차분하고 따뜻한 파란색
    customdata=male_values,    # 마우스 오버(툴팁) 시 양수로 보여주기 위한 실제 값
    hovertemplate='<b>%{y}</b><br>남성 인구: %{customdata:,}명<extra></extra>'
))

# 여자 데이터 막대 (오른쪽 방향)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_values,
    name='여성',
    orientation='h',
    marker_color='#FF6B6B',   # 따뜻한 분홍/코랄색
    customdata=female_values,
    hovertemplate='<b>%{y}</b><br>여성 인구: %{customdata:,}명<extra></extra>'
))

# X축 눈금 설정 (음수로 입력된 남성 인구 표기를 양수 눈금 레이블로 보정)
max_val = max(max(male_values, default=0), max(female_values, default=0))
if max_val == 0:
    max_val = 100

tick_step = max(1, int(max_val / 4))
tick_vals = list(range(-tick_step * 4, tick_step * 5, tick_step))
tick_text = [f"{abs(v):,}" for v in tick_vals]

# -----------------------------------------------------------------------------
# 축 레이아웃 고정 설정
# - autorange='reversed' 나 값 크기순 정렬 옵션(total ascending 등)은 일체 사용하지 않음
# - categoryorder='array'와 categoryarray=age_labels를 사용하여
#   맨 아래 눈금이 '0세', 맨 위 눈금이 '100세 이상'으로 순서가 고정됨
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
        categoryarray=age_labels  # '0세'가 맨 아래(0번 index position), '100세 이상'이 맨 위에 배치
    ),
    barmode='relative',
    bargap=0.1,
    height=850,  # 0세~100세 이상이 쾌적하게 보이도록 충분한 높이 확보
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(l=60, r=40, t=80, b=40)
)

# Streamlit 화면에 Plotly 차트 출력
st.plotly_chart(fig, use_container_width=True)
