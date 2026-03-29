import pygame
import json
import time
import math
import sys

# Import YOUR existing variables and functions
from main import ser, ser2, get_feedback_full, send_cmd, EOAT_LEVEL

# --- CONFIG ---
STEP = 3.0       # mm to move per tick while holding key
T_STEP = 0.05    # radians to tilt per tick
FPS = 30         # Speed of the loop

# Initialize Pygame
pygame.init()
# Create a small control window (must be focused/clicked to work)
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Robot Jogger Control")
clock = pygame.time.Clock()

def jog_move(x, y, z, t):
    """Uses your existing send_cmd logic."""
    # Using T:1041 for a coordinate move with wrist angle
    cmd = f'{{"T":1041,"x":{x:.3f},"y":{y:.3f},"z":{z:.3f},"t":{t:.5f}}}'
    send_cmd(cmd)

print("\n--- JOGGER READY ---")
print("W / S : Move X")
print("A / D : Move Y")
print("R / F : Move Z (Height)")
print("Q / E : Tilt Wrist")
print("P     : PRINT COORDINATES (For Calibration)")
print("ESC   : Exit")

# Initial Position Sync
print("Syncing with robot current position...")
ax, ay, az, as_angle, ae_angle = get_feedback_full()
if ax is None:
    print("Warning: Could not get feedback. Starting at defaults.")
    ax, ay, az = 300.0, 0.0, 150.0

# Current 't' based on your main's EOAT_LEVEL
# We calculate the current level angle like your linear_move_to does
current_t = (math.pi/2) - as_angle + ae_angle - EOAT_LEVEL

running = True
while running:
    moved = False
    keys = pygame.key.get_pressed()

    # --- Continuous Movement Logic ---
    if keys[pygame.K_w]: ax += STEP; moved = True
    if keys[pygame.K_s]: ax -= STEP; moved = True
    if keys[pygame.K_a]: ay += STEP; moved = True
    if keys[pygame.K_d]: ay -= STEP; moved = True
    if keys[pygame.K_r]: az += STEP; moved = True
    if keys[pygame.K_f]: az -= STEP; moved = True
    if keys[pygame.K_q]: current_t += T_STEP; moved = True
    if keys[pygame.K_e]: current_t -= T_STEP; moved = True

    # --- Event Handling (Single Press) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                # Get fresh feedback for calibration
                fx, fy, fz, fs, fe = get_feedback_full()
                print(f"\n[CALIBRATION FEEDBACK]")
                print(f"X: {fx:.2f}, Y: {fy:.2f}, Z: {fz:.2f}")
                print(f"S-angle: {fs:.4f}, E-angle: {fe:.4f}")
                print(f"Current Level 't': {current_t:.5f}")
            if event.key == pygame.K_ESCAPE:
                running = False

    if moved:
        jog_move(ax, ay, az, current_t)
        # Small delay to prevent serial buffer overflow
        time.sleep(0.08) 

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()