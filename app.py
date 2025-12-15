import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import heapq
from io import BytesIO

st.set_page_config(page_title="Đồ án: Ứng dụng thuật toán Đồ thị", layout="wide", page_icon="🎓")


# ==============================================================================
# PHẦN 1: SỬ DỤNG THƯ VIỆN NETWORKX CHO THUẬT TOÁN
# ==============================================================================

def my_bfs(G, start_node):
    """BFS dùng NetworkX"""
    # nx.bfs_edges trả về các cạnh theo thứ tự duyệt BFS
    edges = list(nx.bfs_edges(G, source=start_node))
    
    # Để lấy thứ tự các đỉnh duyệt, ta có thể dùng bfs_tree hoặc duyệt qua edges
    # Cách đơn giản nhất để lấy list node theo thứ tự:
    path_order = [start_node] + [v for u, v in edges]
    
    return edges, path_order

def my_dfs(G, start_node):
    """DFS dùng NetworkX"""
    # nx.dfs_edges trả về các cạnh theo thứ tự duyệt DFS
    edges = list(nx.dfs_edges(G, source=start_node))
    
    # Lấy thứ tự đỉnh
    path_order = list(nx.dfs_preorder_nodes(G, source=start_node))
    
    return edges, path_order

def my_dijkstra(G, start_node, end_node):
    """Dijkstra dùng NetworkX"""
    try:
        # Tìm đường đi ngắn nhất (trả về danh sách đỉnh)
        path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
        # Tính tổng chi phí
        dist = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
        return path, dist
    except nx.NetworkXNoPath:
        return None, 0

def my_prim(G):
    """Prim MST dùng NetworkX"""
    if G.is_directed(): return None, "Prim chỉ dùng cho đồ thị Vô hướng!"
    if not nx.is_connected(G): return None, "Đồ thị không liên thông!"
    
    # nx.minimum_spanning_tree dùng thuật toán Kruskal hoặc Prim (mặc định Kruskal)
    # Để ép dùng Prim, ta dùng algorithm='prim'
    T = nx.minimum_spanning_tree(G, weight='weight', algorithm='prim')
    
    mst_edges = list(T.edges(data=False))
    total_w = T.size(weight='weight')
    
    return mst_edges, total_w

def my_kruskal(G):
    """Kruskal MST dùng NetworkX"""
    # Kruskal cũng dùng cho đồ thị vô hướng
    if G.is_directed(): # NetworkX vẫn chạy được trên Directed nhưng kết quả là Arborescence, thường MST học là Vô hướng
         # Tuy nhiên hàm minimum_spanning_tree của nx mặc định convert sang undirected nếu cần hoặc chạy trên undirected view
         # Để an toàn và đúng lý thuyết cơ bản:
         return None, "Kruskal thường áp dụng cho đồ thị Vô hướng!"

    T = nx.minimum_spanning_tree(G, weight='weight', algorithm='kruskal')
    
    mst_edges = list(T.edges(data=False))
    total_w = T.size(weight='weight')
    return mst_edges, total_w

def my_ford_fulkerson(G, source, sink):
    """Ford-Fulkerson (Edmonds-Karp) dùng NetworkX"""
    if not G.is_directed(): return None, "Max Flow cần đồ thị CÓ HƯỚNG!"
    
    try:
        # nx.maximum_flow mặc định dùng preflow_push (nhanh hơn), nhưng để đúng tên Ford-Fulkerson/Edmonds-Karp:
        # flow_func=nx.algorithms.flow.edmonds_karp
        from networkx.algorithms.flow import edmonds_karp
        
        flow_value, flow_dict = nx.maximum_flow(G, source, sink, capacity='weight', flow_func=edmonds_karp)
        
        # flow_dict chứa thông tin luồng cụ thể trên từng cạnh, nhưng để đơn giản ta chỉ trả về giá trị max flow
        # và một thông báo thành công. Chi tiết đường đi tăng luồng thì thư viện không trả về trực tiếp dạng list path.
        return flow_value, "Thành công"
    except Exception as e:
        return None, str(e)

