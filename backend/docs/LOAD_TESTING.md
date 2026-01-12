# Locust Load Testing

This directory contains load testing configuration using [Locust](https://locust.io/).

## Installation

```bash
pip install locust
```

Or add to requirements:
```bash
pip install locust gevent
```

## Quick Start

### 1. Basic Usage (Web UI)

```bash
# From the backend directory
cd Iksan-AI-Interview-Backend

# Run Locust with web UI
locust -f locustfile.py --host=http://localhost:8000

# Open browser at http://localhost:8089
```

### 2. Headless Mode (CLI)

```bash
# Run with 100 users, spawning 10 per second
locust -f locustfile.py --headless --users 100 --spawn-rate 10 -H http://localhost:8000

# Run for specific duration
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m -H http://localhost:8000
```

### 3. Using Configuration File

```bash
# Copy example config
cp locust.conf.example locust.conf

# Edit locust.conf with your settings
# Then run:
locust -f locustfile.py
```

## Test User Classes

The `locustfile.py` includes several user classes that simulate different usage patterns:

| User Class | Weight | Description |
|------------|--------|-------------|
| `AnonymousUser` | 3 | Tests public endpoints (schools, majors, roles) |
| `AuthenticatedUser` | 5 | Tests authenticated endpoints (users, teachers, students) |
| `StudentUser` | 7 | Tests student-specific endpoints (sessions, feedback) |
| `AuthStressUser` | 1 | Stress tests authentication (login/register) |
| `HeavyLoadUser` | 2 | Rapid requests for stress testing |

### Running Specific User Classes

```bash
# Run only AnonymousUser tests
locust -f locustfile.py AnonymousUser --host=http://localhost:8000

# Run only StudentUser tests
locust -f locustfile.py StudentUser --host=http://localhost:8000

# Run multiple specific users
locust -f locustfile.py AnonymousUser StudentUser --host=http://localhost:8000
```

### Using Tags

Tasks are tagged for selective execution:

```bash
# Run only public endpoint tests
locust -f locustfile.py --tags public --host=http://localhost:8000

# Run authentication tests only
locust -f locustfile.py --tags auth --host=http://localhost:8000

# Exclude heavy load tests
locust -f locustfile.py --exclude-tags heavy --host=http://localhost:8000
```

Available tags:
- `public` - Public endpoints (no auth required)
- `auth` - Authentication endpoints
- `health` - Health check endpoints
- `schools`, `majors`, `roles`, `classes` - Specific resource endpoints
- `student`, `sessions` - Student-specific endpoints
- `search` - Search functionality
- `heavy` - Intensive load tests

## Configuration

### Environment Variables

Set these for authentication tests:

```bash
export LOCUST_TEST_EMAIL="your-test-user@example.com"
export LOCUST_TEST_PASSWORD="your-test-password"
export LOCUST_BASE_EMAIL="loadtest"
export LOCUST_EMAIL_DOMAIN="example.com"
```

### Configuration File

Create `locust.conf` from the example:

```ini
# locust.conf
host = http://localhost:8000
users = 50
spawn-rate = 5
run-time = 5m
headless = true
csv = results/locust
html = results/report.html
```

## Output and Reports

### CSV Export

```bash
# Export stats to CSV files
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m \
  --csv=results/load_test -H http://localhost:8000
```

This creates:
- `results/load_test_stats.csv` - Request statistics
- `results/load_test_failures.csv` - Failed requests
- `results/load_test_stats_history.csv` - Stats over time

### HTML Report

```bash
# Generate HTML report
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m \
  --html=results/report.html -H http://localhost:8000
```

## Distributed Testing

For high-load testing, run Locust in distributed mode:

### Master Node

```bash
locust -f locustfile.py --master --host=http://localhost:8000
```

### Worker Nodes

```bash
# On each worker machine
locust -f locustfile.py --worker --master-host=<master-ip>
```

### Using Docker

```bash
# Pull Locust image
docker pull locustio/locust

# Run master
docker run -p 8089:8089 -v $PWD:/mnt/locust locustio/locust \
  -f /mnt/locust/locustfile.py --master -H http://host.docker.internal:8000

# Run workers
docker run -v $PWD:/mnt/locust locustio/locust \
  -f /mnt/locust/locustfile.py --worker --master-host=<master-ip>
```

## Test Scenarios

### Scenario 1: Light Load (Smoke Test)

```bash
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 1m \
  -H http://localhost:8000
```

### Scenario 2: Normal Load

```bash
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m \
  -H http://localhost:8000
```

### Scenario 3: Stress Test

```bash
locust -f locustfile.py --headless --users 200 --spawn-rate 20 --run-time 10m \
  -H http://localhost:8000
```

### Scenario 4: Spike Test

```bash
# Start with low load, then spike
locust -f locustfile.py --headless --users 500 --spawn-rate 100 --run-time 2m \
  -H http://localhost:8000
```

### Scenario 5: Soak Test (Endurance)

```bash
locust -f locustfile.py --headless --users 30 --spawn-rate 5 --run-time 1h \
  -H http://localhost:8000
```

## Interpreting Results

Key metrics to monitor:

| Metric | Description | Good Value |
|--------|-------------|------------|
| RPS | Requests per second | Depends on server capacity |
| Response Time (Median) | 50th percentile | < 200ms for API |
| Response Time (95th) | 95th percentile | < 500ms |
| Failure Rate | % of failed requests | < 1% |

### Warning Signs

- **Response time increasing linearly** - Server approaching capacity
- **Response time spiking** - Server overloaded
- **High failure rate** - System unstable
- **RPS plateauing** - Bottleneck reached

## Troubleshooting

### Rate Limiting Issues

The backend has rate limiting enabled. If you see many 429 errors:

1. Reduce spawn rate
2. Increase wait_time between tasks
3. Use the `--tags` option to avoid auth-heavy tests

### Connection Errors

```bash
# Increase connection pool
export LOCUST_USERS=100
# Or use fewer workers with more users each
```

### Memory Issues

For large tests, run workers on separate machines or use:

```bash
# Use FastHttpUser for better performance (modify locustfile.py)
from locust import FastHttpUser
```

## Best Practices

1. **Start small** - Begin with 10 users and scale up
2. **Monitor server** - Watch CPU, memory, and database connections
3. **Use realistic data** - Test with production-like data volumes
4. **Test incrementally** - Gradually increase load to find breaking points
5. **Document baselines** - Record baseline performance for comparison
6. **Test regularly** - Run load tests in CI/CD pipeline
