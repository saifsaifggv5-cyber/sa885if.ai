# run.py
import nest_asyncio
nest_asyncio.apply()

from pyngrok import ngrok
import uvicorn
import asyncio

# فتح نفق ngrok
public_url = ngrok.connect(8000)
print(f"\n{'='*50}")
print(f"🚀 المنصة شغالة على: {public_url}")
print(f"{'='*50}\n")

# تشغيل السيرفر
uvicorn.run("main:app", host="0.0.0.0", port=8000)