def my_hierholzer(G):
    """Chu trình Euler dùng NetworkX"""
    # Kiểm tra điều kiện Euler
    if not nx.is_eulerian(G):
        return None, "Đồ thị không có chu trình Euler!"
    
    # nx.eulerian_circuit trả về iterator các cạnh
    circuit_edges = list(nx.eulerian_circuit(G))
    
    # Chuyển đổi danh sách cạnh thành danh sách đỉnh tuần tự
    path = [u for u, v in circuit_edges]
    path.append(circuit_edges[-1][1]) # Thêm đỉnh cuối cùng
    
    return path, "Thành công"

def my_fleury(G):
    """Đường đi Euler (Fleury tương đương) dùng NetworkX"""
    # NetworkX có hàm has_eulerian_path để kiểm tra đường đi Euler
    if nx.has_eulerian_path(G):
         # nx.eulerian_path tìm đường đi Euler (nếu có chu trình thì nó trả về chu trình)
         path_edges = list(nx.eulerian_path(G))
         path = [u for u, v in path_edges]
         path.append(path_edges[-1][1])
         return path, "Thành công"
    else:
        return None, "Không có đường đi Euler."

def check_bipartite_manual(G):
    """Kiểm tra 2 phía dùng NetworkX"""
    if nx.is_bipartite(G):
        # Lấy 2 tập hợp màu
        color_map = nx.bipartite.color(G)
        return True, color_map
    else:
        return False, {}


# ==============================================================================
# PHẦN 2: GIAO DIỆN & HÀM VẼ (GIỮ NGUYÊN FORM)
# ==============================================================================

def ve_do_thi(G, highlight_edges=None, highlight_nodes=None, title="", color_map=None, show_weights=True):
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 5))
    
    node_colors = 'lightblue'
    if color_map:
        node_colors = [color_map.get(node, 'gray') for node in G.nodes()]
        node_colors = ['#ff7675' if c == 0 else '#74b9ff' if c == 1 else 'gray' for c in node_colors]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=600)
    nx.draw_networkx_labels(G, pos, font_weight='bold')
    nx.draw_networkx_edges(G, pos, edge_color='#b2bec3', width=1, arrows=G.is_directed(), arrowsize=15)
    
    if show_weights:
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    
    if highlight_edges:
        nx.draw_networkx_edges(G, pos, edgelist=highlight_edges, edge_color='#e17055', width=3)
    if highlight_nodes:
        nx.draw_networkx_nodes(G, pos, nodelist=highlight_nodes, node_color='#fab1a0', node_size=650)
        
    plt.title(title, fontsize=14)
    plt.axis('off')
    return plt

st.title("🎓 ỨNG DỤNG THUẬT TOÁN ĐỒ THỊ ")
st.markdown("---")

with st.sidebar:
    st.header("1. Nhập Dữ Liệu")
    
    # Thêm tùy chọn Có/Không trọng số
    type_g = st.radio("Hướng đồ thị:", ["Vô hướng", "Có hướng"])
    is_weighted = st.checkbox("Đồ thị có trọng số?", value=True)
    
    input_text = st.text_area("Nhập cạnh (u v w):", "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4")
    
    st.caption("Nếu không chọn 'Có trọng số', giá trị w sẽ bị bỏ qua (mặc định = 1).")
    
    if st.button("🚀 Khởi tạo Đồ thị", type="primary"):
        G = nx.DiGraph() if type_g == "Có hướng" else nx.Graph()
        try:
            for line in input_text.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    u, v = parts[0], parts[1]
                    if is_weighted and len(parts) > 2:
                        w = int(parts[2])
                    else:
                        w = 1 
                    
                    G.add_edge(u, v, weight=w)
            
            st.session_state['graph'] = G
            st.session_state['input_raw'] = input_text
            st.session_state['is_weighted'] = is_weighted 
            st.success("Đã nạp dữ liệu!")
        except ValueError: st.error("Lỗi: Trọng số phải là số nguyên!")
        except Exception as e: st.error(f"Lỗi định dạng: {e}")

    if 'input_raw' in st.session_state:
        st.divider()
        st.write("📂 **Lưu trữ:**")
        st.download_button("💾 Tải file Graph.txt", st.session_state['input_raw'], "graph.txt")

