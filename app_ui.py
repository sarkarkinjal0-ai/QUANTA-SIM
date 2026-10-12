import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# DOWNSTREAM DATA INTEGRATION
# The UI team imports the raw data generator from YOUR experiments module.
# ---------------------------------------------------------
from physics_experiments import InterferometryExperiments

def render_terminal_ui():
    """
    [TEAM ROLE: UI, Visualization & Integration]
    Handles all user input, terminal printing, and Matplotlib graphing.
    No quantum physics logic happens in this file.
    """
    print("==============================================")
    print("      QUANTA-SIM: UI & VISUALIZATION APP      ")
    print("==============================================\n")
    
    # UI Input Phase
    user_input = input("Enter an imperfect beam splitter reflectivity (0.0 to 1.0) [Default 0.45]: ")
    try:
        ref_val = float(user_input)
        if not (0.0 <= ref_val <= 1.0):
            ref_val = 0.45
    except ValueError:
        ref_val = 0.45
        
    print(f"\n=> Backend System configured for Reflectivity: {ref_val}\n")

    # Fetch Data from Physics Experiments Team
    print("Fetching HOM data from backend...")
    hom_data = InterferometryExperiments.run_hom_analysis(ref_val)
    
    print("\n--- Hong-Ou-Mandel (HOM) Results ---")
    print(f"Ideal 50:50 BS Coincidence P(|1,1>): {hom_data['ideal_coincidence']:.4f} (Perfect Bunching)")
    print(f"Imperfect BS Coincidence P(|1,1>):   {hom_data['imperfect_coincidence']:.4f} (Degraded)")

    # Fetch Data and Plot MZI Fringes
    print("\nFetching MZI data from backend and rendering graph...")
    mzi_data = InterferometryExperiments.run_mzi_sweep(ref_val)
    
    # UI Graphing Phase
    plt.figure(figsize=(10, 6))
    plt.plot(mzi_data["phi_values"], mzi_data["p0_ideal"], label="Detector 0 (Ideal)", color='blue', linewidth=2)
    plt.plot(mzi_data["phi_values"], mzi_data["p1_ideal"], label="Detector 1 (Ideal)", color='red', linestyle='--', linewidth=2)
    plt.scatter(mzi_data["phi_values"], mzi_data["p0_noisy"], label=f"Detector 0 (Noisy/R={ref_val})", color='green', marker='x')
    
    plt.title("Mach-Zehnder Interferometer (UI Module View)", fontsize=16)
    plt.xlabel(r"Internal Phase Shift Angle $\phi$ (radians)", fontsize=14)
    plt.ylabel("Output Detection Probability", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    render_terminal_ui()