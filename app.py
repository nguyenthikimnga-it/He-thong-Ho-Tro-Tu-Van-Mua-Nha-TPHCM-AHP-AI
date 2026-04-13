import streamlit as st
import pandas as pd
import psycopg2
import numpy as np
import plotly.express as px


# 1. Cấu hình trang 
st.set_page_config(page_title="Hệ thống tư vấn nhà TP.HCM", layout="wide")

# 2. Định nghĩa hàm kết nối TRƯỚC khi sử dụng
def get_conn():
    try:
        # Sử dụng cấu trúc secrets chuẩn của Streamlit cho PostgreSQL
        return psycopg2.connect(
            host=st.secrets["connections"]["postgresql"]["host"],
            database=st.secrets["connections"]["postgresql"]["database"],
            user=st.secrets["connections"]["postgresql"]["user"],
            password=st.secrets["connections"]["postgresql"]["password"],
            port=st.secrets["connections"]["postgresql"]["port"]
        )
    except Exception as e:
        st.error(f"❌ Không thể kết nối Database: {e}")
        st.stop()

# 3. Các hàm xử lý dữ liệu
@st.cache_data(ttl=60)
def load_data():
    try:
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM danh_sach_nha", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Lỗi nạp dữ liệu từ Supabase: {e}")
        return None

def save_chat_to_db(user_msg, ai_res):
    try:
        conn = get_conn()
        cur = conn.cursor()
        customer_name = st.session_state.get('cust_name', 'Khách vãng lai')
        query = """
            INSERT INTO chat_history (customer_name, user_message, ai_response)
            VALUES (%s, %s, %s)
        """
        cur.execute(query, (customer_name, user_msg, ai_res))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Lỗi lưu chat: {e}")

# --- PHẦN GIAO DIỆN CHÍNH ---
st.markdown("""
<h1 class="main-title">
🏠 Hệ thống Hỗ trợ Quyết định Bất động sản tại TP.HCM
</h1>
""", unsafe_allow_html=True)

# Kiểm tra kết nối ngay khi vào App
try:
    with st.spinner('Đang kết nối hệ thống...'):
        conn_test = get_conn()      
        conn_test.close()
except:
    pass


