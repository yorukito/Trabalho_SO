import sys              # pegar qual arquitetura vai rodar
import os               # pegar a utilizacao da cpu
import json             # pegar a quantidade dos servidores
import psutil           # pegar o uso de memoria

from master import TaskManager
from server import Server

arquiteture = sys.argv[1]

def capture_utilization():
    pass

if __name__ == '__main__':
    if arquiteture in ['rr', 'sjf', 'priority']:
        
        with open('tasks.json', 'r') as file:
            data = json.load(file)
            
        servidores = []
        threads_servidores = []
        for serv_data in data["servidores"]:
            servidor = Server(serv_data['id'], serv_data['capacidade'])
            servidores.append(servidor)
            threads_servidores.append(servidor)
        requisicoes = data['requisicoes']
        
        t1 = TaskManager(arquiteture, servidores, requisicoes)
        t1.start()
        
        # tread para pegar a utilizacao dos componentes
        # capture_utilization()


