import time
import requests
import statistics

# =========================
# CONFIGURE YOUR AWS NODES
# =========================
NODE_A = "http://3.99.213.215:8000"
NODE_B = "http://3.99.130.16:8001"
NODE_C = "http://15.156.8.206:8002"

# Choose one node to send requests to
BASE = NODE_A


# =========================
# HELPERS
# =========================
def create_driver(driver_id, name, x, y):
    payload = {
        "driver_id": driver_id,
        "name": name,
        "x": x,
        "y": y
    }
    requests.post(f"{BASE}/drivers/", json=payload)


def create_ride(ride_id, rider, px, py, dx, dy):
    payload = {
        "ride_id": ride_id,
        "rider_name": rider,
        "pickup_x": px,
        "pickup_y": py,
        "dropoff_x": dx,
        "dropoff_y": dy
    }
    requests.post(f"{BASE}/rides/", json=payload)


def set_mode(mode):
    payload = {"mode": mode}
    requests.put(f"{BASE}/rides/mode", json=payload)


def assign_ride(ride_id):
    start = time.time()
    response = requests.post(f"{BASE}/rides/{ride_id}/assign")
    end = time.time()
    latency = end - start
    return latency, response.json()


# =========================
# TEST 1: ASSIGNMENT LATENCY
# =========================
def latency_test(mode="cp", runs=5):
    print(f"\n=== LATENCY TEST ({mode.upper()}) ===")
    set_mode(mode)

    latencies = []

    for i in range(runs):
        driver_id = f"D9{mode}{i}"
        ride_id = f"R9{mode}{i}"

        create_driver(driver_id, f"Driver{i}", i + 1, i + 1)
        create_ride(ride_id, f"User{i}", i + 2, i + 2, 9, 9)

        latency, result = assign_ride(ride_id)
        latencies.append(latency)

        print(f"Run {i+1}: {latency:.3f}s")

    avg = statistics.mean(latencies)
    print(f"\nAverage latency ({mode.upper()}): {avg:.3f}s")


# =========================
# TEST 2: RECOVERY TIME
# =========================
def recovery_test(ride_id, recovered_node_url):
    print("\n=== RECOVERY TEST ===")
    print("Restart the stopped node NOW, then press Enter...")
    input()

    start = time.time()

    while True:
        try:
            r = requests.get(f"{recovered_node_url}/rides/{ride_id}", timeout=2)
            if r.status_code == 200:
                end = time.time()
                total = end - start
                print(f"Recovered in {total:.3f}s")
                break
        except:
            pass

        time.sleep(1)


# =========================
# MAIN MENU
# =========================
if __name__ == "__main__":
    while True:
        print("\n===== EVALUATION MENU =====")
        print("1. CP Latency Test")
        print("2. AP Latency Test")
        print("3. Recovery Test")
        print("4. Exit")

        choice = input("Choose: ")

        if choice == "1":
            latency_test("cp")
        elif choice == "2":
            latency_test("ap")
        elif choice == "3":
            ride_id = input("Enter ride ID to watch: ")
            node = input("Recovered node URL (example http://3.99.130.16:8001): ")
            recovery_test(ride_id, node)
        elif choice == "4":
            break
        else:
            print("Invalid choice")