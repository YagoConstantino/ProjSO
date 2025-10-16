// main_teste.cpp
#include <iostream>
#include <list>
#include "Escalonador.hpp"
#include "TCB.hpp"

using namespace std;

int main()
{
    TCB a(1,0,{255,0,0});
    TCB b(2,0,{0,255,0});
    TCB c(3,0,{0,0,255});
    TCB d(4,0,{255,255,0});

    a.inicio = 0; a.duracao = 3;
    b.inicio = 0; b.duracao = 4;
    c.inicio = 1; c.duracao = 2;
    d.inicio = 2; d.duracao = 1;

    // Monta a lista (banco de TCBs) usando std::list
    std::list<TCB*> lista;
    lista.push_back(&a);
    lista.push_back(&b);
    lista.push_back(&c);
    lista.push_back(&d);

    // Cria o escalonador: quantum=2, mode=1 (debug), algo = 2 (PRIOp por exemplo)
    Escalonador esc(2, 1, 2, lista);

    esc.statusAtual();
    esc.executar();

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
