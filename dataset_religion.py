import pandas as pd

def to_csv(df,filename):
    path = r"C:/Users/lea/DigitalHumanities/msc/SpatialHum/project"
    full_path = f"{path}//{filename}"
    df.to_csv(full_path, index = False)

df_religion = pd.read_csv(r'C:/Users/lea/DigitalHumanities/msc/SpatialHum/project/religion_1971.csv')
df_religion.head()
for index, row in df_religion.iterrows():
    df_religion['Area'] = df_religion['Area'].str.upper()
    df_religion['Distribution'] = (df_religion['Protestant in %'] - df_religion['Roman Catholic in %'])
df_religion = df_religion.drop(index=0)
to_csv(df_religion, 'religious_distribution.csv')