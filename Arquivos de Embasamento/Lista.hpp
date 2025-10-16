#ifndef _LISTA_HPP
#define _LISTA_HPP

#include <iostream>

namespace DataStructures
{
    template <typename T>
    class Lista
    {
        public:
        /////////////////////////////////////////// Classe Elemento//////////////////////////////////////////
            class Elemento
            {
                private:
                    T info;
                    Elemento *next;
                    Elemento *prev;

                public:
                    Elemento(Elemento*n = nullptr,Elemento*p = nullptr,T inf = nullptr):next(n),prev(p),info(inf){}
                    Elemento(Elemento &el):next(el.next),prev(el.prev),info(el.info){} 
                    ~Elemento()
                    {
                        next = nullptr;
                        prev = nullptr;
                    }

                    void setNext(Elemento *ne){next = ne;}
                    void setPrev(Elemento *pr) {prev = pr;}
                    void setInfo(T inf){info = inf;}

                    Elemento *getNext() const {return next;}
                    Elemento *getPrev() const {return prev;}
                    T getInfo(){return info;} 
            };

            //Class Iterator

            class Iterator
            {
                private:
                    Elemento* current;

                public:
                    Iterator(Elemento *cabeca = nullptr):current(cabeca){};
                    Iterator(Iterator *it):current(it->getCurrent()){};
                    ~Iterator(){};

                    Elemento* getCurrent()const{return current;}

                    T operator*() const { return current->getInfo(); }
                    T& operator->() const { return &current->getInfo(); }

                    // ++Prefixo 
                    Iterator& operator++() {
                        current = current->getNext();
                        return *this;
                    }
                  
                    bool operator==(const Iterator& other)const {return current == other.current;};
                    bool operator!=(const Iterator& other)const {return current != other.current;};
            };
        
            ////////////Metodos da Lista////////////
            Lista() : head(nullptr), tail(nullptr), size(0) {}

            ~Lista() { limpar(); }

            void insert_front(T Tipo);
            void insert_back(T Tipo);
            void remove_front();
            void remove_back();
            std::size_t getSize() const { return size; }
            void limpar();
            bool empty()const {return getSize() == 0;};

            Elemento* getHead() const { return head; }
            Elemento* getTail() const { return tail; }
            void setHead(Elemento* elem) { head = elem; }
            void setTail(Elemento* elem) { tail = elem; }

            void operator--() { if (size > 0) size--; }
            Elemento* operator[](int i);

            Iterator begin(){ return Iterator(head); }
            Iterator end(){return Iterator(); }

            Iterator begin()const { return Iterator(head); }
            Iterator end()const { return Iterator();}


            //////////Metodos Uteis://///////////////////////
            const bool inList(T data);
            Lista* merge(Lista *B);
            const bool similar(Lista *B);
            Lista *copy()const;
            int position (T data);
            bool removeK(T K);
            void reverterLista();



        private:
            Elemento *head;
            Elemento *tail;
            std::size_t size;
    };

    template <typename T>
    inline void Lista<T>::insert_front(T Tipo)
    {
        Elemento *novo = new Elemento(nullptr,nullptr,Tipo);

        if(head == nullptr && tail == nullptr)
        {
            head = novo;
            tail = novo;
        }
        else
        {
            novo->setNext(head);
            head->setPrev(novo);
            head = novo;
        }
        size++;
    }

    template <typename T>
    inline void Lista<T>::insert_back(T Tipo)
    {
         Elemento *novo = new Elemento(nullptr,nullptr,Tipo);

        if(head == nullptr && tail == nullptr)
        {
            head = novo;
            tail = novo;
        }
        else
        {
            novo->setPrev(tail);
            tail->setNext(novo);
            tail = novo;
        }
        size++;
    }

