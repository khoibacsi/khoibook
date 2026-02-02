from flask import Flask, request, redirect, session, send_from_directory
import psycopg2, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

UPLOAD = "uploads/images"
os.makedirs(UPLOAD, exist_ok=True)

# ================= DB =================

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    database=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASS"],
    port=os.environ["DB_PORT"],
)

def q(sql, args=(), one=False):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        if cur.description:
            r = cur.fetchall()
            return (r[0] if r else None) if one else r
        conn.commit()

# ================= AUTH =================

@app.route("/register", methods=["POST"])
def register():
    u = request.form["username"]
    p = generate_password_hash(request.form["password"])
    q("insert into users (username,password) values (%s,%s)", (u,p))
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"]
    p = request.form["password"]
    user = q("select id,password from users where username=%s",(u,),one=True)
    if user and check_password_hash(user[1], p):
        session["uid"] = user[0]
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= HOME =================

@app.route("/")
def index():
    posts = q("""
      select users.username, posts.image_url, posts.caption, posts.created_at
      from posts join users on posts.user_id=users.id
      order by posts.created_at desc
    """)

    return f"""
<!doctype html><html><head>
<meta charset=utf-8><meta name=viewport content=width=device-width>
<title>Khoibook</title>
<style>
body{{background:#020617;color:#e5e7eb;font-family:system-ui;margin:0}}
nav{{padding:12px;text-align:center}}
a{{color:#38bdf8;margin:0 8px}}
.container{{max-width:600px;margin:auto;padding:16px}}
.post{{background:#0f172a;padding:12px;border-radius:12px;margin-bottom:12px}}
img{{max-width:100%;border-radius:10px}}
</style></head><body>

<nav>
<a href="/">Feed</a>
<a href="/chat">Chat</a>
{"<a href=/logout>Logout</a>" if session.get("uid") else ""}
</nav>

<div class=container>

{""
if session.get("uid") else """
<form method=post action=/login>
<input name=username placeholder=Username>
<input name=password type=password placeholder=Password>
<button>Login</button>
</form>
<form method=post action=/register>
<input name=username placeholder=New username>
<input name=password type=password placeholder=Password>
<button>Register</button>
</form>
"""}

<form method=post action=/post enctype=multipart/form-data>
<input type=file name=image required>
<input name=caption placeholder=Caption>
<button>Post</button>
</form>

<hr>

{''.join(f"""
<div class=post>
<b>{u}</b><br>
<img src='/img/{i}'>
<p>{c}</p>
<small>{t.strftime('%d-%m %H:%M')}</small>
</div>
""" for u,i,c,t in posts)}

</div></body></html>
"""

# ================= POST =================

@app.route("/post", methods=["POST"])
def post():
    if not session.get("uid"):
        return redirect("/")

    img = request.files["image"]
    name = f"{int(datetime.now().timestamp())}_{img.filename}"
    img.save(os.path.join(UPLOAD, name))

    q(
      "insert into posts (user_id,image_url,caption) values (%s,%s,%s)",
      (session["uid"], name, request.form.get("caption"))
    )
    return redirect("/")

@app.route("/img/<n>")
def img(n):
    return send_from_directory(UPLOAD, n)

# ================= CHAT =================

@app.route("/chat")
def chat():
    return """
<!doctype html><html><body style="background:#020617;color:white">
<div id=box></div>
<input id=text><button onclick=send()>Send</button>
<script>
async function load(){
 let r=await fetch('/messages'); let d=await r.json();
 box.innerHTML=d.map(m=>`<p><b>${m.u}</b>: ${m.t}</p>`).join('')
}
async function send(){
 await fetch('/send',{method:'POST',
 headers:{'Content-Type':'application/x-www-form-urlencoded'},
 body:'text='+text.value})
 text.value=''
}
setInterval(load,1000); load()
</script></body></html>
"""

@app.route("/send", methods=["POST"])
def send():
    if not session.get("uid"): return "NO"
    q("insert into messages (user_id,text) values (%s,%s)",
      (session["uid"], request.form["text"]))
    return "OK"

@app.route("/messages")
def messages():
    rows = q("""
      select users.username, messages.text
      from messages join users on messages.user_id=users.id
      order by messages.created_at desc limit 50
    """)
    return [{"u":u,"t":t} for u,t in rows]

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
