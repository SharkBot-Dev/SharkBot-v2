module.exports = {
  apps : [{
    name: "shark-youtube",
    script: "uvicorn",
    args: "main:asgi_app --port 6010",
    interpreter: "../venv/bin/python3",
    watch: false
  }]
}