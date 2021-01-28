# DrfDjango
# Инструкция по разворачиванию приложения локально
Установить *Python*.  
Создать виртуальное пространство.

`pip install virtualenv`
 
`python -m venv`

Зайти в виртуальное пространство через командную строку и ввести


`venv\Scripts\activate`

Установить *Django*, *Django REST framework* (Используя данные `requirements.txt`).  
Запустить миграцию БД (приложение создавалось и тестировалось на *SQLite*).

    python manage.py migrate

# Инструкция по разворачиванию приложения в *Docker*
Установить *Docker*.  
Создать образ:

    docker build -t <image name> .

Создать и запустить контейнер из образа:

    docker run --name <container name> -d -p <host port>:8000 <image name>

Зайти в запущенный контейнер:

    docker exec -it <container name> /bin/bash

# Администрирование
Создать суперпользователя:

    python manage.py createsuperuser

Для аутентификации используется *token authentication*. Аутентификация требуется администраторам, а также анонимным
пользователям для прохождения опросов и доступа к пройденным опросам.

Администратору можно получить токен через консоль:

    python manage.py drf_create_token <username>

Для аутентификации в каждом запросе к API используется http header `Authorization`:

Для администратора:

    Authorization: Token <token>

Для анонимного пользователя:

    Authorization: Anonim <token>

# Разрешения
**IsAdminUser** - администраторы (`user.is_staff = True`).  
**IsAnonymousUserWithCredentials** - аутентифицированные анонимные пользователи.  
**AllowAny** - неаутентифицированные анонимные пользователи.

