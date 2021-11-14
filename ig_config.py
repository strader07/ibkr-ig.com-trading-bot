import pandas as pd

try:
    df = pd.read_csv("IG_CONFIG.csv")
    username = df[df["KEY"] == "USERNAME"].iloc[0]["VALUE"]
    password = df[df["KEY"] == "PASSWORD"].iloc[0]["VALUE"]
    api_key = df[df["KEY"] == "API_KEY"].iloc[0]["VALUE"]
    acc_type = df[df["KEY"] == "ACCOUNT_TYPE"].iloc[0]["VALUE"]
    acc_number = df[df["KEY"] == "ACCOUNT_NUMBER"].iloc[0]["VALUE"]
except:
    df = pd.DataFrame(columns=["KEY", "VALUE"])
    username = "jackie"
    password = "Layerstack1!"
    api_key = "7999be55780e83c6c85725ab7731011d9fb78308"
    acc_type = "DEMO"  # LIVE / DEMO
    acc_number = "Z3QT87"  # Z3REWL (CFD), Z3REWM (spread betting)

    df["KEY"] = ["USERNAME", "PASSWORD", "API_KEY", "ACCOUNT_TYPE", "ACCOUNT_NUMBER"]
    df["VALUE"] = [username, password, api_key, acc_type, acc_number]
    df.to_csv("IG_CONFIG.CSV", index=False)


class config(object):
    username = username
    password = password
    api_key = api_key
    acc_type = acc_type
    acc_number = acc_number
