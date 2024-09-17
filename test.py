import pandas as pd
df = pd.read_csv('темы - 7 класс.csv')
QUESTIONS = df['тема'].tolist()
print(QUESTIONS)