import threading
import sys
import psutil           # pegar o uso de memoria

arquiteture = sys.argv[1]

class TaskManager(threading.Thread):
    def __init__(self, arquiteture, servidores, requisicoes):
        super().__init__()
        self.arquiteture = arquiteture
        self.servidores = servidores      
        self.requisicoes = requisicoes
    
    def run(self):
        if self.arquiteture == 'rr':
            print('rr')
            self.run_rr_scheduler()
            memory = psutil.virtual_memory()

            print(f"Memória Total: {memory.total / (1024**3):.2f} GB") # Total em GB
            print(f"Memória Disponível: {memory.available / (1024**3):.2f} GB") # Disponível em GB
            print(f"Porcentagem de Uso: {memory.percent}%") # Porcentagem de uso
            print(f"Memória Usada: {memory.used / (1024**3):.2f} GB") # Usada em GB
            
        elif self.arquiteture == 'sjf':
            print('sjf')

        elif self.arquiteture == 'priority':
            print('priority')
            
    def run_rr_scheduler(self):
        print('rr: Atribuição e Execução Paralela')
        sorted_by_arrivial = sorted(self.requisicoes, key=lambda x: x['temp_chegada'])
        
        num_servidores = len(self.servidores)
        
        if num_servidores == 0:
            print("Erro: Nenhum servidor disponível para atribuição.")
            return

        print("\n--- ATRIBUIÇÃO DAS TAREFAS (Round-Robin) ---")
        
        for i, task in enumerate(sorted_by_arrivial):
            server_index = i % num_servidores
            self.servidores[server_index].assign_task(task=task)
        
        print("\n--- EXECUÇÃO PARALELA ---")
        
        active_servers = []
        for server in self.servidores:
            server.start()
            active_servers.append(server)
            
        for server in active_servers:
            server.join()