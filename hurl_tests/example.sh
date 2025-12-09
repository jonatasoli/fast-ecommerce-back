#!/bin/bash

http GET http://localhost:8000/health_check

http GET http://localhost:8000/task/1

http GET http://localhost:8000/tasks

http POST http://localhost:8001/cart/product product_id="1" quantity=1

http PUT http://localhost:8000/task/{id} name="Tarefa atualizada" completed:=true

http POST http://localhost:8001/cart/product product_id="1" quantity=1

