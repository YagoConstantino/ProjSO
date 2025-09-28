#include <iostream>
#include "Lista.hpp"  

using namespace DataStructures;

int main()
{
    Lista<int> lista;
    Lista<int> listaB;
    listaB.insert_back(21);
    listaB.insert_back(29);
    listaB.insert_back(32);

    // Inserindo alguns valores
    lista.insert_back(10);
    lista.insert_back(20);
    lista.insert_back(30);
    lista.insert_back(22);
    lista.insert_back(17);
    lista.insert_back(36);
    lista.insert_back(8);
    lista.insert_front(5);

    std::cout << "Tamanho da lista: " << lista.getSize() << "\n";
    std::cout<< "Contem 10 "<<lista.inList(10) << " Nao contem 35 "<<lista.inList(35)<<std::endl;

    // Acessando via operator[]
    for (int i = 0; i < lista.getSize(); ++i)
    {
        auto el = lista[i];
        if (el)
            std::cout << "Elemento [" << i << "] = " << lista[i]->getInfo() << "\n";
        else
            std::cout << "Elemento [" << i << "] = nullptr\n";
    }

    std::cout << "Testando iteração com range-based for (Iterator):\n\n";
    Lista<int>::Iterator it;
    for(it = lista.begin();it!=lista.end();++it)
    {
        std::cout<<(*it)<<std::endl;
    }
    std::cout<<std::endl<<std::endl;

    lista.merge(&listaB);
    for (auto val : lista) std::cout << val << " "<<std::endl<<std::endl;

    Lista<int> *C = lista.copy();
    for(auto val:*C)std::cout << val << " "<<std::endl;

    std::cout<< "Lista C Similar a lista ???   "<<lista.similar(C)<<std::endl;

    // Testando acesso fora de faixa
    if (lista[lista.getSize()] == nullptr)
        std::cout << "\n\nAcesso fora de faixa corretamente retorna nullptr\n";

    C->removeK(22);
    C->removeK(36);
    C->removeK(17);

    for(auto val:*C)std::cout << val << " "<<std::endl<<std::endl;
    C->reverterLista();
    for(auto val:*C)std::cout << val << " "<<std::endl;


    // Teste de limpar
    lista.limpar();
    std::cout << "Após limpar(), getSize() = " << lista.getSize() << "\n\n";
    


 

    return 0;
}
