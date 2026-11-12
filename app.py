import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import re
from datetime import datetime
from PIL import Image

# ----------------------------------------------------
# 1. 페이지 설정 및 커스텀 스타일
# ----------------------------------------------------
st.set_page_config(
    page_title="스마트 가계부 정산기",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 5px;
    }
    .income-text { color: #2563EB; }
    .expense-text { color: #DC2626; }
    .balance-text { color: #059669; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 데이터베이스 / 로컬 파일 영속성 관리
# ----------------------------------------------------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ledger_data.csv')

DEFAULT_COLUMNS = ['날짜', '구분', '카테고리', '항목명', '금액', '결제수단', '메모', '출처']

def get_initial_sample_data():
    today = datetime.now()
    y = today.year
    m = today.month
    return pd.DataFrame([
        {'날짜': f"{y}-{m:02d}-01", '구분': '수입', '카테고리': '급여', '항목명': '정기 급여', '금액': 3500000, '결제수단': '계좌이체', '메모': '월급', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-02", '구분': '지출', '카테고리': '식비', '항목명': '김치찌개 식당', '금액': 10000, '결제수단': '카드', '메모': '점심', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-03", '구분': '지출', '카테고리': '카페/간식', '항목명': '스타벅스 아메리카노', '금액': 4500, '결제수단': '카드', '메모': '커피', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-05", '구분': '지출', '카테고리': '생활/마트', '항목명': '이마트 장보기', '금액': 68500, '결제수단': '카드', '메모': '식료품', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-07", '구분': '지출', '카테고리': '교통', '항목명': '지하철 후불교통', '금액': 45000, '결제수단': '카드', '메모': '대중교통', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-08", '구분': '지출', '카테고리': '주거/통신', '항목명': '휴대폰 요금', '금액': 55000, '결제수단': '계좌이체', '메모': '통신비', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-10", '구분': '지출', '카테고리': '쇼핑', '항목명': '무신사 겨울니트', '금액': 89000, '결제수단': '카드', '메모': '의류', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-11", '구분': '지출', '카테고리': '식비', '항목명': '배달의민족 치킨', '금액': 24000, '결제수단': '카드', '메모': '야식', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-12", '구분': '수입', '카테고리': '부수입', '항목명': '당근마켓 중고판매', '금액': 30000, '결제수단': '현금', '메모': '물품판매', '출처': '샘플'},
        {'날짜': f"{y}-{m:02d}-12", '구분': '지출', '카테고리': '문화/여가', '항목명': 'CGV 영화 관람', '금액': 15000, '결제수단': '카드', '메모': '영화', '출처': '샘플'}
    ])

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            if not df.empty and set(DEFAULT_COLUMNS).issubset(df.columns):
                df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0).astype(int)
                df['날짜'] = df['날짜'].astype(str)
                return df
        except Exception:
            pass
    # 파일이 없으면 초기 샘플 생성 후 저장
    initial_df = get_initial_sample_data()
    save_data(initial_df)
    return initial_df

def save_data(df):
    try:
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"데이터 저장 실패: {e}")

# 세션 상태에 가계부 데이터 로드
if 'ledger_df' not in st.session_state:
    st.session_state.ledger_df = load_data()

# ----------------------------------------------------
# 3. 카테고리 자동 유추 엔진
# ----------------------------------------------------
CATEGORY_KEYWORDS = {
    '식비': [
        '식당', '밥', '국밥', '찌개', '고기', '삼겹살', '치킨', '피자', '버거', '맥도날드', 
        '롯데리아', '버거킹', '맘스터치', '서브웨이', '분식', '김밥', '떡볶이', '중국집', '짜장', 
        '짬뽕', '초밥', '스시', '돈까스', '칼국수', '배달의민족', '배민', '요기요', '쿠팡이츠', 
        '한식', '일식', '중식', '양식', '식사', '푸드', '반찬', '구내식당', '갈비', '포차'
    ],
    '카페/간식': [
        '카페', '커피', '스타벅스', '스벅', '투썸', '메가커피', '컴포즈', '빽다방', '이디야', 
        '할리스', '파스쿠찌', '폴바셋', '블루보틀', '디저트', '베이커리', '빵', '파리바게뜨', 
        '뚜레쥬르', '도넛', '던킨', '크리스피', '와플', '빙수', '설빙', '공차', '버블티', 
        '케이크', '아이스크림', '배스킨라빈스', '베스킨'
    ],
    '생활/마트': [
        '마트', '이마트', '홈플러스', '롯데마트', '하나로마트', '다이소', '노브랜드', '코스트코', 
        '트레이더스', '슈퍼', 'GS25', 'CU', '씨유', '세븐일레븐', '이마트24', '미니스톱', 
        '편의점', '식료품', '잡화', '생활용품', '컬리', '마켓컬리', '정육', '청과'
    ],
    '교통': [
        '교통', '지하철', '버스', '택시', '카카오T', '카카오택시', '코레일', 'SRT', 'KTX', 
        '철도', '티머니', '하이패스', '주유', '주유소', 'GS칼텍스', 'SK에너지', 'S-OIL', 
        '현대오일뱅크', '주차', '주차장', '쏘카', '그린카', '따릉이'
    ],
    '쇼핑': [
        '쿠팡', '네이버페이', '11번가', 'G마켓', '옥션', '위메프', '티몬', 'SSG', '무신사', 
        '지그재그', '에이블리', '올리브영', '백화점', '현대백화점', '신세계', '롯데백화점', 
        '아울렛', '유니클로', 'ZARA', '자라', '의류', '패션', '화장품', '신발', '가방'
    ],
    '주거/통신': [
        '관리비', '월세', '전세', '가스', '도시가스', '전기요금', '수도요금', '아파트관리비', 
        'KT', 'SKT', 'LGU+', 'LG유플러스', '알뜰폰', '인터넷', '통신비', '핸드폰', '휴대폰'
    ],
    '의료/건강': [
        '병원', '의원', '내과', '이비인후과', '정형외과', '안과', '치과', '피부과', '한의원', 
        '약국', '약', '헬스', '피트니스', '필라테스', '요가', '짐', '건강검진'
    ],
    '문화/여가': [
        '영화', 'CGV', '메가박스', '롯데시네마', '넷플릭스', '유튜브', '티빙', '웨이브', '왓챠', 
        '디즈니', '도서', '교보문고', '영풍문고', '알라딘', '노래방', 'PC방', '볼링', '골프', '스크린골프'
    ],
    '교육': ['학원', '강의', '스터디', '인강', '클래스101', '패스트캠퍼스', '독서실', '스터디카페', '수강료', '자격증'],
    '급여': ['급여', '월급', '상여', '보너스', '수당', '연봉'],
    '부수입': ['용돈', '이자', '배당', '환급', '캐시백', '중고', '당근', '중고나라', '번개장터']
}

CATEGORIES_EXPENSE = ['식비', '카페/간식', '생활/마트', '교통', '쇼핑', '주거/통신', '의료/건강', '문화/여가', '교육', '기타지출']
CATEGORIES_INCOME = ['급여', '부수입', '기타수입']

def guess_category(text, is_income=False):
    if not text:
        return '기타수입' if is_income else '기타지출'
    text_lower = str(text).lower().replace(' ', '')
    
    if is_income:
        for kw in CATEGORY_KEYWORDS['급여']:
            if kw.lower() in text_lower:
                return '급여'
        for kw in CATEGORY_KEYWORDS['부수입']:
            if kw.lower() in text_lower:
                return '부수입'
        return '기타수입'
        
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat in ['급여', '부수입']:
            continue
        for kw in keywords:
            if kw.lower() in text_lower:
                return cat
    return '기타지출'

# ----------------------------------------------------
# 4. 엑셀 / CSV 스마트 파서
# ----------------------------------------------------
def parse_excel_or_csv(file):
    is_csv = file.name.lower().endswith('.csv')
    if is_csv:
        df = None
        for enc in ['utf-8-sig', 'cp949', 'euc-kr', 'utf-8']:
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            raise ValueError("CSV 인코딩을 읽을 수 없습니다.")
    else:
        file.seek(0)
        df = pd.read_excel(file)
        
    df.columns = [str(c).strip().replace('\n', '') for c in df.columns]
    cols = df.columns.tolist()
    
    date_col = next((c for c in cols if any(k in c.lower() for k in ['일자', '날짜', 'date', '거래일', '승인일', '결제일'])), None)
    type_col = next((c for c in cols if any(k in c.lower() for k in ['구분', '유형', '입출', '수입/지출', 'type'])), None)
    cat_col = next((c for c in cols if any(k in c.lower() for k in ['카테고리', '분류', 'category', '업종'])), None)
    title_col = next((c for c in cols if any(k in c.lower() for k in ['내용', '항목', '적요', '가맹점', '상호', '사용처', 'title', '품목'])), None)
    expense_col = next((c for c in cols if any(k in c.lower() for k in ['출금', '출금액', '지출', '지출액', '이용금액'])), None)
    income_col = next((c for c in cols if any(k in c.lower() for k in ['입금', '입금액', '수입', '수입액'])), None)
    amount_col = next((c for c in cols if any(k in c.lower() for k in ['금액', 'amount', '거래금액', '승인금액'])), None)
    method_col = next((c for c in cols if any(k in c.lower() for k in ['수단', '결제수단', '방법', '카드', 'method'])), None)
    memo_col = next((c for c in cols if any(k in c.lower() for k in ['메모', '비고', 'memo', 'note'])), None)

    records = []
    for _, row in df.iterrows():
        # 날짜 정규화
        raw_date = str(row.get(date_col, ''))
        m_dt = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', raw_date)
        if m_dt:
            dt = f"{int(m_dt.group(1)):04d}-{int(m_dt.group(2)):02d}-{int(m_dt.group(3)):02d}"
        else:
            try:
                dt = pd.to_datetime(raw_date).strftime('%Y-%m-%d')
            except Exception:
                dt = datetime.now().strftime('%Y-%m-%d')
                
        # 제목
        title = str(row.get(title_col, '')).strip()
        if not title or title == 'nan':
            other_cols = [c for c in cols if c not in [date_col, expense_col, income_col, amount_col]]
            title = str(row[other_cols[0]]) if other_cols else '미지정 내역'
            
        # 금액 및 유형 판별
        entry_type = '지출'
        amount = 0
        if expense_col or income_col:
            exp_val = clean_number(row.get(expense_col, 0)) if expense_col else 0
            inc_val = clean_number(row.get(income_col, 0)) if income_col else 0
            if inc_val > 0 and exp_val == 0:
                entry_type = '수입'
                amount = inc_val
            elif exp_val > 0:
                entry_type = '지출'
                amount = exp_val
            elif inc_val > 0:
                entry_type = '수입'
                amount = inc_val
        elif amount_col:
            amt_val = clean_number(row.get(amount_col, 0))
            if amt_val < 0:
                entry_type = '지출'
                amount = abs(amt_val)
            else:
                amount = amt_val
                
        if type_col and pd.notna(row.get(type_col)):
            val_t = str(row.get(type_col)).strip()
            if any(k in val_t for k in ['수입', '입금', '급여']):
                entry_type = '수입'
            elif any(k in val_t for k in ['지출', '출금', '소비']):
                entry_type = '지출'

        if amount == 0 and (title == '미지정 내역' or not title):
            continue
            
        # 카테고리
        cat = str(row.get(cat_col, '')).strip() if cat_col and pd.notna(row.get(cat_col)) else ''
        if not cat or cat == 'nan':
            cat = guess_category(title, is_income=(entry_type == '수입'))
            
        method = str(row.get(method_col, '카드')).strip() if method_col and pd.notna(row.get(method_col)) else '카드'
        memo = str(row.get(memo_col, '')).strip() if memo_col and pd.notna(row.get(memo_col)) else ''
        if memo == 'nan':
            memo = ''

        records.append({
            '날짜': dt,
            '구분': entry_type,
            '카테고리': cat,
            '항목명': title,
            '금액': int(amount),
            '결제수단': method,
            '메모': memo,
            '출처': file.name
        })
    return pd.DataFrame(records)

def clean_number(val):
    if pd.isna(val) or val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(round(val))
    s = str(val).replace(',', '').replace('원', '').replace('₩', '').replace(' ', '')
    try:
        return int(round(float(s)))
    except Exception:
        return 0

# ----------------------------------------------------
# 5. 영수증 이미지 OCR 및 데이터 파서
# ----------------------------------------------------
def parse_receipt_image(image_bytes):
    raw_text = ""
    lines = []
    
    # 윈도우 내장 OCR 시도
    try:
        import winocr
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        w, h = img.size
        if w < 600:
            scale = 600 / w
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        result = winocr.recognize_pil_sync(img, lang='ko')
        raw_text = result.get('text', '')
        lines = [line.get('text', '').strip() for line in result.get('lines', []) if line.get('text', '').strip()]
        if not lines and raw_text:
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    except Exception as e:
        raw_text = f"OCR 처리 중 안내: {e}"

    # 파싱 기본값
    today_str = datetime.now().strftime('%Y-%m-%d')
    date_val = today_str
    title_val = "영수증 지출"
    amount_val = 0
    cat_val = "기타지출"
    method_val = "카드"

    # 1. 날짜 탐지
    date_pats = [
        r'(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})',
        r'(\d{2})[-/.](\d{1,2})[-/.](\d{1,2})',
        r'(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})월\s*(\d{1,2})일'
    ]
    for line in lines:
        matched = False
        for p in date_pats:
            m = re.search(p, line)
            if m:
                g = m.groups()
                if len(g) == 3:
                    y, mo, d = g
                    if len(y) == 2:
                        y = f"20{y}"
                    date_val = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
                    matched = True
                    break
                elif len(g) == 2:
                    mo, d = g
                    date_val = f"{datetime.now().year:04d}-{int(mo):02d}-{int(d):02d}"
                    matched = True
                    break
        if matched:
            break

    # 2. 금액 탐지
    kws = ['합계', '합 계', '총액', '결제금액', '승인금액', '받을금액', '합계금액', 'TOTAL', '이용금액']
    candidates = []
    for i, line in enumerate(lines):
        clean_l = line.replace(' ', '')
        for kw in kws:
            if kw.replace(' ', '') in clean_l:
                m = re.findall(r'(\d{1,3}(?:,\d{3})+|\d+)\s*(?:원)?', line)
                if m:
                    for s in m:
                        v = int(s.replace(',', ''))
                        if v > 0:
                            candidates.append((10, v))
                elif i + 1 < len(lines):
                    next_l = lines[i+1]
                    m_next = re.findall(r'(\d{1,3}(?:,\d{3})+|\d+)\s*(?:원)?', next_l)
                    for s in m_next:
                        v = int(s.replace(',', ''))
                        if v > 0:
                            candidates.append((8, v))

    for line in lines:
        if re.search(r'0\d{1,2}-\d{3,4}-\d{4}', line) or re.search(r'\d{3}-\d{2}-\d{5}', line):
            continue
        m = re.findall(r'(\d{1,3}(?:,\d{3})+)\s*(?:원)?', line)
        for s in m:
            v = int(s.replace(',', ''))
            if 100 <= v <= 20000000:
                candidates.append((5, v))

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        amount_val = candidates[0][1]

    # 3. 상호명 탐지
    for line in lines[:8]:
        m = re.search(r'(?:상호|가맹점|매장명|상호명)[:\s]+([^\s\d]+[^\n]*)', line)
        if m:
            title_val = m.group(1).strip()
            break
            
    if title_val == "영수증 지출":
        ignore_words = ['영수증', '신용카드', '매출전표', '승인', '고객용', '카드사', '사업자', '전화', 'TEL', '주소', '일시']
        for line in lines[:6]:
            if any(w in line for w in ignore_words):
                continue
            cleaned = re.sub(r'[\d\-.,:()\[\]]', '', line).strip()
            if len(cleaned) >= 2:
                title_val = line.strip()
                break

    # 4. 결제 수단 및 카테고리
    all_str = " ".join(lines)
    if any(k in all_str for k in ['현금영수증', '현금']):
        method_val = '현금'
    elif any(k in all_str for k in ['카카오페이', '네이버페이', '토스', '페이코']):
        method_val = '간편결제'
    elif any(k in all_str for k in ['계좌이체', '송금']):
        method_val = '계좌이체'
    else:
        method_val = '카드'

    cat_val = guess_category(f"{title_val} {all_str}")

    return {
        '날짜': date_val,
        '구분': '지출',
        '카테고리': cat_val,
        '항목명': title_val,
        '금액': amount_val,
        '결제수단': method_val,
        '메모': '영수증 OCR 추출',
        '출처': '영수증',
        'raw_text': raw_text
    }

# ----------------------------------------------------
# 6. 사이드바 네비게이션 & 공통 도구
# ----------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/money-box.png", width=64)
    st.markdown("### 스마트 가계부 시스템")
    menu = st.radio("메뉴 이동", ["📊 지출 대시보드", "📁 파일 업로드 및 정산", "➕ 수동 내역 등록"])
    
    st.divider()
    st.markdown("#### ⚙️ 데이터 도구")
    
    # 엑셀 다운로드
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.ledger_df.to_excel(writer, index=False, sheet_name='가계부내역')
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 전체 가계부 엑셀 다운로드",
        data=excel_data,
        file_name=f"스마트가계부_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    # 샘플 엑셀 템플릿 다운로드
    sample_df = get_initial_sample_data()
    sample_out = io.BytesIO()
    with pd.ExcelWriter(sample_out, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False, sheet_name='샘플가계부')
    st.download_button(
        label="📄 샘플 엑셀 서식 받기",
        data=sample_out.getvalue(),
        file_name="가계부_샘플_템플릿.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    if st.button("🔄 샘플 데이터로 초기화", use_container_width=True):
        st.session_state.ledger_df = get_initial_sample_data()
        save_data(st.session_state.ledger_df)
        st.success("데이터가 초기화되었습니다.")
        st.rerun()

# ----------------------------------------------------
# 7. 메뉴 1: 지출 대시보드
# ----------------------------------------------------
if menu == "📊 지출 대시보드":
    st.markdown('<div class="main-header">월별 지출 통계 및 대시보드</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">수입과 지출 현황, 카테고리별 소비 패턴을 한눈에 파악하세요.</div>', unsafe_allow_html=True)

    df = st.session_state.ledger_df.copy()
    
    if df.empty:
        st.warning("등록된 가계부 내역이 없습니다. [파일 업로드 및 정산] 메뉴에서 내역을 추가해 보세요!")
    else:
        # 날짜 정렬
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        df = df.dropna(subset=['날짜']).sort_values('날짜', ascending=False)
        df['날짜_str'] = df['날짜'].dt.strftime('%Y-%m-%d')
        df['년월'] = df['날짜'].dt.strftime('%Y-%m')

        # 필터 컨트롤 영역
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            all_months = ['전체 기간'] + sorted(df['년월'].unique().tolist(), reverse=True)
            selected_month = st.selectbox("📅 조회 기간 선택", all_months, index=0)
        with col_f2:
            all_cats = ['전체 카테고리'] + sorted(df['카테고리'].unique().tolist())
            selected_cat = st.selectbox("🏷️ 카테고리 필터", all_cats, index=0)

        # 필터 적용
        filtered_df = df.copy()
        if selected_month != '전체 기간':
            filtered_df = filtered_df[filtered_df['년월'] == selected_month]
        if selected_cat != '전체 카테고리':
            filtered_df = filtered_df[filtered_df['카테고리'] == selected_cat]

        # 핵심 지표 산출
        income_sum = int(filtered_df[filtered_df['구분'] == '수입']['금액'].sum())
        expense_sum = int(filtered_df[filtered_df['구분'] == '지출']['금액'].sum())
        balance = income_sum - expense_sum
        tx_count = len(filtered_df)

        # 핵심 지표 카드 렌더링
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: #64748B; font-size: 0.95rem;">총 지출</div>
                <div class="metric-val expense-text">{expense_sum:,}원</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: #64748B; font-size: 0.95rem;">총 수입</div>
                <div class="metric-val income-text">{income_sum:,}원</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: #64748B; font-size: 0.95rem;">순 잔액 (수입 - 지출)</div>
                <div class="metric-val balance-text">{balance:+,}원</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div style="color: #64748B; font-size: 0.95rem;">거래 내역 건수</div>
                <div class="metric-val" style="color: #475569;">{tx_count:,}건</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 차트 분석 영역
        chart_col1, chart_col2 = st.columns([1, 1])

        with chart_col1:
            st.subheader("📌 카테고리별 지출 분석")
            expense_only = filtered_df[filtered_df['구분'] == '지출']
            if not expense_only.empty:
                cat_chart = expense_only.groupby('카테고리')['금액'].sum().sort_values(ascending=False)
                st.bar_chart(cat_chart, color="#EF4444")
            else:
                st.info("지출 내역이 없습니다.")

        with chart_col2:
            st.subheader("📈 일자별 지출 추이")
            if not expense_only.empty:
                daily_trend = expense_only.groupby('날짜_str')['금액'].sum().sort_index()
                st.line_chart(daily_trend, color="#3B82F6")
            else:
                st.info("지출 내역이 없습니다.")

        # 상세 거래 내역 테이블
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 상세 거래 내역 목록")
        
        display_df = filtered_df[['날짜_str', '구분', '카테고리', '항목명', '금액', '결제수단', '메모', '출처']].rename(
            columns={'날짜_str': '날짜'}
        )
        
        # 포맷팅을 위한 데이터 복사
        display_df_view = display_df.copy()
        display_df_view['금액'] = display_df_view['금액'].apply(lambda x: f"{x:,}원")
        st.dataframe(display_df_view, use_container_width=True, hide_index=True)

# ----------------------------------------------------
# 8. 메뉴 2: 파일 업로드 및 정산
# ----------------------------------------------------
elif menu == "📁 파일 업로드 및 정산":
    st.markdown('<div class="main-header">지출 내역 업로드 및 스마트 정산</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">은행/카드사 엑셀 파일이나 영수증 사진을 업로드하면 AI/OCR이 자동으로 정리합니다.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 엑셀/CSV 파일 정산", "🧾 영수증 이미지 분석"])

    # 탭 1: 엑셀 / CSV 업로드
    with tab1:
        st.write("카드사, 은행 거래내역 엑셀 또는 CSV 파일을 업로드하세요. 컬럼명을 자동으로 매핑하고 카테고리를 자동 분류합니다.")
        
        excel_file = st.file_uploader(
            "은행/카드사 엑셀(XLSX, XLS, CSV) 파일을 선택하세요",
            type=["xlsx", "xls", "csv"],
            key="excel_uploader"
        )

        if excel_file is not None:
            try:
                parsed_df = parse_excel_or_csv(excel_file)
                st.success(f"총 {len(parsed_df)}건의 거래 내역을 성공적으로 파싱 및 분류했습니다!")
                
                st.subheader("🔎 파싱 결과 미리보기")
                preview_df = parsed_df.copy()
                preview_df['금액_표시'] = preview_df['금액'].apply(lambda x: f"{x:,}원")
                st.dataframe(preview_df[['날짜', '구분', '카테고리', '항목명', '금액_표시', '결제수단', '메모']], use_container_width=True)

                c1, c2 = st.columns([1, 4])
                with c1:
                    if st.button("💾 가계부에 전체 저장", type="primary", use_container_width=True):
                        st.session_state.ledger_df = pd.concat([st.session_state.ledger_df, parsed_df], ignore_index=True)
                        save_data(st.session_state.ledger_df)
                        st.balloons()
                        st.success(f"{len(parsed_df)}건이 가계부에 성공적으로 반영되었습니다!")
                with c2:
                    st.caption("저장 후 [지출 대시보드] 메뉴에서 실시간 통계와 차트를 확인할 수 있습니다.")

            except Exception as e:
                st.error(f"파일 파싱 중 오류가 발생했습니다: {e}")

    # 탭 2: 영수증 이미지 분석
    with tab2:
        st.write("결제 영수증이나 결제 승인 문자/앱 캡처 이미지를 업로드하면 날짜, 상호명, 금액을 자동 인식합니다.")
        
        receipt_image = st.file_uploader(
            "영수증 이미지를 업로드하세요 (PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"],
            key="receipt_uploader"
        )

        if receipt_image is not None:
            col_img, col_info = st.columns([1, 1])
            img_bytes = receipt_image.read()

            with col_img:
                st.image(img_bytes, caption="업로드된 영수증", use_container_width=True)

            with col_info:
                st.subheader("🧾 영수증 분석 결과")
                with st.spinner("영수증 이미지에서 텍스트 및 결제 정보를 추출 중입니다..."):
                    parsed_receipt = parse_receipt_image(img_bytes)

                st.info("💡 추출된 정보를 확인하시고 필요 시 수정 후 저장하세요.")

                # 수정 가능한 입력 폼
                with st.form("receipt_form"):
                    f_date = st.text_input("결제 일자", value=parsed_receipt['날짜'])
                    f_type = st.selectbox("구분", ["지출", "수입"], index=0)
                    
                    cat_list = CATEGORIES_EXPENSE if f_type == '지출' else CATEGORIES_INCOME
                    def_cat_idx = cat_list.index(parsed_receipt['카테고리']) if parsed_receipt['카테고리'] in cat_list else 0
                    f_category = st.selectbox("카테고리", cat_list, index=def_cat_idx)
                    
                    f_title = st.text_input("상호 / 항목명", value=parsed_receipt['항목명'])
                    f_amount = st.number_input("결제 금액 (원)", value=int(parsed_receipt['금액']), step=100)
                    f_method = st.selectbox("결제 수단", ["카드", "현금", "간편결제", "계좌이체"], 
                                            index=["카드", "현금", "간편결제", "계좌이체"].index(parsed_receipt['결제수단']) if parsed_receipt['결제수단'] in ["카드", "현금", "간편결제", "계좌이체"] else 0)
                    f_memo = st.text_input("메모", value=parsed_receipt['메모'])

                    submitted = st.form_submit_button("✅ 가계부에 반영하기", type="primary", use_container_width=True)
                    if submitted:
                        new_row = pd.DataFrame([{
                            '날짜': f_date,
                            '구분': f_type,
                            '카테고리': f_category,
                            '항목명': f_title,
                            '금액': int(f_amount),
                            '결제수단': f_method,
                            '메모': f_memo,
                            '출처': '영수증'
                        }])
                        st.session_state.ledger_df = pd.concat([st.session_state.ledger_df, new_row], ignore_index=True)
                        save_data(st.session_state.ledger_df)
                        st.success(f"'{f_title}' ({f_amount:,}원, {f_category}) 내역이 가계부에 등록되었습니다!")

                with st.expander("🔍 OCR 추출 원본 텍스트 확인"):
                    st.text(parsed_receipt.get('raw_text', '텍스트 없음'))

# ----------------------------------------------------
# 9. 메뉴 3: 수동 내역 등록
# ----------------------------------------------------
elif menu == "➕ 수동 내역 등록":
    st.markdown('<div class="main-header">수동 거래 내역 직접 등록</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">영수증이나 엑셀이 없어도 한 건씩 바로 가계부에 등록할 수 있습니다.</div>', unsafe_allow_html=True)

    with st.form("manual_entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            m_date = st.date_input("거래 일자", value=datetime.now())
            m_type = st.radio("거래 구분", ["지출", "수입"], horizontal=True)
            cat_options = CATEGORIES_EXPENSE if m_type == "지출" else CATEGORIES_INCOME
            m_category = st.selectbox("카테고리", cat_options)
            m_title = st.text_input("항목명 / 사용처", placeholder="예: 스타벅스 강남점, 이마트 역삼점")
            
        with col2:
            m_amount = st.number_input("금액 (원)", min_value=0, step=1000, value=10000)
            m_method = st.selectbox("결제 수단", ["카드", "현금", "계좌이체", "간편결제"])
            m_memo = st.text_area("메모 (선택사항)", placeholder="상세 내용이나 특이사항을 적어두세요.")

        btn = st.form_submit_button("➕ 가계부에 등록하기", type="primary", use_container_width=True)
        if btn:
            if not m_title:
                st.error("항목명을 입력해 주세요.")
            elif m_amount <= 0:
                st.error("금액은 0원보다 커야 합니다.")
            else:
                new_entry = pd.DataFrame([{
                    '날짜': m_date.strftime('%Y-%m-%d'),
                    '구분': m_type,
                    '카테고리': m_category,
                    '항목명': m_title,
                    '금액': int(m_amount),
                    '결제수단': m_method,
                    '메모': m_memo,
                    '출처': '직접입력'
                }])
                st.session_state.ledger_df = pd.concat([st.session_state.ledger_df, new_entry], ignore_index=True)
                save_data(st.session_state.ledger_df)
                st.success(f"'{m_title}' ({m_amount:,}원) 내역이 성공적으로 추가되었습니다!")

