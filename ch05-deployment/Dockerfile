FROM python:3.10-slim

WORKDIR /app

# 换清华源（阿里云对大包不稳定，见第五章坑3）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

COPY requirements.txt .

# --no-cache-dir 避免层缓存问题（见第五章坑2）
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
