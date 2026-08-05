![Stability](https://img.shields.io/badge/stability-work_in_progress-lightgrey?style=flat&color=ffff00)

![GitHub repo size](https://img.shields.io/github/repo-size/UserAccountNotFound/dbcs?style=flat)

# dbcs
digital business card service

![Linux](https://img.shields.io/badge/-Linux-6C6694.svg?logo=linux&style=flat)
![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=Python&style=flat)


## Instalation backend

```
cd $INSTALL_DIR/dbcs

chmod +x ./deploy/scripts/deploy_backend.sh
chmod +x ./deploy/scripts/deploy_backend.sh
./deploy/scripts/deploy_backend.sh
./deploy/scripts/deploy_backend.sh
```

UPDATE users SET role = 'SUPERADMIN' WHERE email = 'твой_email@example.com';

curl -s -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@dbcs.example",
    "password": "StrongPassw0rd!123"
  }'
