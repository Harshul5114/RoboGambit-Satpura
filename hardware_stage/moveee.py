import requests
import json
import sys

# --- CONFIG ---
ROBOT_IP = "192.168.4.1" 
JOG_STEP = 5.0 # mm to move per keypress

def send_cmd(cmd):
    url = f"http://{ROBOT_IP}/js?json={json.dumps(cmd)}"
    try:
        response = requests.get(url, timeout=1)
        return response.json()
    except:
        return None

def get_status():
    # T:105 gets current coordinates and joint angles
    data = send_cmd({"T": 105})
    if data:
        print(f"\n[CURRENT POS] X: {data['x']:.2f}, Y: {data['y']:.2f}, Z: {data['z']:.2f}")
        print(f"[JOINTS] Shoulder: {data['s']:.2f}, Elbow: {data['e']:.2f}")
        return data
    print("\n[!] Connection Error")
    return None

def move_abs(x, y, z):
    # T:104 is coordinate move
    send_cmd({"T": 104, "x": x, "y": y, "z": z, "t": 3.14, "speed": 0})

print("=== RoArm Remote Jogger ===")
print(f"Connecting to {ROBOT_IP}...")
status = get_status()

if not status:
    print("Could not connect. Ensure you are on the RoArm Wi-Fi.")
    sys.exit()

print("\nCONTROLS:")
print("W/S: X +/- | A/D: Y +/- | R/F: Z +/-")
print("G: Get Current Coordinates | M: Manual XYZ Input | Q: Quit")

while True:
    key = input("\nAction > ").lower()
    
    status = get_status()
    if not status: continue
    
    x, y, z = status['x'], status['y'], status['z']

    if key == 'w': move_abs(x + JOG_STEP, y, z)
    elif key == 's': move_abs(x - JOG_STEP, y, z)
    elif key == 'a': move_abs(x, y + JOG_STEP, z)
    elif key == 'd': move_abs(x, y - JOG_STEP, z)
    elif key == 'r': move_abs(x, y, z + JOG_STEP)
    elif key == 'f': move_abs(x, y, z - JOG_STEP)
    elif key == 'g': get_status() # Just print status
    elif key == 'm':
        try:
            nx = float(input("Target X: "))
            ny = float(input("Target Y: "))
            nz = float(input("Target Z: "))
            move_abs(nx, ny, nz)
        except ValueError:
            print("Invalid input.")
    elif key == 'q':
        break