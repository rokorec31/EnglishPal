FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 複製 requirements 文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式文件
COPY . .

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "app.py"]