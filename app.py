import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import heapq
from io import BytesIO

st.set_page_config(page_title="Đồ án: Ứng dụng thuật toán Đồ thị", layout="wide", page_icon="🎓")


def my_bfs(G, start_node):
    visited = set()
    queue = [start_node]
    visited.add(start_node)
    path_order = []
    edges_path = []
    
    while queue:
        u = queue.pop(0)
        path_order.append(u)
        neighbors = sorted(list(G.neighbors(u))) 
        for v in neighbors:
            if v not in visited:
                visited.add(v)
                queue.append(v)
                edges_path.append((u, v))
    return edges_path, path_order

def my_dfs(G, start_node):
    visited = set()
    stack = [start_node]
    path_order = []
    edges_path = []
    
    while stack:
        u = stack.pop()
        if u not in visited:
            visited.add(u)
            path_order.append(u)
            neighbors = sorted(list(G.neighbors(u)), reverse=True) 
            for v in neighbors:
                if v not in visited:
                    stack.append(v)
                    edges_path.append((u, v))
    return edges_path, path_order

def my_dijkstra(G, start_node, end_node):
    distances = {node: float('infinity') for node in G.nodes()}
    distances[start_node] = 0
    pq = [(0, start_node)]
    parent = {node: None for node in G.nodes()}
    
    while pq:
        d, u = heapq.heappop(pq)
        if u == end_node: break
        if d > distances[u]: continue
        
        for v in G.neighbors(u):
            weight = G[u][v].get('weight', 1)
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                parent[v] = u
                heapq.heappush(pq, (distances[v], v))
    
    path = []
    curr = end_node
    if distances[end_node] == float('infinity'): return None, 0
    while curr is not None:
        path.insert(0, curr)
        curr = parent[curr]
    return path, distances[end_node]

def my_prim(G):
    if G.is_directed(): return None, "Prim chỉ dùng cho đồ thị Vô hướng!"
    if not nx.is_connected(G): return None, "Đồ thị không liên thông!"
    
    start_node = list(G.nodes())[0]
    mst_edges = []
    visited = {start_node}
    edges_heap = []
    
    for v in G.neighbors(start_node):
        w = G[start_node][v].get('weight', 1)
        heapq.heappush(edges_heap, (w, start_node, v))
        
    total_w = 0
    while len(mst_edges) < len(G.nodes()) - 1 and edges_heap:
        w, u, v = heapq.heappop(edges_heap)
        if v not in visited:
            visited.add(v)
            mst_edges.append((u, v))
            total_w += w
            for next_n in G.neighbors(v):
                if next_n not in visited:
                    new_w = G[v][next_n].get('weight', 1)
                    heapq.heappush(edges_heap, (new_w, v, next_n))
    return mst_edges, total_w

def my_kruskal(G):
    edges = sorted([(data.get('weight', 1), u, v) for u, v, data in G.edges(data=True)])
    parent = {n: n for n in G.nodes()}
    def find(n):
        if parent[n] != n: parent[n] = find(parent[n])
        return parent[n]
    def union(u, v):
        r1, r2 = find(u), find(v)
        if r1 != r2: parent[r1] = r2; return True
        return False
    
    mst = []
    total_w = 0
    for w, u, v in edges:
        if union(u, v):
            mst.append((u, v))
            total_w += w
    return mst, total_w

def my_ford_fulkerson(G, source, sink):
    if not G.is_directed(): return None, "Max Flow cần đồ thị CÓ HƯỚNG!"
    
    R = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        capacity = data.get('weight', 1)
        R.add_edge(u, v, capacity=capacity)
        R.add_edge(v, u, capacity=0) 
        
    max_flow = 0
    path_flow_details = []
    
    while True:
        parent = {node: None for node in R.nodes()}
        queue = [source]
        path_found = False
        while queue:
            u = queue.pop(0)
            if u == sink:
                path_found = True
                break
            for v in R.neighbors(u):
                if parent[v] is None and R[u][v]['capacity'] > 0:
                    parent[v] = u
                    queue.append(v)
        
        if not path_found: break
        
        path_flow = float('inf')
        v = sink
        path = []
        while v != source:
            u = parent[v]
            path.insert(0, v); path.insert(0, u)
            path_flow = min(path_flow, R[u][v]['capacity'])
            v = u
            
        max_flow += path_flow
        path_flow_details.append((list(dict.fromkeys(path)), path_flow))
        
        v = sink
        while v != source:
            u = parent[v]
            R[u][v]['capacity'] -= path_flow
            R[v][u]['capacity'] += path_flow
            v = u
            
    return max_flow, path_flow_details

def my_hierholzer(G):
    if not nx.is_connected(G.to_undirected()): return None, "Đồ thị không liên thông!"
    
    if not G.is_directed():
        odd_nodes = [v for v, d in G.degree() if d % 2 != 0]
        if odd_nodes: return None, "Không có chu trình Euler (Có đỉnh bậc lẻ)."
    else:
        for v in G.nodes():
            if G.out_degree(v) != G.in_degree(v):
                return None, "Không có chu trình Euler (Bán bậc ra != Bán bậc vào)."

    temp_G = G.copy()
    if G.is_directed(): temp_G = nx.MultiDiGraph(G)
    else: temp_G = nx.MultiGraph(G)
        
    stack = [list(temp_G.nodes())[0]]
    circuit = []
    
    while stack:
        u = stack[-1]
        if temp_G.degree(u) > 0:
            v = list(temp_G.neighbors(u))[0]
            temp_G.remove_edge(u, v)
            stack.append(v)
        else:
            circuit.append(stack.pop())
            
    return circuit[::-1], "Thành công"

