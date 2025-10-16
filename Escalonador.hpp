#pragma once
#include <iostream>
#include <vector>
#include <list>

class TCB;

class Escalonador
{
private:
    int time;
    int quantum;
    // mode = 1 Debug, mode = 0 Normal
    int mode;

    TCB* taskAtual;

    // algo = 0 FIFO, algo = 1 SRTF, algo = 2 PRIOp;
    int algo;
    std::vector<int> inicioDasTask;

    // listas usando STL por valor
    std::list<TCB*> list;
    std::list<TCB*> listaProntas;
    
public:
    // construtores / destrutor
    Escalonador(int q, int m, int al);
    Escalonador(int q, int m, int al, const std::list<TCB*>& novaLista);
    ~Escalonador();

    // métodos
    void InserirLista(const std::list<TCB*>& novaLista);
    void preemptar();
    void verificarProntas();
    void limparListaProntas();
    void FIFO();
    void SRTF();
    void RoundRobin();
    void PRIOp();
    void statusAtual();
    void tick();
    void executar();
};