    template <typename T>
    inline void Lista<T>::remove_front()
    {
        if(head == nullptr || size == 0) return;

        Elemento* aux = head;
        head = head->getNext();

        if (head) {
            head->setPrev(nullptr);
        }
        else {
            tail = nullptr; // Lista ficou vazia
        }

        delete aux;
        size--;
    }
    template <typename T>
    inline void Lista<T>::remove_back()
    {
        if(tail == nullptr || size == 0) return;

        Elemento* aux = tail;

        tail = tail->getPrev();
        if(tail)
        {
            tail->setNext(nullptr);
        }
        else
        {
            head = nullptr;
        }

        delete aux;
        size--;

    }
    
    template <typename T>
    inline void Lista<T>::limpar()
    {
        Elemento* atual = head;
        while (atual) 
        {
            Elemento* prox = atual->getNext();
            delete atual;
            atual = nullptr;
            atual = prox;
        }
        head = tail = nullptr;
        size = 0;
    }

    template <typename T>
    inline typename Lista<T>::Elemento* Lista<T>::operator[](int i)
    {
        if (i < 0 || i >= size) 
            return nullptr;

        Elemento *aux = head;
        int iterador = 0;

        while (iterador != i)
        {
            aux = aux->getNext();
            ++iterador;           
        }
        return aux;
    }
    template <typename T>
    inline const bool Lista<T>::inList(T data)
    {
        Iterator it;

        for(it = begin();it != end();++it)
        {
            if((*it) == data) return true;
        }
        
        return false;
    }
    template <typename T>
    inline Lista<T> *Lista<T>::merge(Lista<T> *B)
    {
        if(B == nullptr || B->getHead()==nullptr)
        {
            printf("Erro Lista B Nula ou Vazia\n");
            return this;
        }

        if(head == nullptr)
        {
            head = B->getHead();
            tail = B->getTail();
            size = B->getSize();
        }
        else
        {
            tail->setNext(B->getHead());
            B->getHead()->setPrev(tail);
            size += B->getSize();
            tail = B->getTail();
        }

        B->head = nullptr;
        B->tail = nullptr;
        B->size = 0;
        
        return this;
    }
    template <typename T>
    inline const bool Lista<T>::similar(Lista<T> *B)
    {
        if(size != B->getSize()) return false;
        Iterator itA,itB;

        for(itA = begin(),itB = B->begin();itA!= end(),itB != B->end();++itA,++itB)
        {
            if(*itA != *itB) return false;
        }
        return true;
    }

    template <typename T>
    inline Lista<T> *Lista<T>::copy()const
    {
        Iterator it;

        Lista<T> *nova = new Lista<T>();
        for(it = begin();it!= end();++it)
        {
            nova->insert_back(*it);
        }
        return nova;
    }
    template <typename T>
    inline int Lista<T>::position(T data)
    {
        Iterator it = begin();
        int cont = 0;
        while(it != end())
        {
            if((*it) == data ) return cont;
            cont++;
            ++it;
        }
        return -1;
    }
    template <typename T>
    inline bool Lista<T>::removeK(T K)
    {
    
        if (!head) 
            return false;

        Elemento* atual = head;
        while (atual) 
        {
            if (atual->getInfo() == K) 
            {
    
                if (atual == head) 
                {
                    head = head->getNext();
                    if (head) head->setPrev(nullptr);
                    else tail = nullptr;
                }
            
                else if (atual == tail) {
                    tail = tail->getPrev();
                    tail->setNext(nullptr);
                }
                else {
                    Elemento* ant = atual->getPrev();
                    Elemento* prox = atual->getNext();
                    ant->setNext(prox);
                    prox->setPrev(ant);
                }

                delete atual;
                --size;
                return true;
            }
            atual = atual->getNext();
        }
        return false;
    }
    template <typename T>
    inline void Lista<T>::reverterLista()
    {
        Elemento* atual = head;
        
        while(atual != nullptr)
        {
            Elemento *prox = atual->getNext();
            atual->setNext(atual->getPrev());
            atual->setPrev(prox);
            atual = prox;
        }
        Elemento *aux = head;
        head = tail;
        tail = aux;
    }
}
#endif