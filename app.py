import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import heapq
from io import BytesIO

st.set_page_config(page_title="Đồ án: Ứng dụng thuật toán Đồ thị", layout="wide", page_icon="🎓")

def my_bfs(G, start_node):
    """Duyệt chiều rộng (Queue) - Độ phức tạp O(V+E)"""
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
    """Dijkstra dùng Min-Heap - Độ phức tạp O(E log V)"""
    distances = {node: float('infinity') for node in G.nodes()}
    distances[start_node] = 0
    pq = [(0, start_node)]
    parent = {node: None for node in G.nodes()}
    
    while pq:
        d, u = heapq.heappop(pq)
        if u == end_node:""
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
    st.info("👈 Bạn nhập thanh bên trái để bắt đầu nhé .")

