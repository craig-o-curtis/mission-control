import uvicorn


# This is needed because uvicorn.run() is a blocking call, and we want to be able to
# run the app in a separate thread for testing purposes. If we didn't have this,
# the app would block the test runner and prevent tests from running.
def main() -> None:
    uvicorn.run("missions_api.missions:app", reload=True)
