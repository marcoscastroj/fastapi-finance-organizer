# Usa uma imagem oficial do Python, versão slim para ficar leve
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências primeiro (ajuda no cache do Docker)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do seu código para dentro do container
COPY . .

# Expõe a porta 8000 (a mesma que configuramos no docker-compose)
EXPOSE 8000

# Comando para iniciar a sua API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]