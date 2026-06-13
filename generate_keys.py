from utils.licensing import LicenseManager

def main():
    print("========================================")
    print("INVENTORY POS - LICENSE KEY GENERATOR")
    print("Developed by Joachim Korang Amponsah")
    print("========================================\n")
    
    machine_id = input("Enter Customer's Machine ID: ").strip()
    
    if not machine_id:
        print("Error: Machine ID cannot be empty.")
        return
        
    license_key = LicenseManager.generate_license_hash(machine_id)
    
    print("\n----------------------------------------")
    print(f"VALID KEY: {license_key}")
    print("----------------------------------------")
    print("\nSend this key to the customer to activate their software.")

if __name__ == "__main__":
    main()
