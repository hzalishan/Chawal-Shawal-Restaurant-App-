# 🍛 Chawal Shawal - Restaurant Management System

A real-time, multi-device restaurant management solution built with **Python**, utilizing **Socket Programming** for communication and **SQLite** for data persistence. This system connects Waiters directly to the Kitchen staff over a Local Area Network (LAN).

---

## 🏗️ System Architecture

The project follows a **Client-Server Architecture**:
- **Server (Kitchen):** Acts as the central hub. It listens for incoming orders, displays them on a KDS (Kitchen Display System), and logs everything into the database.
- **Client (Waiter):** A mobile/laptop interface for taking orders and transmitting them instantly to the server.
- **Admin Panel:** A dedicated management tool to view sales analytics and manage order history.



[Image of client server network diagram]


---

## ✨ Key Features

- **Real-time Order Sync:** Instant transmission of orders from Waiter to Kitchen using TCP Sockets.
- **Kitchen Display System (KDS):** A dark-themed, high-visibility interface for chefs to track pending orders.
- **Database Persistence:** Every order is stored in `chawal_shawal.db`, ensuring no data is lost even if the system restarts.
- **Multi-threaded Server:** Capable of handling multiple Waiter connections simultaneously without performance lag.
- **Order Status Tracking:** Ability to mark orders as `PENDING` or `READY`.
- **Admin Reporting:** Automated total sales calculation and order history management.
- **Network Optimized:** Designed to work over any local Wi-Fi or Ethernet connection.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.x |
| **GUI Framework** | Tkinter |
| **Networking** | Socket (TCP/IP) |
| **Database** | SQLite3 |
| **Concurrency** | Threading |
| **Packaging** | PyInstaller |

---

## 📂 Project Structure

### 1. `server.py` (The Kitchen Hub)
- Starts a socket server on a specified port (default: `9999`).
- Handles incoming data strings and parses them into Table No, Items, and Price.
- Updates the GUI in real-time using `root.after()` to ensure thread safety.

### 2. `waiter.py` (The Client App)
- Features a categorized menu (Burgers, Desi, Drinks).
- Connects to the Server IP on the local network.
- Sends formatted data packets: `Table | Items | Price`.

### 3. `admin.py` (Management Interface)
- Connects to the SQLite database.
- Uses a `Treeview` widget to display historical data.
- Includes a "Clear History" feature for database maintenance.

---

## 🚀 Installation & Usage

### Prerequisites
- Python 3.x installed on all machines.
- All devices must be on the **same Wi-Fi/LAN**.

### Steps to Run
1. **Find Server IP:** On the Kitchen laptop, run `ipconfig` in CMD to find your local IP (e.g., `10.21.202.211`).
2. **Configure Client:** Open `waiter.py` and update the `SERVER_IP` variable with the Kitchen laptop's IP.
3. **Firewall:** Ensure Port `9999` is allowed through the Windows Firewall.
4. **Execution:**
   - Run `python server.py` first.
   - Run `python waiter.py` on the waiter's device.
   - Run `python admin.py` on the manager's device to view reports.

---

## 🛡️ Firewall & Networking Notes
To allow communication between devices:
- Go to **Windows Defender Firewall** > **Turn Windows Defender Firewall on or off**.
- Turn it **OFF** for Private and Public networks (or add a specific Inbound Rule for Port `9999`).

---
**Developed Hafiz Ali Shan**
