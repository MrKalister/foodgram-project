# foodgram_project
Для переноса своих данных из локального проекта на сервер необходимо проделать следующее:
1. Через консоль перейдите к проекту на локальном компьютере.
2. Зайдите в директорию с файлом manage.py.
3. Экспортируйте данные в файл.
```
python manage.py dumpdata > dump.json
```
4. Копируйте файл dump.json с локального компьютера на сервер при помощи утилиты scp.Выполните команду:
```
scp dump.json <username>@<HOST>:/home/<username>/.../<dir_of_project_with_manage.py>/
```

На сервере открыть bash в контейнере
```
docker-compose exec backend bash
```
Создайте миграции
```
python manage.py makemigrations
```
Примените миграции
```
python manage.py migrate
```
открываем редактор shell
```
python manage.py shell
```
выполнить в открывшемся терминале:
```
from django.contrib.contenttypes.models import ContentType
ContentType.objects.all().delete()
quit()
```
Загружаем тестовую базу.
```
python manage.py loaddata data/test_db.json
```