if 'graph' in st.session_state:
    G = st.session_state['graph']
    weighted_mode = st.session_state.get('is_weighted', True)
    
    tab1, tab2, tab3 = st.tabs(["🖼️ Thuật toán & Trực quan", "📊 Cấu trúc dữ liệu", "🔍 Kiểm tra tính chất"])
    
    # TAB 1: THUẬT TOÁN
    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Bảng điều khiển")
            algo = st.selectbox("Chọn thuật toán:", 
                ["BFS", 
                 "DFS", 
                 "Dijkstra", 
                 "Prim", 
                 "Kruskal", 
                 "Ford-Fulkerson", 
                 "Hierholzer",
                 "Fleury"])
            
            nodes = list(G.nodes())
            start = st.selectbox("Đỉnh bắt đầu:", nodes)
            end = st.selectbox("Đỉnh đích:", nodes, index=len(nodes)-1)
            
            run_btn = st.button("▶️ Chạy mô phỏng", type="primary")

            with st.expander("📚 Kiến thức thuật toán"):
                if "BFS" in algo:
                    st.markdown("**Độ phức tạp:** O(V + E)")
                    st.write("Sử dụng hàng đợi (Queue). Duyệt theo từng lớp lan rộng ra xung quanh.")
                elif "DFS" in algo:
                    st.markdown("**Độ phức tạp:** O(V + E)")
                    st.write("Sử dụng ngăn xếp (Stack) hoặc đệ quy. Đi sâu nhất có thể trước khi quay lui.")
                elif "Dijkstra" in algo:
                    st.markdown("**Độ phức tạp:** O((V + E) log V)")
                    st.write("Sử dụng Min-Heap. Giải thuật tham lam chọn đỉnh có đường đi ngắn nhất hiện tại.")
                elif "Prim" in algo:
                    st.markdown("**Độ phức tạp:** O(E log V)")
                    st.write("Giống Dijkstra nhưng dùng để tìm cây khung nhỏ nhất. Phát triển cây từ 1 đỉnh.")
                elif "Kruskal" in algo:
                    st.markdown("**Độ phức tạp:** O(E log E)")
                    st.write("Sắp xếp các cạnh tăng dần và dùng cấu trúc Union-Find để nối các đỉnh.")
                elif "Ford-Fulkerson" in algo:
                    st.markdown("**Độ phức tạp:** O(V E^2)")
                    st.write("Sử dụng phương pháp Edmonds-Karp (BFS) để tìm đường tăng luồng trên đồ thị thặng dư.")
                else:
                    st.write("Thuật toán tìm chu trình đi qua tất cả các cạnh đúng 1 lần.")
            
        with c2:
            fig = None
            msg = ""
            if run_btn:
                try:
                    # Truyền tham số show_weights=weighted_mode vào hàm vẽ
                    
                    if "BFS" in algo:
                        edges, order = my_bfs(G, start)
                        fig = ve_do_thi(G, highlight_edges=edges, title=f"BFS từ {start}", show_weights=weighted_mode)
                        msg = f"Thứ tự duyệt: {order}"
                        
                    elif "DFS" in algo:
                        edges, order = my_dfs(G, start)
                        fig = ve_do_thi(G, highlight_edges=edges, title=f"DFS từ {start}", show_weights=weighted_mode)
                        msg = f"Thứ tự duyệt: {order}"
                        
                    elif "Dijkstra" in algo:
                        path, dist = my_dijkstra(G, start, end)
                        if path:
                            edges = list(zip(path, path[1:]))
                            fig = ve_do_thi(G, highlight_edges=edges, highlight_nodes=path, title=f"Chi phí: {dist}", show_weights=weighted_mode)
                            msg = f"Đường đi: {' → '.join(path)}"
                        else: st.error("Không có đường đi")
                        
                    elif "Prim" in algo:
                        mst, w = my_prim(G)
                        if mst:
                            fig = ve_do_thi(G, highlight_edges=mst, title=f"Prim Cost: {w}", show_weights=weighted_mode)
                            msg = f"Các cạnh MST: {mst}"
                        else: st.error(w)
                        
                    elif "Kruskal" in algo:
                        mst, w = my_kruskal(G)
                        if mst:
                            fig = ve_do_thi(G, highlight_edges=mst, title=f"Kruskal Cost: {w}", show_weights=weighted_mode)
                            msg = f"Các cạnh MST: {mst}"
                        else: st.error(w)
                        
                    elif "Ford-Fulkerson" in algo:
                        val, details = my_ford_fulkerson(G, start, end)
                        if val is not None:
                            fig = ve_do_thi(G, title=f"Max Flow: {val}", show_weights=weighted_mode)
                            msg = f"Luồng cực đại: {val}"
                        else: st.error(details)

                    elif "Hierholzer" in algo:
                        path, err = my_hierholzer(G)
                        if path:
                            edges = list(zip(path, path[1:]))
                            fig = ve_do_thi(G, highlight_edges=edges, title="Hierholzer Circuit", show_weights=weighted_mode)
                            msg = f"Chu trình: {' → '.join(map(str, path))}"
                        else: st.error(err)
                        
                    elif "Fleury" in algo:
                        path, err = my_fleury(G)
                        if path:
                            edges = list(zip(path, path[1:]))
                            fig = ve_do_thi(G, highlight_edges=edges, title="Fleury Path", show_weights=weighted_mode)
                            msg = f"Đường đi Euler: {' → '.join(map(str, path))}"
                        else: st.error(err)
                        
                except Exception as e: st.error(f"Lỗi runtime: {e}")
            
            else:
                fig = ve_do_thi(G, title="Đồ thị ban đầu", show_weights=weighted_mode)

            st.pyplot(fig)
            if msg: st.info(msg)

    # TAB 2: BIỂU DIỄN DỮ LIỆU
    with tab2:
        st.subheader("🔁 Chuyển đổi các dạng biểu diễn")
        st.markdown("Giúp so sánh cách máy tính lưu trữ đồ thị trong bộ nhớ.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write("###### 1. Danh sách cạnh ")
            df_edges = nx.to_pandas_edgelist(G)
            if not weighted_mode and 'weight' in df_edges.columns:
                df_edges = df_edges.drop(columns=['weight'])
            st.dataframe(df_edges, hide_index=True, use_container_width=True)
        with c2:
            st.write("###### 2. Ma trận kề ")
            matrix = nx.adjacency_matrix(G).todense()
            st.dataframe(pd.DataFrame(matrix, index=G.nodes(), columns=G.nodes()), use_container_width=True)
        with c3:
            st.write("###### 3. Danh sách kề ")
            adj_dict = {n: list(G.neighbors(n)) for n in G.nodes()}
            st.json(adj_dict)

    # TAB 3: KIỂM TRA TÍNH CHẤT
    with tab3:
        st.subheader("Kiểm tra Đồ thị 2 phía ")
        is_bi, color_map = check_bipartite_manual(G)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            if is_bi:
                st.success("✅ ĐÚNG là đồ thị 2 phía")
                set_0 = [n for n, c in color_map.items() if c == 0]
                set_1 = [n for n, c in color_map.items() if c == 1]
                st.write(f"**Tập U:** {set_0}")
                st.write(f"**Tập V:** {set_1}")
            else:
                st.error("❌ KHÔNG PHẢI đồ thị 2 phía")
        with c2:
            if is_bi:
                fig_bi = ve_do_thi(G, title="Phân lớp 2 phía (Đỏ - Xanh)", color_map=color_map, show_weights=weighted_mode)
                st.pyplot(fig_bi)

else:
    st.info("👈Bạn nhập thanh dữ liệu bên trái để bắt đầu nhé .")
