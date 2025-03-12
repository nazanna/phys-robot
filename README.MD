## Как запускать

Есть Dockerfile, собрать образ и запустить контейнер надо через [скрипт](./docker.run.sh). Важно, чтобы в папке [secrets](/secrets/) находился файл [authorized_key.json](./secrets/authorized_key.json) с ключом сервисного аккаунта от Яндекс облака. Этот файл не будет передаваться в контейнер напрямую, только во время build. Там же должен лежать [credentials.json](/secrets/credentials.json) с кредами от GoogleAPI, он передается в контейнер.

Продовый бот: [@physro_bot](https://t.me/physro_bot).

Тестовый бот: [@bot_physici_bot](https://t.me/bot_physici_bot).