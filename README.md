**Trabalho SO**

Este repositório contém uma implementação simples de um gerenciador de tarefas/servidores para estudo de escalonamento (algoritmos como Round-Robin, SJF e Prioridade). Os scripts principais são:

- `main.py` — ponto de entrada/auxiliar (dependendo da implementação local).
- `master.py` — contém a classe `TaskManager` e lógica de escalonamento.
- `server.py` — definição de servidores que processam tarefas (threads).
- `tasks.json` — arquivo de tarefas de exemplo usado pelo sistema.

**Requisitos**
- Python 3.8+ (recomendado 3.10+)
- `colors.py` que já está no repositório e psutil.

**Instalação (opcional)**

Recomenda-se usar um ambiente virtual para isolar dependências.

PowerShell (Windows):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.bat
pip install --upgrade pip
pip install psutil
```

**Uso / Execução**

Os scripts podem ser executados diretamente com Python. Os comandos abaixo são exemplos genéricos; ajuste conforme sua necessidade.

PowerShell:

```powershell
# Executar o main com o modelo desejado
python main.py rr           # Round Robin
python main.py sjf          # Shortest Job First
python main.py priority     # Priority Scheduling
```
**Formato e edição de `tasks.json`**

O arquivo `tasks.json` contém as tarefas que o sistema escalona. Ele costuma incluir, por tarefa, campos como:

- `id`: identificador único
- `temp_chegada`: tempo de chegada relativo ao início (segundos)
- `tempo_exec`: tempo de execução estimado (segundos)

Exemplo mínimo (JSON):

```json
{
    "servidores": [
        {"id": 1, "capacidade": 3},
        {"id": 2, "capacidade": 2},
        {"id": 3, "capacidade": 1}
    ],
    "requisicoes": [
        {"id": 101, "tipo": "visao_computacional", "prioridade": 1, "tempo_exec": 8, "temp_chegada" : 3},
        {"id": 102, "tipo": "nlp", "prioridade": 3, "tempo_exec": 3, "temp_chegada" : 6},
        {"id": 103, "tipo": "voz", "prioridade": 2, "tempo_exec": 5, "temp_chegada" : 0}
    ]
}
```

Edite `tasks.json` para ajustar cargas e testar diferentes cenários de escalonamento.

**Parâmetros de escalonamento**

No `master.py` existem referências a arquiteturas suportadas, por exemplo:

- `rr` — Round-Robin (preemptivo, com `quantum` configurável)
- `sjf` — Shortest Job First (não-preemptivo)
- `priority` —  Priority Scheduling (não-preemptivo)

Você pode alterar `TaskManager(arquitecture=...)` conforme necessário ao instanciar o gerenciador para testar cada algoritmo.

**Métricas e saídas**

Ao final da execução, `TaskManager` imprime um resumo com métricas como:

- Tempo médio de resposta
- Utilização média da CPU (estimada)
- Taxa de espera máxima (calculada dinamicamente)
- Throughput (tarefas por segundo)

Essas métricas ajudam a comparar comportamento entre algoritmos e configurações.

**Depuração e resolução de problemas**

- Para problemas de sincronização entre threads, verifique o uso de locks (`completion_lock`) em `master.py`.

**Executando um teste simples**

1. Ajuste `tasks.json` com 3–5 tarefas curtas.
2. Execute `python main.py (rr, sjf ou priority)`.
3. Observe a saída no console e compare os resumos entre execuções alterando a arquitetura usada.