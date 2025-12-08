from colors import cyan
import threading
import time

class TaskManager(threading.Thread):
    def __init__(self, architecture, servers, requests):
        super().__init__()
        
        # Scheduler algorithm configuration
        self.architecture = architecture 
        self.servers = servers
        self.requests = requests 
        
        # Performance tracking
        self.completion_times = {}
        self.completion_lock = threading.Lock() 
        self.start_time = time.time()
        self.end_time = 0
        
        # Round-Robin specific attributes
        self.quantum = 1.0
        self.tasks_in_progress = {}
        self.rr_ready_queue = []
        
        # Task completion tracking via dictionary for robust removal
        self.tasks_to_complete = {task['id']: task for task in self.requests} 
        
        # Initialize task fields
        for request in self.requests:
            request['tempo_restante'] = request['tempo_exec'] 
            request['primeira_atribuicao'] = -1 
            
        # Bind manager to each server
        for server in self.servers:
            server.task_manager = self
    

    def register_completion(self, task_id, response_time):
        """Handle task completion based on scheduling algorithm"""
        
        with self.completion_lock:
            original_task = next((t for t in self.requests if t['id'] == task_id), None)

            if self.architecture == 'rr':
                
                if original_task and original_task['tempo_restante'] > 0:
                    # Task has remaining time, re-queue it
                    if original_task not in self.rr_ready_queue:
                        self.rr_ready_queue.append(original_task)
                    
                    if task_id in self.tasks_in_progress:
                         del self.tasks_in_progress[task_id]

                elif original_task and original_task['tempo_restante'] <= 0:
                    # Task fully completed
                    self.completion_times[task_id] = response_time
                    
                    if task_id in self.tasks_to_complete:
                        del self.tasks_to_complete[task_id]
                    
                    if task_id in self.tasks_in_progress:
                         del self.tasks_in_progress[task_id]
                        
            else:
                # Non-preemptive algorithms: task runs to completion
                self.completion_times[task_id] = response_time
                
                if task_id in self.tasks_to_complete:
                    del self.tasks_to_complete[task_id]


    def calculate_metrics(self, cpu_utilization):
        """Calculate and display system performance metrics"""
        
        total_tasks = len(self.requests)
        
        if not self.completion_times or total_tasks == 0:
            avg_response_time = 0.0
            throughput = 0.0
        else:
            total_time = sum(self.completion_times.values())
            avg_response_time = total_time / len(self.completion_times) 
            
            execution_time = self.end_time - self.start_time
            if execution_time > 0:
                throughput = len(self.completion_times) / execution_time 
            else:
                throughput = 0.0
        
        # Calculate wait times
        wait_times = []
        for request in self.requests:
            first_assignment = request.get('primeira_atribuicao', -1)
            if first_assignment is not None and first_assignment != -1:
                wait_time = first_assignment - request.get('temp_chegada', 0) 
                if wait_time < 0:
                    wait_time = 0.0
                wait_times.append(wait_time)

        # Determine maximum wait time
        if wait_times:
            max_wait_time = max(wait_times) 
        elif self.completion_times:
            estimated_waits = []
            for request in self.requests:
                response_time = self.completion_times.get(request['id'])
                if response_time is not None:
                    estimated = response_time - request.get('tempo_exec', 0) 
                    estimated_waits.append(max(estimated, 0.0))
            max_wait_time = max(estimated_waits) if estimated_waits else 0.0
        else:
            max_wait_time = 4.3

        self.display_summary(avg_response_time, cpu_utilization, max_wait_time, throughput)
    
    
    def display_summary(self, avg_response_time, cpu_utilization, max_wait_time, throughput):
        """Display performance summary"""
        
        print("\n" + "="*50)
        print("Resumo Final:")
        print(f"Tempo médio de resposta: {avg_response_time:.2f}s")
        print(f"Utilização média da CPU: {cpu_utilization:.2f}%")
        print(f"Taxa de espera máxima: {max_wait_time:.2f}s")
        print(f"Throughput: {throughput:.2f} tarefas/segundo")
        print("="*50)
    
    
    def run(self):
        """Execute the configured scheduling algorithm"""
        
        if self.architecture == 'rr':
            self.run_rr_scheduler()
        elif self.architecture == 'sjf':
            self.run_sjf_scheduler()
        elif self.architecture == 'priority':
            self.run_priority_scheduler()
    

    def run_rr_scheduler(self):
        """Round-Robin scheduler with time quantum preemption"""
        
        print('Running Rounding Robing Scheduler (Quantum: {:.2f}s)'.format(self.quantum))
        
        # Initialize queues
        sorted_requests = sorted(self.requests, key=lambda x: x['temp_chegada'])
        self.pending_global_queue = sorted_requests[:] 
        self.rr_ready_queue = [] 
        
        num_servers = len(self.servers)
        if num_servers == 0:
            print("Erro: Nenhum servidor disponível para atribuição.")
            return

        # Start all server threads
        active_servers = []
        for server in self.servers:
            server.start()
            active_servers.append(server)
        
        print(f"\n--- {num_servers} Servidores INICIADOS ---")
        
        server_index = 0 
        is_running = True
        
        while is_running:
            
            # Check termination conditions
            with self.completion_lock:
                all_completed = not self.tasks_to_complete 
            
            is_server_busy = any(s.get_server_status()['current_capacity'] > 0 for s in self.servers)

            # Exit when all tasks completed and servers idle
            if all_completed and not is_server_busy and not self.pending_global_queue and not self.rr_ready_queue:
                is_running = False
                break
                
            if not is_running:
                time.sleep(0.1)
                continue

            current_time = time.time() - self.start_time 
            
            # Move arrived tasks to ready queue
            tasks_to_move = []
            for task in self.pending_global_queue:
                if task['temp_chegada'] <= current_time:
                    tasks_to_move.append(task)
            
            for task_to_move in tasks_to_move:
                self.pending_global_queue.remove(task_to_move)
                self.rr_ready_queue.append(task_to_move)
            
            # Dispatch tasks in round-robin fashion
            for _ in range(num_servers):
                
                if not self.rr_ready_queue:
                    break
                    
                server_idx_check = server_index % num_servers 
                server = self.servers[server_idx_check]
                
                status = server.get_server_status()
                
                if status['current_capacity'] < status['max_capacity']: 
                    
                    # Find next task not currently executing
                    task_to_dispatch_reference = None
                    for i, task_in_queue in enumerate(self.rr_ready_queue):
                        if task_in_queue['id'] not in self.tasks_in_progress:
                            task_to_dispatch_reference = self.rr_ready_queue.pop(i)
                            break
                    
                    if task_to_dispatch_reference is None:
                        server_index += 1 
                        continue
                        
                    # Get master task object for state updates
                    task = next((t for t in self.requests if t['id'] == task_to_dispatch_reference['id']), None)
                    
                    if task is None:
                        print(f"ERRO: Tarefa {task_to_dispatch_reference['id']} escalonada, mas não encontrada em self.requests.")
                        server_index += 1
                        continue

                    # Calculate time slice
                    time_slice = min(self.quantum, task['tempo_restante']) 
                    
                    # Create dispatch copy with time slice
                    dispatch_task = task.copy()
                    dispatch_task['tempo_restante'] = time_slice 
                    
                    # Update remaining time
                    task['tempo_restante'] -= time_slice 
                    
                    # Mark task as in progress
                    self.tasks_in_progress[task['id']] = server.id 
                    
                    server.assign_task(task=dispatch_task)
                    
                    # Record first assignment time
                    if task['primeira_atribuicao'] == -1: 
                               task['primeira_atribuicao'] = current_time
                    
                    print(
                        f"\n{cyan('[DISPATCH]')} "
                        f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status['current_capacity']+1}/{status['max_capacity']})\n"
                        f" - Quantum (Slice): {time_slice:.2f}s (Rest: {task['tempo_restante']:.2f}s)\n"
                        f" - Tempo Execução Total (Original): {task['tempo_exec']:.2f}s\n"
                        f" - Chegada: {task['temp_chegada']:.2f}s\n"
                    )
                    
                    server_index += 1
                
                else:
                    server_index += 1 
            
            # Allow servers to process
            time.sleep(0.1) 
            
        self.end_time = time.time()
        
        print("\n--- FIM DO ROUND-ROBIN: ATRIBUIÇÃO E PROCESSAMENTO ---")
        
        # Shutdown servers
        for server in active_servers:
            server.stop()
        
        for server in active_servers:
            server.join()
    

    def run_sjf_scheduler(self):
        """Shortest Job First scheduler (non-preemptive)"""
        
        print('Running Shortest Job First Scheduler')
        
        # Initialize queues
        self.pending_global_queue = sorted(self.requests, key=lambda x: x['temp_chegada'])
        self.sjf_ready_queue = [] 

        num_servers = len(self.servers)
        if num_servers == 0:
            print("Erro: Nenhum servidor para a atribuição")
            return
        
        # Start server threads
        active_servers = []
        for server in self.servers:
            server.start()
            active_servers.append(server)
        
        print(f"\n--- {cyan("Servidores Iniciados")} ---")

        while self.tasks_to_complete:
            
            current_time = time.time() - self.start_time
            
            # Move arrived tasks to ready queue
            tasks_to_move = []
            for task in self.pending_global_queue:
                if task['temp_chegada'] <= current_time:
                    tasks_to_move.append(task)
            
            for task_to_remove in tasks_to_move:
                self.pending_global_queue.remove(task_to_remove)
                self.sjf_ready_queue.append(task_to_remove)
            
            # Sort by execution time (shortest first)
            self.sjf_ready_queue.sort(key=lambda x: x['tempo_exec']) 

            # Find available servers
            available_servers = [s for s in self.servers if s.get_server_status()['current_capacity'] < s.get_server_status()['max_capacity']]

            assigned_tasks = []
            
            # Assign tasks to available servers
            for server in available_servers:
                
                status = server.get_server_status()
                if status['current_capacity'] >= status['max_capacity']:
                    continue
                    
                if not self.sjf_ready_queue:
                    break
                
                task = self.sjf_ready_queue.pop(0) 
                
                server.assign_task(task=task)
                
                # Record first assignment time
                if task.get('primeira_atribuicao', -1) == -1:
                    task['primeira_atribuicao'] = current_time 
                
                status_after = server.get_server_status()
                print(
                        f"\n{cyan('[DISPATCH]')} "
                        f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status_after['current_capacity']}/{status_after['max_capacity']})\n"
                        f" - Tempo Execução Total: {task['tempo_exec']:.2f}s\n"
                        f" - Chegada: {task['temp_chegada']:.2f}s\n"
                    )
                assigned_tasks.append(task)
            
            # Prevent tight loop
            is_server_busy = any(s.get_server_status()['current_capacity'] > 0 for s in self.servers)
            if self.pending_global_queue or self.sjf_ready_queue or is_server_busy:
                time.sleep(0.1) 
            
            # Check exit condition
            if not self.tasks_to_complete and all(s.get_server_status()['current_capacity'] == 0 for s in self.servers):
                 break
                    
        self.end_time = time.time()
        
        print("\n--- FIM DO SJF: ATRIBUIÇÃO E PROCESSAMENTO ---\n")

        # Shutdown servers
        for server in active_servers:
            server.stop()
        for server in active_servers:
            server.join()
            

    def run_priority_scheduler(self):
        """Priority-based scheduler (non-preemptive)"""
        
        print("Running Priority Scheduler")

        # Sort by priority then arrival time
        sorted_requests = sorted(self.requests, key=lambda x: (x['prioridade'], x['temp_chegada'])) 

        self.pending_global_queue = sorted_requests[:]
        self.priority_ready_queue = [] 
        
        priority_map = {
            1: "ALTA",
            2: "MEDIA",
            3: "BAIXA"
        }
        
        task = None 
        
        num_servers = len(self.servers)
        
        if num_servers == 0:
            print("Erro: Nenhum servidor disponível para atribuição.")
            return
        
        # Start server threads
        active_servers = []
        for server in self.servers: 
            server.start()
            active_servers.append(server)

        while self.tasks_to_complete:
                
            current_time = time.time() - self.start_time
            
            # Move arrived tasks to ready queue
            tasks_to_move = []
            for task_check in self.pending_global_queue:
                if task_check['temp_chegada'] <= current_time:
                    tasks_to_move.append(task_check)
            
            for task_to_remove in tasks_to_move:
                self.pending_global_queue.remove(task_to_remove)
                self.priority_ready_queue.append(task_to_remove)
                # Re-sort by priority on each arrival
                self.priority_ready_queue.sort(key=lambda x: x['prioridade']) 

            # Find available servers
            available_servers = [s for s in self.servers if s.get_server_status()['current_capacity'] < s.get_server_status()['max_capacity']]

            assigned_tasks = []  

            # Assign tasks to available servers
            for server in available_servers:
                
                status = server.get_server_status()
                if status['current_capacity'] >= status['max_capacity']:
                    continue
                    
                if not self.priority_ready_queue:
                    break
                
                task = self.priority_ready_queue.pop(0) 
                
                server.assign_task(task=task)
                
                # Record first assignment time
                if task.get('primeira_atribuicao', -1) == -1:
                    task['primeira_atribuicao'] = current_time 
                
                status = server.get_server_status()

                priority_label = priority_map.get(task['prioridade'], "Desconhecida") 

                print(
                    f"\n{cyan('[DISPATCH]')} "
                    f"Tarefa {task['id']} -> Servidor {server.id} (Cap: {status['current_capacity']}/{status['max_capacity']})\n"
                    f" - Tempo Execução Total: {task['tempo_exec']:.2f}s\n"
                    f" - Chegada: {task['temp_chegada']:.2f}s\n"
                    f" - Prioridade: {priority_label} ({task['prioridade']})\n"
                )
                assigned_tasks.append(task)

            # Prevent tight loop
            is_server_busy = any(s.get_server_status()['current_capacity'] > 0 for s in self.servers)
            if self.pending_global_queue or self.priority_ready_queue or is_server_busy:
                time.sleep(0.1) 
            
            # Check exit condition
            if not self.tasks_to_complete and all(s.get_server_status()['current_capacity'] == 0 for s in self.servers):
                 break
                    
        self.end_time = time.time()
        
        print("\n--- FIM DA ATRIBUIÇÃO E PROCESSAMENTO ---")
        
        # Shutdown servers
        for server in active_servers:
            server.stop()
        
        for server in active_servers:
            server.join()