import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import socket
import threading

# --- AUTO DISCOVERY SETTINGS ---
TCP_PORT = 9999
BROADCAST_PORT = 55555

def scan_for_server():
    """Network par chillata hai: 'SERVER KAHAN HAI?'"""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(1)
    
    msg = "DISCOVER_SERVER"
    server_ip = None
    
    try:
        for _ in range(3):
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
    SERVER_IP = "127.0.0.1"

print(f"Server Found at: {SERVER_IP}")

# --- THEME SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- DATA ---
MENU = {
    "🍔 Burgers": [("Zinger", 350), ("Beef", 450), ("Patty", 200)],
    "🍛 Desi": [("Biryani", 400), ("Pulao", 350), ("Karahi", 1200)],
    "🥤 Drinks": [("Coke", 100), ("Water", 50), ("Chaye", 80)]
}

TABLE_OPTIONS = [f"Table-{i}" for i in range(1, 11)]

cart = []
last_server_response = "" 

# --- FUNCTIONS ---
def add_cart(name, price):
    cart.append((name, price))
    refresh_cart()

def refresh_cart():
    cart_list.delete(0, tk.END)
    total = sum(item[1] for item in cart)
    for name, price in cart:
        cart_list.insert(tk.END, f" {name}  -  Rs. {price}")
    lbl_total.configure(text=f"Total: Rs. {total}")

# 1. LOCAL CLEAR (Bhejne se pehle safaya)
def clear_local_cart():
    cart.clear()
    refresh_cart()

def send_order():
    if not cart:
        messagebox.showwarning("Empty", "Cart khali hai!")
        return
    
    btn_send.configure(state="disabled", text="Sending...", fg_color="gray")
    app.update()

    table = selected_table_var.get()
    items_str = ", ".join([x[0] for x in cart])
    total_price = str(sum([x[1] for x in cart]))
    msg = f"{table} | {items_str} | {total_price}"

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, TCP_PORT))
        client.send(msg.encode('utf-8'))
        resp = client.recv(1024).decode('utf-8')
        
        messagebox.showinfo("Success", resp)
        cart.clear()
        refresh_cart()
        client.close()
    except Exception as e:
        messagebox.showerror("Error", f"Server Error: {e}")
    finally:
        btn_send.configure(state="normal", text="🚀 SEND ORDER", fg_color="#00b894")

# 2. SERVER CANCEL (Bhejne ke baad delete karna)
def cancel_sent_order():
    table = selected_table_var.get()
    
    # Confirmation lo
    if not messagebox.askyesno("Cancel Order", f"Are you sure you want to CANCEL orders for {table}?"):
        return

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, TCP_PORT))
        # Nayi Command Bhejo
        client.send(f"CANCEL_ORDER:{table}".encode('utf-8'))
        
        resp = client.recv(1024).decode('utf-8')
        client.close()
        
        if "Success" in resp:
            messagebox.showinfo("Cancelled", f"{table} ka order cancel kar diya gaya.")
        else:
            messagebox.showwarning("Failed", f"Cancel nahi hua.\nReason: {resp}")
            
    except Exception as e:
        messagebox.showerror("Error", f"Connection Error: {e}")

