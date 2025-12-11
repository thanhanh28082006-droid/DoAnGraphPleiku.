import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Graph Theory Master", layout="wide", page_icon="🔮")


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #f0f2f6; 
        border-right: 1px solid #e0e0e0;
    }
    
    /* Tiêu đề */
    .main-header {
        font-family: 'JetBrains Mono', monospace;
        color: #2d3436;
        font-weight: 700;
        font-size: 2.2em;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #0984e3;
    }
    
    /* Card chứa đồ thị */
    .viz-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #dfe6e9;
        margin-bottom: 20px;
    }
    
    /* Kết quả thuật toán */
    .algo-result {
        background-color: #2d3436;
        color: #00cec9;
        padding: 15px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        border-left: 5px solid #00cec9;
    }
    
    /* Nút bấm */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO SESSION
if 'do_thi' not in st.session_state: st.session_state['do_thi'] = nx.Graph()
if 'algo_run' not in st.session_state: st.session_state['algo_run'] = None
if 'algo_result_fig' not in st.session_state: st.session_state['algo_result_fig'] = None
if 'algo_message' not in st.session_state: st.session_state['algo_message'] = ""

# 3. CÁC HÀM HỖ TRỢ & THUẬT TOÁN
def ve_do_thi(do_thi, duong_di=None, danh_sach_canh=None, tieu_de="", highlight_color='#e74c3c'):
    is_directed = do_thi.is_directed()
    fig, ax = plt.subplots(figsize=(8, 6)) 
    
    try:
        pos = nx.spring_layout(do_thi, seed=42, k=0.5)
        
        nx.draw_networkx_nodes(do_thi, pos, node_color='white', edgecolors='#2d3436', node_size=600, ax=ax)
        nx.draw_networkx_labels(do_thi, pos, font_size=10, font_family='sans-serif', font_weight='bold', ax=ax)
        nx.draw_networkx_edges(do_thi, pos, edge_color='#b2bec3', width=1.5, ax=ax, arrows=is_directed, arrowstyle='-|>', arrowsize=15)
        
        labels = nx.get_edge_attributes(do_thi, 'weight')
        nx.draw_networkx_edge_labels(do_thi, pos, edge_labels=labels, font_size=9, ax=ax)

        if duong_di:
            # Vẽ Node trên đường đi
            nx.draw_networkx_nodes(do_thi, pos, nodelist=duong_di, node_color=highlight_color, node_size=600, ax=ax)
            # Vẽ Cạnh trên đường đi
            path_edges = list(zip(duong_di, duong_di[1:]))
            nx.draw_networkx_edges(do_thi, pos, edgelist=path_edges, edge_color=highlight_color, width=3, ax=ax, arrows=is_directed)
            
        if danh_sach_canh:
            nodes_in_edges = set()
            for u, v in danh_sach_canh:
                nodes_in_edges.add(u); nodes_in_edges.add(v)
            nx.draw_networkx_nodes(do_thi, pos, nodelist=list(nodes_in_edges), node_color=highlight_color, node_size=600, ax=ax)
            nx.draw_networkx_edges(do_thi, pos, edgelist=danh_sach_canh, edge_color=highlight_color, width=3, ax=ax, arrows=is_directed)

        ax.set_title(tieu_de, fontsize=14, fontweight='bold', color='#2d3436', pad=10)
        ax.axis('off')
        return fig
    except Exception as e:
        return None

def thuat_toan_fleury(G_input):
    G = G_input.copy()
    bac_le = [v for v, d in G.degree() if d % 2 == 1]
    if len(bac_le) not in [0, 2]: return None, "Không thỏa mãn điều kiện Euler (Số bậc lẻ != 0 hoặc 2)"
    u = bac_le[0] if len(bac_le) == 2 else list(G.nodes())[0]
    path = []; edges_path = []
    
    while G.number_of_edges() > 0:
        neighbors = list(G.neighbors(u))
        if not neighbors: return None, "Đồ thị không liên thông"
        next_v = None
        for v in neighbors:
            if G.degree(u) == 1: next_v = v; break
            G.remove_edge(u, v)
            if nx.has_path(G, u, v): next_v = v; G.add_edge(u, v); break
            else: G.add_edge(u, v, weight=1)
        if next_v is None: next_v = neighbors[0]
        if G.has_edge(u, next_v):
            G.remove_edge(u, next_v); edges_path.append((u, next_v)); path.append(next_v); u = next_v
    return edges_path, "Thành công"

# =============================================================================
# 4. GIAO DIỆN 
# =============================================================================

# --- HEADER ---
st.markdown('<div class="main-header">🔮 GRAPH THEORY MASTER</div>', unsafe_allow_html=True)

