## Foodgram

### Автор: 
Алаткин Александр

### Описание:
Foodgram — социальная сеть для публикации и поиска рецептов. Проект позволяет обмениваться рецептами любимых блюд с описанием их особенностей и фотографиями. Есть возможность скачивания списка ингридиентов, необходимых для приготовления выбранных блюд.

### Использующиеся технологии:
```
Django
Django Rest Framework
Djoser
PostgreSQL
Gunicorn
Nginx
Docker
GitHub Actions
```
### Установка. Как развернуть проект на удаленном сервере:

Подключиться к удаленному серверу.

Перейдите в домашнюю директорию и создайте там папку foodgram/ и заполните в этой директории файл .env:

```
mkdir foodgram
```

Поочерёдно выполните на сервере команды для установки Docker и Docker Compose для Linux:

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

Установите и запустите Nginx:

```
sudo apt install nginx -y
sudo systemctl start nginx
```

Укажите файрволу, какие порты должны остаться открытыми:

```
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
```

Теперь включите файрвол:

```
sudo ufw enable
```

Внесите изменения в файл конфигурации веб-сервера так, что все запросы пойдут в Docker, на порт 9000:

```
sudo nano /etc/nginx/sites-enabled/default
```

Далее перезагрузите конфигурацию Nginx:

```
sudo systemctl reload nginx
```

Запушьте проект на гит, далее проект Foodgram будет развернут на сервере с помощью GitHub Actions.
