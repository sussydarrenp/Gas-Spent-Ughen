import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt

def initialize_firebase(credpath):
    # Initialize Firebase
    login = credentials.Certificate(credpath)
    firebase_admin.initialize_app(login)
   
    # Initialize Firestore
    db = firestore.client()
   
    return db


def fetch_data(wallet_address, chain, month, db):
    doc_ref = db.collection("accounts").document(wallet_address)
   
    try:
        doc = doc_ref.get()
        data = doc.to_dict()
        if data:
            if "chains" in data and chain in data["chains"]:
                chain_data = data["chains"][chain]
                if month in chain_data:
                    month_data = chain_data[month]
                    return month_data
    except Exception as e:
        print(f"Error fetching data: {e}")
   
    return None


def calculate_total_fees(wallet_addresses, chains, db):
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    monthly_total_fees = {month: [] for month in months}

    for month in months:
        total_fee = 0
        for wallet_address in wallet_addresses:
            for chain in chains:
                data = fetch_data(wallet_address, chain, month, db)
                if data:
                    total_fee += sum(data.values())


        print(f"{month}: {total_fee:.2f} USD")
        monthly_total_fees[month].append(total_fee)

    plt.figure(figsize=(10, 6))
    colors = plt.cm.get_cmap('tab20').colors  # Using a colormap for different colors
    num_colors = len(months)

    for i, (month, fees) in enumerate(monthly_total_fees.items()):
        plt.bar(month, fees[0], color=colors[i % num_colors])

    plt.xlabel('Months')
    plt.ylabel('Total Fees (USD)')
    plt.title('Total Gas Fees per Month')
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.tight_layout()

    plt.show()


def main():
    # Initialize Firebase
    credpath = "gasspent-firebase-adminsdk-kht62-2a8e40aed1.json"
    db = initialize_firebase(credpath)


    # Read the list of chains from the "chains.txt" file
    chains_file = "chains.txt"
    with open(chains_file, 'r') as f:
        chains = [line.strip() for line in f.readlines()]


    # Read wallet addresses from "accounts.txt" file
    wallet_addresses_file = "accounts.txt"
    with open(wallet_addresses_file, 'r') as f:
        wallet_addresses = [line.strip() for line in f.readlines()]


    # Calculate and print total gas fees for each month
    calculate_total_fees(wallet_addresses, chains, db)


if __name__ == "__main__":
    main()