def hien_thi_khung_chat(top_1):
    # 1. Khởi tạo biến show_chat nếu chưa có
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # 2. Nút bấm để mở/đóng chat
    if st.button("💬 Chat với Trợ lý ảo (AI Advisor)"):
        st.session_state.show_chat = not st.session_state.show_chat
        st.rerun()

    # 3. Giao diện khung chat
    if st.session_state.show_chat:
        st.markdown("---")
        # Đưa vào giữa màn hình
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.info(f"🤖 Đang hỗ trợ thông tin căn **{top_1['id']}**")
            
            # Hiển thị các tin nhắn cũ trong khung có thanh cuộn
            chat_box = st.container(height=350, border=True)
            with chat_box:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # Ô nhập liệu bằng st.chat_input (tự động xử lý Enter)
            prompt = st.chat_input("Hỏi AI về giá, diện tích, pháp lý...")
            
            if prompt:
                # Lưu tin nhắn khách
                st.session_state.messages.append({"role": "user", "content": prompt})
                
               # Logic AI xử lý linh động hơn
                p_lower = prompt.lower()
                
                # 1. Xử lý về Giá
                if any(k in p_lower for k in ["giá", "bao nhiêu", "tiền", "tỷ"]):
                    res = f"Căn **{top_1['id']}** có giá là **{top_1['gia_ban']} tỷ**. Đây là mức giá tối ưu nhất sau khi em chạy thuật toán AHP đấy ạ!"
                    
                # 2. Xử lý về Diện tích
                elif any(k in p_lower for k in ["diện tích", "rộng", "m2", "kích thước"]):
                    res = f"Diện tích căn này là **{top_1['dien_tich']} m²**. Với không gian này, bạn sẽ rất thoải mái trong việc bố trí nội thất."
                    
                # 3. Xử lý về Vị trí
                elif any(k in p_lower for k in ["vị trí", "ở đâu", "địa chỉ", "quận"]):
                    res = f"Căn này tọa lạc tại **{top_1['ten_quan']}**. Vị trí này đạt điểm số cao về tính thuận tiện trong hệ thống phân tích của em."
                    
                # 4. Xử lý về Pháp lý
                elif any(k in p_lower for k in ["pháp lý", "sổ", "giấy tờ", "sổ hồng"]):
                    res = f"Bạn yên tâm nhé, căn nhà này đã có **{top_1['giay_to']}**. Hồ sơ pháp lý rất sạch và rõ ràng."

                # 5. MỚI: Xử lý về Môi giới (Lấy thông tin từ database)
                elif any(k in p_lower for k in ["môi giới", "ai bán", "liên hệ ai", "người phụ trách", "số điện thoại"]):
                    res = ("Căn nhà này đang được các chuyên viên của hệ thống quản lý trực tiếp. "
                        "Để bảo mật thông tin, bạn vui lòng để lại lời nhắn hoặc số điện thoại, "
                         "mình sẽ kết nối bạn với môi giới nắm rõ nhất khu vực này trong 5 phút nữa nhé!")

                # 6. MỚI: Xử lý về Phong thủy / Hướng
                elif any(k in p_lower for k in ["phong thủy", "hướng", "đông nam", "tây bắc", "hợp tuổi"]):
                    huong = top_1.get('huong_nha', 'đã được kiểm định')
                    res = f"Căn nhà có hướng chính là **{huong}**. Theo đánh giá sơ bộ, hướng này đón ánh sáng tốt và rất vượng khí cho gia chủ."
                             
                # 7. MỚI: Xử lý về đặc điểm
                elif any(k in p_lower for k in ["đặc điểm", "thông tin", "nở hậu", "vuông vức"]):
                    dacdiem_nha = top_1.get('dac_diem', 'Bạn thấy căn này thế nào?')
                    res = f"Đặc điểm nổi bật là **{dacdiem_nha}**.."

                # 8. Xử lý câu chào hỏi hoặc khen ngợi
                elif any(k in p_lower for k in ["chào", "hi", "hello", "cảm ơn", "tốt"]):
                    res = "Rất sẵn lòng hỗ trợ bạn! Bạn cần biết thêm chi tiết gì về căn nhà 'điểm 10' này không?"

                # 9. Trường hợp không hiểu
                else:
                    res = " Câu hỏi này hơi khó, để mình kết nối bạn với chuyên viên môi giới thực tế nhé?"

                # GỌI HÀM LƯU VÀO DATABASE
                save_chat_to_db(prompt, res)
                
                # Lưu tin nhắn AI và làm mới
                st.session_state.messages.append({"role": "assistant", "content": res})
                st.rerun()

def view_all_appointments():
    try:
        conn = get_conn()

        query = """
            SELECT 
                a.ngay_xem, 
                a.gio_xem, 
                c.full_name, 
                a.id, 
                a.ghi_chu
            FROM appointments a
            JOIN customers c ON a.customer_id = c.customer_id
            ORDER BY a.ngay_xem DESC
        """

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    except Exception as e:
        st.error(f"Lỗi khi nạp lịch hẹn: {e}")
        return None


def save_appointment(cust_name, id, date, time, note):
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT customer_id FROM customers WHERE full_name = %s ORDER BY customer_id DESC LIMIT 1",
            (cust_name,)
        )
        result = cur.fetchone()

        if result:
            c_id = result[0]
            cur.execute("""
                INSERT INTO appointments (customer_id, id, ngay_xem, gio_xem, ghi_chu)
                VALUES (%s, %s, %s, %s, %s)
            """, (c_id, id, date, time, note))

            conn.commit()
            cur.close()
            conn.close()
            return True

        else:
            st.error("Không tìm thấy khách hàng")
            return False

    except Exception as e:
        st.error(f"❌ Lỗi hệ thống: {e}")
        return False


def delete_consultation_history():
    try:
        conn = get_conn()
        
        cur = conn.cursor()
        cur.execute("DELETE FROM consultation_history")
        cur.execute("DELETE FROM customers")
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi khi xóa dữ liệu: {e}")
        return False

def load_consultation_history():
    try:
        conn = get_conn()

        query = """
            SELECT c.full_name, c.phone, h.id, 
                   h.score_ahp, h.loi_khuyen_ai, h.ngay_tu_van
            FROM consultation_history h
            JOIN customers c ON h.customer_id = c.customer_id
            ORDER BY h.ngay_tu_van DESC
        """

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    except Exception as e:
        st.error(f"❌ Lỗi nạp lịch sử: {e}")
        return None

