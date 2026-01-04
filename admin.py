import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import webbrowser
import os
import customtkinter as ctk  # <--- Modern UI Library

# --- AUTO DISCOVERY SETTINGS ---
TCP_PORT = 9999
BROADCAST_PORT = 55555

def scan_for_server():
    """Network par chillata hai: 'SERVER KAHAN HAI?'"""
    print("Scanning for Server...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(1)
    
    msg = "DISCOVER_SERVER"
    server_ip = None
    
    try:
        for _ in range(3): # 3 baar koshish karega
            udp_socket.sendto(msg.encode('utf-8'), ('<broadcast>', BROADCAST_PORT))
            try:
                data, addr = udp_socket.recvfrom(1024)
                if data.decode('utf-8') == "SERVER_HERE":
                    server_ip = addr[0]
                    break
            except socket.timeout:
                continue
    except:
        pass
    
    udp_socket.close()
    return server_ip

# --- INITIALIZE CONNECTION ---
SERVER_IP = scan_for_server()
if not SERVER_IP:
    SERVER_IP = "127.0.0.1" # Fallback

print(f"Server Found at: {SERVER_IP}")

# --- THEME SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- FUNCTION: Generate & Print Report ---
def print_report():
    rows = get_data_from_server()
    if not rows:
        messagebox.showwarning("Empty", "No data available to print!")
        return

    total_sales = sum(float(row[3]) for row in rows if row[4] == 'DONE')
    total_orders = len(rows)

    html_content = f"""
    <html>
    <head>
        <title>Sales Report</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            h1 {{ text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #007bff; color: white; }}
            .done {{ color: green; font-weight: bold; }}
            .pending {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>🧾 SALES REPORT</h1>
        <div>Total Orders: {total_orders} <br> Total Earnings: Rs. {total_sales:.2f}</div>
        <table>
            <tr><th>ID</th><th>Table</th><th>Items</th><th>Price</th><th>Status</th><th>Time</th></tr>
    """

    for row in rows:
        r_id, r_table, r_items, r_price, r_status, r_time = row
        status_class = "done" if r_status == 'DONE' else "pending"
        html_content += f"<tr><td>{r_id}</td><td>{r_table}</td><td>{r_items}</td><td>{r_price}</td><td class='{status_class}'>{r_status}</td><td>{r_time}</td></tr>"

    html_content += "</table><script>window.print();</script></body></html>"

    file_path = os.path.abspath("sales_report.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    webbrowser.open(f"file://{file_path}")

# --- FUNCTION: Network Fetch ---
def get_data_from_server():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        client.connect((SERVER_IP, TCP_PORT))
        client.send("ADMIN_GET_DATA".encode('utf-8'))
        
        data = b""
        while True:
            packet = client.recv(4096)
            if not packet: break
            data += packet
        
        client.close()
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        return []

# --- GUI UPDATER ---
def load_data():
    for item in tree.get_children():
        tree.delete(item)
    
    rows = get_data_from_server()
    
    if not rows:
        lbl_status.configure(text=f"Status: 🔴 Disconnected (Last IP: {SERVER_IP})", text_color="#ff7675")
        return

    for row in rows:
        status = row[4]
        tag = 'done' if status == 'DONE' else ('ready' if status == 'READY' else 'pending')
        tree.insert("", tk.END, values=row, tags=(tag,))
        
    total_sales = sum(float(row[3]) for row in rows if row[4] == 'DONE')
    total_count = len(rows)
    
    lbl_status.configure(text=f"🟢 Connected to {SERVER_IP} | Orders: {total_count}", text_color="#55efc4")
    lbl_total_sales.configure(text=f"Total Earnings: Rs. {total_sales:.2f}")

def delete_history():
    if not messagebox.askyesno("Critical Action", "⚠️ WARNING: DELETE ALL HISTORY?\nThis cannot be undone."): return
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, TCP_PORT))
        client.send("ADMIN_DELETE_HISTORY".encode('utf-8'))
        client.close()
        load_data()
        messagebox.showinfo("Success", "History Cleared!")
    except Exception as e:
        messagebox.showerror("Error", f"Connection Failed: {e}")

# --- GUI SETUP (Modern) ---
app = ctk.CTk()
app.title("📊 ADMIN DASHBOARD - Remote Access")
app.geometry("950x650")

# 1. Header
header = ctk.CTkFrame(app, height=60, corner_radius=0, fg_color="#2d3436")
header.pack(fill="x")
ctk.CTkLabel(header, text="💰 CHAWAL SHAWAL", font=("Roboto", 22, "bold"), text_color="#ff623f").pack(pady=15)

# 2. Stats Bar
stats_frame = ctk.CTkFrame(app, fg_color="transparent")
stats_frame.pack(fill="x", padx=20, pady=(20, 0))

lbl_status = ctk.CTkLabel(stats_frame, text="Scanning...", font=("Arial", 14), anchor="w")
lbl_status.pack(side="left")

lbl_total_sales = ctk.CTkLabel(stats_frame, text="Total Earnings: Rs. 0.00", font=("Arial", 20, "bold"), text_color="#00b894")
lbl_total_sales.pack(side="right")

# 3. Table Area (Styled Treeview)
table_frame = ctk.CTkFrame(app, fg_color="#2d3436", corner_radius=15)
table_frame.pack(fill="both", expand=True, padx=20, pady=10)

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", 
                background="#2d3436", 
                foreground="white", 
                fieldbackground="#2d3436", 
                rowheight=30,
                font=("Arial", 12))
style.configure("Treeview.Heading", 
                background="#0984e3", 
                foreground="white", 
                font=("Arial", 12, "bold"))
style.map("Treeview", background=[('selected', '#00b894')])

cols = ("ID", "Table No", "Items", "Price", "Status", "Time")
tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Treeview")

for col in cols: tree.heading(col, text=col)

tree.column("ID", width=50, anchor='center')
tree.column("Table No", width=100, anchor='center')
tree.column("Items", width=300)
tree.column("Price", width=100, anchor='center')
tree.column("Status", width=100, anchor='center')
tree.column("Time", width=100, anchor='center')

tree.tag_configure('pending', foreground='#fab1a0')
tree.tag_configure('ready', foreground='#55efc4')
tree.tag_configure('done', foreground='#74b9ff')

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y", padx=(0,5), pady=5)
tree.pack(fill="both", expand=True, padx=5, pady=5)

# 4. Action Buttons
btn_frame = ctk.CTkFrame(app, height=80, fg_color="transparent")
btn_frame.pack(fill="x", padx=20, pady=20)

btn_refresh = ctk.CTkButton(btn_frame, text="🔄 REFRESH", command=load_data, 
                            fg_color="#0984e3", hover_color="#74b9ff", height=45, font=("Arial", 14, "bold"))
btn_refresh.pack(side="left", fill="x", expand=True, padx=5)

btn_print = ctk.CTkButton(btn_frame, text="🖨️ PRINT REPORT", command=print_report, 
                          fg_color="#6c5ce7", hover_color="#a29bfe", height=45, font=("Arial", 14, "bold"))
btn_print.pack(side="left", fill="x", expand=True, padx=5)

btn_delete = ctk.CTkButton(btn_frame, text="🗑️ DELETE HISTORY", command=delete_history, 
                           fg_color="#d63031", hover_color="#ff7675", height=45, font=("Arial", 14, "bold"))
btn_delete.pack(side="left", fill="x", expand=True, padx=5)

def auto_refresh():
    load_data()
    app.after(5000, auto_refresh)

app.after(1000, auto_refresh)
app.mainloop()