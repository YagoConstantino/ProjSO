#include "Escalonador.hpp"
#include "TCB.hpp"
#include <climits> 

Escalonador::Escalonador(int q,int m, int al):
time(-1),quantum(q),mode(m),algo(al),list(),taskAtual()
{
    listaProntas = new DataStructures::Lista<TCB*>();
}
Escalonador::Escalonador(int q,int m,int al,DataStructures::Lista<TCB*> *novaLista):
time(-1),quantum(q),mode(m),algo(al),list(novaLista),taskAtual(nullptr)
{
    
    DataStructures::Lista<TCB*>::Iterator it;
    for(it = list->begin();it != list->end();++it)
    {
        inicioDasTask.push_back((*it)->inicio);
    }
    listaProntas = new DataStructures::Lista<TCB*>();

}
Escalonador::~Escalonador()
{
    if(listaProntas) {
    delete listaProntas;
    listaProntas = nullptr;
    }
    //não deletamos list pois pode ser fornecida externamente 

}
void Escalonador::InserirLista(DataStructures::Lista<TCB*> novaLista)
{

}

void Escalonador::preemptar()
{
    if(algo == 0)
    {
        FIFO();
    }

    
    if(algo == 1)
    {
        SRTF();
    }
    /*
    if(algo == 2)
    {

    }
    */
}

void Escalonador::verificarProntas()
{
    DataStructures::Lista<TCB*>::Iterator it;
    for(it = list->begin();it!= list->end();++it)
    {
        if((*it)->inicio == time)
        {
            listaProntas->insert_back(*it);
            //2 = pronta
            (*it)->state = 2;
        }
    }
}

void Escalonador::limparListaProntas()
{
    if (!listaProntas) return;

    DataStructures::Lista<TCB*>::Iterator it = listaProntas->begin();
    // percorre avançando o iterador ANTES de possivelmente remover o elemento atual
    while (it != listaProntas->end())
    {
        TCB* t = *it;
        ++it; // avança primeiro (evita invalidar o iterador que estamos usando)
        if (t && t->duracao <= 0)
        {
            // removeK vai apagar o nodo (Elemento) que contém o ponteiro t
            t->state = 5; //5 = finalizada
            listaProntas->removeK(t);
        }
    }
}

//Talvez seja válido criar uma fila so para o Fifo inves de alterar direto na lista de prontas
void Escalonador::FIFO()
{
    // se existe uma task em execução, coloca ela ao final das prontas
    if(taskAtual)
    {
        listaProntas->insert_back(taskAtual);
    }

    // seleciona a próxima (assumimos que getHead() retorna nullptr se vazio)
    if(listaProntas->getHead() != nullptr)
    {
        taskAtual = listaProntas->getHead()->getInfo();
        //3 = executando
        taskAtual->state = 3;
        listaProntas->remove_front();
    } 
    else 
    {
        taskAtual = nullptr;
    }
}

