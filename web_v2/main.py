from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Trik biar bisa import 'src' dari folder luar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, utils

app = FastAPI()

# Setup Templates (HTML)
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Load Config Tags (Biar warna badge sinkron sama Admin)
TAGS_MAP = utils.load_tags_config()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": None})

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    results = []
    if q:
        # Panggil logic database yang SAMA PERSIS dengan Streamlit & Bot
        # Filter "Semua Modul" biar general search
        raw = database.search_faq(q, filter_tag="Semua Modul", n_results=10)
        
        if raw and raw['ids'][0]:
            for i in range(len(raw['ids'][0])):
                meta = raw['metadatas'][0][i]
                dist = raw['distances'][0][i]
                score = max(0, (1 - dist) * 100)
                
                # Filter Score > 30% biar hasil sampah ga muncul
                if score > 30:
                    meta['score'] = int(score)
                    # Ambil warna badge dari config
                    tag_info = TAGS_MAP.get(meta['tag'], {})
                    meta['color'] = tag_info.get('color', '#808080')
                    
                    # Potong teks jawaban biar ga kepanjangan di preview
                    text = meta.get('jawaban_tampil', '')
                    meta['snippet'] = text[:200] + "..." if len(text) > 200 else text
                    
                    results.append(meta)
            
            # Ambil Top 5
            results = results[:5]

    return templates.TemplateResponse("index.html", {"request": request, "results": results, "query": q})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)