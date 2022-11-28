import base64
import hmac
import hashlib
from typing import Optional
from fastapi import FastAPI, Form, Cookie
from fastapi.responses import Response
from data import SECRET_KEY 
# SECRET_KEY Хранится в модуле data и создается с помощью <openssl rand -hex 32>


app = FastAPI()


def sign_data(data: str) -> str:
    """Возвращает подписанные данные"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    """Разделяем usename и хеш и проверяем корректность"""
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username



users = {
    "zubrilov@alex.com": {
        "name": "Алексей!!!",
        "password": "some_password1",
        "balance": 100_000
    },
    "sergey@alexandrov.com": {
        "name": "Сергей",
        "password": "some_password2",
        "balance": 333_000
    }
}


@app.get("/")
def index_page(username: Optional[str] = Cookie(default=None)):
    with open("templates/login.html", "r") as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type="text/html")
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username") 
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    return Response(f"Привет! {users[valid_username]['name']}", media_type="text/html")


@app.post("/login")
# используя fastapi достаем данные из полей формы. Функция Form передаст их как атрибуты для login_process
def login_process(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or user["password"] != password:
        return Response("Я вас не знаю", media_type="text/html")
    response =  Response(f"Привет<br />Логин: {username}<br />Пароль: {password}<br />Баланс: {user['balance']}", media_type="text/html")
    signed_username = base64.b64encode(username.encode()).decode() + "." + \
        sign_data(username)
    response.set_cookie(key="username", value=signed_username)
    return response