def save_consultation(name, phone, email, id, score, advice):
    try:
        conn = get_conn()
        
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (full_name, phone, email) VALUES (%s, %s, %s) RETURNING customer_id", (name, phone, email))
        c_id = cur.fetchone()[0]
        cur.execute("INSERT INTO consultation_history (customer_id, id, score_ahp, loi_khuyen_ai) VALUES (%s, %s, %s, %s)", (c_id, id
                                                                                                                             , score, advice))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu Database: {e}")
        return False



# --- 2. CẤU HÌNH GIAO DIỆN ---
if 'registered' not in st.session_state:
    st.session_state.registered = False

def set_bg():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1494526585095-c41746248156");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #222 !important;
        }

        /* Overlay + blur */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            backdrop-filter: blur(6px);
            background: rgba(255,255,255,0.25); /* đổi từ đen sang trắng */
            z-index: -1;
        }

        /* ép màu chữ */
        h1, h2, h3, h4, h5, h6, p, span, div, label {
            color: #222 !important;
        }

        .block-container {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 15px;
        }

        .stButton>button {
            background-color: #2E8B57;
            color: white;
            border-radius: 8px;
        }


/* Mobile */
@media (max-width: 768px){

    /* thu nhỏ padding */
    .block-container{
        padding: 1rem !important;
    }

    /* thu nhỏ tiêu đề lớn */
    h1{
        font-size: 24px !important;
        line-height: 1.3 !important;
    }

    h2{
        font-size: 20px !important;
    }

    h3{
        font-size: 18px !important;
    }

    /* số KPI */
    .metric-container{
        font-size: 14px !important;
    }

    /* card */
    .card{
        padding: 12px !important;
        border-radius: 12px !important;
    }

    /* ảnh card */
    img{
        border-radius: 12px !important;
    }

    /* button */
    .stButton>button{
        width: 100% !important;
        font-size: 14px !important;
    }

}

/* Mobile nhỏ */
@media (max-width: 480px){

    h1{
        font-size: 20px !important;
    }

    h2{
        font-size: 18px !important;
    }

    .block-container{
        padding: 0.7rem !important;
    }
}
.main-title{
    width:100%;
    display:block;
}

/* mobile */
@media (max-width:768px){
    .main-title{
        font-size: 22px;
        line-height: 1.4;
        word-break: keep-all;
    }
}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg()



try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ load_data lỗi: {e}")
    df_raw = None



