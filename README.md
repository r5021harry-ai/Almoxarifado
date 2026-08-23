# 📦 Sistema de Almoxarifado — Oficina

Sistema completo para controle de estoque, com retirada rápida via QR Code pelo celular
e administração completa pelo computador. Rodando 100% local na rede Wi-Fi da oficina.

## 1. O que já vem pronto neste pacote

- Banco SQLite (`database/estoque.db`) já criado e **populado com seus 394 produtos**
  (importados do relatório "286 - Consultar Produtos").
- Cada produto já foi classificado automaticamente em uma **seção** por palavra-chave
  (Ferramentas, Elétrica, Motor e Transmissão, Freio e Suspensão, Thermo King, Direção e
  Cabine, Fixação e Diversos, Pintura e Química, EPI/Segurança, Pneus e Rodas, Geral).
  **Revise a classificação na tela Produtos** — a lógica está em
  `services/import_produtos.py`, na lista `REGRAS_SECAO`, e pode ser editada livremente
  (basta rodar `python services/import_produtos.py` de novo depois de editar).
- Usuário administrador padrão: **usuário `admin`, PIN `1234`** — troque assim que possível
  na tela Usuários.

## 2. Instalação

```bash
# 1. Instale o Python 3.10+ (se ainda não tiver)
# 2. Dentro da pasta do projeto:
pip install -r requirements.txt --break-system-packages
```

## 3. Rodar o sistema

```bash
streamlit run app.py --server.address 0.0.0.0
```

O terminal vai mostrar um endereço tipo `http://192.168.0.X:8501` — esse é o endereço
que os **celulares** devem acessar (estando na mesma rede Wi-Fi do computador).
No computador, use `http://localhost:8501`.

## 4. Primeiro acesso

1. Acesse pelo computador, faça login com `admin` / `1234`.
2. Vá em **Usuários** e troque o PIN do admin / crie um usuário para cada almoxarife.
3. Vá em **Funcionários** e cadastre os solicitantes (mecânicos, auxiliares).
4. Vá em **Veículos** e cadastre as placas.
5. Vá em **Produtos** e confira/ajuste a seção, localização e estoque mínimo dos itens
   mais usados.
6. Vá em **QR Codes**, selecione os produtos e clique em "Gerar etiquetas" para imprimir
   (baixa um .zip com uma etiqueta PNG por produto, pronta pra imprimir).

## 5. Uso diário

**No celular (almoxarife fazendo retirada):**
Acesse o endereço da rede → **Nova Saída** → selecione solicitante e veículo →
aba "Ler QR Code" → tire a foto do QR Code do produto → informe a quantidade →
"Adicionar" → repita para os próximos materiais → "Confirmar Saída".

> A leitura do QR Code usa a câmera do navegador (`st.camera_input`) e decodifica a
> imagem no servidor com OpenCV — não precisa instalar nenhum app extra no celular,
> só abrir o navegador.

**No computador (administração):**
- **Entrada**: registrar chegada de mercadoria/fornecedor.
- **Requisições**: consultar/imprimir/cancelar requisições já feitas.
- **Relatórios**: exportar Excel diário, semanal, mensal, personalizado, estoque atual
  e a planilha simplificada para o **faturamento**.
- **Dashboard** (tela inicial): visão geral de estoque baixo/crítico e últimas movimentações.

## 6. Estrutura do projeto

```
almoxarifado/
├── app.py                     # login + navegação (st.navigation / views)
├── database/
│   ├── schema.sql              # estrutura das tabelas
│   ├── db.py                   # conexão + criação do banco + autenticação
│   └── estoque.db              # banco de dados (gerado)
├── data/
│   ├── produtos_raw.txt        # lista original dos 394 produtos
│   └── produtos.csv            # lista já processada com seção classificada
├── services/
│   ├── import_produtos.py      # importador + classificador por seção
│   ├── qrcode_service.py       # geração de QR Codes e etiquetas
│   ├── requisicao_service.py   # regras de saída, entrada e ajuste de estoque
│   └── excel_export.py         # geração das planilhas de relatório
├── views/                      # cada tela do sistema (st.Page, registradas em app.py)
│   ├── dashboard.py
│   ├── nova_saida.py
│   ├── entrada.py
│   ├── produtos.py
│   ├── funcionarios.py
│   ├── veiculos.py
│   ├── requisicoes.py
│   ├── relatorios.py
│   ├── qrcodes.py
│   └── usuarios.py             # só aparece no menu para usuários admin
├── uploads/produtos/           # fotos dos produtos
├── qrcodes/                    # QR Codes e etiquetas gerados
├── exports/                    # planilhas Excel geradas
└── requirements.txt
```

## 7. Próximos passos sugeridos (não incluídos ainda)

Este pacote entrega o **núcleo funcional completo**: cadastros, QR Code real,
retirada rápida com carrinho e conferência de estoque, entrada, requisições,
relatórios/Excel formatado, dashboard, login com PIN, cancelamento de requisição
com auditoria simples. Para a próxima etapa, dá pra evoluir:

- Deploy em Supabase/Postgres para acesso fora da rede local (se quiser migrar de
  SQLite local para nuvem).
- Página de QR Code hospedada (link direto por produto, para leitura por qualquer
  leitor de QR, não só pela câmera do app).
- Tela de auditoria completa (hoje só o cancelamento de requisição grava auditoria).
- Backup automático agendado do `estoque.db`.
- Refinar ainda mais a classificação por seção conforme você for revisando os 394 itens.