# --- SIDEBAR: KHU VỰC ĐIỀU KHIỂN ---
with st.sidebar:
    st.header("⚙️ CẤU HÌNH")
    
    # 1. Nhập liệu
    with st.expander("📝 Dữ liệu Đồ thị", expanded=True):
        loai_do_thi = st.radio("Loại:", ["Vô hướng (Graph)", "Có hướng (DiGraph)"], horizontal=True)
        is_directed = True if "Có hướng" in loai_do_thi else False
        
        default_data = "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4"
        raw_data = st.text_area("Nhập cạnh (u v w):", value=default_data, height=150, help="Mỗi dòng một cạnh. Ví dụ: A B 4")
        
        if st.button("🔄 KHỞI TẠO / RESET", type="primary"):
            try:
                G = nx.DiGraph() if is_directed else nx.Graph()
                for line in raw_data.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        u, v = parts[0], parts[1]
                        w = int(parts[2]) if len(parts) > 2 else 1
                        G.add_edge(u, v, weight=w)
                st.session_state['do_thi'] = G
                st.session_state['algo_run'] = None # Reset kết quả cũ
                st.success(f"Đã tạo: {G.number_of_nodes()} đỉnh, {G.number_of_edges()} cạnh")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi dữ liệu: {e}")

    # 2. Chọn thuật toán
    st.divider()
    st.header("🧮 THUẬT TOÁN")
    
    if len(st.session_state['do_thi']) > 0:
        algo = st.selectbox("Chọn giải thuật:", 
            ["Dijkstra (Ngắn nhất)", "BFS (Chiều rộng)", "DFS (Chiều sâu)", 
             "Prim (MST)", "Kruskal (MST)", "Fleury (Euler)", "Ford-Fulkerson (Max Flow)"])
        
        # Hiển thị input start/end tùy thuật toán
        col_start, col_end = st.columns(2)
        nodes = list(st.session_state['do_thi'].nodes())
        
        with col_start:
            start_node = st.selectbox("Start:", nodes) if nodes else None
        
        with col_end:
            # Các thuật toán cần điểm đích
            need_target = ["Dijkstra", "Ford-Fulkerson"]
            # Các thuật toán cần điểm đích (tùy chọn cho BFS/DFS visual)
            if any(x in algo for x in need_target) or "BFS" in algo or "DFS" in algo:
                end_node = st.selectbox("End:", nodes, index=len(nodes)-1) if nodes else None
            else:
                end_node = None

        if st.button("▶️ CHẠY THUẬT TOÁN"):
            G_curr = st.session_state['do_thi']
            fig = None
            msg = ""
            
            try:
                if "BFS" in algo:
                    tree = list(nx.bfs_tree(G_curr, start_node).edges())
                    fig = ve_do_thi(G_curr, danh_sach_canh=tree, tieu_de=f"BFS Tree từ {start_node}", highlight_color='#0984e3')
                    msg = f"Đã duyệt {len(tree)} cạnh theo chiều rộng."
                    
                elif "DFS" in algo:
                    tree = list(nx.dfs_tree(G_curr, start_node).edges())
                    fig = ve_do_thi(G_curr, danh_sach_canh=tree, tieu_de=f"DFS Tree từ {start_node}", highlight_color='#e84393')
                    msg = f"Đã duyệt {len(tree)} cạnh theo chiều sâu."
                    
                elif "Dijkstra" in algo:
                    try:
                        path = nx.shortest_path(G_curr, start_node, end_node, weight='weight')
                        length = nx.shortest_path_length(G_curr, start_node, end_node, weight='weight')
                        fig = ve_do_thi(G_curr, duong_di=path, tieu_de=f"Dijkstra: {start_node} → {end_node} (W={length})", highlight_color='#00b894')
                        msg = f"Đường đi ngắn nhất: {' → '.join(path)}\nTổng trọng số: {length}"
                    except:
                        msg = "Không có đường đi giữa 2 điểm này."
                
                elif "Prim" in algo:
                    if not G_curr.is_directed() and nx.is_connected(G_curr):
                        mst = list(nx.minimum_spanning_tree(G_curr, algorithm='prim').edges())
                        w = sum(G_curr[u][v]['weight'] for u,v in mst)
                        fig = ve_do_thi(G_curr, danh_sach_canh=mst, tieu_de=f"Prim MST (Total W={w})", highlight_color='#fdcb6e')
                        msg = f"Cây khung nhỏ nhất (Prim): {len(mst)} cạnh.\nTổng trọng số: {w}"
                    else: msg = "Lỗi: Prim chỉ áp dụng cho đồ thị Vô hướng & Liên thông."
                
                elif "Kruskal" in algo:
                    if not G_curr.is_directed() and nx.is_connected(G_curr):
                        mst = list(nx.minimum_spanning_tree(G_curr, algorithm='kruskal').edges())
                        w = sum(G_curr[u][v]['weight'] for u,v in mst)
                        fig = ve_do_thi(G_curr, danh_sach_canh=mst, tieu_de=f"Kruskal MST (Total W={w})", highlight_color='#fdcb6e')
                        msg = f"Cây khung nhỏ nhất (Kruskal): {len(mst)} cạnh.\nTổng trọng số: {w}"
                    else: msg = "Lỗi: Kruskal chỉ áp dụng cho đồ thị Vô hướng & Liên thông."
                
                elif "Fleury" in algo:
                    if not G_curr.is_directed() and nx.is_connected(G_curr):
                        path, err = thuat_toan_fleury(G_curr)
                        if path:
                            fig = ve_do_thi(G_curr, danh_sach_canh=path, tieu_de="Fleury (Euler Path/Circuit)", highlight_color='#6c5ce7')
                            msg = f"Tìm thấy đường đi Euler qua {len(path)} cạnh."
                        else: msg = f"Lỗi: {err}"
                    else: msg = "Lỗi: Cần đồ thị Vô hướng & Liên thông."
                
                elif "Ford-Fulkerson" in algo:
                    if G_curr.is_directed():
                        val, flow_dict = nx.maximum_flow(G_curr, start_node, end_node, capacity='weight')
                        edges_flow = [(u, v) for u in flow_dict for v, f in flow_dict[u].items() if f > 0]
                        fig = ve_do_thi(G_curr, danh_sach_canh=edges_flow, tieu_de=f"Max Flow: {val}", highlight_color='#d63031')
                        msg = f"Luồng cực đại từ {start_node} đến {end_node}: {val}"
                    else: msg = "Lỗi: Ford-Fulkerson cần đồ thị CÓ HƯỚNG."

            except Exception as e:
                msg = f"Đã xảy ra lỗi: {e}"
            
            st.session_state['algo_run'] = True
            st.session_state['algo_result_fig'] = fig
            st.session_state['algo_message'] = msg
            st.rerun()

