#include <iostream>
#include "Lista/Lista.hpp"
#include <array>
using namespace std;

/*
Disclaimer
parte da estrutura desse TCB foi inspirado no modelo de task do projeto PPOS do professor Mazieiro da UFPR
*/
class TCB
{
    //Variáveis
    public:
        //Classe para a task do escalonador
        int id;
        //valores para armazenar a cor de cada task
        array<int,3> RGB ;

        //indica o estado de uma tarefa (ver defines no final do arquivo ppos.h):
        //1 - nova, 2 - pronta, 3 - executando, 4 - suspensa, 5 - terminada
        // da para mudar para char (n - nova, r - pronta, x - executando, s - suspensa, e - terminada)
        int state;

        //códigos / timers / prioridades / estatísticas
        int exitCode;
        int awakeTime; //quando deve ser acordada (timestamp ou tick)

        //campos adicionais
        int prio_s =  0;     // prioridade estática
        int prio_d = 0;     // prioridade dinâmica
        //int quantum = 20;   // quantum padrão = 20

        int inicio = 0;
        int fim = 0;
        int inicioExec = 0;
        int fimExec = 0;
        int somaExec = 0;
        int ativacoes = 0;
        int duracao = 0;
    /////////////////////////////////////////////////////////
    public:
        TCB(int ID,int sta,const array<int,3>v):id(ID),state(sta),RGB(v)
        {

        }
        TCB(int ID,const array<int,3>v,int pris,int ini,int dura):
        id(ID),RGB(v),prio_s(pris),inicio(ini),duracao(dura),
        exitCode(0),awakeTime(0)
        {
            prio_d = prio_s;
            state = 1;
        }
        ~TCB(){};

    /*     // -------- GETTERS --------
    int getState() const { return state; }
    int getExitCode() const { return exitCode; }
    int getAwakeTime() const { return awakeTime; }
    int getPrioD() const { return prio_d; }
    //int getQuantum() const { return quantum; }
    int getFim() const { return fim; }
    int getInicioExec() const { return inicioExec; }
    int getFimExec() const { return fimExec; }
    int getSomaExec() const { return somaExec; }
    int getAtivacoes() const { return ativacoes; }

    // -------- SETTERS --------
    void setState(int s) { state = s; }
    void setExitCode(int code) { exitCode = code; }
    void setAwakeTime(int t) { awakeTime = t; }
    void setPrioD(int p) { prio_d = p; }
    //void setQuantum(int q) { quantum = q; }
    void setFim(int f) { fim = f; }
    void setInicioExec(int v) { inicioExec = v; }
    void setFimExec(int v) { fimExec = v; }
    void setSomaExec(int s) { somaExec = s; }
    void setAtivacoes(int a) { ativacoes = a; }
    */
     
};
