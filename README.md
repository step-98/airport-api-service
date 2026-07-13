# ✈️ Airport Api service

A Django REST Framework API for managing flight operations - airports, routes, airplanes, crews, flights and ticket booking with JWT authentication and Swagger/Redoc documentation

## Features

- **JWT authentication** (access/refresh tokens via `djangorestframework-simplejwt`)
- **Custom user model** with email-based login (no username field)
- **Flight management**: airports, routes, airplanes (with type and image upload), crew, and flights
- **Ticket booking**: order-based ticket creation with seat validation
  - Prevents seat overbooking within a single order
  - Prevents seat conflicts against already booked tickets on the same flight
- **Role-based permissions**: staff can manage reference data; authenticated users get read access and can manage their own orders
- **Filtering**: routes and flights can be filtered by source/destination city; flights also by route and departure time
- **Auto-generated API docs**: Swagger UI and Redoc via `drf-spectacular`
- **Dockerized**: runs with PostgreSQL out of the box via Docker Compose

## Data Model Overview
 
- **Airport** — name and closest city
- **Route** — source and destination airport, distance
- **AirplaneType** / **Airplane** — airplane specs (rows, seats per row, type, image)
- **Crew** — crew members, linked to flights (many-to-many)
- **Flight** — route + airplane + crew + schedule
- **Order** — a user's booking, containing one or more tickets
- **Ticket** — a specific seat (row, seat) on a flight, tied to an order; seat and row are validated against the airplane's capacity, and duplicate seat bookings are rejected

## Installation
 
### 1. Get the code from GitHub
 
```bash
git clone https://github.com/<your-username>/airport_api_service.git
cd airport_api_service
```
 
### 2. Create a `.env` file
 
Create a `.env` file in the project root (used both by Docker and by local runs):
 
```env
POSTGRES_DB=terminal
POSTGRES_USER=terminal
POSTGRES_PASSWORD=terminal
POSTGRES_HOST=terminal_db
POSTGRES_PORT=5432
PGDATA=/var/lib/postgresql/data
 
SECRET_KEY=your-secret-key-here
DEBUG=True
```


## Running the Project
 
You can run the project either with Docker (recommended, no local Postgres/Python setup needed) or directly on your machine.
 
### Option A — With Docker
 
```bash
docker compose up --build
```
 
This will:
- Start a PostgreSQL container
- Wait for the database to be ready
- Apply migrations
- Start the development server at `http://localhost:8000`
Create a superuser (optional, for Django admin):
 
```bash
docker compose exec terminal python manage.py createsuperuser
```

### Option B — Without Docker
 
Requires Python 3.12 and a running PostgreSQL instance on your machine.
 
```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
 
# 2. Install dependencies
pip install -r requirements.txt
 
# 3. Make sure PostgreSQL is running locally, and .env has:
#    POSTGRES_HOST=localhost
 
# 4. Apply migrations
python manage.py migrate
 
# 5. (Optional) create a superuser for Django admin
python manage.py createsuperuser
 
# 6. Run the development server
python manage.py runserver
```
 
The API will be available at `http://localhost:8000`.

## Getting Access (Create a User & Get a Token)

    - create user via /api/user/register
    - get access token via /api/user/token


## Loading Sample Data (optional)
 
To quickly populate the database with demo airports, routes, airplanes, flights and tickets:
 
> ⚠️ Run this on a **fresh database**, right after `migrate`, and **before** registering any other users — the fixture assumes a user with `id=1` already exists (it's used as the owner of the sample orders).
 
```bash
# 1. Create the first user (via Docker)
docker compose exec terminal python manage.py createsuperuser
 
# 2. Load the sample data
docker compose exec terminal python manage.py loaddata sample_data
```
 
Without Docker, run the same commands without the `docker compose exec terminal` prefix.

## Running Tests
 
```bash
docker compose exec terminal python manage.py test
```

## Notes
 
- Media files (e.g. airplane images) are stored in a persistent Docker volume mounted at `/app/media`.
- The project uses PostgreSQL in all environments (including local development via Docker) rather than SQLite.
