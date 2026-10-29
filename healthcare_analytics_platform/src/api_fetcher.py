import requests
import pandas as pd

def fetch_external_patient_data():
    api_url = "https://jsonplaceholder.typicode.com/users"
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            formatted_data = []
            for user in data:
                formatted_data.append({
                    "Patient_ID": f"API-{user['id']}",
                    "Patient_Name": user["name"],
                    "Contact_Email": user["email"],
                    "City": user["address"]["city"],
                    "Company_Affiliation": user["company"]["name"]
                })
            return pd.DataFrame(formatted_data)
        else:
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        return pd.DataFrame([
            {"Patient_ID": "FB-101", "Patient_Name": "Fallback Patient A", "Contact_Email": "a@example.com", "City": "Delhi", "Company_Affiliation": "General Health"},
            {"Patient_ID": "FB-102", "Patient_Name": "Fallback Patient B", "Contact_Email": "b@example.com", "City": "Mumbai", "Company_Affiliation": "General Health"}
        ])
