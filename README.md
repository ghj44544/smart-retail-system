# smart-retail-system
智能零售用户行为分析系统

E:\program\mysql\bin\mysqld.exe

E:\program\Redis\redis-server.exe

cd E:\workspace\lingshou\smart-retail-system\backend
$env:DEBUG='true'
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

cd E:\workspace\lingshou\smart-retail-system\frontend
npm.cmd run dev



