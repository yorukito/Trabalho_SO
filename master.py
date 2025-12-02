from colors import cyan
import threading
import time

class TaskManager(threading.Thread):
    def __init__(self, arquiteture, servidores, requisicoes):
        super().__init__()
        # Algoritmo de escalonamento (e.g., 'rr', 'sjf', 'priority')
        self.arquiteture = arquiteture 
        self.servidores = servidores
        self.requisicoes = requisicoes
        # Armazena tempos de conclusão {task_id: tempo_resposta}
        self.completion_times = {}
        # Sincronização para completion_times
        self.completion_lock = threading.Lock() 
        self.start_time = time.time()
        self.end_time = 0
        
        # Atributos específicos para Round-Robin
        # Fatia de tempo para preempção (Round-Robin)
        self.quantum = 1.0 
        # Rastreia tarefas em execução {task_id: server_id}
        self.tasks_in_progress = {} 
        # Fila de prontos para RR
        self.fila_de_prontos_rr = [] 
        
        # Inicializa campos nas requisições
        for req in self.requisicoes:
            # Tempo que falta executar
            req['tempo_restante'] = req['tempo_exec'] 
            # Momento da primeira atribuição
            req['primeira_atribuicao'] = -1 
        
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
                    # Remove da lista de tarefas em progresso
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
            # Tempo médio de resposta
            avg_response_time = total_time / total_tasks 
            
            execution_time = self.end_time - self.start_time
            if execution_time > 0:
                # Vazão
                throughput = len(self.completion_times) / execution_time 
            else:
                throughput = 0.0
        
        wait_times = []
        for req in self.requisicoes:
            primeira = req.get('primeira_atribuicao', -1)
            if primeira is not None and primeira != -1:
                # Tempo de espera = primeira atribuição - tempo de chegada
                wait = primeira - req.get('temp_chegada', 0) 
                if wait < 0:
                    wait = 0.0
                wait_times.append(wait)

        if wait_times:
            # Tempo máximo de espera calculado
            max_wait_time = max(wait_times) 
        elif self.completion_times:
            est_waits = []
            for req in self.requisicoes:
                rt = self.completion_times.get(req['id'])
                if rt is not None:
                    # Estima espera para tarefas completas sem primeira atribuição
                    est = rt - req.get('tempo_exec', 0) 
                    est_waits.append(max(est, 0.0))
            max_wait_time = max(est_waits) if est_waits else 0.0
        else:
            # Valor padrão se nenhuma tarefa foi concluída
            max_wait_time = 4.3 

        self.display_summary(avg_response_time, cpu_utilization, max_wait_time, throughput)
    
    def display_summary(self, avg_response_time, cpu_utilization, max_wait_time, throughput):
        # Exibe métricas de desempenho
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
        # Tarefas que ainda não chegaram
        self.fila_global_pendente = sorted_requisicoes[:] 
        # Tarefas prontas para executar
        self.fila_de_prontos_rr = [] 
        
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
        
        # Índice para distribuição circular entre servidores
        server_index_rr = 0 
        
        # Loop principal: continua enquanto houver trabalho
        while self.fila_global_pendente or self.fila_de_prontos_rr or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
            
            # Tempo decorrido
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
                    
                # Servidor atual para checagem
                server_index_to_check = server_index_rr % num_servidores 
                server = self.servidores[server_index_to_check]
                
                status = server.get_server_status()
                
                # Servidor tem capacidade livre
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
                        f" - Chegada: {task['temp_chegada']:.2f}s\n"
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
        # Fila persistente de tarefas prontas
        self.fila_de_prontos_sjf = [] 
    
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
                
                status_pos_dispatch = server.get_server_status()
                print(
                        f"\n{cyan('[DISPATCH]')} "
                        f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status_pos_dispatch['current_capacity']}/{status_pos_dispatch['max_capacity']})\n"
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
            
    
    # Implementa o escalonamento de Prioridade
    def run_priority_scheduler(self):
        print("Running Priority Scheduler")

        # Ordena por prioridade (decrescente) e tempo de chegada (crescente)
        sorted_requisicoes = sorted(self.requisicoes, key=lambda x: (x['prioridade'], x['temp_chegada'])) 

        self.fila_global_pendente = sorted_requisicoes[:]
        # Fila persistente de tarefas prontas
        self.fila_de_prontos_priority = [] 
        
        priority_map = {
            1: "ALTA",
            2: "MEDIA",
            3: "BAIXA"
        }
        
        # Inicializa 'task' com None para evitar UnboundLocalError se a fila estiver vazia no início.
        task = None 
        
        num_servidores = len(self.servidores)
        
        if num_servidores == 0:
            print("Erro: Nenhum servidor disponível para atribuição.")
            return
        
        active_servers = []
        # Inicia servidores como threads
        for server in self.servidores: 
            server.start()
            active_servers.append(server)

        # Loop principal: continua enquanto houver trabalho
        while self.fila_global_pendente or self.fila_de_prontos_priority or any(s.get_server_status()['current_capacity'] > 0 for s in self.servidores):
                
                tempo_atual = time.time() - self.start_time
                
                # Move tarefas que chegaram para fila de prontos
                tasks_ready_to_move = []
                for task_check in self.fila_global_pendente:
                    if task_check['temp_chegada'] <= tempo_atual:
                        tasks_ready_to_move.append(task_check)
                
                for task_to_remove in tasks_ready_to_move:
                    self.fila_global_pendente.remove(task_to_remove)
                    self.fila_de_prontos_priority.append(task_to_remove)
                    # Reordena a fila pela prioridade a cada chegada
                    self.fila_de_prontos_priority.sort(key=lambda x: x['prioridade']) 

                # Identifica servidores disponíveis
                disponiveis = [s for s in self.servidores if s.get_server_status()['current_capacity'] < s.get_server_status()['max_capacity']]

                tasks_atribuidas = []  

                # Atribui tarefas aos servidores disponíveis
                for server in disponiveis:
                
                    status = server.get_server_status()
                    if status['current_capacity'] >= status['max_capacity']:
                        continue
                        
                    if not self.fila_de_prontos_priority:
                        break
                    
                    # Pega a tarefa de maior prioridade da fila
                    task = self.fila_de_prontos_priority.pop(0) 
                    
                    server.assign_task(task=task)
                    
                    status = server.get_server_status()

                    # Obtém a string de prioridade
                    priority_label = priority_map.get(task['prioridade'], "Desconhecida") 

                    print(
                        f"\n{cyan('[DISPATCH]')} "
                        f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status['current_capacity']}/{status['max_capacity']})\n"
                        f" - Tempo Execução Total: {task['tempo_exec']:.2f}s\n"
                        f" - Chegada: {task['temp_chegada']:.2f}s\n"
                        f" - Prioridade: {priority_label} ({task['prioridade']})\n"
                    )
                    tasks_atribuidas.append(task)

                # Aguarda se há tarefas mas nenhum servidor livre
                if (self.fila_global_pendente or self.fila_de_prontos_priority) and not disponiveis : # Correção: Usar 'disponiveis' em vez de 'self.servidores'
                    time.sleep(0.5) 
                    continue
                
                if self.fila_global_pendente:
                    time.sleep(0.1) 
                
                # Encerra quando tudo foi processado
                if not self.fila_global_pendente and not self.fila_de_prontos_priority and all(s.get_server_status()['current_capacity'] == 0 for s in self.servidores):
                    break
                    
        self.end_time = time.time()
        
        print("\n--- FIM DA ATRIBUIÇÃO E PROCESSAMENTO ---")
        
        # Finaliza servidores
        for server in active_servers:
            server.stop()
        
        for server in active_servers:
            server.join()