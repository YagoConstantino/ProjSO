// main_teste.cpp
#include <iostream>
#include "Escalonador.hpp"
#include "TCB.hpp"

using namespace std;

int main()
{
    // Cria 4 TCBs (usa o construtor que você já tem)
    // Depois garantimos inicio/duracao manualmente para o teste.
    TCB a(1,0,{255,0,0});
    TCB b(2,0,{0,255,0});
    TCB c(3,0,{0,0,255});
    TCB d(4,0,{255,255,0});

    // Define início e duração explicitamente para o cenário de teste
    // a chega no tempo 0 e precisa de 3 ticks
    a.inicio = 0; a.duracao = 3;
    // b chega no tempo 2 e precisa de 4 ticks
    b.inicio = 0; b.duracao = 4;
    // c chega no tempo 1 e precisa de 2 ticks
    c.inicio = 1; c.duracao = 2;
    // d chega no tempo 4 e precisa de 1 tick
    d.inicio = 2; d.duracao = 1;

    // Monta a lista (banco de TCBs)
    DataStructures::Lista<TCB*> lista;
    lista.insert_back(&a);
    lista.insert_back(&b);
    lista.insert_back(&c);
    lista.insert_back(&d);

    // Cria o escalonador: quantum=2, mode=1 (debug), algo=0 (FIFO)
    Escalonador esc(2, 1, 0, &lista);

    // Mostra status inicial
    esc.statusAtual();

    // Executa o escalonador até todas as tarefas terminarem
    esc.executar();

    // Mostra estado final das tasks
    cout << "\n=== Estado final das tasks ===\n";
    for(auto it = lista.begin(); it != lista.end(); ++it)
    {
        TCB* t = *it;
        cout << "Task " << t->id
             << " | inicio=" << t->inicio
             << " | duracao_remanescente=" << t->duracao
             << " | estado=" << t->state
             << endl;
    }

    return 0;
}
