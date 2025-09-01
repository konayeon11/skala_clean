
# fastapi_app_embeddings_ui.py
# Run: python -m uvicorn fastapi_app_embeddings_ui:app --reload --host 127.0.0.1 --port 8010
import os, json
import psycopg2, psycopg2.extras
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

def get_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST","localhost"),
        port=os.getenv("PGPORT","5432"),
        dbname=os.getenv("PGDATABASE","postgres"),
        user=os.getenv("PGUSER","postgres"),
        password=os.getenv("PGPASSWORD","postgres"),
    )

app = FastAPI(title="User Embeddings API (with UI)")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/neighbors")
def neighbors(user_id: str | None = None, x: float | None = None, y: float | None = None, k: int = 5):
    if not user_id and (x is None or y is None):
        raise HTTPException(status_code=400, detail="Provide user_id OR both x and y")

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if user_id:
        cur.execute("SELECT embedding FROM user_embeddings WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
        qvec = row["embedding"]
        sql = """
            SELECT user_id, embedding <=> %s::vector AS cosine_distance
            FROM user_embeddings
            WHERE user_id <> %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = (qvec, user_id, qvec, k)
    else:
        vec_literal = f"[{x}, {y}]"
        sql = f"""
            SELECT user_id, embedding <=> %s::vector AS cosine_distance
            FROM user_embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = (vec_literal, vec_literal, k)

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

@app.get("/", response_class=HTMLResponse)
def index():
    # minimal, clean UI with a form + table rendering
    html = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>User Embeddings UI</title>
  <style>
    :root { --bg:#0b132b; --card:#1c2541; --ink:#e0e6f5; --accent:#5bc0be; }
    *{box-sizing:border-box} body{margin:0;background:var(--bg);font-family:system-ui,Segoe UI,Roboto,Apple SD Gothic Neo,sans-serif;color:var(--ink)}
    .wrap{max-width:900px;margin:40px auto;padding:0 16px}
    .card{background:var(--card);border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,.25);padding:20px;margin-bottom:16px}
    h1{font-size:24px;margin:0 0 8px} p{margin:0 0 12px;color:#c1c7de}
    label{display:block;margin:8px 0 4px} input,select{width:100%;padding:10px;border-radius:10px;border:1px solid #2e3a67;background:#0f1b3d;color:var(--ink)}
    .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .actions{display:flex;gap:12px;margin-top:12px}
    button{padding:10px 14px;border-radius:10px;border:0;background:var(--accent);color:#062b2b;font-weight:700;cursor:pointer}
    table{width:100%;border-collapse:collapse;margin-top:12px}
    th,td{padding:10px;border-bottom:1px solid #2a355f;text-align:left}
    .muted{opacity:.75}
    .footer{color:#94a1c8;font-size:12px;margin-top:12px}
    @media (max-width:640px){.row{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>유저 임베딩 추천 데모</h1>
      <p class="muted">user_id로 조회하거나, 2D 벡터(x,y)로 직접 조회할 수 있습니다.</p>
      <div class="row">
        <div>
          <label>user_id</label>
          <input id="userId" placeholder="예: U0001" />
        </div>
        <div>
          <label>Top-K</label>
          <input id="topK" type="number" min="1" max="20" value="5" />
        </div>
      </div>
      <div class="row" style="margin-top:8px">
        <div>
          <label>x (선택)</label>
          <input id="xVal" type="number" step="0.0001" placeholder="예: 0.12" />
        </div>
        <div>
          <label>y (선택)</label>
          <input id="yVal" type="number" step="0.0001" placeholder="예: -1.03" />
        </div>
      </div>
      <div class="actions">
        <button onclick="queryNeighbors()">이웃 조회</button>
        <button onclick="resetForm()">초기화</button>
      </div>
      <div id="status" class="muted"></div>
      <table id="resultTable" style="display:none">
        <thead><tr><th>user_id</th><th>cosine_distance</th></tr></thead>
        <tbody></tbody>
      </table>
      <div class="footer">/neighbors API를 호출해 결과를 표시합니다.</div>
    </div>
  </div>
<script>
async function queryNeighbors(){
  const userId = document.getElementById('userId').value.trim();
  const k = document.getElementById('topK').value || 5;
  const x = document.getElementById('xVal').value.trim();
  const y = document.getElementById('yVal').value.trim();
  let url = '/neighbors?';
  if(userId){
    url += `user_id=${encodeURIComponent(userId)}&k=${k}`;
  }else if(x && y){
    url += `x=${encodeURIComponent(x)}&y=${encodeURIComponent(y)}&k=${k}`;
  }else{
    alert('user_id 또는 x,y를 입력하세요.');
    return;
  }
  document.getElementById('status').innerText = '조회 중...';
  try{
    const resp = await fetch(url);
    const data = await resp.json();
    renderTable(data);
    document.getElementById('status').innerText = `결과 ${data.length}건`;
  }catch(e){
    console.error(e);
    document.getElementById('status').innerText = '오류가 발생했습니다.';
  }
}
function renderTable(rows){
  const table = document.getElementById('resultTable');
  const tbody = table.querySelector('tbody');
  tbody.innerHTML='';
  for(const r of rows){
    const tr = document.createElement('tr');
    const td1 = document.createElement('td'); td1.textContent = r.user_id;
    const td2 = document.createElement('td'); td2.textContent = typeof r.cosine_distance==='number'? r.cosine_distance.toFixed(6): r.cosine_distance;
    tr.appendChild(td1); tr.appendChild(td2);
    tbody.appendChild(tr);
  }
  table.style.display = rows.length? 'table':'none';
}
function resetForm(){
  ['userId','xVal','yVal'].forEach(id => document.getElementById(id).value='');
  document.getElementById('status').innerText = '';
  document.getElementById('resultTable').style.display='none';
}
</script>
</body>
</html>
    """
    return HTMLResponse(content=html)
