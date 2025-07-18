![Stability](https://img.shields.io/badge/stability-work_in_progress-lightgrey?style=flat&color=ffff00)

![GitHub repo size](https://img.shields.io/github/repo-size/UserAccountNotFound/dbcs?style=flat)

# dbcs
digital business card service

![Linux](https://img.shields.io/badge/-Linux-6C6694.svg?logo=linux&style=flat)
![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=Python&style=flat)
![Java](https://img.shields.io/badge/Java-007396.svg?logo=Java&style=flat)
![Flask](https://img.shields.io/badge/Flask-%23000.svg?logo=flask&style=flat&logoColor=white)

## Instalation

1. Устанавливаем необходимые системные пакеты:
``` bash
sudo apt install python3 python3-pip python3-venv gunicorn
```

2. Клонируем репозиторий
```bash
git clone https://github.com/UserAccountNotFound/dbcs.git /opt/dbcs && \
cd /opt/dbcs
```

3. Создаем виртуальное окружение и активируем его
```bash
python3 -m venv .venv && \
source .venv/bin/activate
```

4. Копирууем фаил переременных и заполняем его:
```bash
cp /opt/dbcs/_deploy/env.example /opt/dbcs/.env 
```
  4.1 
``` python
import os
os.urandom(16).hex()
```

5. Устанавливаем зависимости сервиса:
```bash
pip install -r requirements.txt
```

6. Создаем пользователя
```bash
python3 /opt/dbcs/_deploy/create_admin.py
```

7. Запуск сервиса:

7.1. Запуск DEV-окружения:
```bash
flask run --host=0.0.0.0
```

7.2. Запуск PROD-окружения:
```bash
cp /opt/dbcs/_deploy/dbcs.service /etc/systemd/system/dbcs.service && \
sudo systemctl start dbcs && \
sudo systemctl enable dbcs && \
sudo systemctl status dbcs
```

## Contributing
Кроме меня это ни кому не нужно.

## License
Проект распространяется под Apache License Version 2.0 - подробности смотрите в файле LICENSE.

## Acknowledgments
Особая благодарность всем проектам с открытым исходным кодом,
и людям что готовы делиться знаниями.