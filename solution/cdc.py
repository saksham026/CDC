import pandas as pd
import json
import os
pd.options.mode.chained_assignment = None


def merge_logic(df2, df1, path):

    flag = 0

    if df2.empty or df1.at[0, 'op'] == "c":
        prop2 = df1.at[0, 'data']
        prop2 = json.loads(prop2)

        if 'savings_account_id' in prop2.keys():
            df1.at[0, 'savings_account_id'] = prop2["savings_account_id"]

        if 'card_id' in prop2.keys():
            df1.at[0, 'card_id'] = prop2["card_id"]

        df2 = df2.append(df1, ignore_index=True)
        df2["status"] = "latest"

        return df2

    else:
        for index2, row2 in df2.iterrows():
            for index1, row1 in df1.iterrows():
                if row2['id'] == row1['id'] and row2['status'] == "latest":
                    flag = 1
                    prop2 = df2.at[index2, 'data']

                    prop2 = json.loads(prop2)

                    prop1 = df1.at[index1, 'data']

                    prop1 = json.loads(prop1)

                    sa = 0
                    c = 0
                    tc = 0

                    for key in prop1:
                        if key == "savings_account_id":
                            sa = 1

                        if key == "card_id":
                            c = 1

                        if key == "credit_used" or key == "balance":
                            tc += 1

                        if key in prop2:
                            prop2[key] = prop1[key]
                        else:
                            prop2[key] = prop1[key]

                    df1.at[index1, 'data'] = json.dumps(prop2)

                    df1.at[index1, 'status'] = "latest"
                    df2.at[index2, 'status'] = "old"

                    if sa == 1:
                        df1.at[index1, 'savings_account_id'] = prop1["savings_account_id"]
                    elif 'savings_account_id' in df2.keys():
                        df1.at[index1, 'savings_account_id'] = df2.at[index2, 'savings_account_id']
                    if c == 1:
                        df1.at[index1, 'card_id'] = prop1["card_id"]
                    elif 'card_id' in df2.keys():
                        df1.at[index1, 'card_id'] = df2.at[index2, 'card_id']

                    if tc != 0:
                        if path == "savings_accounts":
                            colN = "transaction_s"
                        elif path == "cards":
                            colN = "transaction_c"

                        df1.at[index1, colN] = tc

                else:
                    continue

    if flag == 0:
        df1["status"] = "latest"
        df2 = df2.append(df1, ignore_index=True)
        return df2

    df2 = df2.append(df1, ignore_index=True)
    return df2


def get_historical(path):
    # for local
    # path_to_json = '../data/' + path + '/'
    
    # for docker
    path_to_json = '/app/data/' + path + '/'

    json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]

    df2 = pd.DataFrame()

    for a in json_files:
        f = open(path_to_json + a)

        # returns JSON object as
        # a dictionary
        data = json.load(f)

        jsnest = json.dumps(data)

        df = pd.json_normalize(data)

        df.columns = df.columns.map(lambda x: x.split(".")[-1])

        if "data" in json.loads(jsnest):
            df["data"] = json.dumps(json.loads(jsnest)["data"])
        elif "set" in json.loads(jsnest):
            df["data"] = json.dumps(json.loads(jsnest)["set"])

        df1 = df[['id', 'op', 'ts', 'data']]

        df2 = merge_logic(df2, df1, path)

    return df2


accdf = get_historical("accounts")
savdf = get_historical("savings_accounts")
cardsdf = get_historical("cards")


print("Historical view for Accounts:")
print(accdf)

print("Historical view for Savings:")
print(savdf)

print("Historical view for Cards:")
print(cardsdf)


accsavdf = pd.merge(accdf, savdf, on='savings_account_id', how='inner')

mergedf = pd.merge(accsavdf, cardsdf, on='card_id', how='inner')


print("Merged View Joined")
print(mergedf)


print("count of transaction")


totalTransactions = cardsdf["transaction_c"].notnull().sum() + savdf["transaction_s"].notnull().sum()

print(totalTransactions)