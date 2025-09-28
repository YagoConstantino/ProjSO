#pragma once
#include <iostream>
#include "Lista/Lista.hpp"
#include <queue>
#include <vector>
using namespace std;
class TCB;
class Escalonador
{
private:
    int time;
    int quantum;
    // mode = 1 Debug, mode = 0 Normal
    int mode;

    TCB* taskAtual;

    //algo = 0 FIFO, algo = 1 SRTF, algo = 2 PrioE;
    int algo;
    std::vector<int> inicioDasTask;
    DataStructures::Lista<TCB*> *list;
    DataStructures::Lista<TCB*> *listaProntas;
    
public:
    Escalonador(int q,int m, int al);
    Escalonador(int q,int m,int al,DataStructures::Lista<TCB*> *novaLista);
    ~Escalonador();
    void InserirLista(DataStructures::Lista<TCB*> novaLista);
    void preemptar();
    void verificarProntas();
    void limparListaProntas();
    void FIFO();
    void SRTF();
    void statusAtual();
    void tick();
    void executar();

};
