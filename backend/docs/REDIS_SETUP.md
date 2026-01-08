# How to setup Redis on Railway for queue implementation

1. Open existing railway project
2. Add a new service from github, and select the same repo as the main service
3. (Optional) rename this service "worker-service"
4. Add the same variables used as the main service
5. Don't generate domain, make sure "PUBLIC NETWORKING" section is empty
6. Set the "Railway Config File" to "/railway_worker.json". The file should exist in the repo.
7. Add a new service -> database -> "Add Redis"
8. Redis service -> variables -> copy REDIS_URL
9. Go to the "worker-service" -> variables -> add new variable "REDIS_URL" and add the previous copied URL
10. Pray it works :v

## Upon running, project logs should show:
    1. (From the main service) RedisClient - Connected successfully to Redis at caboose.proxy.rlwy...
    2. (From the worker service)
        
        2025-12-15 15:41:53,464 - Q_GEN - Initializing Supabase Client...

        2025-12-15 15:41:53,523 - Q_GEN - Initializing Redis Client at caboose.proxy.rlwy.net:10297...
        
        2025-12-15 15:41:53,523 - Q_GEN - Starting Interview Generation Worker. Target interval: 7s