# --- NOTIFICATION LOGIC ---
def refresh_notifications():
    global last_server_response
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect((SERVER_IP, TCP_PORT))
        client.send("GET_ALL_READY".encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        client.close()

        if response == last_server_response:
            app.after(2000, refresh_notifications)
            return

        last_server_response = response
        notif_list.delete(0, tk.END)

        if response.startswith("LIST:"):
            raw_data = response.split(":")[1]
            if raw_data:
                tables = raw_data.split(",")
                for t in tables:
                    notif_list.insert(tk.END, f" 🚀  ORDER READY: {t}")
                    notif_list.itemconfig(tk.END, {'bg':'#2d3436', 'fg':'#00b894'}) 
    except:
        pass
    
    app.after(2000, refresh_notifications)

def mark_delivered():
    try:
        idx = notif_list.curselection()
        if not idx: return
        text = notif_list.get(idx)
        table_name = text.split(":")[1].strip()
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, TCP_PORT))
        client.send(f"MARK_DONE:{table_name}".encode('utf-8'))
        client.close()
        
        notif_list.delete(idx)
        global last_server_response
        last_server_response = "" 
        
        messagebox.showinfo("Great!", f"{table_name} Delivered!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# --- GUI SETUP ---
app = ctk.CTk()
app.title("🍽️ CHAWAL SHAWAL - Waiter App")
app.geometry("900x650")

# Header
header_frame = ctk.CTkFrame(app, height=50, corner_radius=0, fg_color="#2d3436")
header_frame.pack(fill="x")
ctk.CTkLabel(header_frame, text="🔥 CHAWAL SHAWAL", font=("Roboto", 20, "bold"), text_color="#ff623f").pack(pady=10)

# Main Tabs
tabview = ctk.CTkTabview(app, width=850, height=500)
tabview.pack(pady=10, padx=10, fill="both", expand=True)

t1 = tabview.add("📝 New Order")
t2 = tabview.add("🔔 Notifications")

# === TAB 1: ORDERING ===
# Left: Menu
left_frame = ctk.CTkScrollableFrame(t1, width=500, label_text="🍔 MENU ITEMS")
left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

for cat, items in MENU.items():
    ctk.CTkLabel(left_frame, text=cat, font=("Arial", 16, "bold"), text_color="#74b9ff").pack(anchor="w", pady=5)
    grid_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    grid_frame.pack(fill="x", pady=5)
    
    r, c = 0, 0
    for n, p in items:
        btn = ctk.CTkButton(grid_frame, text=f"{n}\nRs.{p}", width=100, height=60, 
                            corner_radius=15, fg_color="#0984e3", hover_color="#74b9ff",
                            font=("Arial", 12, "bold"),
                            command=lambda n=n, p=p: add_cart(n, p))
        btn.grid(row=r, column=c, padx=5, pady=5)
        c += 1
        if c > 2: c=0; r+=1

# Right: Cart
right_frame = ctk.CTkFrame(t1, width=300, fg_color="#2d3436")
right_frame.pack(side="right", fill="y", padx=5, pady=5)

ctk.CTkLabel(right_frame, text="Select Table:", font=("Arial", 14, "bold"), text_color="white").pack(pady=10)

selected_table_var = ctk.StringVar(value=TABLE_OPTIONS[0]) 
table_dropdown = ctk.CTkOptionMenu(right_frame, values=TABLE_OPTIONS,
                                   variable=selected_table_var,
                                   width=200, height=40,
                                   fg_color="#0984e3", button_color="#005291",
                                   dropdown_fg_color="#2d3436",
                                   font=("Arial", 14, "bold"))
table_dropdown.pack(pady=5)

ctk.CTkLabel(right_frame, text="Current Order", text_color="#b2bec3").pack(pady=10)

cart_list = tk.Listbox(right_frame, height=15, bg="#dfe6e9", fg="#2d3436", font=("Courier", 12, "bold"), borderwidth=0)
cart_list.pack(fill="both", expand=True, padx=10, pady=5)

# Clear Cart Button (Inside Listbox area or below)
btn_clear = ctk.CTkButton(right_frame, text="🗑️ Clear Cart", width=100, height=30,
                          fg_color="#d63031", hover_color="#ff7675",
                          command=clear_local_cart)
btn_clear.pack(pady=5)

lbl_total = ctk.CTkLabel(right_frame, text="Total: Rs. 0", font=("Arial", 18, "bold"), text_color="#00b894")
lbl_total.pack(pady=10)

btn_send = ctk.CTkButton(right_frame, text="🚀 SEND ORDER", width=250, height=50, 
                         fg_color="#00b894", hover_color="#55efc4", 
                         font=("Arial", 15, "bold"), command=send_order)
btn_send.pack(pady=10, padx=10)

# Cancel Sent Order Button
btn_cancel_sent = ctk.CTkButton(right_frame, text="❌ CANCEL SENT ORDER", width=250, height=40,
                                fg_color="#636e72", hover_color="#b2bec3",
                                font=("Arial", 12, "bold"), command=cancel_sent_order)
btn_cancel_sent.pack(pady=(20, 10))

# === TAB 2: NOTIFICATIONS ===
notif_frame = ctk.CTkFrame(t2, fg_color="transparent")
notif_frame.pack(fill="both", expand=True, padx=20, pady=20)

ctk.CTkLabel(notif_frame, text="Ready for Delivery", font=("Arial", 20, "bold"), text_color="#fdcb6e").pack(pady=10)

notif_list = tk.Listbox(notif_frame, font=("Arial", 14), bg="#2d3436", fg="white", height=12, borderwidth=0, selectbackground="#0984e3")
notif_list.pack(fill="both", expand=True, padx=10, pady=10)

btn_done = ctk.CTkButton(notif_frame, text="✅ MARK AS DELIVERED", height=50, 
                         fg_color="#0984e3", hover_color="#004377", 
                         font=("Arial", 16, "bold"), command=mark_delivered)
btn_done.pack(pady=20, fill="x", padx=50)

refresh_notifications()
app.mainloop()