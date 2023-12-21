import os
import time

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GRAPHQL_ENDPOINT = os.environ.get("GITHUB_GRAPHQL_ENDPOINT")


def check_execute(fn):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration for {fn.__name__} is {toc - tic:0.4f} seconds")
        return result

    return wrapper


def main():
    ...


if __name__ == "__main__":
    main()
