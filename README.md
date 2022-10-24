# desarrollo-cloud
Pasos para ejecutar la aplicación en docker

Es requerido tener instalado docker en la maquina

Nota importante!
Todos los archivos deben finalizar con new line "LF" (Unix) y no "CRLF" (Windows)

1. Realizar el clone del repositorio y hacer git checkout a la rama dockerCron
2. Ingresar a la carpeta clonada desarrollo-cloud
```
$ cd desarrollo-cloud
``` 
3. Ejecutar el siguiente comando para crear el contenedor de la base de datos
```
$ docker compose up -d db
``` 
4. Ejecutar el siguiente comando para crear el contenedor de la aplicación
```
$ docker compose up --build flaskapp
``` 
5. Una vez finalizada la creación del contenedor ejecutar pruebas con postman. La aplicación esta corriendo desde localhost:5000

6. En caso de utilizar un maquina Windows, se debe realizar un pequeño ajuste en el archivo entrypoint.sh seleccionando LF como "End of Line Sequence" en vez de CRLF.
