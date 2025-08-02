import streamlit as st
import pandas as pd
from io import BytesIO
import time

def format_card_number(card_num: str) -> str:
    card_num = card_num.zfill(16)  # 혹시라도 앞자리 누락 시 보완
    return f"{card_num[:4]}-{card_num[4:8]}-{card_num[8:12]}-{card_num[12:]}"

def generate_excel(df, unit: int, progress_callback):
    import time
    import pandas as pd

    df = df.reset_index(drop=True)
    total = len(df)
    processed = 0
    results = []
    box_number = 1

    # 영업점명으로 그룹핑
    grouped = df.groupby('영업점명', sort=False)

    for branch, group_df in grouped:
        group_df = group_df.reset_index(drop=True)
        group_total = len(group_df)
        idx = 0

        while idx < group_total:
            remaining = group_total - idx
            count = min(unit, remaining)

            slice_df = group_df.iloc[idx : idx + count]

            front_card = format_card_number(str(slice_df.iloc[0]['카드번호']))
            back_card = format_card_number(str(slice_df.iloc[-1]['카드번호']))
            amount = slice_df.iloc[0]['권면금액']

            results.append({
                '번호': box_number,
                '박스번호': box_number,
                '앞번호': front_card,
                '뒷번호': back_card,
                '매수': count,
                '카드명': branch,
                '권종': amount
            })

            box_number += 1
            idx += count
            processed += count

            progress_callback(min(processed / total, 1.0))
            time.sleep(0.01)

    return pd.DataFrame(results)


def to_excel_file(df: pd.DataFrame) -> BytesIO:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# --- Streamlit UI ---
st.set_page_config(page_title="카드데이터 변환기", layout="wide")
st.title("🧾 카드데이터 박스 변환 프로그램")
st.markdown("업로드한 원본 데이터를 지정한 수량 단위로 나누어 Excel로 변환합니다.")

uploaded_file = st.file_uploader("📂 원본 파일 업로드 (CSV 또는 XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    unit = st.number_input("📦 박스 단위 (매수)", min_value=100, step=100, value=2000)
    convert_button = st.button("🔁 변환 실행")

    if convert_button:
        with st.spinner("📊 파일을 처리 중입니다..."):
            try:
                # 파일 로딩
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, dtype=str)
                else:
                    df = pd.read_excel(uploaded_file, dtype=str)

                required_cols = {'카드번호', '권면금액', '상품번호', '시퀀스', '영업점번호', '영업점명'}
                if not required_cols.issubset(df.columns):
                    st.error(f"❌ 누락된 컬럼이 있습니다: {required_cols - set(df.columns)}")
                else:
                    progress_bar = st.progress(0)
                    result_df = generate_excel(df, unit, lambda p: progress_bar.progress(p))
                    excel_io = to_excel_file(result_df)
                    file_name = f"{unit}_변환엑셀파일.xlsx"

                    st.success("✅ 변환이 완료되었습니다.")
                    st.download_button(
                        label="📥 변환된 엑셀 다운로드",
                        data=excel_io.getvalue(),
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"❌ 처리 중 오류 발생: {e}")
