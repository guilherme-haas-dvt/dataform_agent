# Usamos una versión ligera de Python
FROM python:3.12-slim

# Hugging Face exige crear un usuario sin permisos de administrador
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app2

# Copiamos la lista de paquetes e instalamos
COPY --chown=user requirements2.txt .
RUN pip install --no-cache-dir -r requirements2.txt

# Copiamos todo tu código
COPY --chown=user . .

# Arrancamos Chainlit en el puerto 7860 que exige Hugging Face
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860", "--headless"]