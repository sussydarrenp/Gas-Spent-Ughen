import requests
from requests.auth import HTTPBasicAuth
import json
from web3 import Web3
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
from concurrent.futures import ThreadPoolExecutor



credpath = "gasspent-firebase-adminsdk-kht62-2a8e40aed1.json"

login = credentials.Certificate(credpath)

firebase_admin.initialize_app(login)

db = firestore.client()
accounts_collection = db.collection("accounts")

with open('accounts.txt', 'r') as f:
    account_addresses = [line.strip() for line in f.readlines()]

with open('chains.txt', 'r') as f:
    chains = [line.strip() for line in f.readlines()]

url = "https://api.covalenthq.com/v1/{}/address/{}/transactions_v3/?"
headers = {"accept": "application/json"}
basic = HTTPBasicAuth('cqt_rQmHwxtcb4Bv97qXdPDg6pwyrKdD', '')

max_threads = 4
api_rate_limit = 4

def process_account(account):
    print(f"\nAccount: {account}")

    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    account_data = {
        "address": account,
        "total_gas_spent": 0,
        "chains": {}
    }

    total_account_fee = 0

    for chain in chains:
        print(f"\n*Scanning Chain: {chain}")

        chain_month_fees = {month: {"days": {str(day): 0 for day in range(1, 32)}} for month in months}

        total_chain_fee = 0

        # Add a sleep to comply with the API rate limit
        time.sleep(1 / api_rate_limit)

        response = requests.get(url.format(chain, account), headers=headers, auth=basic)

        if response.status_code == 200:
            result = json.loads(response.text)
            if "data" in result and "items" in result["data"]:
                transactions = result["data"]["items"]

                if len(transactions) == 0:  # Check if transactions list is empty
                    print("No transactions found on this chain.")
                    continue
                
                elif not any(Web3.to_checksum_address(transaction["from_address"]) == str(account) for transaction in transactions):
                    print(f"No gas spent from us on {chain} for this account.")
                    continue  # Skip this chain if there are no transactions from the account address
                
                else:
                    for transaction in transactions:
                        if Web3.to_checksum_address(transaction["from_address"]) == str(account):
                            if transaction["successful"]:
                                date = transaction["block_signed_at"]
                                parsed_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                                month = parsed_date.strftime("%B")
                                day_of_month = parsed_date.day

                                # Ensure valid keys
                                day_key = str(day_of_month)

                                transaction_fee_str = transaction["fees_paid"]
                                transaction_fee_int = int(transaction_fee_str)
                                converted_fee = transaction_fee_int / 10**18
                                gas_quote_rate = transaction["gas_quote_rate"]
                                usdt_value = converted_fee * gas_quote_rate

                                # Accumulate gas fees for the day of the month
                                chain_month_fees[month]["days"][day_key] += usdt_value
                                total_chain_fee += usdt_value
        
        # Add the month and day-wise fees for the chain if fees are not zero
        non_zero_data = {month: {day: fee for day, fee in fees["days"].items() if fee != 0} for month, fees in chain_month_fees.items() if any(fees["days"].values())}
        if non_zero_data:
            account_data["chains"][chain] = non_zero_data
        
        # Add the total chain fee to the account data
        account_data["chains"][chain]["total_fee"] = total_chain_fee
        total_account_fee += total_chain_fee
    
    # Add the total fee for the account across all chains
    account_data["total_gas_spent"] = total_account_fee

    print("\nAccount Data to be Written:", account_data)

    # Add the account data to Firebase Firestore
    accounts_collection.document(account).set(account_data)

# for account in account_addresses:
#     process_account(account)

with ThreadPoolExecutor(max_threads) as executor:
    executor.map(process_account, account_addresses)

print("\nScript has completed writing data to Firebase Firestore.")
















































# for account in account_addresses:
#     process_account(account)
























































# def process_account(account):
#     print(f"\nAccount: {account}")

#     account_data = {
#         "address": account,
#         "gas_spent": {}
#     }

#     for chain in chains:
#         print(f"\n*Scanning Chain: {chain}")

#         response = requests.get(url.format(chain, account), headers=headers, auth=basic)

#         if response.status_code == 200:
#             result = json.loads(response.text)
#             if "data" in result and "items" in result["data"]:
#                 transactions = result["data"]["items"]

#                 for transaction in transactions:
#                     if Web3.to_checksum_address(transaction["from_address"]) == str(account):
#                         if transaction["successful"]:
#                             date = transaction["block_signed_at"]
#                             parsed_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
#                             month = parsed_date.strftime("%B")
#                             day_of_month = parsed_date.day

#                             transaction_fee_str = transaction["fees_paid"]
#                             transaction_fee_int = int(transaction_fee_str)
#                             converted_fee = transaction_fee_int / 10**18
#                             gas_quote_rate = transaction["gas_quote_rate"]
#                             usdt_value = converted_fee * gas_quote_rate

#                             # Ensure valid keys
#                             month_key = month.replace(" ", "_")
#                             day_key = str(day_of_month)

#                             if month_key not in account_data["gas_spent"]:
#                                 account_data["gas_spent"][month_key] = {}

#                             if day_key not in account_data["gas_spent"][month_key]:
#                                 account_data["gas_spent"][month_key][day_key] = 0

#                             account_data["gas_spent"][month_key][day_key] += usdt_value

#     print("\nAccount Data to be Written:", account_data)

#     # Add the account data to Firebase Firestore
#     accounts_collection.document(account).set(account_data)

# for account in account_addresses:
#     process_account(account)

# print("\nScript has completed writing data to Firebase Firestore.")

