import perception
import numpy as np
import cv2
import time

def run_perception_test():
    print("--- PERCEPTION MODULE TEST ---")
    print(f"Target Server: {perception.SERVER_IP}:{perception.SERVER_PORT}")
    
    # 1. Initialize the socket connection
    try:
        sock = perception.init_perception()
    except Exception as e:
        print(f"[ERROR] Could not connect to camera server: {e}")
        return

    try:
        while True:
            print("\nScanning for stable board state...")
            # 2. Call your stable board logic
            # stability_required=5 means it needs 5 identical frames to return
            board, poses = perception.get_stable_board(sock, stability_required=5)

            if board is not None:
                print("\n[SUCCESS] Stable Board Detected:")
                print("-" * 25)
                # Print the 6x6 grid
                print(board)
                print("-" * 25)

                if poses:
                    print("\n[PIECE POSITIONS] Precise Robot Coordinates (mm):")
                    for piece_id, coords in poses.items():
                        # Most pieces have 1 coordinate, but list handles multiples
                        coord_str = ", ".join([f"({x:.1f}, {y:.1f})" for x, y in coords])
                        print(f"  ID {piece_id:2}: {coord_str}")
                else:
                    print("\n[WARNING] Board is empty or no pieces (IDs 1-10) detected.")
            
            print("\n" + "="*40)
            user_input = input("Press ENTER to scan again, or 'q' to quit: ").lower()
            if user_input == 'q':
                break

    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    finally:
        print("Closing socket...")
        sock.close()

if __name__ == "__main__":
    run_perception_test()