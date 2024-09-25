import pandas as pd
from constants import workdir

df = pd.read_csv(f'{workdir}/questions_7_8_grade.csv', )
QUESTIONS = df['тема'].tolist()

IMAGES = [f'{workdir}/Problems/'+'00'+str(num)+'.png' for num in range(1, 10)]
for num in range(10, len(QUESTIONS) + 1):
    IMAGES.append(f'{workdir}/Problems/'+'0'+str(num)+'.png')
