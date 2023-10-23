from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
from db_conn import DB_URL
from send_email import sending_email
from datetime import datetime
import pandas as pd


app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/sign_in")
async def sign_in(request: Request):
    form_data = await request.form()
    login = form_data["login"]
    password = form_data["password"]
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT * from users")
    data = cur.fetchall()
    conn.commit()
    conn.close()
    verified = None
    for line in data:
        if str(line[1]) == login and str(line[3]) == password:
            verified = 1
    if verified:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        login_error = 'Неправильный логин или пароль'
        return templates.TemplateResponse("index.html", {"request": request, "login_error": login_error})


@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/mails")
async def mails(request: Request):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            '''select u.*, m.*, ms.*, row_number() over(order by m.mailing_id)
            from mailings m
            left join users u on u.id = m.created_by
            left join mailing_statuses ms on ms.status_id = m.fk_mailing_status_id
            where m.is_deleted is not true
            order by m.mailing_id'''
        )
        data = cur.fetchall()
        conn.commit()
        conn.close()
        df = pd.DataFrame(data)
        nums = [num for num in df[11]]
        dates = [datetime.fromisoformat(str(date)).strftime('%d.%m.%Y %H:%M') for date in df[12]]
        statuses = [status for status in df[len([title for title in df]) - 2]]
        subjects = [subj for subj in df[len([title for title in df]) - 7]]
        users = [user for user in df[10]]
        sort = list(range(1, len(nums) + 1))
        res_df = pd.DataFrame({
            "#": nums,
            "Дата": dates,
            "Статус": statuses,
            "Пользователь": users,
            "Тема": subjects,
            "sort": sort
        })
        return templates.TemplateResponse("mails.html", {
            "request": request,
            "res_df": res_df
        })
    except Exception as _ex:
        return f"Возникла ошибка\nКод:{_ex}"


@app.get("/mails/{mailing_id}")
async def get_mail(request: Request, mailing_id: int):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            f"""SELECT
                m.mailing_id,
                to_char(m.created_at, 'dd.mm.yyyy hh24:mi'),
                ms.status_name,
                u.initials,
                right(left(m.recipients::text, -2), -2) as recipients,
                m.subject,
                m.mail_text,
                coalesce(m.parent_mailing_id, 0)
            FROM mailings m
            LEFT JOIN users u ON u.id = m.created_by
            LEFT JOIN mailing_statuses ms ON ms.status_id = m.fk_mailing_status_id
            WHERE m.mailing_id = {mailing_id}"""
        )
        mail_data = cur.fetchall()
        conn.commit()
        conn.close()
        return templates.TemplateResponse("mail.html", {
            "request": request,
            "mail_data": mail_data
        })
    except Exception as _ex:
        return templates.TemplateResponse("mail.html", {
            "request": Request,
            "Error": f"Ошибка!\nКод: {_ex}"
        })


@app.get("/create/simple_mail_sending")
async def simple_mail_sending(request: Request):
    return templates.TemplateResponse("simple_mail_sending.html", {"request": request})


@app.get("/mails/dlt/{mailing_id}")
async def mail_delete(mailing_id, request: Request):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            f"""CALL mailings_is_deleted_update({int(mailing_id)}) """
        )
        conn.commit()
        conn.close()
        mes = f"Рассылка №{mailing_id} успешно удалена!"
        return templates.TemplateResponse("mail_sending_status.html", {
            "request": request,
            "mes": mes
        })
    except Exception as _ex:
        return templates.TemplateResponse("mail_sending_status.html", {
            "request": request,
            "mes": _ex
        })


@app.post("/mails/simple_mail_sending/create")
async def simple_mail_sending_create(request: Request):
    try:
        form_data = await request.form()
        email = form_data["email"]
        subj = form_data["subj"]
        msg = form_data["msg"]
        parent = form_data["parent"]
        mes = sending_email(email, subj, msg, parent)
        return templates.TemplateResponse("mail_sending_status.html", {
            "request": request,
            "mes": mes
        })
    except Exception as _ex:
        return templates.TemplateResponse("mail_sending_status.html", {
            "request": request,
            "mes": _ex
        })
