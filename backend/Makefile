ifneq (,$(wildcard ./.env))
    include .env
    export
endif
run_gunicorn:
	gunicorn --bind 0.0.0.0:${GUNICORN_PORT} config.wsgi