# Distributed Ride Assignment Service

## Overview

This project is a distributed backend system that simulates ride assignment across multiple nodes. It was built to demonstrate practical distributed systems tradeoffs between:

* **Consistency First**: coordinated assignment using quorum approval
* **Availability First**: local assignment with later synchronization

The system is deployed as multiple FastAPI services, supports persistent storage with MongoDB Atlas, and can run locally with Docker or across cloud virtual machines.

---

## Features

* Multi node ride assignment service
* Driver and ride creation APIs
* Nearest available driver selection
* Quorum based coordinated assignment
* Availability focused local assignment
* Inter node replication and synchronization
* Conflict resolution for divergent state
* MongoDB persistent storage
* Dockerized deployment
* Evaluation scripts for latency and recovery testing

---

## Tech Stack

* Python 3
* FastAPI
* Uvicorn
* HTTPX
* Pydantic
* MongoDB Atlas
* Docker / Docker Compose
* AWS EC2 (optional cloud deployment)

---

## Project Structure

```text
RIDE-REQUESTER/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── state.py
│   ├── routes/
│   │   ├── drivers.py
│   │   ├── rides.py
│   │   └── internal.py
│   └── services/
│       ├── assignment.py
│       ├── replication.py
│       └── conflict_resolution.py
├── tests/
│   └── evaluate.py
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## How It Works

### Consistency First Mode

1. A node receives an assignment request.
2. It selects the nearest available driver.
3. Peer nodes vote on the proposal.
4. The assignment commits only if quorum is reached.

### Availability First Mode

1. A node receives an assignment request.
2. It assigns locally immediately.
3. Changes are replicated afterward.
4. Conflicts are reconciled if needed.

---

## Prerequisites

Install:

* Python 3.10+
* Docker Desktop (recommended)
* MongoDB Atlas account

---

## Environment Configuration

Create a `.env` file in the project root:

```env
MONGODB_URI=your_mongodb_connection_string
DB_NAME=ride_requester_db
```

---

## Run Locally with Docker Compose

```bash
docker compose up --build
```

This starts three nodes by default:

* Node A → [http://localhost:8000](http://localhost:8000)
* Node B → [http://localhost:8001](http://localhost:8001)
* Node C → [http://localhost:8002](http://localhost:8002)

---

## API Usage

Open interactive docs in your browser:

* [http://localhost:8000/docs](http://localhost:8000/docs)
* [http://localhost:8001/docs](http://localhost:8001/docs)
* [http://localhost:8002/docs](http://localhost:8002/docs)

### Create Driver

`POST /drivers/`

Example body:

```json
{
  "driver_id": "D1",
  "name": "Alex",
  "x": 2,
  "y": 3
}
```

### Create Ride

`POST /rides/`

```json
{
  "ride_id": "R1",
  "rider_name": "Sara",
  "pickup_x": 5,
  "pickup_y": 5,
  "dropoff_x": 9,
  "dropoff_y": 2
}
```

### Assign Ride

`POST /rides/R1/assign`

### Change Mode

`PUT /rides/mode`

```json
{
  "mode": "cp"
}
```

or

```json
{
  "mode": "ap"
}
```

---

## Running Without Docker

Install dependencies:

```bash
pip install -r requirements.txt
```

Run one node:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

To simulate multiple nodes manually, run additional terminals with different `NODE_ID`, `PORT`, and `PEERS` values.

---

## Evaluation

Run the evaluation script:

```bash
python tests/evaluate.py
```

Typical tests include:

* CP latency
  n- AP latency
* Recovery time
* Failure scenarios

---

## Cloud Deployment

The system can be deployed to multiple AWS EC2 instances:

1. Launch three VMs.
2. Copy the repo to each machine.
3. Configure `.env` and peer IP addresses.
4. Install Docker.
5. Run containers.

---

## Example Use Cases

* Distributed systems demonstrations
* CAP tradeoff experiments
* Quorum logic examples
* FastAPI microservice learning
* Docker multi service practice

---

## Limitations

* Small three node cluster
* Simplified ride matching logic
* No authentication
* No load balancer
* Intended for education and experimentation

---

## Author

Tracy Erivwode
COEN 691 Final Project
Concordia University