# --- MAIN CONTENT ---
col_viz, col_data = st.columns([2, 1])

# CỘT TRÁI: HIỂN THỊ ĐỒ THỊ
with col_viz:
    st.markdown('<div class="viz-card">', unsafe_allow_html=True)
    if st.session_state['algo_run'] and st.session_state['algo_result_fig']:
        # Hiển thị kết quả thuật toán
        st.pyplot(st.session_state['algo_result_fig'])
        st.markdown(f'<div class="algo-result">{st.session_state["algo_message"]}</div>', unsafe_allow_html=True)
    elif len(st.session_state['do_thi']) > 0:
        # Hiển thị đồ thị gốc
        fig = ve_do_thi(st.session_state['do_thi'], tieu_de="Đồ thị ban đầu")
        st.pyplot(fig)
        st.info("👈 Chọn thuật toán bên trái để bắt đầu phân tích.")
    else:
        st.warning("Chưa có dữ liệu. Vui lòng tạo đồ thị ở thanh bên trái.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_data:
    st.markdown("### 📊 Dữ liệu chi tiết")
    if len(st.session_state['do_thi']) > 0:
        G = st.session_state['do_thi']
        
        tab_mat, tab_ds, tab_canh = st.tabs(["Ma trận", "Danh sách kề", "Cạnh"])
        
        with tab_mat:
            # Ma trận kề
            df_mat = nx.adjacency_matrix(G).todense()
            st.dataframe(pd.DataFrame(df_mat, index=G.nodes(), columns=G.nodes()), height=400)
            
        with tab_ds:
            # Danh sách kề
            adj_data = [{"Đỉnh": n, "Kề": str([f"{nbr}({w['weight']})" for nbr, w in nbrs.items()])} 
                        for n, nbrs in nx.to_dict_of_dicts(G).items()]
            st.dataframe(pd.DataFrame(adj_data), height=400, hide_index=True)
            
        with tab_canh:
            # Danh sách cạnh
            edge_data = [{"U": u, "V": v, "Weight": d['weight']} for u, v, d in G.edges(data=True)]
            st.dataframe(pd.DataFrame(edge_data), height=400, hide_index=True)
            
        # Thống kê nhanh
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Số đỉnh", G.number_of_nodes())
        c2.metric("Số cạnh", G.number_of_edges())
        st.caption(f"Đồ thị 2 phía: {'✅ Có' if nx.is_bipartite(G) else '❌ Không'}")
