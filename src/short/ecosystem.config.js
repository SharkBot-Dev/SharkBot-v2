module.exports = {
  apps : [{
    name: "shorturl",
    script: "uvicorn",
    args: "main:asgi_app --port 3116",
    interpreter: "../venv/bin/python3",
    watch: false
  }]
}