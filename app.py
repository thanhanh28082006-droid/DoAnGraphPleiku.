import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from folium.plugins import AntPath, MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import warnings

# Tắt cảnh báo
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN & CSS ĐẸP MẮT
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Pleiku City Navigation", layout="wide", page_icon="🗺️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

    /* Header */
    h1 { color: #2C3E50; text-align: center; font-weight: 700; letter-spacing: 1px; margin-bottom: 20px; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 20px; }
    .stTabs [data-baseweb="tab"] { background-color: #ECF0F1; border-radius: 10px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #3498DB; color: white !important; font-weight: bold; }

    /* Cards Lộ trình */
    .route-container {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        padding: 20px;
        max-height: 600px;
        overflow-y: auto;
    }

    .timeline-item {
        display: flex;
        padding-bottom: 15px;
        position: relative;
    }

    .timeline-item:last-child { padding-bottom: 0; }

    .timeline-marker {
        flex-shrink: 0;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #E8F6F3;
        color: #1ABC9C;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 15px;
        z-index: 1;
        border: 2px solid #1ABC9C;
    }

    .timeline-content {
        flex-grow: 1;
        background-color: #F8F9F9;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #BDC3C7;
    }

    .timeline-content:hover { background-color: #F0F3F4; border-left-color: #3498DB; transition: 0.3s; }

    .street-name { font-weight: bold; color: #2C3E50; font-size: 1.05em; display: block; }
    .dist-tag { float: right; font-size: 0.85em; color: #E74C3C; font-weight: bold; background: #FADBD8; padding: 2px 8px; border-radius: 10px; }

    /* Stats Box */
    .stats-box {
        display: flex;
        justify-content: space-around;
        background: linear-gradient(135deg, #6DD5FA 0%, #2980B9 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(52, 152, 219, 0.3);
    }
    .stat-item { text-align: center; }
    .stat-value { font-size: 1.5em; font-weight: bold; }
    .stat-label { font-size: 0.9em; opacity: 0.9; }

    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session
if 'G' not in st.session_state: st.session_state['G'] = nx.Graph()
if 'path_nodes' not in st.session_state: st.session_state['path_nodes'] = []
if 'path_detail' not in st.session_state: st.session_state['path_detail'] = []
if 'map_center' not in st.session_state: st.session_state['map_center'] = [13.9785, 108.0051]
if 'mst_edges' not in st.session_state: st.session_state['mst_edges'] = []  # Lưu kết quả Prim/Kruskal


# -----------------------------------------------------------------------------
# HÀM XỬ LÝ LỘ TRÌNH THÔNG MINH
# -----------------------------------------------------------------------------
def get_route_details(G, path_nodes):
    if not path_nodes or len(path_nodes) < 2: return []
    steps = []
    curr_name = None
    curr_dist = 0

    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        data = G.get_edge_data(u, v)[0]
        length = data.get('length', 0)
        name = data.get('name', 'Đường nội bộ')
        if isinstance(name, list): name = name[0]  # Lấy tên đầu tiên nếu có nhiều tên

        if name == curr_name:
            curr_dist += length
        else:
            if curr_name: steps.append({"name": curr_name, "dist": curr_dist})
            curr_name = name
            curr_dist = length
    if curr_name: steps.append({"name": curr_name, "dist": curr_dist})
    return steps


# -----------------------------------------------------------------------------
# HÀM VẼ LÝ THUYẾT
# -----------------------------------------------------------------------------
def draw_theory(graph, path=None, edges=None, title=""):
    fig, ax = plt.subplots(figsize=(8, 5))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw(graph, pos, with_labels=True, node_color='#D6EAF8', edge_color='#BDC3C7', node_size=600, font_weight='bold',
            ax=ax)
    labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels, font_size=9, ax=ax)

    if path:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_color='#E74C3C', node_size=700, ax=ax)
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=3, edge_color='#E74C3C', ax=ax)

    if edges:
        nx.draw_networkx_edges(graph, pos, edgelist=edges, width=3, edge_color='#27AE60', ax=ax)

    ax.set_title(title, color="#2C3E50", fontsize=12)
    st.pyplot(fig)


# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
st.title("🏙️ ỨNG DỤNG CÁC THUẬT TOÁN CHO HỆ THỐNG DẪN ĐƯỜNG THÔNG MINH TP. PLEIKU")

tab1, tab2 = st.tabs(["📚 PHẦN 1: LÝ THUYẾT ĐỒ THỊ", "🚀 PHẦN 2: BẢN ĐỒ THỰC TẾ "])

# =============================================================================
# TAB 1: LÝ THUYẾT
# =============================================================================
with tab1:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.subheader("🛠️ Cấu hình")
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"], horizontal=True)
        directed = True if type_opt == "Có hướng" else False
        inp = st.text_area("Nhập cạnh (u v w):", "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)

        if st.button("Khởi tạo Đồ thị"):
            try:
                G = nx.DiGraph() if directed else nx.Graph()
                for l in inp.split('\n'):
                    p = l.split()
                    if len(p) >= 2: G.add_edge(p[0], p[1], weight=int(p[2]) if len(p) > 2 else 1)
                st.session_state['G'] = G
                st.success("Thành công!")
            except:
                st.error("Lỗi dữ liệu")

    with c2:
        if len(st.session_state['G']) > 0: draw_theory(st.session_state['G'], title="Mô hình trực quan")

    if len(st.session_state['G']) > 0:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("Biểu diễn")
            st.json(nx.to_dict_of_lists(st.session_state['G']), expanded=False)
            st.write(f"Bipartite: {nx.is_bipartite(st.session_state['G'])}")
        with col2:
            st.warning("Thuật toán")
            s = st.selectbox("Start", list(st.session_state['G'].nodes()))
            e = st.selectbox("End", list(st.session_state['G'].nodes()), index=len(st.session_state['G']) - 1)
            if st.button("BFS"):
                p = list(dict(nx.bfs_successors(st.session_state['G'], s)).keys());
                p.insert(0, s)
                draw_theory(st.session_state['G'], path=p, title="BFS Traversal")
            if st.button("DFS"):
                p = list(nx.dfs_preorder_nodes(st.session_state['G'], s))
                draw_theory(st.session_state['G'], path=p, title="DFS Traversal")
            if st.button("Dijkstra"):
                try:
                    p = nx.shortest_path(st.session_state['G'], s, e, weight='weight')
                    draw_theory(st.session_state['G'], path=p, title="Shortest Path")
                except:
                    st.error("No Path")
        with col3:
            st.success("Nâng cao (Cây khung)")
            # CHIA LÀM 2 CỘT CHO PRIM VÀ KRUSKAL
            ck1, ck2 = st.columns(2)
            with ck1:
                if st.button("Prim"):
                    if not directed and nx.is_connected(st.session_state['G']):
                        mst = nx.minimum_spanning_tree(st.session_state['G'], algorithm='prim')
                        draw_theory(st.session_state['G'], edges=list(mst.edges()),
                                    title=f"Prim MST (W={mst.size(weight='weight')})")
                    else:
                        st.error("Lỗi: Đồ thị phải vô hướng & liên thông")
            with ck2:
                if st.button("Kruskal"):  # <-- ĐÃ THÊM KRUSKAL
                    if not directed and nx.is_connected(st.session_state['G']):
                        mst = nx.minimum_spanning_tree(st.session_state['G'], algorithm='kruskal')
                        draw_theory(st.session_state['G'], edges=list(mst.edges()),
                                    title=f"Kruskal MST (W={mst.size(weight='weight')})")
                    else:
                        st.error("Lỗi: Đồ thị phải vô hướng & liên thông")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (100 ĐỊA ĐIỂM)
# =============================================================================
with tab2:
    @st.cache_resource
    def load_map():
        # Bán kính 7km để bao trùm 100 điểm
        return ox.graph_from_point((13.9785, 108.0051), dist=7000, network_type='drive')


    with st.spinner("Đang tải dữ liệu bản đồ TP. Pleiku (Khoảng 45s - Vui lòng đợi)..."):
        try:
            G_map = load_map(); st.success("✅ Đã tải xong bản đồ!")
        except:
            st.error("Lỗi tải map"); st.stop()

    # DANH SÁCH ~100 ĐỊA ĐIỂM (Đã chuẩn hóa tọa độ)
    locations = {
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
    valid_locs = {k: v for k, v in locations.items() if v != (0, 0)}

    c_start, c_end, c_algo = st.columns([1.5, 1.5, 1])
    start = c_start.selectbox("📍 Điểm đi:", list(valid_locs.keys()), index=0)
    end = c_end.selectbox("🏁 Điểm đến:", list(valid_locs.keys()), index=8)
    algo = c_algo.selectbox("Thuật toán:", ["Dijkstra (Tối ưu)", "BFS (Ít rẽ)", "DFS (Minh họa)"])

    st.divider()  # Kẻ ngang phân cách

    # CHIA LÀM 2 CỘT NÚT BẤM (TÌM ĐƯỜNG & QUY HOẠCH)
    col_btn_path, col_btn_plan = st.columns([1, 1])

    with col_btn_path:
        btn_find = st.button("🚀 TÌM ĐƯỜNG (A -> B)", type="primary", use_container_width=True)

    with col_btn_plan:
        # SELECT BOX ĐỂ CHỌN PRIM HOẶC KRUSKAL
        mst_algo_choice = st.selectbox("Thuật toán Quy hoạch:", ["Prim", "Kruskal"], label_visibility="collapsed")
        btn_mst = st.button(f"🌲 QUY HOẠCH ({mst_algo_choice.upper()})", use_container_width=True)

    # --- LOGIC TÌM ĐƯỜNG (A->B) ---
    if btn_find:
        st.session_state['mst_edges'] = []  # Reset MST
        try:
            u_coord, v_coord = valid_locs[start], valid_locs[end]
            orig = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])

            path = []
            if "Dijkstra" in algo:
                path = nx.shortest_path(G_map, orig, dest, weight='length')
            elif "BFS" in algo:
                path = nx.shortest_path(G_map, orig, dest, weight=None)
            elif "DFS" in algo:
                try:
                    path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=150))
                except:
                    path = []

            st.session_state['path_nodes'] = path
            st.session_state['path_detail'] = get_route_details(G_map, path)
            st.session_state['map_center'] = [(u_coord[0] + v_coord[0]) / 2, (u_coord[1] + v_coord[1]) / 2]

        except Exception as e:
            st.error(f"Không tìm thấy đường: {e}")

    # --- LOGIC QUY HOẠCH (MST - PRIM/KRUSKAL) ---
    if btn_mst:
        st.session_state['path_nodes'] = []  # Reset Tìm đường
        try:
            with st.spinner(f"Đang chạy thuật toán {mst_algo_choice} để nối mạng lưới trung tâm..."):
                # Lấy đồ thị con (Bán kính 2km) để chạy nhanh
                center_node = ox.distance.nearest_nodes(G_map, 108.0051, 13.9785)
                subgraph = nx.ego_graph(G_map, center_node, radius=2000, distance='length')

                # CHỌN THUẬT TOÁN DỰA TRÊN SELECTBOX
                algo_key = 'prim' if mst_algo_choice == 'Prim' else 'kruskal'
                mst = nx.minimum_spanning_tree(subgraph.to_undirected(), weight='length', algorithm=algo_key)

                edges_coords = []
                for u, v, data in mst.edges(data=True):
                    if 'geometry' in data:
                        xs, ys = data['geometry'].xy
                        edges_coords.append(list(zip(ys, xs)))
                    else:
                        u_node, v_node = G_map.nodes[u], G_map.nodes[v]
                        edges_coords.append([(u_node['y'], u_node['x']), (v_node['y'], v_node['x'])])

                st.session_state['mst_edges'] = edges_coords
                st.session_state['map_center'] = [13.9785, 108.0051]
                st.success(
                    f"Đã quy hoạch xong bằng {mst_algo_choice}! Tổng chiều dài cáp: {mst.size(weight='length') / 1000:.2f} km")
        except Exception as e:
            st.error(f"Lỗi thuật toán: {e}")

    # --- HIỂN THỊ KẾT QUẢ ---
    if st.session_state['path_nodes']:
        path = st.session_state['path_nodes']
        details = st.session_state['path_detail']
        total_km = sum(d['dist'] for d in details) / 1000

        st.markdown(f"""
        <div class="stats-box">
            <div class="stat-item"><div class="stat-value">{total_km:.2f} km</div><div class="stat-label">Tổng quãng đường</div></div>
            <div class="stat-item"><div class="stat-value">{len(details)}</div><div class="stat-label">Số đoạn đường</div></div>
            <div class="stat-item"><div class="stat-value">{int(total_km * 2)} phút</div><div class="stat-label">Thời gian dự kiến</div></div>
        </div>
        """, unsafe_allow_html=True)

        col_map, col_list = st.columns([2, 1.2])

        with col_list:
            st.markdown("### 📋 Chi tiết lộ trình")
            with st.container(height=600):
                st.markdown('<div class="route-container">', unsafe_allow_html=True)
                st.markdown(f'''
                <div class="timeline-item">
                    <div class="timeline-marker" style="background:#D5F5E3; border-color:#2ECC71; color:#27AE60;">A</div>
                    <div class="timeline-content"><span class="street-name">Bắt đầu: {start}</span></div>
                </div>
                ''', unsafe_allow_html=True)

                for i, step in enumerate(details):
                    st.markdown(f'''
                    <div class="timeline-item">
                        <div class="timeline-marker">{i + 1}</div>
                        <div class="timeline-content">
                            <span class="dist-tag">{step['dist']:.0f} m</span>
                            <span class="street-name">{step['name']}</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                st.markdown(f'''
                <div class="timeline-item">
                    <div class="timeline-marker" style="background:#FADBD8; border-color:#E74C3C; color:#C0392B;">B</div>
                    <div class="timeline-content"><span class="street-name">Đích đến: {end}</span></div>
                </div>
                ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with col_map:
            m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="cartodbpositron")
            Fullscreen().add_to(m)

            folium.Marker(valid_locs[start], icon=folium.Icon(color="green", icon="play", prefix='fa'),
                          popup="START").add_to(m)
            folium.Marker(valid_locs[end], icon=folium.Icon(color="red", icon="flag", prefix='fa'), popup="END").add_to(
                m)

            route_coords = []
            start_node = G_map.nodes[path[0]]
            route_coords.append((start_node['y'], start_node['x']))

            for u, v in zip(path[:-1], path[1:]):
                edge = G_map.get_edge_data(u, v)[0]
                if 'geometry' in edge:
                    xs, ys = edge['geometry'].xy
                    route_coords.extend(list(zip(ys, xs)))
                else:
                    node_v = G_map.nodes[v]
                    route_coords.extend([(node_v['y'], node_v['x'])])

            color = "orange" if "DFS" in algo else ("purple" if "BFS" in algo else "#3498DB")
            AntPath(route_coords, color=color, weight=6, opacity=0.8, delay=1000).add_to(m)

            folium.PolyLine([valid_locs[start], route_coords[0]], color="gray", weight=2, dash_array='5, 5').add_to(m)
            folium.PolyLine([valid_locs[end], route_coords[-1]], color="gray", weight=2, dash_array='5, 5').add_to(m)

            st_folium(m, width=900, height=600)

    # --- HIỂN THỊ MST (PRIM/KRUSKAL) ---
    elif st.session_state['mst_edges']:
        m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="cartodbpositron")
        Fullscreen().add_to(m)

        for edge_coords in st.session_state['mst_edges']:
            folium.PolyLine(edge_coords, color="#27AE60", weight=3, opacity=0.7).add_to(m)

        st_folium(m, width=1200, height=600)

    # --- MẶC ĐỊNH ---
    else:
        m = folium.Map(location=[13.9785, 108.0051], zoom_start=14, tiles="cartodbpositron")
        st_folium(m, width=1200, height=600)