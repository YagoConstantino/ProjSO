    #include "Escalonador.hpp"
    #include "TCB.hpp"
    #include <climits> 

    Escalonador::Escalonador(int q,int m, int al):
        time(-1), quantum(q), mode(m), algo(al), list(), listaProntas(), taskAtual(nullptr)
    {
        // list já é inicializada vazia por valor; listaProntas também.
    }

    Escalonador::Escalonador(int q,int m,int al,const std::list<TCB*> &novaLista):
        time(-1), quantum(q), mode(m), algo(al), list(novaLista), listaProntas(), taskAtual(nullptr)
    {
        // copia os inicios das tasks
        for(auto it = list.begin(); it != list.end(); ++it)
        {
            if (*it) inicioDasTask.push_back((*it)->inicio);
        }
    }

    Escalonador::~Escalonador()
    {
        // não precisamos deletar nada: usamos listas por valor.
        // Não deletamos as TCBs - elas são gerenciadas externamente no exemplo.
    }

    void Escalonador::InserirLista(const std::list<TCB*> &novaLista)
    {
        // insere no final da lista interna
        list.insert(list.end(), novaLista.begin(), novaLista.end());

        // atualiza vetor de inícios caso queira manter esse vetor sincronizado
        for (auto t : novaLista) {
            if (t) inicioDasTask.push_back(t->inicio);
        }
    }

    void Escalonador::preemptar()
    {
        if(algo == 0)
        {
            FIFO();
        }
        else if(algo == 1)
        {
            SRTF();
        }
        else if(algo == 2)
        {
            PRIOp();
        }
        else if(algo == 3)
        {
            RoundRobin();
        }
    }

    void Escalonador::verificarProntas()
    {
        for(auto it = list.begin(); it != list.end(); ++it)
        {
            TCB* t = *it;
            if (!t) continue;
            if(t->inicio == time)
            {
                listaProntas.push_back(t);
                // 2 = pronta
                t->state = 2;
            }
        }
    }

    void Escalonador::limparListaProntas()
    {
        // percorre e remove elementos cuja duração <= 0,
        // ajustando o state antes de remover
        for (auto it = listaProntas.begin(); it != listaProntas.end(); )
        {
            TCB* t = *it;
            if (t && t->duracao <= 0)
            {
                t->state = 5; // 5 = finalizada
                it = listaProntas.erase(it); // erase retorna próximo iterador
            }
            else
            {
                ++it;
            }
        }
    }

    void Escalonador::FIFO()
    {
        // Se existe uma task em execução e ela ainda tem duração, NÃO trocamos (FIFO é não-preemptivo).
        if (taskAtual && taskAtual->duracao > 0)
        {
            taskAtual->state = 3; // executando
            return;
        }

        // Caso contrário — CPU livre — pega a próxima da fila de prontas (se houver)
        if (!listaProntas.empty())
        {
            taskAtual = listaProntas.front();
            taskAtual->state = 3; // executando
            listaProntas.pop_front();
        }
        else
        {
            taskAtual = nullptr; // sem tarefa para executar
        }
    }

    void Escalonador::SRTF()
    {
        if (listaProntas.empty()) return;            // proteção
        limparListaProntas();                        

        if (listaProntas.empty()) return;

        int menorDur = INT_MAX;
        int menorId  = INT_MAX;
        TCB* escolhido = nullptr;

        // procura menor (duracao, id)
        for (auto t : listaProntas)
        {
            if (!t) continue;
            if (t->duracao <= 0) continue;   // ignora já terminadas
            if (t->state == 5) continue;     // ignora por estado (se estiver terminada)

            if (t->duracao < menorDur || (t->duracao == menorDur && t->id < menorId))
            {
                menorDur = t->duracao;
                menorId  = t->id;
                escolhido = t;
            }
        }

        if (!escolhido) return; // nada válido para escolher

        // se já é a task atual, apenas garante estado
        if (taskAtual == escolhido)
        {
            taskAtual->state = 3;
            return;
        }

        // se existia uma task atual diferente, marca-a como pronta 
        if (taskAtual)
        {
            taskAtual->state = 2; // pronta 
        }

        // escolhe a nova taskAtual (sem removê-la da lista de prontas)
        taskAtual = escolhido;
        taskAtual->state = 3; // executando
    }

    void Escalonador::RoundRobin()
    {
        // se existe uma task em execução, coloca ela ao final das prontas
        if(taskAtual)
        {
            listaProntas.push_back(taskAtual);
        }

        // seleciona a próxima (assumimos que front() é válido se não vazio)
        if(!listaProntas.empty())
        {
            taskAtual = listaProntas.front();
            taskAtual->state = 3; // executando
            listaProntas.pop_front();
        } 
        else 
        {
            taskAtual = nullptr;
        }
    }

    void Escalonador::PRIOp()
    {
        if(listaProntas.empty()) return;
        limparListaProntas();

        if(listaProntas.empty()) return;

        int maiorPrioridade = INT_MIN; // pode ser negativo dependendo da sua definição
        int menorID = INT_MAX;
        TCB* escolhido = nullptr;

        for (auto t : listaProntas)
        {
            if(!t) continue;
            if(t->duracao <= 0) continue;
            if(t->state == 5 || t->state == 3) continue; // ignora se já terminou ou se está executando agora

            // procura maior prio_s; em empate, menor id
            if(t->prio_s > maiorPrioridade || (t->prio_s == maiorPrioridade && t->id < menorID))
            {
                maiorPrioridade = t->prio_s;
                menorID = t->id;
                escolhido = t;
            }
        }

        // se existe uma task atual, marca ela como pronta
        if(taskAtual)
        {
            taskAtual->state = 2; // 2 = pronta 
        }

        // escolhe a nova task atual e seta o state dela como executando
        taskAtual = escolhido;
        if (taskAtual) taskAtual->state = 3;
    }

    void Escalonador::statusAtual()
    {
        std::cout<<"Time atual: "<<time<<" mode atual "<<mode<< " Algoritmo atual "<<algo<<std::endl;
    }

    void Escalonador::tick()
    {
        time += 1;

        if(taskAtual)
        {
            taskAtual->duracao--;
            std::cout<<"Task atual: "<<taskAtual->id<<" duração restante "<<taskAtual->duracao<<" Time atual "<<time<<std::endl;
            if(taskAtual->duracao <= 0)
            {
                //5 = terminada
                taskAtual->state = 5;
            }
        }
        else
        {
            std::cout<<"CPU ociosa nesse tick"<<std::endl;
        }
    }

    void Escalonador::executar()
    {
        if (quantum <= 0) {
            std::cout << "Erro, quantum 0" << std::endl;
            return;
        }

        int remQuantum = quantum;

        while (true) {
            // 0) Condição de término: todas as tasks terminaram, não há task atual e fila de prontas vazia
            bool todasTerminadas = true;
            for (auto t : list) {
                if (t && t->duracao > 0) { todasTerminadas = false; break; }
            }

            bool prontasVazia = listaProntas.empty();

            if (todasTerminadas && taskAtual == nullptr && prontasVazia) {
                std::cout << "Todas as tasks finalizadas em time " << time << std::endl;
                break;
            }

            // 1) contar tasks cujo inicio == time atual
            int tasksNovas = 0;
            for (auto t : list) {
                if (t && t->inicio == time) tasksNovas++;
            }

            // 2) inserir as tasks novas (se houver)
            if (tasksNovas > 0) {
                if (mode == 1) { /* debug: poderia logar aqui */ }

                verificarProntas();

                prontasVazia = listaProntas.empty();

                if (taskAtual) {
                    if (algo != 0) { // se não for FIFO, pré-empata por chegada
                        if (mode == 1) std::cout << "Preemptando devido a chegada de novas tasks (algoritmo preemptivo)\n";
                        if (!prontasVazia) {
                            preemptar();
                            remQuantum = quantum;
                        }
                    } else {
                        if (mode == 1) std::cout << "Chegada não preempta (FIFO): mantendo a task atual.\n";
                    }
                }
            }

            // 3) se CPU livre e há prontas -> escalona
            prontasVazia = listaProntas.empty();
            if (taskAtual == nullptr && !prontasVazia) {
                if (mode == 1) std::cout << "CPU estava livre — escalonando próxima task\n";
                preemptar();
                remQuantum = quantum;
            }

            // 4) executa um tick (avança tempo e decrementa duração da task atual)
            tick();

            // 5) após o tick, tratar término ou quantum zerado
            if (taskAtual) {
                if (taskAtual->duracao <= 0) {
                    if (mode == 1) std::cout << "Task " << taskAtual->id << " terminou no tempo " << time << std::endl;
                    taskAtual = nullptr;
                    remQuantum = quantum;

                    if (!listaProntas.empty()) {
                        preemptar();
                        remQuantum = quantum;
                    }
                } else {
                    remQuantum--;
                    if (remQuantum <= 0) {
                        if (mode == 1) std::cout << "Quantum zerado em time " << time << " -> preemptando (se o algoritmo permitir)\n";
                        if (!listaProntas.empty()) {
                            if (algo >= 2) { // 2 = PRIOp (considerado preemptivo) e 3 = RoundRobin
                                preemptar();
                            } else {
                                if (mode == 1) {
                                    if (algo == 1) std::cout << "SRTF configurado: não preempta por quantum, somente por chegada de novas tasks.\n";
                                    else if (algo == 0) std::cout << "FIFO configurado: não preempta por quantum.\n";
                                }
                            }
                        }
                        remQuantum = quantum;
                    }
                }
            }

            // loop continua (próximo tick)
        } // fim while
    }
