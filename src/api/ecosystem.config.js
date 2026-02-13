module.exports = {
  apps : [{
    name: "shark-api",
    script: "uvicorn",
    args: "api:asgi_app --port 5002",
    interpreter: "../venv/bin/python3",
    watch: false
  }]
}