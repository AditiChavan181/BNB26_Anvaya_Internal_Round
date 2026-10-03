# ModelLedger

ModelLedger is a prototype workspace for exploring provenance and integrity tracking for AI model artifacts. The repository is organized around a web client, a Python backend area, and an EVM smart-contract project.

> **Project status:** Early scaffold. The frontend is still the default React/Vite starter, the blockchain project contains a Hardhat `Counter` example, and the backend directories do not yet contain an implementation or dependency manifest. Model registration, artifact verification, and an end-to-end workflow are not implemented yet.

## Repository Layout

| Path             | Purpose                                                            | Current state                                                          |
| ---------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| `frontend/`      | React web client built with Vite                                   | Starter UI; development server, build, and lint scripts are configured |
| `backend/app/`   | Intended Python API, database, models, and services                | Directory structure only                                               |
| `blockchain/`    | Solidity contracts, Hardhat tests, and Ignition deployment modules | Hardhat example project containing `Counter`                           |
| `sample-assets/` | Intended sample inputs grouped by trust category                   | `trusted/`, `tampered/`, and `unknown/` folders are currently empty    |
| `docs/`          | Project documentation                                              | Currently empty                                                        |

## Prerequisites

- Node.js 22.12 or later and npm
- Git

The backend has no runnable setup yet. Python dependencies, configuration, and API startup instructions will be added when that implementation is in place.

## Run the Frontend

From the repository root:

```shell
cd frontend
npm install
npm run dev
```

Vite prints the local development URL in the terminal. Other available frontend commands are:

```shell
npm run build
npm run lint
npm run preview
```

## Test the Blockchain Project

```shell
cd blockchain
npm install
npx hardhat test
```

The tests exercise the example `Counter` contract. To deploy that example to a local simulated network:

```shell
npx hardhat ignition deploy ignition/modules/Counter.ts
```

The Hardhat configuration also defines a Sepolia network. To deploy there, configure `SEPOLIA_RPC_URL` and `SEPOLIA_PRIVATE_KEY` using Hardhat's keystore, then run:

```shell
npx hardhat keystore set SEPOLIA_RPC_URL
npx hardhat keystore set SEPOLIA_PRIVATE_KEY
npx hardhat ignition deploy --network sepolia ignition/modules/Counter.ts
```

Never commit private keys, RPC credentials, or other secrets to the repository.

## Contributing

Contributions are welcome. For substantial changes, open an issue first to discuss the intended behavior. Keep frontend changes inside `frontend/`, contract changes inside `blockchain/`, and add or update tests alongside behavior changes.

## License

No license has been specified for this repository yet. Add a `LICENSE` file before distributing or reusing the project publicly.
