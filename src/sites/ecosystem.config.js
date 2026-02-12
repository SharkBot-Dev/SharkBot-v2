module.exports = {
  apps : [{
    name: "shark-sites",
    script: "uvicorn",
    args: "main:asgi_app --port 5000",
    interpreter: "../venv/bin/python3",
    watch: false
  }]
}