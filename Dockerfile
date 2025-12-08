# Usamos una imagen ligera de Node
FROM node:18-alpine

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiamos los archivos de dependencias primero
COPY package*.json ./

# Instalamos las dependencias
RUN npm install

# Copiamos el resto del código
COPY . .

# Exponemos el puerto (tu server.js usa process.env.PORT o 5000)
EXPOSE 5000

# Comando para iniciar la aplicación
CMD ["npm", "start"]