void Escalonador::SRTF()
{
    if (!listaProntas) return;            // proteção
    limparListaProntas();                 // remove prontas com duração <= 0

    // proteção: lista pode ter ficado vazia depois da limpeza
    if (listaProntas->getHead() == nullptr) return;

    DataStructures::Lista<TCB*>::Iterator it;
    int menorDur = INT_MAX;
    int menorId  = INT_MAX;
    TCB* escolhido = nullptr;

    // procura menor (duracao, id)
    for (it = listaProntas->begin(); it != listaProntas->end(); ++it)
    {
        TCB* t = *it;
        if (!t) continue;
        if (t->duracao <= 0) continue;   // ignora já terminadas
        if (t->state == 5) continue;     // ignora por estado (se estiver usando)

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

    // se existia uma task atual diferente, marca-a como pronta (sem reinserir)
    if (taskAtual)
    {
        taskAtual->state = 2; // pronta (não vamos inserir na lista de prontas aqui)
    }

    // escolhe a nova taskAtual (sem removê-la da lista de prontas)
    taskAtual = escolhido;
    taskAtual->state = 3; // executando
    
}

void Escalonador::statusAtual()
{
    cout<<"Time atual: "<<time<<" mode atual "<<mode<< " Algoritmo atual "<<algo<<endl;
}

void Escalonador::tick()
{
    time+=1;
    cout<<"Time antes "<<time-1<<" Time atual "<<time<<endl;

    if(taskAtual)
    {
        taskAtual->duracao--;
        cout<<"Task atual: "<<taskAtual->id<<" duracção restante "<<taskAtual->duracao<<endl;
        if(taskAtual->duracao <= 0)
        {
            //5 = terminada
            taskAtual->state = 5;
        }
    }
    else
    {
        cout<<"CPU ociosa nesse tick"<<endl;
    }
        
}

void Escalonador::executar()
{
    if (quantum <= 0) {
        cout << "Erro, quantum 0" << endl;
        return;
    }

    int remQuantum = quantum;

    while (true) {
        // 0) Condição de término: todas as tasks terminaram, não há task atual e fila de prontas vazia
        bool todasTerminadas = true;
        if (list) {
            for (auto it = list->begin(); it != list->end(); ++it) {
                if ((*it)->duracao > 0) { todasTerminadas = false; break; }
            }
        }

        bool prontasVazia = (listaProntas == nullptr) || (listaProntas->getHead() == nullptr);

        if (todasTerminadas && taskAtual == nullptr && prontasVazia) {
            cout << "Todas as tasks finalizadas em time " << time << endl;
            break;
        }

        // 1) contar tasks cujo inicio == time atual
        int tasksNovas = 0;
        if (list) {
            for (auto it = list->begin(); it != list->end(); ++it) {
                if ((*it)->inicio == time) tasksNovas++;
            }
        }

        // 2) inserir as tasks novas (se houver)
        if (tasksNovas > 0) {
            if (mode == 1) cout << "Chegaram " << tasksNovas << " tasks no tempo " << time << endl;

            // verifica e insere na fila de prontas; já marca estado em verificarProntas()
            verificarProntas();

            // após inserir, recomputa se a fila de prontas está vazia
            prontasVazia = (listaProntas == nullptr) || (listaProntas->getHead() == nullptr);

            // se já existe task em execução, em ALGORITMOS PREEMPTIVOS podemos preemptar.
            // MAS no FIFO (algo == 0) **não** devemos trocar a task atual por causa da chegada.
            if (taskAtual) {
                if (algo != 0) { // se não for FIFO, pré-empata por chegada (se quiser esse comportamento)
                    if (mode == 1) cout << "Preemptando devido a chegada de novas tasks (algoritmo preemptivo)\n";
                    if (!prontasVazia) {
                        preemptar();
                        remQuantum = quantum;
                    }
                } else {
                    // FIFO: chegada não preempta. Apenas log (se modo debug).
                    if (mode == 1) cout << "Chegada não preempta (FIFO): mantendo a task atual.\n";
                }
            }
        }

        // 3) se CPU livre e há prontas -> escalona
        prontasVazia = (listaProntas == nullptr) || (listaProntas->getHead() == nullptr);
        if (taskAtual == nullptr && !prontasVazia) {
            if (mode == 1) cout << "CPU estava livre — escalonando próxima task\n";
            preemptar();
            remQuantum = quantum;
        }

        // 4) executa um tick (avança tempo e decrementa duração da task atual)
        tick();

        // 5) após o tick, tratar término ou quantum zerado
        if (taskAtual) {
            if (taskAtual->duracao <= 0) {
                if (mode == 1) cout << "Task " << taskAtual->id << " terminou no tempo " << time << endl;
                taskAtual = nullptr;
                remQuantum = quantum;

                // se tiver prontas, já escalona imediatamente
                if (listaProntas && listaProntas->getHead() != nullptr) {
                    preemptar();
                    remQuantum = quantum;
                }
            } else {
                // diminui quantum restante
                remQuantum--;
                if (remQuantum <= 0) {
                    if (mode == 1) cout << "Quantum zerado em time " << time << " -> preemptando\n";
                    // só preempta se houver outra task pronta
                    if (listaProntas && listaProntas->getHead() != nullptr) {
                        preemptar(); // aqui pode usar FIFO() que vai mover taskAtual para o fim e pegar próxima
                    }
                    remQuantum = quantum;
                }
            }
        }

        // loop continua (próximo tick)
    } // fim while
}