# Документация по API:
[/token](#token)  
[/anonymim-token](#anonymous-token)  
[/polls](#polls)  
[/active-polls](#active-polls)  
[/poll](#poll)  
[/poll/&lt;int id опроса&gt;](#pollint-id-опроса)  
[/question](#question)  
[/question/&lt;int id&gt;](#questionint-id)  
[/choice](#choice)  
[/choice/&lt;int id&gt;](#choiceint-id)  
[/text-response](#text-response)  
[/single-choice-response](#single-choice-response)  
[/multiple-choices-response](#multiple-choices-response)  
[/finished-polls](#finished-polls)  
[/unfinished-polls](#unfinished-polls)

## /token

### POST:
Возвращает токен для аутентификации админа через http header: `Authorization: Token <token>`

*permissions*: **AllowAny**

#### request:

```
{"username": <username>, "password": <password>}
```

#### response:

```
{
    "token": <str токен>
}
```

## /anonim-token

### POST:
Создает запись анонимного пользователя в БД и возвращает токен для аутентификации через http header:
`Authorization: Anonim <token>`

*permissions*: **AllowAny**

#### request:

Тело запроса отсутствует.

#### response:

```
{
    "token": <str токен>
}
```

## /polls
### GET
Список всех опросов.

*permissions*: **IsAdminUser**

#### response:

```
[
    {
        "id": <int id>,
        "name": <str название>,
        "description": <str описание>,
        "start": <str дата старта (гггг-мм-чч)>,
        "end": <str дата окончания (гггг-мм-чч)>
    },
    ...
]
```

## /active-polls
### GET
Список активных опросов.

*permissions*: **AllowAny**

#### response:
Аналогичный `/polls`

## /poll

### POST
Создание опроса. Дата старта должна быть в будущем, дата окончания должна быть больше даты старта.
С даты окончания опрос не активен. Изменение опроса с даты старта запрещено. Дата старта не может быть изменена.

*permissions*: **IsAdminUser**

#### request:

```
{
    "name": <str название>,
    "description": <str описание>,
    "start": <str дата старта (гггг-мм-чч)>,
    "end": <str дата окончания (гггг-мм-чч)>
}
```

## /poll/&lt;int id опроса&gt;
### GET
Возвращает объект опроса. Анонимным пользователям можно просматривать **только** активные опросы.

*permissions*: **AllowAny**

```
{
    "id": <int id>,    
    "name": <str название>,
    "description": <str описание>,
    "start": <str дата старта (гггг-мм-чч)>,
    "end": <str дата окончания (гггг-мм-чч)>,
    "questions": [<int id вопроса>, ...]
}
```

### PUT/PATCH

*permissions*: **IsAdminUser**

#### request:

```
{
    "name": <str название>,
    "description": <str описание>,
    "start": <str дата старта (гггг-мм-чч)>,
    "end": <str дата окончания (гггг-мм-чч)>
}
```

### DELETE

*permissions*: **IsAdminUser**

## /question

### POST
Создание вопроса. В одном опросе не могут быть вопросы с одинаковым текстом.
Добавить вопрос к опросу с даты старта нельзя.

*permissions*: **IsAdminUser**

#### request:

```
{
    "poll": <int id опроса>,
    "text": <str текст вопроса>,
    "type": <int тип вопроса>
}
```

**Типы вопросов**:  
1 - текстовый  
2 - с выбором одного варианта  
3 - с выбором нескольких вариантов  

## /question/&lt;int id&gt;

### GET
Получение вопроса. Анонимные пользователи могут просматривать только вопросы в активных опросах.
Если тип вопроса предполагает варианты ответа, то они включены в возвращаемый объект.

*permissions*: **AllowAny**

#### response:

```
{
    "id": <int id>,
    "poll": <int id опроса>,
    "text": <str текст вопроса>,
    "type": <int тип вопроса>,
    "choices": [
        {
            "id": <int id варианта>,
            "text": <str текст варианта>
        },
        ...
    ]
}
```

### PUT/PATCH
Изменение вопросов в опросе с даты старта нельзя.
Если тип меняется на текстовый, то варианты принадлежащие ему удаляются.

*permissions*: **IsAdminUser**

#### request:

```
{
    "id": <int id>,
    "poll": <int id опроса>,
    "text": <str текст вопроса>,
    "type": <int тип вопроса>
}
```

### DELETE
Удалять вопросы с даты старта опроса нельзя.

*permissions*: **IsAdminUser**

## /choice
### POST
Создание варианта ответа для вопросов с типом `2` и `3`. Добавлять вопросы к опросу с даты старта нельзя.
Добавить вопросы с одинаковы текстом к одному вопросу нельзя.

*permissions*: **IsAdminUser**

#### request:

```
{
    "question": <int id вопроса>,
    "text": <str текст варианта>
}
```

## /choice/&lt;int id&gt;

### GET:

*permissions*: **IsAdminUser**

#### response:

```
{
    "id": <int id>,
    "question": <int id вопроса>,
    "text": <str текст варианта>
}
```

### PUT/PATCH
Изменять вариант у опроса с даты старта нельзя.

*permissions*: **IsAdminUser**

#### request:

```
{
    "question": <int id вопроса>,
    "text": <str текст варианта>
}
```

### DELETE
Удалять вариант у опроса с даты старта нельзя.

*permissions*: **IsAdminUser**

## Прохождение опроса:
Для авторизации используется хедер `Authorization` и токен анонимного пользователя который сгенерирован по адресу
`/anonymous-token`. Проходить неактивные опросы нельзя.

## /text-response

### POST
Ввод ответа на вопрос с типом текст (тип `1`)

*permissions*: **IsAnonymousUserWithCredentials**

#### request:

```
{
    "question": <int id вопроса>,
    "text": <str текст ответа>
}
```

## /single-choice-response

### POST
Ввод ответа на вопрос с выбором одного варианта (тип `2`)

*permissions*: **IsAnonymousUserWithCredentials**

#### request:

```
{
    "choice": <int id варианта>
}
```

## /multiple-choices-response

### POST
Ввод ответа на вопрос с выбором нескольких вариантов (тип `3`). `choices` не может быть пустым списком.
Все варианты должны принадлежать одному вопросу. На один вопрос можно ответить только один раз.

*permissions*: **IsAnonymousUserWithCredentials**

#### request:

```
{
    "choices": [<int id варианта>, ...]
}
```

## Получение пройденных опросов:
Для авторизации используется хедер `Authorization` и токен анонимного пользователя который сгенерирован по адресу
`/anonim-token`.

## /finished-polls

### GET
Получение полностью пройденных пользователем опросов с детализацией по ответам.

*permissions*: **IsAnonymousUserWithCredentials**

#### response:

```
[
    {
        "id": <int id>,
        "name": <str название>,
        "description": <str описание>,
        "start": <str дата старта (гггг-мм-чч)>,
        "end": <str дата окончания (гггг-мм-чч)>,
        "questions": [
            {
                "id": <int id вопроса>,
                "text": <str текст вопроса>,
                "type": 1,
                "response": <str текст ответа>
            },
            {
                "id": <int id вопроса>,
                "text": <str текст вопроса>,
                "type": 2,
                "response": <str текст выбранного варианта>
            },
            {
                "id": <int id вопроса>,
                "text": <str текст вопроса>,
                "type": 3,
                "response": [
                    <str текст выбранного варианта>,
                    ...
                ]
            },
            ...
        ]
    },
    ...
]
```

## /unfinished-polls

### GET
Получение частично пройденных пользователем опросов с детализацией по ответам.

*permissions*: **IsAnonymousUserWithCredentials**

#### response:
Аналогичный `/finished-polls`, но в поле `response` у вопросов без ответа значение `null`.