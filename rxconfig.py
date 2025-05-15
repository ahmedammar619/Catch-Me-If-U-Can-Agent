import reflex as rx

config = rx.Config(
    app_name="admin",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
) 