import socket
import threading
import tkinter as tk
from tkinter import messagebox
import json
import customtkinter as ctk 
import database 

# --- CONFIGURATION ---
HOST = '0.0.0.0'
TCP_PORT = 9999      # Data bhejne ke liye
BROADCAST_PORT = 55555 # Dhoondne ke liye (Discovery)

# --- THEME ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") 

# Dictionary for cards (Order ID -> Widget)
active_order_widgets = {}

# --- AUTO DISCOVERY LISTENER ---
def start_broadcast_listener():
    """Ye function chup chap sunta rahega k koi Server ko dhoond to nahi raha"""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', BROADCAST_PORT)) # Sab ki suno
    
    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)
            message = data.decode('utf-8')
            
            if message == "DISCOVER_SERVER":
                reply = "SERVER_HERE"
                udp_socket.sendto(reply.encode('utf-8'), addr)
        except:
            pass

# --- GUI HELPER: CREATE CARD ---
def create_order_card(order_id, table, items, total, timestamp):
    card = ctk.CTkFrame(orders_container, fg_color="#2d3436", corner_radius=15, border_width=2, border_color="#444")
    card.pack(fill="x", pady=10, padx=10)

    info_frame = ctk.CTkFrame(card, fg_color="transparent")
    info_frame.pack(side="left", padx=15, pady=10)
    
    ctk.CTkLabel(info_frame, text=f"{table}", font=("Arial", 28, "bold"), text_color="#fdcb6e").pack(anchor="w")
    ctk.CTkLabel(info_frame, text=f"ID: #{order_id} | {timestamp}", font=("Arial", 12), text_color="#b2bec3").pack(anchor="w")
    ctk.CTkLabel(info_frame, text=f"Total: Rs. {total}", font=("Arial", 14, "bold"), text_color="#00b894").pack(anchor="w", pady=(5,0))

    items_frame = ctk.CTkFrame(card, fg_color="#353b48", corner_radius=10)
    items_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    
    formatted_items = "• " + items.replace(",", "\n• ")
    ctk.CTkLabel(items_frame, text=formatted_items, font=("Courier New", 16, "bold"), text_color="white", justify="left").pack(padx=10, pady=5, anchor="w")

    btn_ready = ctk.CTkButton(card, text="✔ READY", width=120, height=50,
                              fg_color="#00b894", hover_color="#00cec9",
                              font=("Arial", 14, "bold"),
                              command=lambda: mark_specific_order_ready(order_id))
    btn_ready.pack(side="right", padx=15, pady=10)

    active_order_widgets[str(order_id)] = card

# --- GUI HELPER: REMOVE CARD ---
def remove_card_from_screen(order_id):
    """Screen se card hatane ke liye helper function"""
    oid_str = str(order_id)
    if oid_str in active_order_widgets:
        active_order_widgets[oid_str].destroy()
        del active_order_widgets[oid_str]

# --- NETWORK HANDLER ---
def handle_client(client_socket):
    try:
        request = client_socket.recv(1024 * 16).decode('utf-8')
        if not request: return

        if request == "ADMIN_GET_DATA":
            rows = database.get_all_orders()
            client_socket.send(json.dumps(rows).encode('utf-8'))

        elif request == "ADMIN_DELETE_HISTORY":
            database.clear_history()
            client_socket.send("OK".encode('utf-8'))

        elif request == "GET_ALL_READY":
            tables = database.get_ready_tables()
            if tables:
                ready_msg = ",".join(tables)
                client_socket.send(f"LIST:{ready_msg}".encode('utf-8'))
            else:
                client_socket.send("EMPTY".encode('utf-8'))

        elif request.startswith("MARK_DONE:"):
            table_no = request.split(":")[1].strip()
            database.mark_status_done(table_no)
            client_socket.send("OK".encode('utf-8'))

        # --- NEW: CANCEL ORDER LOGIC ---
        elif request.startswith("CANCEL_ORDER:"):
            table_no = request.split(":")[1].strip()
            
            # Database se delete karwao (Returns IDs jo delete hue)
            deleted_ids = database.cancel_pending_order(table_no)
            
            if deleted_ids:
                # Agar DB se delete ho gaya, to Screen se bhi card hatao
                for oid in deleted_ids:
                    app.after(0, lambda i=oid: remove_card_from_screen(i))
                
                client_socket.send("Order Cancelled Successfully!".encode('utf-8'))
            else:
                client_socket.send("Fail: No Pending Order Found".encode('utf-8'))

        # --- NEW ORDER LOGIC ---
        elif "|" in request:
            parts = request.split('|')
            if len(parts) == 3:
                table = parts[0].strip()
                items = parts[1].strip()
                total = parts[2].strip()

                order_id, timestamp = database.add_order(table, items, total)
                app.after(0, lambda: create_order_card(order_id, table, items, total, timestamp))
                client_socket.send("Order Received!".encode('utf-8'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# --- SERVER LOOP ---
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((HOST, TCP_PORT))
        server.listen(5)
        print(f"Kitchen Server Started on {HOST}:{TCP_PORT}...")
        
        # Start Discovery Listener
        broadcast_thread = threading.Thread(target=start_broadcast_listener, daemon=True)
        broadcast_thread.start()
        
        while True:
            client, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client,))
            t.daemon = True
            t.start()
    except Exception as e:
        print(f"Server Error: {e}")

# --- GUI LOGIC ---
def mark_specific_order_ready(order_id):
    try:
        database.mark_status_ready(order_id)
        # Use common function to remove card
        remove_card_from_screen(order_id)
    except Exception as e:
        print(f"Error marking ready: {e}")

# --- MAIN GUI SETUP ---
if __name__ == "__main__":
    database.init_db()

    app = ctk.CTk()
    app.title("👨‍🍳 KITCHEN DISPLAY SYSTEM (Auto Connect)")
    app.geometry("1000x700")

    header = ctk.CTkFrame(app, height=70, corner_radius=0, fg_color="#1e272e")
    header.pack(fill="x")
    ctk.CTkLabel(header, text="🔥CHAWAL SHAWAL", font=("Roboto", 26, "bold"), text_color="#ffa502").pack(pady=15)

    orders_container = ctk.CTkScrollableFrame(app, fg_color="transparent")
    orders_container.pack(fill="both", expand=True, padx=20, pady=20)

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    app.mainloop()