if df_raw is not None:
    # --- LỚP 1: BỘ LỌC TRI THỨC (SIDEBAR) ---

    # Phân loại khu vực chuẩn theo thực tế 20 quận/huyện trong DB của bạn
    dict_khu_vuc = {
        "🏙️ Vùng Trung tâm": ["Quận 1", "Quận 3", "Quận 4", "Quận 5", "Quận 10", "Phú Nhuận"],
        "🏠 Vùng Nội thành": ["Quận 6", "Quận 7", "Quận 8", "Quận 11", "Quận 12", "Bình Tân", "Bình Thạnh", "Gò Vấp", "Tân Bình", "Tân Phú", "Thủ Đức"],
        "🌳 Vùng Ngoại thành": ["Bình Chánh", "Hóc Môn", "Nhà Bè", "Củ Chi", "Cần Giờ"]
    }

    with st.sidebar.expander("📍 Chọn khu vực chi tiết", expanded=True):
                
        chon_trung_tam = st.multiselect("Trung tâm TP:", options=dict_khu_vuc["🏙️ Vùng Trung tâm"], default=[])
        chon_noi_thanh = st.multiselect("Nội thành:", options=dict_khu_vuc["🏠 Vùng Nội thành"], default=[])
        chon_ngoai_thanh = st.multiselect("Ngoại thành:", options=dict_khu_vuc["🌳 Vùng Ngoại thành"], default=[])
        
        # Gộp tất cả lựa chọn
        quan_chon = chon_trung_tam + chon_noi_thanh + chon_ngoai_thanh
        
        if quan_chon:
            st.success(f"✅ Đã chọn {len(quan_chon)} khu vực")
        else:
            st.warning("⚠️ Hãy chọn ít nhất một khu vực")

    # Bộ lọc Slider
    min_gia = float(df_raw['gia_ban'].min())
    max_gia = float(df_raw['gia_ban'].max())
    budget = st.sidebar.slider("Ngân sách tối đa (Tỷ đồng):", min_gia, max_gia, max_gia)

    min_dt = float(df_raw['dien_tich'].min())
    max_dt = float(df_raw['dien_tich'].max())
    area_range = st.sidebar.slider("Diện tích mong muốn (m2):", min_dt, max_dt, (min_dt, max_dt))

    # Luật chuyên gia
    st.sidebar.markdown("---")
    st.sidebar.subheader("Luật chuyên gia ưu tiên:")
    L_hinh_the = st.sidebar.checkbox("Ưu tiên nhà hình thể đẹp (>= 8đ)")
    L_phap_ly = st.sidebar.checkbox("Chỉ chọn nhà có Pháp lý an toàn (10đ)")
    L_duong = st.sidebar.checkbox("Ưu tiên đường rộng (>= 7đ)")

    #  Các Luật còn lại giấu vào Expander cho gọn
    with st.sidebar.expander("🛠️ Các luật bổ sung"):       
        L_tien_ich = st.checkbox("🏬 Gần tiện ích công cộng (>= 8đ)")
        L_quy_hoach = st.checkbox("🏗️ Không vướng quy hoạch (10đ)")
        L_loai_hinh = st.checkbox("🏢 Chỉ chọn Nhà phố/Biệt thự")

    # Tại phần Sidebar
    st.sidebar.header("🧭 Tiêu chí phong thủy")
    list_huong = ['Tất cả','Đông', 'Tây', 'Nam', 'Bắc', 'Đông Nam', 'Đông Bắc', 'Tây Nam', 'Tây Bắc']
    huong_chon = st.sidebar.selectbox("Chọn hướng nhà mong muốn:", list_huong)
   

    # --- THỰC THI LỌC DỮ LIỆU ---
    if not quan_chon:
        st.info("👈 Vui lòng chọn khu vực ở Sidebar để bắt đầu phân tích.")
        df_l1 = pd.DataFrame()
    else:
        mask = (
            (df_raw['ten_quan'].isin(quan_chon)) & 
            (df_raw['gia_ban'] <= budget) & 
            (df_raw['dien_tich'] >= area_range[0]) & 
            (df_raw['dien_tich'] <= area_range[1])
        )
        df_l1 = df_raw[mask].copy()
        
        # Áp dụng luật chuyên gia
        if L_hinh_the and not df_l1.empty: 
            df_l1 = df_l1[df_l1['hinh_the'] >= 8]
        if L_phap_ly and not df_l1.empty: 
            df_l1 = df_l1[df_l1['phap_ly'] >= 10]
        if L_duong and not df_l1.empty: 
            df_l1 = df_l1[df_l1['loai_duong'] >= 7]
        
        # lọc dữ liệu    
        if huong_chon != 'Tất cả':
            df_l1 = df_l1[df_l1['huong_nha'] == huong_chon]


    # Lớp 2: Tính điểm AHP
    if not df_l1.empty:
        # Danh sách các tiêu chí tính điểm    
        cols_calc = ['quan_diem', 'loai_hinh', 'gia_diem', 'dien_tich_diem', 'vi_tri_diem', 'hinh_the', 'loai_duong', 'phap_ly', 'diem_tien_ich']
        
        # Ma trận trọng số AHP 
        weights = np.array([0.2917, 0.2009, 0.1332, 0.1332, 0.0889, 0.0606, 0.0416, 0.0289, 0.0209])
           
        # Tính điểm tổng hợp
        df_l1['score'] = np.dot(df_l1[cols_calc].values, weights)
        
        # Sắp xếp và lấy Top
        df_ranked = df_l1.sort_values(by=['score', 'gia_ban'], ascending=[False, True])            
        top_5 = df_ranked.head(5)
        best_choice = top_5.iloc[0]

        # Hiển thị KPI
        st.header("🎯 KẾT QUẢ PHÂN TÍCH RA QUYẾT ĐỊNH")

        # KPI Cards
        k1, k2, k3 = st.columns(3)
        k1.metric("🏠 Căn thỏa mãn", len(df_l1))
        k2.metric("🏆 Điểm tối ưu", f"{best_choice['score']:.4f}")
        k3.metric("💰 Giá tốt nhất", f"{best_choice['gia_ban']} tỷ")

        if not st.session_state.registered:
            with st.form("lock_form"):
                st.warning("🔒 Vui lòng để lại thông tin để mở khóa báo cáo chi tiết.")
                c1, c2, c3 = st.columns(3)
                name_in = c1.text_input("Họ và tên *")
                phone_in = c2.text_input("Số điện thoại *")
                email_in = c3.text_input("Email (nếu có)")
                if st.form_submit_button("🚀 NHẬN BÁO CÁO"):
                    if name_in and phone_in:
                        save_consultation(name_in, phone_in, "", str(best_choice['id']), float(best_choice['score']), "Tư vấn phương án tối ưu")
                        st.session_state.registered, st.session_state.cust_name = True, name_in
                        st.rerun()
        else:
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Xếp hạng AHP", "🔍 Thông số chi tiết", "🤖 Tư vấn Expert", "Quản trị viên Admin"])
                
            with tab1:
                fig = px.bar(top_5.sort_values('score'), x='score', y='id', orientation='h', title="Top 5 phương án tốt nhất", color='score', color_continuous_scale='Reds')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(top_5[['id', 'ten_quan', 'gia_ban', 'score']], use_container_width=True)
             
            with tab2:
                st.subheader("🏡 Top nhà đề xuất")

                cols = st.columns(3)

                for i, (_, data) in enumerate(df_ranked.head(6).iterrows()):
                    with cols[i % 3]:

                        img_url = "https://images.unsplash.com/photo-1568605114967-8130f3a36994"

                        # CARD HTML
                        st.markdown(f"""                                

                                    
                            <div class="card">
                                <img src="{img_url}" style="width:100%; border-radius:10px;">
                                <h4>🏠 {data['id']}</h4>
                            </div>
                        """, unsafe_allow_html=True)

                        # 👇 TEXT (Python thật)
                        st.write(f"📍 **Khu vực:** {data['ten_quan']}")
                        st.write(f"💰 **Giá:** {data['gia_ban']} tỷ")
                        st.write(f"📐 **Diện tích:** {data['dien_tich']} m²")
                        st.write(f"📄 **Pháp lý:** {data['giay_to']}")
                        st.write(f"🛣️ Đường: {data['duong']}")
                        st.write(f"✨ Đặc điểm: {data['dac_diem']}")
                        st.write(f"🏬 Tiện ích: {data['tien_ich']}")
                        st.write(f"📍 Vị trí: {data['vi_tri']} km")
                        st.write(f"🧭 Hướng: {data['huong_nha']}")

                        # progress bar
                        st.progress(min(float(data['score']), 1.0))

            with tab3:
                st.subheader("🤖 Trợ lý ảo giải thích lựa chọn (Explainable AI)")
                
                # --- 1. TÍNH TOÁN CÁC THÔNG SỐ PHỤ TRỢ ---
                # Mapping lại tên tiêu chí để hiển thị cho đẹp
                criteria_names = {
                    "vi_tri_diem": "Vị trí",
                    "dien_tich_diem": "Diện tích",
                    "gia_diem": "Giá bán",
                    "hinh_the": "Hình thể/Phong thủy",
                    "loai_duong": "Hạ tầng đường",
                    "diem_tien_ich": "Tiện ích xung quanh"
                }
                
                criteria_scores = {k: best_choice[k] for k in criteria_names.keys()}
                strongest_key = max(criteria_scores, key=criteria_scores.get)
                strongest_point = criteria_names[strongest_key]

                # --- 2. LOGIC KIỂM TRA CHÉO (SENSITIVITY) ---
                # Giả định kịch bản: Người dùng thay đổi ý định sang ưu tiên Giá (50%)             
                w_uu_tien_gia = np.array([0.1, 0.1, 0.5, 0.1, 0.05, 0.05, 0.04, 0.03, 0.03])
                diem_gia_re = np.dot(df_l1[cols_calc].values, w_uu_tien_gia)
                idx_best_gia = np.argmax(diem_gia_re)
                id_gia_re = df_l1.iloc[idx_best_gia]['id']
                
                # --- 3. TRÌNH BÀY DẠNG TƯ VẤN ---
                st.markdown(f"#### 🏆 Tại sao căn ID {best_choice['id']} lại đứng đầu?")
                
                if str(id_gia_re) == str(best_choice['id']):
                    st.success(f"🌟 **Lựa chọn vàng:** Căn nhà này đứng đầu ở mọi kịch bản (Robust Decision). Anh/ Chị có ưu tiên về vị trí hay giá rẻ, hệ thống vẫn chọn căn này. Đây là phương án vượt trội hoàn toàn về mọi mặt.")
                else:
                    st.info(f"💡 **Phân tích so sánh:** Căn này tối ưu nhất về tổng thể theo trọng số hiện tại. Tuy nhiên, nếu sau này Cô muốn đổi sang ưu tiên tuyệt đối vào **'Giá rẻ nhất có thể'** thì căn **ID {id_gia_re}** sẽ là đối thủ thay thế tốt nhất.")

                avg_score = df_l1['score'].mean()
                if avg_score > 0:
                    cach_biet = ((best_choice['score'] - avg_score) / avg_score) * 100
                else:
                    cach_biet = 0.0
                         
                # Lấy dữ liệu căn tốt nhất
                top_1 = df_ranked.iloc[0]
                top_2 = df_ranked.iloc[1] if len(df_ranked) > 1 else None                  
              
                # Dòng này giúp bạn soi xem điểm số thực tế là bao nhiêu
                st.write(f"Điểm căn Top 1: {best_choice['score']}")
                st.write(f"Điểm trung bình các căn khác: {df_l1[df_l1['id'] != best_choice['id']]['score'].mean()}")
                
                
                st.write(f"""
                **Kết luận từ Hệ chuyên gia:**
                * **Độ vượt trội:** Điểm số cao hơn **{cach_biet:.1f}%** so với trung bình các căn cùng phân khúc.
                * **Điểm sáng lớn nhất:** Thế mạnh nằm ở ID **{top_1['id']}** đứng đầu vì có giá bán hấp dẫn hơn (**{top_1['gia_ban']} tỷ**).
                * **Lời khuyên:** Đây là lựa chọn đạt sự cân bằng (Optimization) cao nhất giữa giá trị sử dụng và tính an toàn pháp lý.
                """)
                st.info(f"🤖 Trợ lý AI: 'Căn nhà này không chỉ có điểm số cao mà còn có hướng **{top_1['huong_nha']}** rất hợp với yêu cầu của bạn.'")
       
                    
                if top_2 is not None and abs(top_1['score'] - top_2['score']) < 0.0001:
                    st.info(f"🏆 **ID {top_1['id']}** chiếm ưu thế tuyệt đối với điểm số cao nhất {top_1['score']:.4f}.")
                
                # 1. Hiển thị thông báo thành công từ bộ nhớ (nếu có)
                if 'booking_success_msg' in st.session_state:
                    st.success(st.session_state.booking_success_msg)
                    # Xóa sau khi hiện để không bị lặp lại vô tận
                    del st.session_state.booking_success_msg    

                dac_diem_val = str(top_1.get('dac_diem', '')).lower()    

                st.markdown("---")
                col_a, col_b = st.columns(2)
                
                with col_a:
                     
                    if "trống" in dac_diem_val or "giao ngay" in dac_diem_val:
                        st.info("⚡ **Thông tin từ chủ nhà:** Căn này đang trống, bạn có thể đặt lịch xem ngay trong ngày!")
                    else:
                        st.warning("📍 **Lưu ý:** Nhà đang có người ở, vui lòng hẹn trước ít nhất 1 ngày.")
                     
                    # 1. Hiển thị Chatbot (giữ nguyên của bạn)
                    hien_thi_khung_chat(top_1) 
                    
                    st.write("") 

                    # 2. Thông báo thành công sau khi tất cả đã xong
                    if 'booking_done' in st.session_state:
                        st.success(st.session_state.booking_done)
                        if st.button("Đặt lịch căn khác"):
                            del st.session_state.booking_done
                            st.rerun()
                    
                    else:
                        # 3. Nút mở Form ban đầu
                        if st.button(f"🗓️ Đặt lịch đi xem căn {top_1['id']}"):
                            st.session_state.show_booking_form = True

                        if st.session_state.get('show_booking_form', False):
                            with st.expander("📝 Chi tiết lịch hẹn", expanded=True):
                                # Dùng container để quản lý trạng thái hiển thị bên trong expander
                                placeholder = st.container()

                                # GIAI ĐOẠN 1: ĐIỀN FORM VÀ GỬI
                                if 'waiting_confirm' not in st.session_state:
                                    with placeholder.form("booking_form"):
                                        d = st.date_input("Chọn ngày xem nhà:")
                                        t = st.time_input("Chọn giờ xem nhà:")
                                        note = st.text_area("Ghi chú cho môi giới:")
                                        
                                        if st.form_submit_button("Gửi yêu cầu đến môi giới"):
                                            # Lưu tạm dữ liệu vào session để chờ xác nhận
                                            st.session_state.temp_booking = {'d': d, 't': t, 'note': note}
                                            st.session_state.waiting_confirm = True
                                            st.toast('Yêu cầu đã soạn xong, vui lòng xác nhận!', icon='📩')
                                            st.rerun()

                                # GIAI ĐOẠN 2: KHÁCH HÀNG XÁC NHẬN LẠI
                                else:
                                    data = st.session_state.temp_booking
                                    placeholder.warning(f"🔔 **Xác nhận lại lịch hẹn:**\n\nNgày {data['d']} lúc {data['t']}. Ghi chú: {data['note']}")
                                    
                                    col1, col2 = placeholder.columns(2)
                                    if col1.button("✅ Xác nhận đặt"):
                                        success = save_appointment(st.session_state.cust_name, top_1['id'], data['d'], data['t'], data['note'])
                                        if success:
                                            st.balloons()
                                            st.session_state.booking_done = f"✅ Đã đặt lịch xem căn {top_1['id']} thành công!"
                                            # Dọn dẹp session
                                            del st.session_state.waiting_confirm
                                            del st.session_state.temp_booking
                                            st.session_state.show_booking_form = False
                                            st.rerun()
                                    
                                    if col2.button("❌ Hủy/Làm lại"):
                                        del st.session_state.waiting_confirm
                                        del st.session_state.temp_booking
                                        st.rerun()
                                   

                                    
                with col_b:
                    st.success(f"👨‍💼 **Chuyên viên hỗ trợ:** Sẵn sàng đàm phán. Hot Line: 037.9494.909")
                    # Nút Zalo
                    st.markdown(f"""
                        <a href="https://zalo.me/0901234567" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #0068ff; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">
                                💬 Chat trực tiếp qua Zalo
                            </div>
                        </a>
                    """, unsafe_allow_html=True)

            with tab4:
                pwd = st.text_input("Nhập mật khẩu Admin:", type="password")
                if pwd == "admin123":
                    st.header("📜 Lịch sử tư vấn AHP")
                    history = load_consultation_history()
                    if history is not None:
                        st.dataframe(history, use_container_width=True)
                        if st.button("🗑️ Xóa lịch sử"):
                            if delete_consultation_history(): 
                                st.rerun()

                    st.markdown("---")
                    st.header("📋 Quản lý lịch xem nhà")
                    df_appointments = view_all_appointments()            

                    if df_appointments is not None and not df_appointments.empty:
                        st.dataframe(df_appointments, use_container_width=True)                                            
                        csv = df_appointments.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Tải danh sách lịch hẹn (CSV)",
                            data=csv,
                            file_name='danh_sach_lich_hen.csv',
                            mime='text/csv',
                        )
                    else:
                        st.info("Chưa có lịch hẹn nào được đăng ký.")

                    st.markdown("---")
                    st.header("💬 Nhật ký tư vấn AI")
                    try:
                        conn_temp = get_conn()
                        df_chat = pd.read_sql(
                            "SELECT * FROM chat_history ORDER BY timestamp DESC",
                            conn_temp
                        )
                        st.dataframe(df_chat, use_container_width=True)
                        conn_temp.close()

                    except Exception as e:
                        st.error(f"Không thể hiển thị nhật ký chat: {e}")
                        
                elif pwd != "":
                    st.error("❌ Mật khẩu không chính xác!")