import sys
import json
import psutil

from master import TaskManager
from server import Server

# Recebe o algoritmo de escalonamento via linha de comando (rr/sjf/priority)
arquiteture = sys.argv[1]

def capture_utilization():
    # Captura o percentual de uso da CPU em 1 segundo
    uso_cpu_geral = psutil.cpu_percent(interval=1) 
    return uso_cpu_geral

if __name__ == '__main__':
    # Valida se o algoritmo fornecido é suportado
    if arquiteture in ['rr', 'sjf', 'priority']:
        
        # Carrega configuração de servidores e requisições do arquivo JSON
        with open('tasks.json', 'r') as file:
            data = json.load(file)
        
        # Instancia os servidores com base nos dados do JSON
        servidores = []
        for serv_data in data["servidores"]:
            servidor = Server(serv_data['id'], serv_data['capacidade'])
            servidores.append(servidor)
        
        requisicoes = data['requisicoes']
        
        # Cria e executa o gerenciador de tarefas com o algoritmo escolhido
        t1 = TaskManager(arquiteture, servidores, requisicoes)
        t1.start()
        t1.join()  # Aguarda conclusão da execução

        # Coleta métricas de CPU e calcula estatísticas finais
        cpu_util = capture_utilization()
        t1.calculate_metrics(cpu_util)
