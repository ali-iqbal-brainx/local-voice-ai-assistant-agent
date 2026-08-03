from livekit.agents import WorkerOptions, cli

from .pipeline import entrypoint


def main() -> None:
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    main()
