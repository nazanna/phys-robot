import pandas as pd
number_of_questions_in_first_poll = 53 # +2 - фамилия и имя
from constants import workdir

df = pd.read_csv(f'{workdir}/questions_7_grade.csv')
QUESTIONS = df['тема'].tolist()

IMAGES = [f'{workdir}/Problems/'+'00'+str(num)+'.png' for num in range(1, 10)]
for num in range(10, number_of_questions_in_first_poll + 1):
    IMAGES.append(f'{workdir}/Problems/'+'0'+str(num)+'.png')
