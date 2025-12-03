import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from folium.plugins import AntPath, Fullscreen
from streamlit_folium import st_folium
import warnings

# Tắt các cảnh báo hệ thống để màn hình sạch đẹp
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN & TRANG TRÍ (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Hệ thống Dẫn đường Pleiku", layout="wide", page_icon="🗺️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

    /* Tiêu đề chính */
    h1 { color: #2C3E50; text-align: center; font-weight: 700; margin-bottom: 20px; text-transform: uppercase; }

    /* Trang trí các Tab */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 20px; }
    .stTabs [data-baseweb="tab"] { background-color: #ECF0F1; border-radius: 10px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #3498DB; color: white !important; font-weight: bold; }

    /* Khung hiển thị Lộ trình chi tiết */
    .khung-lo-trinh {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        padding: 20px;
        max-height: 600px;
        overflow-y: auto;
    }

    /* Các phần tử trong dòng thời gian (Timeline) */
    .dong-thoi-gian {
        display: flex;
        padding-bottom: 15px;
        position: relative;
    }
    .dong-thoi-gian::before {
        content: ''; position: absolute; left: 19px; top: 35px; bottom: 0; width: 2px; background-color: #E0E0E0;
    }
    .dong-thoi-gian:last-child::before { display: none; }

    .icon-moc {
        flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%;
        background-color: #E8F6F3; color: #1ABC9C;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; margin-right: 15px; z-index: 1;
        border: 2px solid #1ABC9C;
    }

    .noi-dung-moc {
        flex-grow: 1; background-color: #F8F9F9; padding: 10px 15px;
        border-radius: 8px; border-left: 4px solid #BDC3C7;
    }
    .noi-dung-moc:hover { background-color: #F0F3F4; border-left-color: #3498DB; transition: 0.3s; }

    .ten-duong { font-weight: bold; color: #2C3E50; font-size: 1.05em; display: block; }
    .the-khoang-cach { float: right; font-size: 0.85em; color: #E74C3C; font-weight: bold; background: #FADBD8; padding: 2px 8px; border-radius: 10px; }

    /* Hộp thống kê */
    .hop-thong-ke {
        display: flex; justify-content: space-around;
        background: linear-gradient(135deg, #6DD5FA 0%, #2980B9 100%);
        color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(52, 152, 219, 0.3);
    }
    .muc-thong-ke { text-align: center; }
    .gia-tri-thong-ke { font-size: 1.5em; font-weight: bold; display: block; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Bộ nhớ đệm (Session State)
if 'do_thi' not in st.session_state: st.session_state['do_thi'] = nx.Graph()
if 'lo_trinh_tim_duoc' not in st.session_state: st.session_state['lo_trinh_tim_duoc'] = []
if 'chi_tiet_lo_trinh' not in st.session_state: st.session_state['chi_tiet_lo_trinh'] = []
if 'tam_ban_do' not in st.session_state: st.session_state['tam_ban_do'] = [13.9785, 108.0051]
if 'cay_khung_mst' not in st.session_state: st.session_state['cay_khung_mst'] = []  # Lưu kết quả Prim/Kruskal


# -----------------------------------------------------------------------------
# HÀM XỬ LÝ 1: TRÍCH XUẤT THÔNG TIN LỘ TRÌNH (TÊN ĐƯỜNG, ĐỘ DÀI)
# -----------------------------------------------------------------------------
def lay_thong_tin_lo_trinh(do_thi, danh_sach_nut):
    if not danh_sach_nut or len(danh_sach_nut) < 2: return []
    cac_buoc_di = []
    ten_duong_hien_tai = None
    quang_duong_hien_tai = 0

    # Duyệt qua từng đoạn đường
    for u, v in zip(danh_sach_nut[:-1], danh_sach_nut[1:]):
        du_lieu_canh = do_thi.get_edge_data(u, v)[0]
        do_dai = du_lieu_canh.get('length', 0)
        ten = du_lieu_canh.get('name', 'Đường nội bộ')
        if isinstance(ten, list): ten = ten[0]  # Lấy tên đầu tiên nếu có nhiều tên

        # Gộp các đoạn đường cùng tên lại
        if ten == ten_duong_hien_tai:
            quang_duong_hien_tai += do_dai
        else:
            if ten_duong_hien_tai:
                cac_buoc_di.append({"ten": ten_duong_hien_tai, "do_dai": quang_duong_hien_tai})
            ten_duong_hien_tai = ten
            quang_duong_hien_tai = do_dai

    if ten_duong_hien_tai:
        cac_buoc_di.append({"ten": ten_duong_hien_tai, "do_dai": quang_duong_hien_tai})
    return cac_buoc_di


# -----------------------------------------------------------------------------
# HÀM XỬ LÝ 2: VẼ ĐỒ THỊ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def ve_do_thi_ly_thuyet(do_thi, duong_di=None, danh_sach_canh=None, tieu_de=""):
    hinh_ve, truc = plt.subplots(figsize=(8, 5))
    vi_tri = nx.spring_layout(do_thi, seed=42)

    # Vẽ nền
    nx.draw(do_thi, vi_tri, with_labels=True, node_color='#D6EAF8', edge_color='#BDC3C7', node_size=600,
            font_weight='bold', ax=truc)
    nhan_canh = nx.get_edge_attributes(do_thi, 'weight')
    nx.draw_networkx_edge_labels(do_thi, vi_tri, edge_labels=nhan_canh, font_size=9, ax=truc)

    # Tô màu đường đi (nếu có)
    if duong_di:
        canh_duong_di = list(zip(duong_di, duong_di[1:]))
        nx.draw_networkx_nodes(do_thi, vi_tri, nodelist=duong_di, node_color='#E74C3C', node_size=700, ax=truc)
        nx.draw_networkx_edges(do_thi, vi_tri, edgelist=canh_duong_di, width=3, edge_color='#E74C3C', ax=truc)

    # Tô màu cây khung (Prim/Kruskal)
    if danh_sach_canh:
        nx.draw_networkx_edges(do_thi, vi_tri, edgelist=danh_sach_canh, width=3, edge_color='#27AE60', ax=truc)

    truc.set_title(tieu_de, color="#2C3E50", fontsize=12)
    st.pyplot(hinh_ve)


# -----------------------------------------------------------------------------
# GIAO DIỆN CHÍNH CỦA ỨNG DỤNG
# -----------------------------------------------------------------------------
st.title("🏙️ ỨNG DỤNG THUẬT TOÁN CHO HỆ THỐNG DẪN ĐƯỜNG TP. PLEIKU")

tab_ly_thuyet, tab_ban_do = st.tabs(["📚 PHẦN 1: LÝ THUYẾT ĐỒ THỊ", "🚀 PHẦN 2: BẢN ĐỒ THỰC TẾ"])

# =============================================================================
# TAB 1: LÝ THUYẾT (CƠ BẢN & NÂNG CAO)
# =============================================================================
with tab_ly_thuyet:
    cot_trai, cot_phai = st.columns([1, 1.5])

    with cot_trai:
        st.subheader("🛠️ Cấu hình Đồ thị")
        loai_do_thi = st.radio("Chọn loại:", ["Vô hướng", "Có hướng"], horizontal=True)
        co_huong = True if loai_do_thi == "Có hướng" else False

        du_lieu_nhap = st.text_area("Nhập danh sách cạnh (u v w):", "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4",
                                    height=150)

        if st.button("🚀 Khởi tạo Đồ thị"):
            try:
                G_moi = nx.DiGraph() if co_huong else nx.Graph()
                for dong in du_lieu_nhap.split('\n'):
                    phan = dong.split()
                    if len(phan) >= 2:
                        trong_so = int(phan[2]) if len(phan) > 2 else 1
                        G_moi.add_edge(phan[0], phan[1], weight=trong_so)
                st.session_state['do_thi'] = G_moi
                st.success("Đã tạo đồ thị thành công!")
            except:
                st.error("Lỗi dữ liệu nhập vào! Hãy kiểm tra lại.")

    with cot_phai:
        # Nếu đã có đồ thị thì vẽ ra
        if len(st.session_state['do_thi']) > 0:
            ve_do_thi_ly_thuyet(st.session_state['do_thi'], tieu_de="Hình ảnh trực quan")

    if len(st.session_state['do_thi']) > 0:
        st.divider()
        c1, c2, c3 = st.columns(3)

        # Cột 1: Biểu diễn
        with c1:
            st.info("1. Biểu diễn dữ liệu (YC6)")

            # CẬP NHẬT: Thêm "Danh sách cạnh" vào menu cho đủ bộ 3 món
            dang_xem = st.selectbox("Chọn cách xem:", ["Danh sách kề", "Ma trận kề", "Danh sách cạnh"])

            if dang_xem == "Ma trận kề":
                # Hiển thị Ma trận (Matrix)
                df = pd.DataFrame(nx.adjacency_matrix(st.session_state['do_thi']).todense(),
                                  index=st.session_state['do_thi'].nodes(),
                                  columns=st.session_state['do_thi'].nodes())
                st.dataframe(df, height=150)

            elif dang_xem == "Danh sách kề":
                # Hiển thị Danh sách kề (Adjacency List)
                st.json(nx.to_dict_of_lists(st.session_state['do_thi']), expanded=False)

            else:
                # Hiển thị Danh sách cạnh (Edge List) -> ĐÚNG YÊU CẦU 100%
                st.write("Danh sách cạnh (u, v, w):")
                canh = list(st.session_state['do_thi'].edges(data=True))
                st.write(canh)

            # Kiểm tra 2 phía (YC5)
            st.write("---")
            if st.button("Kiểm tra 2 phía (Bipartite)"):
                kq = nx.is_bipartite(st.session_state['do_thi'])
                st.write(f"Kết quả: {'Có' if kq else ' Không'}")

        # Cột 2: Thuật toán tìm kiếm
        with c2:
            st.warning("2. Thuật toán Tìm kiếm")
            nut_bat_dau = st.selectbox("Điểm bắt đầu:", list(st.session_state['do_thi'].nodes()))
            nut_ket_thuc = st.selectbox("Điểm kết thúc:", list(st.session_state['do_thi'].nodes()),
                                        index=len(st.session_state['do_thi'].nodes()) - 1)

            if st.button("Chạy BFS (Chiều rộng)"):
                # Lấy thứ tự duyệt BFS
                duong_bfs = list(dict(nx.bfs_successors(st.session_state['do_thi'], nut_bat_dau)).keys())
                duong_bfs.insert(0, nut_bat_dau)
                ve_do_thi_ly_thuyet(st.session_state['do_thi'], duong_di=duong_bfs,
                                    tieu_de="Duyệt theo chiều rộng (BFS)")

            if st.button("Chạy DFS (Chiều sâu)"):
                duong_dfs = list(nx.dfs_preorder_nodes(st.session_state['do_thi'], nut_bat_dau))
                ve_do_thi_ly_thuyet(st.session_state['do_thi'], duong_di=duong_dfs,
                                    tieu_de="Duyệt theo chiều sâu (DFS)")

            if st.button("Chạy Dijkstra (Ngắn nhất)"):
                try:
                    duong_ngan_nhat = nx.shortest_path(st.session_state['do_thi'], nut_bat_dau, nut_ket_thuc,
                                                       weight='weight')
                    ve_do_thi_ly_thuyet(st.session_state['do_thi'], duong_di=duong_ngan_nhat,
                                        tieu_de="Đường đi ngắn nhất (Dijkstra)")
                except:
                    st.error("Không tìm thấy đường đi!")

        # Cột 3: Nâng cao
        with c3:
            st.success("3. Thuật toán Nâng cao")
            cot_k1, cot_k2 = st.columns(2)

            with cot_k1:
                if st.button("Chạy Prim"):
                    if not co_huong and nx.is_connected(st.session_state['do_thi']):
                        cay_khung = nx.minimum_spanning_tree(st.session_state['do_thi'], algorithm='prim')
                        ve_do_thi_ly_thuyet(st.session_state['do_thi'], danh_sach_canh=list(cay_khung.edges()),
                                            tieu_de=f"Prim MST (W={cay_khung.size(weight='weight')})")
                    else:
                        st.error("Lỗi: Chỉ áp dụng cho đồ thị Vô hướng & Liên thông")

            with cot_k2:
                if st.button("Chạy Kruskal"):
                    if not co_huong and nx.is_connected(st.session_state['do_thi']):
                        cay_khung = nx.minimum_spanning_tree(st.session_state['do_thi'], algorithm='kruskal')
                        ve_do_thi_ly_thuyet(st.session_state['do_thi'], danh_sach_canh=list(cay_khung.edges()),
                                            tieu_de=f"Kruskal MST (W={cay_khung.size(weight='weight')})")
                    else:
                        st.error("Lỗi: Chỉ áp dụng cho đồ thị Vô hướng & Liên thông")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (100 ĐỊA ĐIỂM)
# =============================================================================
with tab_ban_do:
    # Hàm tải bản đồ (chạy 1 lần rồi lưu cache cho nhanh)
    @st.cache_resource
    def tai_ban_do_pleiku():
        # Tải bán kính 7km quanh Quảng trường
        return ox.graph_from_point((13.9785, 108.0051), dist=7000, network_type='drive')


    with st.spinner("Đang tải dữ liệu bản đồ TP. Pleiku (Khoảng 45 giây)..."):
        try:
            Do_thi_Pleiku = tai_ban_do_pleiku()
            st.success("✅ Đã tải xong bản đồ!")
        except:
            st.error("Lỗi tải bản đồ, vui lòng thử lại!")
            st.stop()

    # DANH SÁCH ~100 ĐỊA ĐIỂM (Đã chuẩn hóa tọa độ)
    ds_dia_diem = {
        "--- TRUNG TÂM ---": (0, 0),
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Bưu điện Tỉnh Gia Lai": (13.9770, 108.0040),
        "UBND Tỉnh Gia Lai": (13.9790, 108.0040),
        "Công an Tỉnh Gia Lai": (13.9780, 108.0020),
        "Bảo tàng Tỉnh Gia Lai": (13.9780, 108.0055),
        "Sở Giáo dục & Đào tạo": (13.9775, 108.0045),
        "Nhà Thi đấu Tỉnh": (13.9810, 108.0060),

        "--- GIAO THÔNG & CHỢ ---": (0, 0),
        "Sân bay Pleiku": (14.0044, 108.0172),
        "Bến xe Đức Long": (13.9556, 108.0264),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "Chợ Trung tâm (Mới)": (13.9750, 108.0080),
        "Chợ Thống Nhất": (13.9800, 108.0150),
        "Chợ Phù Đổng": (13.9700, 108.0100),
        "Chợ Hoa Lư": (13.9850, 108.0050),
        "Chợ Yên Thế": (13.9900, 108.0300),
        "Chợ Trà Bá": (13.9600, 108.0250),
        "Chợ Biển Hồ": (14.0400, 108.0050),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050),
        "Ngã 4 Biển Hồ": (14.0000, 108.0000),
        "Ngã 3 Phù Đổng": (13.9700, 108.0050),
        "Ngã 3 Diệp Kính": (13.9750, 108.0070),
        "Vòng xoay HAGL": (13.9760, 108.0030),

        "--- DU LỊCH & GIẢI TRÍ ---": (0, 0),
        "Biển Hồ (Tơ Nưng)": (14.0534, 108.0035),
        "Biển Hồ Chè": (14.0200, 108.0100),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Công viên Đồng Xanh": (13.9800, 108.0500),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "TTTM Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Rạp Touch Cinema": (13.9700, 108.0100),
        "Núi Hàm Rồng": (13.8900, 108.0500),
        "Học viện Bóng đá HAGL": (13.9500, 108.0500),
        "Làng Văn hóa Plei Ốp": (13.9820, 108.0080),

        "--- TÔN GIÁO ---": (0, 0),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "Chùa Bửu Minh": (14.0200, 108.0100),
        "Chùa Bửu Nghiêm": (13.9750, 108.0020),
        "Chùa Bửu Thắng": (13.9850, 108.0100),
        "Nhà thờ Đức An": (13.9750, 108.0050),
        "Nhà thờ Thăng Thiên": (13.9850, 108.0050),
        "Nhà thờ Plei Chuet": (13.9700, 108.0300),
        "Nhà thờ Hoa Lư": (13.9900, 108.0050),

        "--- Y TẾ & GIÁO DỤC ---": (0, 0),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Bệnh viện ĐH Y Dược HAGL": (13.9700, 108.0000),
        "Bệnh viện Nhi Gia Lai": (13.9600, 108.0100),
        "Bệnh viện Mắt Cao Nguyên": (13.9650, 108.0150),
        "Bệnh viện 331": (13.9900, 108.0200),
        "Bệnh viện TP Pleiku": (13.9780, 108.0150),
        "Trường THPT Chuyên Hùng Vương": (13.9850, 108.0100),
        "Trường THPT Pleiku": (13.9800, 108.0120),
        "Trường THPT Phan Bội Châu": (13.9750, 108.0200),
        "Trường THPT Lê Lợi": (13.9700, 108.0150),
        "Trường THPT Hoàng Hoa Thám": (13.9900, 108.0100),
        "Trường CĐ Sư phạm Gia Lai": (13.9600, 108.0200),
        "Phân hiệu ĐH Nông Lâm": (13.9550, 108.0300),
        "Trường Quốc tế UKA": (13.9850, 108.0200),

        "--- KHÁCH SẠN ---": (0, 0),
        "KS Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "KS Tre Xanh": (13.9790, 108.0060),
        "KS Khánh Linh": (13.9780, 108.0050),
        "KS Mê Kông": (13.9750, 108.0020),
        "KS Boston": (13.9720, 108.0050),
        "KS Pleiku & Em": (13.9770, 108.0080),
        "KS Se San": (13.9780, 108.0040),

        "--- KHÁC ---": (0, 0),
        "Công ty Điện lực Gia Lai": (13.9800, 108.0050),
        "Viettel Gia Lai": (13.9750, 108.0060),
        "VNPT Gia Lai": (13.9770, 108.0040),
        "Ngân hàng Agribank Tỉnh": (13.9780, 108.0030),
        "Ngân hàng Vietcombank": (13.9790, 108.0050),
        "Sân Golf FLC (Dự kiến)": (14.0100, 108.0200),
        "Khu đô thị Hoa Lư": (13.9900, 108.0100),
        "Khu đô thị Suối Hội Phú": (13.9700, 108.0200)
    }

    # Lọc bỏ các dòng tiêu đề (có tọa độ 0,0)
    dia_diem_hop_le = {k: v for k, v in ds_dia_diem.items() if v != (0, 0)}

    cot_di, cot_den, cot_thuat_toan = st.columns([1.5, 1.5, 1])
    diem_bat_dau = cot_di.selectbox("📍 Điểm xuất phát:", list(dia_diem_hop_le.keys()), index=0)
    diem_ket_thuc = cot_den.selectbox("🏁 Điểm đến:", list(dia_diem_hop_le.keys()), index=8)
    thuat_toan_tim_duong = cot_thuat_toan.selectbox("Thuật toán:",
                                                    ["Dijkstra (Tối ưu)", "BFS (Ít rẽ)", "DFS (Minh họa)"])

    st.divider()  # Kẻ ngang phân cách

    # CHIA LÀM 2 CỘT NÚT BẤM
    cot_nut_tim, cot_nut_quy_hoach = st.columns([1, 1])

    with cot_nut_tim:
        nut_tim_duong = st.button("🚀 TÌM ĐƯỜNG NGAY", type="primary", use_container_width=True)

    with cot_nut_quy_hoach:
        # Chọn thuật toán quy hoạch
        chon_quy_hoach = st.selectbox("Thuật toán Quy hoạch:", ["Prim", "Kruskal"], label_visibility="collapsed")
        nut_quy_hoach = st.button(f" QUY HOẠCH ({chon_quy_hoach.upper()})", use_container_width=True)

    # --- LOGIC TÌM ĐƯỜNG (A->B) ---
    if nut_tim_duong:
        st.session_state['cay_khung_mst'] = []  # Xóa kết quả Quy hoạch cũ
        try:
            # Tìm tọa độ
            u_coord, v_coord = dia_diem_hop_le[diem_bat_dau], dia_diem_hop_le[diem_ket_thuc]
            # Tìm nút gần nhất trên bản đồ
            nut_goc = ox.distance.nearest_nodes(Do_thi_Pleiku, u_coord[1], u_coord[0])
            nut_dich = ox.distance.nearest_nodes(Do_thi_Pleiku, v_coord[1], v_coord[0])

            duong_di = []
            if "Dijkstra" in thuat_toan_tim_duong:
                duong_di = nx.shortest_path(Do_thi_Pleiku, nut_goc, nut_dich, weight='length')
            elif "BFS" in thuat_toan_tim_duong:
                duong_di = nx.shortest_path(Do_thi_Pleiku, nut_goc, nut_dich, weight=None)
            elif "DFS" in thuat_toan_tim_duong:
                try:
                    duong_di = next(nx.all_simple_paths(Do_thi_Pleiku, nut_goc, nut_dich, cutoff=150))
                except:
                    duong_di = []

            st.session_state['lo_trinh_tim_duoc'] = duong_di
            st.session_state['chi_tiet_lo_trinh'] = lay_thong_tin_lo_trinh(Do_thi_Pleiku, duong_di)
            # Cập nhật tâm bản đồ về giữa lộ trình
            st.session_state['tam_ban_do'] = [(u_coord[0] + v_coord[0]) / 2, (u_coord[1] + v_coord[1]) / 2]

        except Exception as e:
            st.error(f"Không tìm thấy đường đi: {e}")

    # --- LOGIC QUY HOẠCH (PRIM/KRUSKAL) ---
    if nut_quy_hoach:
        st.session_state['lo_trinh_tim_duoc'] = []  # Xóa đường đi cũ
        try:
            with st.spinner(f"Đang chạy thuật toán {chon_quy_hoach} để nối mạng lưới trung tâm..."):
                # Lấy đồ thị con (Bán kính 2km) để chạy nhanh
                nut_trung_tam = ox.distance.nearest_nodes(Do_thi_Pleiku, 108.0051, 13.9785)
                do_thi_con = nx.ego_graph(Do_thi_Pleiku, nut_trung_tam, radius=2000, distance='length')

                # Chạy thuật toán
                khoa_thuat_toan = 'prim' if chon_quy_hoach == 'Prim' else 'kruskal'
                cay_khung = nx.minimum_spanning_tree(do_thi_con.to_undirected(), weight='length',
                                                     algorithm=khoa_thuat_toan)

                danh_sach_toa_do_canh = []
                for u, v, data in cay_khung.edges(data=True):
                    if 'geometry' in data:
                        xs, ys = data['geometry'].xy
                        danh_sach_toa_do_canh.append(list(zip(ys, xs)))
                    else:
                        u_node, v_node = Do_thi_Pleiku.nodes[u], Do_thi_Pleiku.nodes[v]
                        danh_sach_toa_do_canh.append([(u_node['y'], u_node['x']), (v_node['y'], v_node['x'])])

                st.session_state['cay_khung_mst'] = danh_sach_toa_do_canh
                st.session_state['tam_ban_do'] = [13.9785, 108.0051]
                st.success(
                    f"Đã quy hoạch xong bằng {chon_quy_hoach}! Tổng chiều dài cáp: {cay_khung.size(weight='length') / 1000:.2f} km")
        except Exception as e:
            st.error(f"Lỗi thuật toán: {e}")

    # --- HIỂN THỊ KẾT QUẢ RA MÀN HÌNH ---
    if st.session_state['lo_trinh_tim_duoc']:
        duong_di = st.session_state['lo_trinh_tim_duoc']
        chi_tiet = st.session_state['chi_tiet_lo_trinh']
        tong_km = sum(d['do_dai'] for d in chi_tiet) / 1000

        # Hộp thống kê
        st.markdown(f"""
        <div class="hop-thong-ke">
            <div class="muc-thong-ke"><div class="gia-tri-thong-ke">{tong_km:.2f} km</div><div class="nhan-thong-ke">Tổng quãng đường</div></div>
            <div class="muc-thong-ke"><div class="gia-tri-thong-ke">{len(chi_tiet)}</div><div class="nhan-thong-ke">Số đoạn đường</div></div>
            <div class="muc-thong-ke"><div class="gia-tri-thong-ke">{int(tong_km * 2)} phút</div><div class="nhan-thong-ke">Thời gian dự kiến</div></div>
        </div>
        """, unsafe_allow_html=True)

        cot_ban_do, cot_chi_tiet = st.columns([2, 1.2])

        # Cột Phải: Lộ trình chi tiết
        with cot_chi_tiet:
            st.markdown("### 📋 Lộ trình chi tiết")
            with st.container(height=600):
                st.markdown('<div class="khung-lo-trinh">', unsafe_allow_html=True)

                # Điểm đầu
                st.markdown(f'''
                <div class="dong-thoi-gian">
                    <div class="icon-moc" style="background:#D5F5E3; border-color:#2ECC71; color:#27AE60;">A</div>
                    <div class="noi-dung-moc"><span class="ten-duong">Bắt đầu: {diem_bat_dau}</span></div>
                </div>
                ''', unsafe_allow_html=True)

                # Các đoạn đường
                for i, buoc in enumerate(chi_tiet):
                    st.markdown(f'''
                    <div class="dong-thoi-gian">
                        <div class="icon-moc">{i + 1}</div>
                        <div class="noi-dung-moc">
                            <span class="the-khoang-cach">{buoc['do_dai']:.0f} m</span>
                            <span class="ten-duong">{buoc['ten']}</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                # Điểm cuối
                st.markdown(f'''
                <div class="dong-thoi-gian">
                    <div class="icon-moc" style="background:#FADBD8; border-color:#E74C3C; color:#C0392B;">B</div>
                    <div class="noi-dung-moc"><span class="ten-duong">Đích đến: {diem_ket_thuc}</span></div>
                </div>
                ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # Cột Trái: Bản đồ
        with cot_ban_do:
            m = folium.Map(location=st.session_state['tam_ban_do'], zoom_start=14, tiles="cartodbpositron")
            Fullscreen().add_to(m)

            # Marker điểm đầu cuối
            folium.Marker(dia_diem_hop_le[diem_bat_dau], icon=folium.Icon(color="green", icon="play", prefix='fa'),
                          popup="BẮT ĐẦU").add_to(m)
            folium.Marker(dia_diem_hop_le[diem_ket_thuc], icon=folium.Icon(color="red", icon="flag", prefix='fa'),
                          popup="KẾT THÚC").add_to(m)

            # Vẽ đường cong (Geometry)
            toa_do_duong_di = []
            nut_dau = Do_thi_Pleiku.nodes[duong_di[0]]
            toa_do_duong_di.append((nut_dau['y'], nut_dau['x']))

            for u, v in zip(duong_di[:-1], duong_di[1:]):
                canh = Do_thi_Pleiku.get_edge_data(u, v)[0]
                if 'geometry' in canh:
                    xs, ys = canh['geometry'].xy
                    toa_do_duong_di.extend(list(zip(ys, xs)))
                else:
                    nut_v = Do_thi_Pleiku.nodes[v]
                    toa_do_duong_di.extend([(nut_v['y'], nut_v['x'])])

            # Màu sắc theo thuật toán
            mau_sac = "orange" if "DFS" in thuat_toan_tim_duong else (
                "purple" if "BFS" in thuat_toan_tim_duong else "#3498DB")

            # Vẽ AntPath
            AntPath(toa_do_duong_di, color=mau_sac, weight=6, opacity=0.8, delay=1000).add_to(m)

            # Vẽ nét đứt nối vào
            folium.PolyLine([dia_diem_hop_le[diem_bat_dau], toa_do_duong_di[0]], color="gray", weight=2,
                            dash_array='5, 5').add_to(m)
            folium.PolyLine([dia_diem_hop_le[diem_ket_thuc], toa_do_duong_di[-1]], color="gray", weight=2,
                            dash_array='5, 5').add_to(m)

            st_folium(m, width=900, height=600)

    # --- HIỂN THỊ CÂY KHUNG (PRIM/KRUSKAL) ---
    elif st.session_state['cay_khung_mst']:
        m = folium.Map(location=st.session_state['tam_ban_do'], zoom_start=14, tiles="cartodbpositron")
        Fullscreen().add_to(m)

        for canh_toa_do in st.session_state['cay_khung_mst']:
            folium.PolyLine(canh_toa_do, color="#27AE60", weight=3, opacity=0.7).add_to(m)

        st_folium(m, width=1200, height=600)

    # --- MẶC ĐỊNH KHI MỚI VÀO ---
    else:
        m = folium.Map(location=[13.9785, 108.0051], zoom_start=14, tiles="cartodbpositron")
        st_folium(m, width=1200, height=600)

