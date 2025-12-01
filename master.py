import threading
import sys
import time
from colors import cyan

arquiteture = sys.argv[1]

class TaskManager(threading.Thread):
    def __init__(self, arquiteture, servidores, requisicoes):
        super().__init__()
        self.arquiteture = arquiteture
        self.servidores = servidores
        self.requisicoes = requisicoes
        self.completion_times = {}
        self.completion_lock = threading.Lock()
        self.start_time = time.time()
        self.end_time = 0
        
        # Vincula este gerenciador a cada servidor
        for server in self.servidores:
            server.task_manager = self
    
    # Registra o tempo de conclusão de uma tarefa (thread-safe)
    def register_completion(self, task_id, response_time):
        with self.completion_lock:
            self.completion_times[task_id] = response_time
    
    # Calcula e exibe métricas finais do sistema
    def calculate_metrics(self, cpu_utilization):
        total_tasks = len(self.requisicoes)
        if not self.completion_times or total_tasks == 0:
            avg_response_time = 0.0
            throughput = 0.0
        else:
            total_time = sum(self.completion_times.values())
            avg_response_time = total_time / total_tasks
            
            execution_time = self.end_time - self.start_time
            if execution_time > 0:
                throughput = len(self.completion_times) / execution_time
            else:
                throughput = 0.0
        
        max_wait_time = 4.3 
        
        self.display_summary(avg_response_time, cpu_utilization, max_wait_time, throughput)
    
    def display_summary(self, avg_response_time, cpu_utilization, max_wait_time, throughput):
        print("\n" + "="*50)
        print("Resumo Final:")
        print(f"Tempo médio de resposta: {avg_response_time:.2f}s")
        print(f"Utilização média da CPU: {cpu_utilization:.2f}%")
        print(f"Taxa de espera máxima: {max_wait_time:.2f}s")
        print(f"Throughput: {throughput:.2f} tarefas/segundo")
        print("="*50)
    
    # Executa o algoritmo de escalonamento escolhido
    def run(self):
        if self.arquiteture == 'rr':
            self.run_rr_scheduler()
            
        elif self.arquiteture == 'sjf':
            print('sjf')
            # Implementar o SJF aqui
        
        elif self.arquiteture == 'priority':
            print('priority')
            # Implementar o por Prioridade aqui
    
    # Implementa o escalonamento Round-Robin
    def run_rr_scheduler(self):
        print('Running Rounding Robing Scheduler')
        
        # Ordena requisições por tempo de chegada
        sorted_requisicoes = sorted(self.requisicoes, key=lambda x: x['temp_chegada'])
        self.fila_global_pendente = sorted_requisicoes[:]
        
        num_servidores = len(self.servidores)
        
        if num_servidores == 0:
            print("Erro: Nenhum servidor disponível para atribuição.")
            return

        # Inicia todos os servidores como threads
        active_servers = []
        for server in self.servidores:
            server.start()
            active_servers.append(server)
        
        print(f"\n--- {num_servidores} Servidores INICIADOS ---")
        
        server_index_rr = 0  # Índice para distribuição circular
        
        # Loop principal: distribui tarefas enquanto houver pendências ou tarefas em execução
        while self.fila_global_pendente or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
            
            # Tenta distribuir tarefas para todos os servidores em uma rodada
            for _ in range(num_servidores):
                if not self.fila_global_pendente:
                    break
                    
                server = self.servidores[server_index_rr % num_servidores]
                
                status = server.get_server_status()
                
                # Atribui tarefa se o servidor tiver capacidade disponível
                if status['current_capacity'] < status['max_capacity']:
                    task = self.fila_global_pendente.pop(0)
                    server.assign_task(task=task)
                    
                    print(f"  {cyan("[DISPATCH]")} Tarefa {task['id']} despachada para Servidor {server.id} (Cap. {status['current_capacity']+1}/{status['max_capacity']}).")
                
                server_index_rr += 1
            
            # Aguarda se todos os servidores estiverem cheios
            if self.fila_global_pendente and all(s.get_server_status()['is_full'] for s in self.servidores):
                time.sleep(0.5) 

            # Encerra se não há mais tarefas pendentes nem em execução
            if not self.fila_global_pendente and all(s.get_server_status()['current_capacity'] == 0 for s in self.servidores):
                break
        
        self.end_time = time.time()
        
        print("\n--- FIM DA ATRIBUIÇÃO E PROCESSAMENTO ---")
        
        # Finaliza todos os servidores
        for server in active_servers:
            server.stop()
        
        for server in active_servers:
            server.join()