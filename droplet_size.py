import pandas as pd

NUM_DIVISIONS = int(input("Input Number of Divisions: "))
CONV = float(input("Input Conversion Factor: "))
fname = input("Input file name (e.g. 'Karlovci_04061998')")
df_dict = {"D":[],"N":[],"DxN":[],"D3":[],"D3xN":[]}

for T in range(1,NUM_DIVISIONS+1):
    droplets_in_division = int(input("Droplets in division %s=?" %(T)))
    df_dict["N"].append(droplets_in_division)
    D3 = T*T*T
    df_dict["D"].append(T)
    df_dict["D3"].append(D3)
    df_dict["D3xN"].append(D3*droplets_in_division)
    df_dict["DxN"].append(T*droplets_in_division) #i ovo moze kasnije

df= pd.DataFrame(df_dict)
df["percentage_of_total"]=(df.DxN/sum(df.DxN))*100
df["accumulative_percentage"] = df["percentage_of_total"].cumsum()
df["actual_droplet_size(DxCF)"] = df.D*CONV
df["D3_percentage_of_total"] = (df.D3xN/sum(df.D3xN))*100
df["D3_accumulative_percentage"] = df["D3_percentage_of_total"].cumsum()
df = df.set_index(df.D)
df["DxN_sum"] = df.DxN.sum()
df["N_sum"] = df.N.sum()
df["D3xN_sum"] = df.D3xN.sum()




#ovo napravi lepse TODO 

poslednji_pre_50 = df[df.accumulative_percentage<50].iloc[-1]
prvi_posle_50 = df[df.accumulative_percentage>=50].iloc[0]
D3_poslednji_pre_50 = df[df.D3_accumulative_percentage<50].iloc[-1]
D3_prvi_posle_50 = df[df.D3_accumulative_percentage>=50].iloc[0]
Y = poslednji_pre_50.accumulative_percentage
J = poslednji_pre_50.D
X = prvi_posle_50.accumulative_percentage
K = prvi_posle_50.D

Y3 = D3_poslednji_pre_50.D3_accumulative_percentage
J3 = D3_poslednji_pre_50.D
X3 = D3_prvi_posle_50.D3_accumulative_percentage
K3 = D3_prvi_posle_50.D

NM = (K+((50-X)/(Y-X))*(J-K))*CONV
VM = (K3+((50-X3)/(Y3-X3))*(J3-K3))*CONV
df["LMD"] = NM
df["VMD"] = VM
df["CF"] = CONV
print("Number Median Diameter = %s microns" %NM)
print("Volume Median Diameter = %s microns" %VM)
df.to_csv("%s.csv" %fname)
