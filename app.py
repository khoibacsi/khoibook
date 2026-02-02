from flask import Flask, request, send_from_directory
import os, json
from datetime import datetime

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD = os.path.join(BASE, "uploads", "images")
DATA = os.path.join(BASE, "data")

os.makedirs(UPLOAD, exist_ok=True)

# ================= HOME =================

@app.route("/")
def index():
    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>Khacebook</title>
<style>
body {{ background:#020617;color:#e5e7eb;font-family:system-ui;margin:0 }}
nav {{ padding:12px;text-align:center;background:#020617 }}
a {{ color:#38bdf8;margin:0 12px;text-decoration:none }}
.container {{ padding:16px;max-width:600px;margin:auto }}
.post {{ background:#0f172a;padding:12px;border-radius:12px;margin-bottom:12px }}
img {{ max-width:100%;border-radius:10px }}
input, textarea, button {{
  width:100%;padding:10px;margin:6px 0;
  border-radius:10px;border:none;font-size:15px
}}
button {{ background:#38bdf8;color:black;font-weight:600 }}
small {{ color:#94a3b8 }}
</style>
</head>

<body>
<nav>
  <a href="/">📸 Feed</a>
  <a href="/chat">💬 Chat</a>
</nav>

<div class="container">

<h3>Đăng ảnh</h3>
<form method="post" action="/post" enctype="multipart/form-data">
  <input name="author" placeholder="Tên (tùy chọn)">
  <input type="file" name="image" required>
  <textarea name="caption" placeholder="Nội dung"></textarea>
  <button>Đăng</button>
</form>

<hr>

<h3>📸 Feed</h3>
{render_feed()}

</div>
</body>
</html>
"""



# ================= FEED =================

def render_feed():
    with open(os.path.join(DATA,"posts.json"), encoding="utf-8") as f:
        posts = json.load(f)

    html = ""
    for p in reversed(posts):
        html += f"""
        <div class="post">
          <b>{p['author']}</b><br>
          <img src="/img/{p['image']}">
          <p>{p['caption']}</p>
          <small>{p['time']}</small>
        </div>
        """
    return html or "<i>Chưa có bài</i>"

# ================= POST =================

@app.route("/post", methods=["POST"])
def post():
    image = request.files.get("image")
    author = request.form.get("author") or "Ẩn danh"
    caption = request.form.get("caption","")

    name = f"{int(datetime.now().timestamp())}_{image.filename}"
    image.save(os.path.join(UPLOAD, name))

    post = {
        "author": author,
        "image": name,
        "caption": caption,
        "time": datetime.now().strftime("%d-%m-%Y %H:%M")
    }

    path = os.path.join(DATA,"posts.json")
    with open(path,"r+",encoding="utf-8") as f:
        data = json.load(f)
        data.append(post)
        f.seek(0)
        json.dump(data,f,ensure_ascii=False,indent=2)

    return "<script>location.href='/'</script>"

# ================= IMAGE =================

@app.route("/img/<name>")
def img(name):
    return send_from_directory(UPLOAD, name)

# ================= CHAT =================

@app.route("/chat")
def chat():
    return """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>Chat</title>
<style>
body{background:#020617;color:#e5e7eb;font-family:system-ui}
.container{max-width:600px;margin:auto;padding:16px}
input,button{width:100%;padding:10px;margin:6px 0;border-radius:10px;border:none}
button{background:#38bdf8;color:black}
.msg{font-size:14px;margin:4px 0}
</style>
</head>
<body>
<div class="container">
<h3>💬 Chat công khai</h3>
<div id="box"></div>
<input id="username" placeholder="Tên">
<input id="text" placeholder="Nội dung">
<button onclick="send()">Gửi</button>
</div>

<script>
const box = document.getElementById("box")
const username = document.getElementById("username")
const text = document.getElementById("text")

async function load(){
  let r = await fetch("/messages")
  let d = await r.json()
  box.innerHTML = d.map(m =>
    `<div class="msg"><b>${m.name}</b>: ${m.text} <small>${m.time}</small></div>`
  ).join("")
}

async function send(){
  await fetch("/send",{
    method:"POST",
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:`name=${encodeURIComponent(username.value)}&text=${encodeURIComponent(text.value)}`
  })
  text.value=""
}

setInterval(load,1000)
load()
</script>

</body>
</html>
"""

@app.route("/send", methods=["POST"])
def send():
    msg = {
        "name": request.form.get("name") or "Ẩn danh",
        "text": request.form.get("text"),
        "time": datetime.now().strftime("%H:%M")
    }

    path = os.path.join(DATA,"messages.json")
    with open(path,"r+",encoding="utf-8") as f:
        data = json.load(f)
        data.append(msg)
        f.seek(0)
        json.dump(data,f,ensure_ascii=False)

    return "OK"

@app.route("/messages")
def messages():
    with open(os.path.join(DATA,"messages.json"),encoding="utf-8") as f:
        return json.dumps(json.load(f),ensure_ascii=False)

# ================= RUN =================

if __name__ == "__main__":
    app.run()

