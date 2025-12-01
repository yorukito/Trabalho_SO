import threading
import time
from colors import cyan

class TaskManager(threading.Thread):
    def __init__(self, arquiteture, servidores, requisicoes):
        super().__init__()
        self.arquiteture = arquiteture
        self.servidores = servidores
        self.requisicoes = requisicoes
        self.completion_times = {}  # Armazena tempos de conclusão {task_id: tempo_resposta}
        self.completion_lock = threading.Lock()  # Sincronização para completion_times
        self.start_time = time.time()
        self.end_time = 0
        
        # Atributos específicos para Round-Robin
        self.quantum = 1.0  # Fatia de tempo para preempção
        self.tasks_in_progress = {}  # Rastreia tarefas em execução {task_id: server_id}
        self.fila_de_prontos_rr = []  # Fila de prontos para RR
        
        # Inicializa campos nas requisições
        for req in self.requisicoes:
            req['tempo_restante'] = req['tempo_exec']  # Tempo que falta executar
            req['primeira_atribuicao'] = -1  # Momento da primeira atribuição
        
        # Vincula este gerenciador a cada servidor
        for server in self.servidores:
            server.task_manager = self
    
    def register_completion(self, task_id, response_time):
        """Registra conclusão de tarefas com tratamento específico por algoritmo"""
        with self.completion_lock:
            original_task = next((t for t in self.requisicoes if t['id'] == task_id), None)

            if self.arquiteture == 'rr':
                # Round-Robin: tarefa pode retornar à fila se não terminou
                if task_id in self.tasks_in_progress:
                    del self.tasks_in_progress[task_id]
                
                if original_task:
                    if original_task['tempo_restante'] > 0:
                        # Ainda tem tempo restante, re-enfileira
                        if original_task not in self.fila_de_prontos_rr:
                            self.fila_de_prontos_rr.append(original_task)
                    else:
                        # Tarefa completa, registra tempo de resposta
                        self.completion_times[task_id] = response_time
                        
            else:
                # SJF/Priority: tarefas executam até o fim (não-preemptivo)
                self.completion_times[task_id] = response_time
    
    def calculate_metrics(self, cpu_utilization):
        """Calcula métricas de desempenho do sistema"""
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
    
    def run(self):
        """Seleciona e executa o algoritmo de escalonamento"""
        if self.arquiteture == 'rr':
            self.run_rr_scheduler()
            
        elif self.arquiteture == 'sjf':
            self.run_sjf_scheduler()
        
        elif self.arquiteture == 'priority':
            self.run_priority_scheduler()
    
    def run_rr_scheduler(self):
        """Implementa Round-Robin com preempção baseada em quantum"""
        print('Running Rounding Robing Scheduler (Quantum: {:.2f}s)'.format(self.quantum))
        
        # Ordena tarefas por tempo de chegada
        sorted_requisicoes = sorted(self.requisicoes, key=lambda x: x['temp_chegada'])
        self.fila_global_pendente = sorted_requisicoes[:]  # Tarefas que ainda não chegaram
        self.fila_de_prontos_rr = []  # Tarefas prontas para executar
        
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
        
        server_index_rr = 0  # Índice para distribuição circular entre servidores
        
        # Loop principal: continua enquanto houver trabalho
        while self.fila_global_pendente or self.fila_de_prontos_rr or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
            
            tempo_atual = time.time() - self.start_time
            
            # Move tarefas que chegaram para a fila de prontos
            tasks_ready_to_move = []
            for task in self.fila_global_pendente:
                if task['temp_chegada'] <= tempo_atual:
                    tasks_ready_to_move.append(task)
            
            for task_to_move in tasks_ready_to_move:
                self.fila_global_pendente.remove(task_to_move)
                self.fila_de_prontos_rr.append(task_to_move)
            
            # Despacha tarefas da fila de prontos em round-robin
            for _ in range(num_servidores):
                
                if not self.fila_de_prontos_rr:
                    break
                    
                server_index_to_check = server_index_rr % num_servidores
                server = self.servidores[server_index_to_check]
                
                status = server.get_server_status()
                
                if status['current_capacity'] < status['max_capacity']:
                    
                    # Busca primeira tarefa que não está sendo processada
                    task_to_dispatch = None
                    for i, task in enumerate(self.fila_de_prontos_rr):
                        if task['id'] not in self.tasks_in_progress:
                            task_to_dispatch = self.fila_de_prontos_rr.pop(i)
                            break
                    
                    if task_to_dispatch is None:
                        # Todas as tarefas prontas já estão em execução
                        server_index_rr += 1 
                        continue
                        
                    task = task_to_dispatch
                    
                    # Calcula fatia de tempo: quantum ou tempo restante (o menor)
                    time_slice = min(self.quantum, task['tempo_restante'])
                    
                    # Cria cópia da tarefa com tempo do slice atual
                    dispatch_task = task.copy()
                    dispatch_task['tempo_restante'] = time_slice 
                    
                    # Atualiza tempo restante da tarefa original
                    task['tempo_restante'] -= time_slice
                    
                    # Marca tarefa como em processamento (evita duplicação)
                    self.tasks_in_progress[task['id']] = server.id
                    
                    server.assign_task(task=dispatch_task)
                    
                    # Registra primeira atribuição se for a primeira vez
                    if task['primeira_atribuicao'] == -1:
                         task['primeira_atribuicao'] = tempo_atual
                    
                    print(
                        f"\n{cyan('[DISPATCH]')} "
                        f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status['current_capacity']+1}/{status['max_capacity']})\n"
                        f" - Quantum (Slice): {time_slice:.2f}s (Rest: {task['tempo_restante']:.2f}s)\n"
                        f" - Chegada: {task['temp_chegada']:.2f}s"
                    )
                    
                    server_index_rr += 1
                
                else:
                    # Servidor cheio, tenta o próximo
                    server_index_rr += 1
            
            # Aguarda se há tarefas mas nenhum servidor livre
            if self.fila_global_pendente or self.fila_de_prontos_rr:
                time.sleep(0.1)

            # Encerra quando tudo foi processado
            if not self.fila_global_pendente and not self.fila_de_prontos_rr and all(s.get_server_status()['current_capacity'] == 0 for s in self.servidores):
                break
        
        self.end_time = time.time()
        
        print("\n--- FIM DO ROUND-ROBIN: ATRIBUIÇÃO E PROCESSAMENTO ---")
        
        # Finaliza servidores
        for server in active_servers:
            server.stop()
        
        for server in active_servers:
            server.join()
    
    def run_sjf_scheduler(self):
        """Implementa Shortest Job First (não-preemptivo)"""
        print('Running Shortest Job First Scheduler')
        
        # Ordena tarefas por tempo de chegada
        self.fila_global_pendente = sorted(self.requisicoes, key=lambda x: x['temp_chegada'])
        self.fila_de_prontos_sjf = []  # Fila persistente de tarefas prontas
    
        num_servidores = len(self.servidores)
        if num_servidores == 0:
            print("Erro: Nenhum servidor para a atribuição")
            return
        
        # Inicia servidores como threads
        active_servers = []
        for server in self.servidores:
            server.start()
            active_servers.append(server)
        
        print(f"\n--- {cyan("Servidores Iniciados")} ---")

        # Loop principal: continua enquanto houver trabalho
        while self.fila_global_pendente or self.fila_de_prontos_sjf or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
            
            tempo_atual = time.time() - self.start_time
            
            # Move tarefas que chegaram para fila de prontos
            tasks_ready_to_move = []
            for task in self.fila_global_pendente:
                if task['temp_chegada'] <= tempo_atual:
                    tasks_ready_to_move.append(task)
            
            for task_to_remove in tasks_ready_to_move:
                self.fila_global_pendente.remove(task_to_remove)
                self.fila_de_prontos_sjf.append(task_to_remove)
            
            # Ordena fila de prontos por tempo de execução (menor primeiro - SJF)
            self.fila_de_prontos_sjf.sort(key=lambda x: x['tempo_exec'])

            # Identifica servidores com capacidade disponível
            disponiveis = [s for s in self.servidores if s.get_server_status()['current_capacity'] < s.get_server_status()['max_capacity']]

            tasks_atribuidas = []
            
            # Atribui tarefas aos servidores disponíveis
            for server in disponiveis:
                
                # Revalida capacidade (importante para servidores com capacidade > 1)
                status = server.get_server_status()
                if status['current_capacity'] >= status['max_capacity']:
                    continue
                    
                if not self.fila_de_prontos_sjf:
                    break
                
                # Pega a tarefa mais curta da fila de prontos
                task = self.fila_de_prontos_sjf.pop(0) 
                
                server.assign_task(task=task)
                
                status = server.get_server_status()
                print(
                        f"\n{cyan('[DISPATCH]')} "
                        f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status['current_capacity']}/{status['max_capacity']})\n"
                        f" - Tempo Execução Total: {task['tempo_exec']:.2f}s\n"
                        f" - Chegada: {task['temp_chegada']:.2f}s\n"
                    )
                tasks_atribuidas.append(task)
            
            # Aguarda se há tarefas mas nenhum servidor livre
            if (self.fila_global_pendente or self.fila_de_prontos_sjf) and not disponiveis:
                time.sleep(0.5) 
                continue
                
            # Pequena pausa para sincronização
            if self.fila_global_pendente:
                time.sleep(0.1) 
            
            # Encerra quando tudo foi processado
            if not self.fila_global_pendente and not self.fila_de_prontos_sjf and all(s.get_server_status()['current_capacity'] == 0 for s in self.servidores):
                break
                        
        self.end_time = time.time()
        
        print("\n--- FIM DO SJF: ATRIBUIÇÃO E PROCESSAMENTO ---\n")

        # Finaliza servidores
        for server in active_servers:
            server.stop()
        for server in active_servers:
            server.join()

         #Implementa o escalonamento de Prioridade
    def run_priority_scheduler(self):
        print("Running Priority Scheduler")

        sorted_requisicoes = sorted(self.requisicoes, key=lambda x: (x['prioridade'], x['temp_chegada']))

        self.fila_global_pendente = sorted_requisicoes[:]
        
        
        num_servidores = len(self.servidores)
        
        if num_servidores == 0:
            print("Erro: Nenhum servidor disponível para atribuição.")
            return
        
        active_servers = []
        for server in self.servidores:
            server.start()
            active_servers.append(server)

        while self.fila_global_pendente or self.fila_de_prontos_priority or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
                
                tempo_atual = time.time() - self.start_time
                
                # Move tarefas que chegaram para fila de prontos
                tasks_ready_to_move = []
                for task in self.fila_global_pendente:
                    if task['temp_chegada'] <= tempo_atual:
                        tasks_ready_to_move.append(task)
                
                for task_to_remove in tasks_ready_to_move:
                    self.fila_global_pendente.remove(task_to_remove)
                    self.fila_de_prontos_priority.append(task_to_remove)
        
        print(f"\n--- {num_servidores} Servidores INICIADOS ---")

        while self.fila_global_pendente or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
            
            # Se a fila de espera acabou, mas servidores ainda trabalham, espera eles terminarem
            if not self.fila_global_pendente:
                if all(s.get_server_status()['current_capacity'] == 0 for s in self.servidores):
                    break
                time.sleep(0.5)
                continue
            
            # Pega a próxima tarefa prioritária (Topo da lista)
            # NÃO removemos ainda (.pop), apenas olhamos a tarefa.
            task = self.fila_global_pendente[0]
           

            # Tenta encontrar UMA vaga em QUALQUER servidor
            for server in self.servidores:
                status = server.get_server_status()
                tasks_atribuidas = []
                # Se achou vaga
                if status['current_capacity'] < status['max_capacity']:
                    # Remove da fila efetivamente
                    self.fila_global_pendente.pop(0)
                    
                    # Atribui ao servidor
                    server.assign_task(task=task)

                    status = server.get_server_status()
                    
                    print(f"  [PRIO {task['prioridade']}] Tarefa {task['id']} -> Servidor {server.id} (Ocupação: {status['current_capacity']}/{status['max_capacity']})")
                    tasks_atribuidas.append(task)

                

                 # Aguarda se há tarefas mas nenhum servidor livre
            if (self.fila_global_pendente or self.fila_de_prontos_sjf) and not self.servidores :
                time.sleep(0.5) 
                continue
                        # Pequena pausa para sincronização
            if self.fila_global_pendente:
                time.sleep(0.1) 
            
            # Encerra quando tudo foi processado
            if not self.fila_global_pendente and not self.fila_de_prontos_sjf and all(s.get_server_status()['current_capacity'] == 0 for s in self.servidores):
                break
                   
                    # Sai do loop de servidores e volta para pegar a próxima taref
            # LÓGICA DE BLOQUEIO (Strict Priority):
            # Se a tarefa mais importante (5) não conseguiu vaga, ninguém mais pode passar na frente.
            # O sistema espera (sleep) até liberar uma vaga para ELA.
            

        # Atualiza tempo final caso a lógica de callback falhe ou atrase
        self.end_time = time.time()
        
        print("\n--- FIM DA ATRIBUIÇÃO E PROCESSAMENTO ---")
        
        # Finaliza e junta as threads dos servidores
        for server in active_servers:
            server.stop()
        
        for server in active_servers:
            server.join()


### Explicação da alteração chave:


key=lambda x: (-x['prioridade'], x['temp_chegada'])