def my_fleury(G):
    if not nx.is_connected(G.to_undirected()): return None, "Đồ thị không liên thông!"
    
    odd_nodes = [v for v, d in G.degree() if d % 2 != 0]
    if len(odd_nodes) > 2: return None, "Không có đường đi Euler (Quá nhiều đỉnh bậc lẻ)."
    
    u = odd_nodes[0] if odd_nodes else list(G.nodes())[0]
    
    temp_G = G.copy()
    path = [u]
    
    while temp_G.number_of_edges() > 0:
        neighbors = list(temp_G.neighbors(u))
        
        next_v = None
        for v in neighbors:
            temp_G.remove_edge(u, v)
            if nx.has_path(temp_G, u, v) or temp_G.degree(u) == 0: 
                next_v = v
                break 
            else:
                temp_G.add_edge(u, v, weight=1)
        
        if next_v is None and neighbors:
            next_v = neighbors[0]
            temp_G.remove_edge(u, next_v)
            
        if next_v:
            path.append(next_v)
            u = next_v
        else:
            break
            
    return path, "Thành công"

def check_bipartite_manual(G):
    """Kiểm tra đồ thị 2 phía bằng BFS tô màu"""
    color = {}
    for node in G.nodes():
        if node not in color:
            color[node] = 0
            queue = [node]
            while queue:
                u = queue.pop(0)
                for v in G.neighbors(u):
                    if v not in color:
                        color[v] = 1 - color[u]
                        queue.append(v)
                    elif color[v] == color[u]:
                        return False, {}
    return True, color


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
                    # Xử lý trọng số dựa trên lựa chọn của người dùng
                    if is_weighted and len(parts) > 2:
                        w = int(parts[2])
                    else:
                        w = 1 # Mặc định là 1 nếu không có trọng số
                    
                    G.add_edge(u, v, weight=w)
            
            st.session_state['graph'] = G
            st.session_state['input_raw'] = input_text
            st.session_state['is_weighted'] = is_weighted # Lưu trạng thái để dùng lúc vẽ
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
                ["BFS (Duyệt chiều rộng)", 
                 "DFS (Duyệt chiều sâu)", 
                 "Dijkstra (Đường đi ngắn nhất)", 
                 "Prim (MST - Cây khung)", 
                 "Kruskal (MST - Cây khung)", 
                 "Ford-Fulkerson (Luồng cực đại)", 
                 "Hierholzer (Chu trình Euler)",
                 "Fleury (Đường đi Euler)"])
            
            nodes = list(G.nodes())
            start = st.selectbox("Đỉnh bắt đầu:", nodes)
            end = st.selectbox("Đỉnh đích:", nodes, index=len(nodes)-1)
            
            run_btn = st.button("▶️ Chạy mô phỏng", type="primary")

            with st.expander("📚 Kiến thức thuật toán (Cho báo cáo)"):
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
            st.write("###### 1. Danh sách cạnh (Edge List)")
            df_edges = nx.to_pandas_edgelist(G)
            # Ẩn cột weight nếu là không trọng số để đỡ rối mắt
            if not weighted_mode and 'weight' in df_edges.columns:
                df_edges = df_edges.drop(columns=['weight'])
            st.dataframe(df_edges, hide_index=True, use_container_width=True)
            st.caption("📝 **Ý nghĩa:** Chỉ lưu trữ các cặp đỉnh nối. Tiết kiệm bộ nhớ nhất (Sparse Graph).")
        with c2:
            st.write("###### 2. Ma trận kề (Adj Matrix)")
            matrix = nx.adjacency_matrix(G).todense()
            st.dataframe(pd.DataFrame(matrix, index=G.nodes(), columns=G.nodes()), use_container_width=True)
            st.caption("📝 **Ý nghĩa:** Dùng mảng 2 chiều. Ô [i][j] > 0 tức là có cạnh. Tra cứu cực nhanh O(1).")
        with c3:
            st.write("###### 3. Danh sách kề (Adj List)")
            adj_dict = {n: list(G.neighbors(n)) for n in G.nodes()}
            st.json(adj_dict)
            st.caption("📝 **Ý nghĩa:** Mỗi đỉnh lưu danh sách các hàng xóm. Cân bằng giữa tốc độ và bộ nhớ.")

    # TAB 3: KIỂM TRA TÍNH CHẤT
    with tab3:
        st.subheader("Kiểm tra Đồ thị 2 phía (Bipartite)")
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
                st.write("Nguyên nhân: Tồn tại chu trình lẻ hoặc cạnh nối 2 đỉnh cùng màu.")
        with c2:
            if is_bi:
                fig_bi = ve_do_thi(G, title="Phân lớp 2 phía (Đỏ - Xanh)", color_map=color_map, show_weights=weighted_mode)
                st.pyplot(fig_bi)

else:
    st.info("👈Bạn nhập thanh dữ liệu bên trái để bắt đầu nhé .")
