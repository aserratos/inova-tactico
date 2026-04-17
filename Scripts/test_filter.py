from app import create_app
app = create_app()
print("Filters in app:", app.jinja_env.filters.keys())
if 'datetime_format' in app.jinja_env.filters:
    print("SUCCESS: datetime_format filter is present.")
else:
    print("FAILURE: datetime_format filter is NOT present.")
