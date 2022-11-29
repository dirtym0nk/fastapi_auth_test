import base64
import hmac
import hashlib
import json
from typing import Optional
from fastapi import FastAPI, Form, Cookie
from fastapi.responses import Response
from data import SECRET_KEY, PASSWORD_SALT
# SECRET_KEY, PASSWORD_SALT Хранится в модуле data и создается с помощью <openssl rand -hex 32>


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


def verify_password(username: str, password: str) -> bool:
    """Проверяет хеш полученного пороля с хешем из базы данных"""
    password_hash = hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    print("хеш пароля в бд", stored_password_hash)
    print("то что получилось в вункции password_hash", password_hash)
    return  stored_password_hash == password_hash.lower()


users = {
    "zubrilov@alex.com": {
        "name": "Алексей!!!",
        "password": "db7eb7b69a9258c46601aa7bea7bc5cb719405bc3d013c67fd631bf1e24c69e9",
        "balance": 100_000
    },
    "sergey@alexandrov.com": {
        "name": "Сергей",
        "password": "5163798d04c6b7c6955750fa25b2a308d1171d45d45192fd09540b42f9e0716e",
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
    return Response(f"Привет! {users[valid_username]['name']}<br />Баланс: {user['balance']}", media_type="text/html")


@app.post("/login")
# используя fastapi достаем данные из полей формы. Функция Form передаст их как атрибуты для login_process
def login_process(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "Я вас не знаю"
            }), 
            media_type="aplication/json")
    response =  Response(
        json.dumps({
            "success": True, 
            "message": f"Привет! {users[username]['name']}<br />Баланс: {user['balance']}"
        }),
        media_type="aplication/json")
    signed_username = base64.b64encode(username.encode()).decode() + "." + \
        sign_data(username)
    response.set_cookie(key="username", value=signed_username)
    return response