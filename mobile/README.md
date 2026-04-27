# Catálogo de Peças CGI — App Android (React Native / Expo)

App mobile React Native que espelha as funcionalidades do sistema Flask de catálogo de peças.

## Pré-requisitos

- [Node.js](https://nodejs.org/) 18+
- [Expo CLI](https://docs.expo.dev/get-started/installation/): `npm install -g expo-cli`
- Servidor Flask rodando na **mesma rede Wi-Fi** do celular
- App **Expo Go** instalado no celular ([Android](https://play.google.com/store/apps/details?id=host.exp.exponent) / [iOS](https://apps.apple.com/app/expo-go/id982107779))

## Instalação

```bash
cd mobile
npm install
```

## Rodando o app

```bash
npm start
# ou
npx expo start
```

Escaneie o QR Code com o app Expo Go.

## Configuração do servidor

1. No PC, inicie o servidor Flask: `python run.py` (escuta em `0.0.0.0:8000` por padrão)
2. Descubra o IP local do PC: `ipconfig` → anote o **IPv4** (ex: `192.168.1.105`)
3. No app, na tela de Login, toque em **"Configurar endereço do servidor"** e informe `http://192.168.1.105:8000`

## Funcionalidades

| Tela | Funcionalidade |
|------|---------------|
| Login | Autenticação com usuário/senha + configuração de servidor |
| Busca (Home) | Busca por código, nome, veículo, montadora — com paginação |
| Detalhe da Peça | Galeria de imagens, aplicações agrupadas, similares, adicionar ao carrinho |
| Carrinho | Gerenciar itens, alterar quantidades, enviar pedido por WhatsApp |
| Contatos | Listar, criar, editar, excluir contatos; abrir WhatsApp direto |
| Configurações | Alterar URL do servidor, ver usuário logado, fazer logout |

## Gerando APK para instalação

```bash
# Instale EAS CLI
npm install -g eas-cli
eas login

# Configure o projeto (primeira vez)
eas build:configure

# Build APK local (sem conta Expo)
npx expo run:android
```

Ou use o **Expo Application Services (EAS)**:
```bash
eas build --platform android --profile preview
```

## Estrutura do projeto

```
mobile/
├── App.js                          # Raiz com Providers
├── src/
│   ├── api/                        # Camada HTTP (axios)
│   │   ├── client.js               # Instância axios com baseURL dinâmico
│   │   ├── auth.js                 # Login / Logout / Me
│   │   ├── products.js             # Busca e detalhes de produtos
│   │   ├── cart.js                 # Carrinho
│   │   └── contacts.js             # CRUD de contatos
│   ├── context/
│   │   ├── AuthContext.js          # Estado de autenticação
│   │   └── CartContext.js          # Estado do carrinho
│   ├── navigation/
│   │   └── AppNavigator.js         # Stack + Tab Navigator
│   ├── screens/
│   │   ├── LoginScreen.js
│   │   ├── HomeScreen.js
│   │   ├── ProductDetailScreen.js
│   │   ├── CartScreen.js
│   │   ├── ContactsScreen.js
│   │   ├── ContactFormScreen.js
│   │   └── SettingsScreen.js
│   ├── components/
│   │   ├── ProductCard.js
│   │   ├── ImageCarousel.js
│   │   ├── ApplicationsList.js
│   │   └── EmptyState.js
│   └── utils/
│       ├── storage.js              # Gerenciamento de URL do servidor
│       └── formatters.js           # Formatação de dados
```

## Endpoints Flask utilizados

Os seguintes endpoints foram adicionados em `api_routes.py`:

- `POST /api/v1/auth/login` — Login JSON
- `POST /api/v1/auth/logout` — Logout
- `GET  /api/v1/auth/me` — Usuário atual
- `GET  /api/v1/buscar?q=...` — Busca de produtos
- `GET  /api/v1/produtos/:id` — Detalhe de produto
- `GET/POST /api/v1/carrinho` — Carrinho
- `POST /api/v1/carrinho/adicionar|remover|atualizar|limpar`
- `GET/POST/PUT/DELETE /api/v1/contatos`
