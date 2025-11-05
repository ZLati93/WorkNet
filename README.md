"# WorkNet"
WorkNet/
│
├── frontend-client/           # Interface React pour les clients
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/          # Appels Axios vers Node.js
│   │   └── App.js
│   └── package.json
│
├── frontend-freelancer/       # Interface React pour les freelances
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/          # Appels Axios vers Node.js
│   │   └── App.js
│   └── package.json
│
├── backend-node/              # Passerelle Node.js
│   ├── routes/
│   │   ├── gigs.js
│   │   ├── users.js
│   │   └── orders.js
│   ├── rpc-client/            # Client RPC pour appeler Python
│   │   └── rpcClient.js
│   ├── server.js
│   └── package.json
│
├── rpc-server/                # Serveur RPC Python
│   ├── server.py              # Implémentation XML-RPC/gRPC
│   ├── services/
│   │   ├── users_service.py
│   │   ├── gigs_service.py
│   │   └── orders_service.py
│   └── requirements.txt
│
├── database/                  # Couche base de données
│   ├── models/
│   │   ├── userModel.js
│   │   ├── gigModel.js
│   │   └── orderModel.js
│   └── dbConfig.js
│
├── integration-qa/            # Tests et intégration
│   ├── tests/
│   │   ├── rpc_tests.py
│   │   └── integration_tests.js
│   └── docker-compose.yml     # Simulation distribuée
│
├── docs/
│   ├── report.docx
│   ├── report.pdf
│   └── presentation.pptx
│
└── README.md
