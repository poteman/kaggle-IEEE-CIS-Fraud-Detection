# coding: utf-8
import pandas as pd
pd.set_option("display.max_columns", 500)
import plotly.offline as py
py.init_notebook_mode(connected=True)
from tqdm import tqdm_notebook
import gc
import warnings
warnings.filterwarnings('ignore')

NROWS = None
# NROWS = 50000

pred_df = pd.read_csv("../features/kfold_predict.csv")
pred_df.columns = ["TransactionID", "pre_isFraud"]


train_identity = pd.read_csv('../input/train_identity.csv', nrows=NROWS)
train_transaction = pd.read_csv('../input/train_transaction.csv', nrows=NROWS)
train = train_transaction.merge(train_identity, how='left', on='TransactionID')
train = train.merge(pred_df, how='left', on='TransactionID')


test_identity = pd.read_csv('../input/test_identity.csv', nrows=NROWS)
test_transaction = pd.read_csv('../input/test_transaction.csv', nrows=NROWS)
test = test_transaction.merge(test_identity, how='left', on='TransactionID')
test = test.merge(pred_df, how='left', on='TransactionID')


# sub = pd.read_csv('../input/sample_submission.csv', nrows=NROWS)

gc.enable()
del train_identity, train_transaction
del test_identity, test_transaction
gc.collect()

print("train.shape:", train.shape)
print("test.shape:", test.shape)


target = "isFraud"

test[target] = -1

df = train.append(test)
df.reset_index()

df['uid'] = df["card1"].apply(lambda x: str(x)) + "_" + df["card2"].apply(lambda x: str(x)) + "_" + df["card3"].apply(lambda x: str(x)) \
            + "_" + df["card4"].apply(lambda x: str(x)) + "_" + df["card5"].apply(lambda x: str(x)) + "_" \
            + df["card6"].apply(lambda x: str(x)) + "_" \
            + df["addr1"].apply(lambda x: str(x)) + "_" + df["addr2"].apply(lambda x: str(x)) + \
            "_" + df["P_emaildomain"].apply(lambda x: str(x))

H_move = 12
df["day"] = (df["TransactionDT"] + 3600 * H_move) // (24 * 60 * 60)

target_feature = "pre_isFraud"

feature_list = ["uid", target, "D10", "day", "TransactionDT", "TransactionID", target_feature]

# 要查找最近交易的天数
lookup_day = 30


# 如果是D10==0,一天内只有一笔交易的话,不能用
uid_D10 = []
for DAY in tqdm_notebook(range(2, 91 + 1)):  # 2, 182+1
    print("DAY: ", DAY)
    for D10 in range(1, min(DAY, lookup_day)):  # 1, DAY
        uid_list = list(df.loc[(df["D10"] == D10) & (df["day"] == DAY), "uid"].values)
        TransactionID_list = list(df.loc[(df["D10"] == D10) & (df["day"] == DAY), "TransactionID"].values)

        for i in range(len(uid_list)):
            TransactionID_ = TransactionID_list[i]
            mean_ = 0
            sum_ = 0
            cnt_ = 0
            temp = df.loc[(df["uid"] == uid_list[i]) & (df["day"] == DAY - D10), feature_list]

            if temp.shape[0] != 0:
                mean_ = temp[target_feature].mean()
                sum_ = temp[target_feature].sum()
                cnt_ = temp[target_feature].shape[0]

            uid_D10.append([TransactionID_, mean_, sum_, cnt_])

uid_D10 = pd.DataFrame(uid_D10)
uid_D10.columns = ["TransactionID", target_feature + "_mean", target_feature + "_sum", target_feature + "_cnt"]
# uid_D10.columns = ["TransactionID", target_feature + "_prev"]
uid_D10.to_csv("../features/uid_D10_" + target_feature + "_train.csv",index=False)


# ### 测试集特征构造
uid_D10_test = []

for DAY in tqdm_notebook(range(93, 182 + 1)):  # test中day的最小值是92,最大值是182
    print("DAY: ", DAY)
    for D10 in range(1, min(DAY-92+1,lookup_day)):
        uid_list = list(df.loc[(df["D10"] == D10) & (df["day"] == DAY), "uid"].values)
        TransactionID_list = list(df.loc[(df["D10"] == D10) & (df["day"] == DAY), "TransactionID"].values)

        for i in range(len(uid_list)):

            TransactionID_ = TransactionID_list[i]
            mean_ = 0
            sum_ = 0
            cnt_ = 0

            temp = df.loc[(df["uid"] == uid_list[i]) & (df["day"] == DAY - D10), feature_list]

            if temp.shape[0] != 0:
                mean_ = temp[target_feature].mean()
                sum_ = temp[target_feature].sum()
                cnt_ = temp[target_feature].shape[0]

            uid_D10_test.append([TransactionID_, mean_, sum_, cnt_])

uid_D10_test = pd.DataFrame(uid_D10_test)
uid_D10_test.columns = ["TransactionID", target_feature + "_mean", target_feature + "_sum", target_feature + "_cnt"]
# uid_D10_test.columns = ["TransactionID", target_feature + "_prev"]
uid_D10_test.to_csv("../features/uid_D10_" + target_feature + "_test.csv",index=False)
