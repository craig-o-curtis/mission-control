"""CLI entry point for checklists API."""

import uvicorn


def main() -> None:
    uvicorn.run("checklists_api.app:app", reload=True)


if __name__ == "__main__":
    main()
